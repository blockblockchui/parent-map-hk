#!/usr/bin/env python3
"""
Source: Hong Kong Public Library (HKPL)
URLs: 
  - https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week
  - https://www.hkpl.gov.hk/tc/extension-activities/event-category/20414/other-talks-and-workshops
  - https://www.hkpl.gov.hk/tc/extension-activities/event-category/23433/talks-workshops
Remarks: event_title
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import PlaywrightCrawler, Event
from typing import List

class HKPLCrawler(PlaywrightCrawler):
    """香港公共圖書館活動爬蟲"""
    
    def __init__(self, url: str = None):
        base_url = url or 'https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week'
        super().__init__(name='HKPL', base_url=base_url)
        self.category_map = {
            '20414': '講座',
            '23433': '工作坊'
        }
    
    def crawl(self) -> List[Event]:
        events = []
        
        if not self.navigate(self.base_url, wait_for='.event_title, .event-item, [class*="event"]', timeout=60000):
            return events
        
        # 滾動加載更多
        self.scroll_to_load(scroll_times=5)
        
        # 尋找所有活動項目
        event_selectors = [
            '.event-item',
            '[class*="event"]',
            '.activity-item',
            '.event_title',
        ]
        
        event_items = []
        for selector in event_selectors:
            items = self.page.query_selector_all(selector)
            if items:
                event_items = items
                print(f"  找到 {len(items)} 個活動項目 (selector: {selector})")
                break
        
        for item in event_items:
            try:
                # 提取標題
                title = ''
                for title_selector in ['.event_title', 'h3', 'h2', '.title', 'a']:
                    title_el = item.query_selector(title_selector)
                    if title_el:
                        title = title_el.inner_text().strip()
                        if title:
                            break
                
                if not title:
                    continue
                
                # 檢查是否親子活動
                item_text = item.inner_text()
                if not self.is_parent_child_event(title + ' ' + item_text):
                    continue
                
                # 提取日期
                date_str = ''
                for date_selector in ['.event_date', '.date', '[class*="date"]', 'time']:
                    date_el = item.query_selector(date_selector)
                    if date_el:
                        date_str = date_el.inner_text().strip()
                        if date_str:
                            break
                
                start_date, end_date = self.parse_date(date_str)
                
                # 提取地點
                venue = '香港公共圖書館'
                for venue_selector in ['.venue', '.library', '.location', '[class*="venue"]']:
                    venue_el = item.query_selector(venue_selector)
                    if venue_el:
                        venue = venue_el.inner_text().strip()
                        if venue:
                            break
                
                # 提取連結
                source_url = self.base_url
                link_el = item.query_selector('a')
                if link_el:
                    href = link_el.get_attribute('href') or ''
                    if href:
                        if href.startswith('http'):
                            source_url = href
                        else:
                            source_url = f"https://www.hkpl.gov.hk{href}"
                
                # 提取描述
                description = title
                for desc_selector in ['.description', '.summary', 'p']:
                    desc_el = item.query_selector(desc_selector)
                    if desc_el:
                        description = desc_el.inner_text().strip()
                        if description:
                            break
                
                # 判斷類別
                category = '工作坊'
                for cat_id, cat_name in self.category_map.items():
                    if cat_id in self.base_url:
                        category = cat_name
                        break
                
                event = Event(
                    name=title[:100],
                    description=description[:200],
                    start_date=start_date,
                    end_date=end_date,
                    location=venue[:100],
                    organizer='香港公共圖書館',
                    source_url=source_url,
                    is_free=True,
                    category=category,
                    age_range='3-12歲'
                )
                events.append(event)
                
            except Exception as e:
                print(f"    解析錯誤: {e}")
                continue
        
        print(f"  ✅ 找到 {len(events)} 個親子活動")
        return events

if __name__ == '__main__':
    print("測試 HKPL 爬蟲...")
    
    urls = [
        'https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week',
        'https://www.hkpl.gov.hk/tc/extension-activities/event-category/20414/other-talks-and-workshops',
        'https://www.hkpl.gov.hk/tc/extension-activities/event-category/23433/talks-workshops'
    ]
    
    all_events = []
    for url in urls:
        print(f"\n🔍 爬取: {url}")
        with HKPLCrawler(url) as crawler:
            events = crawler.crawl()
            all_events.extend(events)
    
    print(f"\n總計: {len(all_events)} 個活動")
    for i, e in enumerate(all_events[:5], 1):
        print(f"{i}. {e.name} ({e.start_date}) - {e.location}")
