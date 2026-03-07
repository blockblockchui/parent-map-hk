#!/usr/bin/env python3
"""
Event Radar - 香港親子限時活動爬蟲
使用 BeautifulSoup + Requests（免費方案）
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import hashlib

@dataclass
class Event:
    """活動資料結構"""
    name: str
    description: str
    start_date: str  # ISO format: 2026-03-15
    end_date: str    # ISO format: 2026-03-20
    location: str
    organizer: str
    source_url: str
    image_url: Optional[str] = None
    age_range: Optional[str] = None
    is_free: bool = True
    category: str = "其他"  # workshop, exhibition, performance, camp, other
    venue_slug: Optional[str] = None  # 關聯到現有地點的 slug
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'location': self.location,
            'organizer': self.organizer,
            'source_url': self.source_url,
            'image_url': self.image_url or '',
            'age_range': self.age_range or '',
            'is_free': '是' if self.is_free else '否',
            'category': self.category,
            'venue_slug': self.venue_slug or '',
            'status': '待審核',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        }

class BaseCrawler:
    """基礎爬蟲類別"""
    
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def fetch(self, url: str) -> Optional[BeautifulSoup]:
        """抓取網頁並返回 BeautifulSoup 對象"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"❌ 抓取失敗 {url}: {e}")
            return None
    
    def parse_date(self, date_str: str) -> tuple:
        """
        解析各種日期格式
        返回: (start_date, end_date) 格式: YYYY-MM-DD
        """
        date_str = date_str.strip()
        today = datetime.now()
        
        # 嘗試匹配 "2026年3月15日"
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if match:
            year, month, day = match.groups()
            date = f"{year}-{int(month):02d}-{int(day):02d}"
            return date, date
        
        # 嘗試匹配 "15/3/2026" 或 "2026-03-15"
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', date_str)
        if match:
            day, month, year = match.groups()
            date = f"{year}-{int(month):02d}-{int(day):02d}"
            return date, date
        
        # 嘗試匹配日期範圍 "2026年3月15日至20日" 或 "15-20/3/2026"
        match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*[-至]\s*(\d{1,2})', date_str)
        if match:
            start_day, month, year, end_day = match.groups()
            start = f"{year}-{int(month):02d}-{int(start_day):02d}"
            end = f"{year}-{int(month):02d}-{int(end_day):02d}"
            return start, end
        
        # 嘗試匹配 "3月15日至4月20日"
        match = re.search(r'(\d{1,2})月(\d{1,2})日\s*[-至]\s*(\d{1,2})月(\d{1,2})日', date_str)
        if match:
            start_month, start_day, end_month, end_day = match.groups()
            year = today.year
            start = f"{year}-{int(start_month):02d}-{int(start_day):02d}"
            end = f"{year}-{int(end_month):02d}-{int(end_day):02d}"
            return start, end
        
        # 默認返回今天（無法解析時）
        return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
    
    def is_parent_child_event(self, text: str) -> bool:
        """檢查是否為親子活動"""
        keywords = [
            '親子', '兒童', 'kids', 'children', 'family', '親子活動',
            '小朋友', '幼兒', '學前', '小學', '親子工作坊'
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)
    
    def crawl(self) -> List[Event]:
        """子類別需要實作此方法"""
        raise NotImplementedError("子類別必須實作 crawl() 方法")

# LCSD 康文署爬蟲（暫時停用，等待正確 URL）
class LCSDCrawler(BaseCrawler):
    """康文署活動爬蟲"""
    
    def __init__(self):
        super().__init__(
            name='康文署',
            base_url='https://www.lcsd.gov.hk/tc/'
        )
    
    def crawl(self) -> List[Event]:
        # 暫時返回空列表，需要手動更新正確的活動頁面 URL
        print(f"⚠️ {self.name}: 暫時停用，請更新正確的活動頁面 URL")
        return []

