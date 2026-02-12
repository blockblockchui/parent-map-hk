"""
Extract places from various sources (RSS, sitemaps, tag pages)
"""

import re
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

import feedparser
from bs4 import BeautifulSoup

from .config import config, SourceConfig
from .models import PlaceExtract, Place
from .http_client import HttpClient
from .cache import cache


class PlaceExtractor:
    """Extract place information from various sources"""
    
    def __init__(self):
        self.client = HttpClient()
    
    async def extract_from_source(self, source: SourceConfig) -> List[PlaceExtract]:
        """Extract places from a configured source"""
        if source.type == "rss":
            return await self._extract_from_rss(source)
        elif source.type == "sitemap":
            return await self._extract_from_sitemap(source)
        elif source.type == "tag_page":
            return await self._extract_from_tag_page(source)
        elif source.type == "manual":
            return []  # Manual sources are handled differently
        else:
            raise ValueError(f"Unknown source type: {source.type}")
    
    async def _extract_from_rss(self, source: SourceConfig) -> List[PlaceExtract]:
        """Extract from RSS feed"""
        extracts = []
        
        # Parse RSS feed
        feed = feedparser.parse(source.url)
        
        for entry in feed.entries:
            # Check recency
            published = self._parse_date(entry.get("published", entry.get("updated", "")))
            if published:
                age_days = (datetime.utcnow() - published).days
                if age_days > source.recency_window_days:
                    continue
            
            # Check keywords
            title = entry.get("title", "")
            summary = entry.get("summary", entry.get("description", ""))
            content = f"{title} {summary}"
            
            if not self._matches_keywords(content, source.category_keywords):
                continue
            
            # Extract place info
            extract = PlaceExtract(
                name=self._extract_name_from_title(title),
                source_url=entry.get("link", source.url),
                source_name=source.name,
                published_at=published,
                description=summary[:500] if summary else None,
                content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            )
            
            extracts.append(extract)
        
        return extracts
    
    async def _extract_from_sitemap(self, source: SourceConfig) -> List[PlaceExtract]:
        """Extract from sitemap.xml"""
        extracts = []
        
        async with self.client as client:
            response = await client.get(source.url)
            soup = BeautifulSoup(response.text, 'xml')
            
            urls = soup.find_all('url')
            
            for url_elem in urls:
                loc = url_elem.find('loc')
                if not loc:
                    continue
                
                url = loc.text
                
                # Check lastmod
                lastmod = url_elem.find('lastmod')
                if lastmod:
                    modified = self._parse_date(lastmod.text)
                    if modified:
                        age_days = (datetime.utcnow() - modified).days
                        if age_days > source.recency_window_days:
                            continue
                
                # Fetch and parse article
                try:
                    article_extract = await self._parse_article(
                        url, source.selectors or {}, source
                    )
                    if article_extract:
                        extracts.append(article_extract)
                except Exception as e:
                    print(f"Error parsing {url}: {e}")
                    continue
        
        return extracts
    
    async def _extract_from_tag_page(self, source: SourceConfig) -> List[PlaceExtract]:
        """Extract from tag/category listing page"""
        extracts = []
        
        async with self.client as client:
            for page in range(1, source.max_pages + 1):
                page_url = source.url
                if page > 1 and source.pagination:
                    page_url = f"{source.url}?page={page}"
                
                response = await client.get(page_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find article elements
                article_selector = source.selectors.get('article_selector', 'article')
                articles = soup.select(article_selector)
                
                for article in articles:
                    try:
                        # Extract link
                        link_selector = source.selectors.get('link_selector', 'a[href]')
                        link_elem = article.select_one(link_selector)
                        if not link_elem:
                            continue
                        
                        url = link_elem.get('href', '')
                        if not url.startswith('http'):
                            url = urljoin(source.url, url)
                        
                        # Extract date
                        date_selector = source.selectors.get('date_selector')
                        if date_selector:
                            date_elem = article.select_one(date_selector)
                            if date_elem:
                                published = self._parse_date(date_elem.get_text(strip=True))
                                if published:
                                    age_days = (datetime.utcnow() - published).days
                                    if age_days > source.recency_window_days:
                                        continue
                        
                        # Fetch article
                        article_extract = await self._parse_article(
                            url, source.selectors or {}, source
                        )
                        if article_extract:
                            extracts.append(article_extract)
                            
                    except Exception as e:
                        print(f"Error extracting article: {e}")
                        continue
        
        return extracts
    
    async def _parse_article(
        self,
        url: str,
        selectors: Dict[str, str],
        source: SourceConfig
    ) -> Optional[PlaceExtract]:
        """Parse an article page for place information"""
        
        async with self.client as client:
            response = await client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title_selector = selectors.get('title_selector', 'h1')
            title_elem = soup.select_one(title_selector)
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract content
            content_selector = selectors.get('content_selector', 'article, .content, .post')
            content_elem = soup.select_one(content_selector)
            content = content_elem.get_text(strip=True) if content_elem else ""
            
            # Check keywords
            if not self._matches_keywords(f"{title} {content}", source.category_keywords):
                return None
            
            # Extract place details using heuristics
            name = self._extract_name_from_title(title)
            address = self._extract_address(content)
            district = self._extract_district(address or content)
            region = self._district_to_region(district)
            
            # Extract price info
            price_note = self._extract_price(content)
            
            # Extract age info
            age_min, age_max = self._extract_age_range(content)
            
            # Extract website
            website = self._extract_website(content, url)
            
            # Extract description (first paragraph or meta)
            description = self._extract_description(content_elem or soup)
            
            return PlaceExtract(
                name=name,
                address=address,
                district=district,
                region=region,
                price_note=price_note,
                age_min=age_min,
                age_max=age_max,
                website_url=website,
                description=description,
                source_url=url,
                source_name=source.name,
                extracted_at=datetime.utcnow(),
                content_hash=hashlib.sha256(content.encode()).hexdigest()[:16],
            )
    
    def _extract_name_from_title(self, title: str) -> str:
        """Extract place name from article title"""
        # Remove common suffixes
        title = re.sub(r'[|\-–—].*$', '', title).strip()
        title = re.sub(r'[（(].*?[)）]', '', title).strip()
        return title[:100]
    
    def _extract_address(self, content: str) -> Optional[str]:
        """Extract address from content"""
        # Look for address patterns
        patterns = [
            r'地址[：:]\s*([^\n。]{5,100})',
            r'地址\s*[:\s]\s*([^\n。]{5,100})',
            r'位於\s*([^\n。]{5,100})',
            r'(香港(?:島|九龍|新界)[^\n。]{5,100})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _extract_district(self, text: str) -> Optional[str]:
        """Extract district from text"""
        districts = [
            "中西區", "灣仔", "東區", "南區",
            "油尖旺", "深水埗", "九龍城", "黃大仙", "觀塘",
            "荃灣", "屯門", "元朗", "北區", "大埔", "沙田", "西貢", "離島", "葵青",
        ]
        
        for district in districts:
            if district in text:
                return district
        
        return None
    
    def _district_to_region(self, district: Optional[str]) -> str:
        """Convert district to region"""
        if not district:
            return "hk-island"
        
        hk_island = ["中西區", "灣仔", "東區", "南區"]
        kowloon = ["油尖旺", "深水埗", "九龍城", "黃大仙", "觀塘"]
        
        if district in hk_island:
            return "hk-island"
        elif district in kowloon:
            return "kowloon"
        else:
            return "nt"
    
    def _extract_price(self, content: str) -> Optional[str]:
        """Extract price information"""
        patterns = [
            r'門票[：:]\s*([^\n。]{3,50})',
            r'收費[：:]\s*([^\n。]{3,50})',
            r'[$＄]\s*(\d+)(?:-\d+)?',
            r'(免費入場|免費參觀)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(0).strip()
        
        return None
    
    def _extract_age_range(self, content: str) -> tuple:
        """Extract age range from content"""
        # Look for age patterns
        patterns = [
            r'適合\s*(\d+)[-–]?(\d+)?\s*歲',
            r'(\d+)[-–](\d+)歲',
            r'(\d+)個月',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                if '個月' in match.group(0):
                    age = int(match.group(1)) / 12
                    return int(age), int(age) + 1
                else:
                    age_min = int(match.group(1))
                    age_max = int(match.group(2)) if match.group(2) else age_min + 6
                    return age_min, age_max
        
        return None, None
    
    def _extract_website(self, content: str, base_url: str) -> Optional[str]:
        """Extract website URL from content"""
        # Look for website links
        patterns = [
            r'官網[：:]\s*(https?://[^\s<>"]+)',
            r'網站[：:]\s*(https?://[^\s<>"]+)',
            r'Facebook[：:]\s*(https?://[^\s<>"]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract description from article"""
        # Try meta description
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta:
            return meta.get('content', '')[:300]
        
        # Try first paragraph
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text(strip=True)[:300]
        
        return None
    
    def _matches_keywords(self, text: str, keywords: List[str]) -> bool:
        """Check if text matches any keywords"""
        if not keywords:
            return True
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        
        return False
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
        if not date_str:
            return None
        
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%a, %d %b %Y %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str[:19], fmt)
            except:
                continue
        
        return None


class DuplicateDetector:
    """Detect and handle duplicate places"""
    
    def __init__(self):
        self.seen_hashes: set = set()
        self.seen_names: Dict[str, str] = {}  # name -> place_id
    
    def is_duplicate(self, extract: PlaceExtract, existing_places: List[Place]) -> Optional[str]:
        """
        Check if extract is a duplicate
        Returns existing place_id if duplicate, None if new
        """
        # Check content hash
        if extract.content_hash in self.seen_hashes:
            return True
        
        # Check name similarity
        normalized_name = self._normalize_name(extract.name)
        
        for place in existing_places:
            existing_normalized = self._normalize_name(place.name)
            
            # Exact match
            if normalized_name == existing_normalized:
                return place.place_id
            
            # Similar name + same district
            if (self._name_similarity(normalized_name, existing_normalized) > 0.8 and
                extract.district == place.district):
                return place.place_id
        
        return None
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison"""
        name = name.lower()
        name = re.sub(r'[^\w\s]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        return name
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity (simple Jaccard)"""
        set1 = set(name1.split())
        set2 = set(name2.split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def add_seen(self, extract: PlaceExtract, place_id: str):
        """Mark extract as seen"""
        if extract.content_hash:
            self.seen_hashes.add(extract.content_hash)
        self.seen_names[self._normalize_name(extract.name)] = place_id
