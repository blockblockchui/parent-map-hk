#!/usr/bin/env python3
"""
Source: Hong Kong Science Museum
URL: https://hk.science.museum/tc/web/scm/event-calendar.html
Remarks: /image/Event/Children-Programme
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import PlaywrightCrawler, Event
from typing import List
import re

class ScienceMuseumCrawler(PlaywrightCrawler):
    """香港科學館活動爬蟲"""
    
    def __init__(self):
        super().__init__(
            name='香港科學館',
            base_url='https://hk.science.museum/tc/web/scm/event-calendar.html',
            headless=True
        )
    
    def crawl(self) -> List[Event]:
        events = []
        
        print("  導航到科學館活動頁...")
        if not self.navigate(self.base_url, timeout=60000):
            print("  ❌ 導航失敗")
            return events
        
        import time
        time.sleep(3)
        
        # 滾動加載更多活動
        self.scroll_to_load(scroll_times=3)
        
        # 獲取所有活動項目
        event_items = self._extract_events()
        
        print(f"  找到 {len(event_items)} 個活動")
        
        # 進入每個詳情頁獲取準確信息
        for i, item in enumerate(event_items[:8], 1):  # 限制8個避免太長
            try:
                print(f"    [{i}/{len(event_items)}] {item['title'][:40]}...")
                
                # 導航到詳情頁
                self.page.goto(item['url'], wait_until="networkidle", timeout=30000)
                time.sleep(2)
                
                # 提取詳情頁信息
                detail = self._extract_from_detail_page()
                
                # 合並信息
                event = Event(
                    name=item['title'],
                    description=detail.get('description') or item['title'],
                    start_date=detail.get('date') or item.get('date') or self.parse_date('')[0],
                    end_date=detail.get('date') or item.get('date') or self.parse_date('')[0],
                    location=detail.get('location') or '香港科學館',
                    organizer='香港科學館',
                    source_url=item['url'],
                    is_free=detail.get('is_free', False),  # 科學館通常收費
                    category='展覽',
                    age_range='6-12歲'
                )
                
                events.append(event)
                print(f"      ✅ {event.start_date} @ {event.location}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"      ❌ 錯誤: {e}")
                continue
        
        print(f"  ✅ 總計找到 {len(events)} 個活動")
        return events
    
    def _extract_events(self) -> List[dict]:
        """從列表頁提取活動"""
        events = []
        
        # 查找所有活動鏈接
        links = self.page.query_selector_all('a[href*="/tc/web/scm/event/"]')
        
        print(f"    找到 {len(links)} 個活動鏈接")
        
        for link in links:
            try:
                href = link.get_attribute('href') or ''
                title = link.inner_text().strip()
                
                if not title or len(title) < 5 or not href:
                    continue
                
                # 過濾非活動鏈接
                if 'event-calendar' in href or 'event.html' == href.split('/')[-1]:
                    continue
                
                # 過濾成人導向的活動（大學、專業、研討會等）
                exclude_keywords = ['大學', '專業', '研討會', 'conference', '學術', '已完結']
                if any(kw in title for kw in exclude_keywords):
                    continue
                
                # 構建完整 URL
                if href.startswith('/'):
                    url = f"https://hk.science.museum{href}"
                elif href.startswith('http'):
                    url = href
                else:
                    url = f"https://hk.science.museum/tc/web/scm/{href}"
                
                # 避免重複
                if any(e['url'] == url for e in events):
                    continue
                
                events.append({
                    'title': title[:100],
                    'url': url,
                    'date': ''
                })
                print(f"      找到: {title[:50]}")
                    
            except Exception as e:
                continue
        
        return events
    
    def _extract_from_detail_page(self) -> dict:
        """從詳情頁提取信息"""
        info = {}
        
        # 獲取頁面文本
        page_text = self.page.content()
        
        # 提取日期
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{4})/(\d{2})/(\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                year = match.group(1)
                month = int(match.group(2))
                day = int(match.group(3))
                info['date'] = f"{year}-{month:02d}-{day:02d}"
                break
        
        # 提取描述
        desc_el = self.page.query_selector('.event-desc, .description, .content, [class*="desc"]')
        if desc_el:
            info['description'] = desc_el.inner_text().strip()[:200]
        
        # 檢查是否免費
        info['is_free'] = '免費' in page_text or 'Free' in page_text
        
        # 地點默認為科學館
        info['location'] = '香港科學館'
        
        return info

if __name__ == '__main__':
    print("="*60)
    print("🎯 Science Museum Crawler - 香港科學館")
    print("="*60)
    
    with ScienceMuseumCrawler() as crawler:
        events = crawler.crawl()
    
    print(f"\n{'='*60}")
    print(f"📊 總計: {len(events)} 個活動")
    print('='*60)
    
    for i, e in enumerate(events, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print(f"   地點: {e.location}")
        print(f"   URL: {e.source_url}")
        print()