# HKPL 圖書館爬蟲
class HKPLCrawler(BaseCrawler):
    """香港公共圖書館活動爬蟲"""
    
    def __init__(self):
        super().__init__(
            name='香港公共圖書館',
            base_url='https://www.hkpl.gov.hk/tc/extension-activities'
        )
    
    def crawl(self) -> List[Event]:
        events = []
        soup = self.fetch(self.base_url)
        if not soup:
            return events
        
        # 尋找活動項目
        event_items = soup.find_all('div', class_='activity-item')
        
        for item in event_items[:15]:
            try:
                title_tag = item.find('h3') or item.find('a', class_='title')
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                
                if not self.is_parent_child_event(title):
                    continue
                
                # 提取日期
                date_tag = item.find('span', class_='date')
                date_str = date_tag.get_text(strip=True) if date_tag else ''
                start_date, end_date = self.parse_date(date_str)
                
                # 提取圖書館名稱
                venue_tag = item.find('span', class_='library') or item.find('div', class_='venue')
                venue = venue_tag.get_text(strip=True) if venue_tag else '香港公共圖書館'
                
                # 提取連結
                link_tag = item.find('a')
                source_url = link_tag.get('href', '') if link_tag else ''
                if source_url and not source_url.startswith('http'):
                    source_url = f"https://www.hkpl.gov.hk{source_url}"
                
                event = Event(
                    name=title,
                    description=title,
                    start_date=start_date,
                    end_date=end_date,
                    location=venue,
                    organizer='香港公共圖書館',
                    source_url=source_url,
                    is_free=True,
                    category='工作坊',
                    age_range='3-12歲'
                )
                events.append(event)
                
            except Exception as e:
                print(f"解析活動時出錯: {e}")
                continue
        
        print(f"✅ {self.name}: 找到 {len(events)} 個親子活動")
        return events

# WKCD 西九文化區爬蟲
class WKCDCrawler(BaseCrawler):
    """西九文化區活動爬蟲"""
    
    def __init__(self):
        super().__init__(
            name='西九文化區',
            base_url='https://www.westkowloon.hk/tc/events'
        )
    
    def crawl(self) -> List[Event]:
        events = []
        soup = self.fetch(self.base_url)
        if not soup:
            return events
        
        # 尋找活動項目
        event_items = soup.find_all('div', class_='event-item') or soup.find_all('article')
        
        for item in event_items[:10]:
            try:
                title_tag = item.find('h2') or item.find('h3') or item.find('a', class_='title')
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                
                if not self.is_parent_child_event(title):
                    continue
                
                # 提取日期
                date_tag = item.find('span', class_='date') or item.find('time')
                date_str = date_tag.get_text(strip=True) if date_tag else ''
                start_date, end_date = self.parse_date(date_str)
                
                # 提取連結
                link_tag = item.find('a')
                source_url = link_tag.get('href', '') if link_tag else ''
                if source_url and not source_url.startswith('http'):
                    source_url = f"https://www.westkowloon.hk{source_url}"
                
                event = Event(
                    name=title,
                    description=title,
                    start_date=start_date,
                    end_date=end_date,
                    location='西九文化區',
                    organizer='西九文化區',
                    source_url=source_url,
                    is_free=True,
                    category='展覽'
                )
                events.append(event)
                
            except Exception as e:
                print(f"解析活動時出錯: {e}")
                continue
        
        print(f"✅ {self.name}: 找到 {len(events)} 個親子活動")
        return events

# 主執行函數
def run_crawlers() -> List[Event]:
    """執行所有爬蟲並返回活動列表"""
    all_events = []
    
    crawlers = [
        # LCSDCrawler(),  # 暫時停用
        HKPLCrawler(),
        WKCDCrawler(),
    ]
    
    for crawler in crawlers:
        try:
            print(f"\n🔍 開始爬取 {crawler.name}...")
            events = crawler.crawl()
            all_events.extend(events)
            time.sleep(2)  # 避免過快請求
        except Exception as e:
            print(f"❌ {crawler.name} 爬取失敗: {e}")
            continue
    
    # 去重（根據名稱+日期）
    seen = set()
    unique_events = []
    for event in all_events:
        key = f"{event.name}_{event.start_date}"
        if key not in seen:
            seen.add(key)
            unique_events.append(event)
    
    print(f"\n📊 總計: {len(unique_events)} 個獨立活動")
    return unique_events

if __name__ == '__main__':
    events = run_crawlers()
    
    # 輸出 JSON 供測試
    output = [e.to_dict() for e in events]
    with open('events_output.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 結果已保存到 events_output.json")
