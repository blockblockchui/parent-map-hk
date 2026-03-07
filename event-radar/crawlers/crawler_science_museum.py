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

class ScienceMuseumCrawler(PlaywrightCrawler):
    """香港科學館活動爬蟲"""
    
    def __init__(self):
        super().__init__(
            name='香港科學館',
            base_url='https://hk.science.museum/tc/web/scm/event-calendar.html'
        )
    
    def crawl(self) -> List[Event]:
        events = []
        
        if not self.navigate(self.base_url, wait_for='.event-item, .calendar-event, [class*="event"]', timeout=60000):
            # 嘗試其他選擇器
            if not self.navigate(self.base_url, timeout=60000):
                return events
        
        # 等待頁面加載
        self.page.wait_for_timeout(3000)
        
        # 滾動加載
        self.scroll_to_load(scroll_times=3)
        
        # 尋找活動項目
        event_selectors = [
            '.event-item',
            '.calendar-event',
            '[class*="event"]',
            '.programme-item',
            '.activity-item'
        ]
        
        event_items = []
        for selector in event_selectors:
            items = self.page.query_selector_all(selector)
            if items:
                event_items = items
                print(f"  找到 {len(items)} 個活動項目 (selector: {selector})")
                break
        
        # 如果沒找到，嘗試更通用的選擇器
        if not event_items:
            # 尋找包含圖片的活動區塊
            items = self.page.query_selector_all('a[href*="Event"], a[href*="event"], .col-md-4, .col-sm-6')
            event_items = [item for item in items if item.query_selector('img')]
            print(f"  找到 {len(event_items)} 個可能活動 (通用選擇器)")
        
        for item in event_items:
            try:
                # 獲取完整文本
                item_text = item.inner_text()
                
                # 檢查是否為兒童/親子活動
                children_keywords = ['兒童', '兒童節目', 'Children', 'Kids', '親子', 'family']
                img_src = item.query_selector('img')
                if img_src:
                    src = img_src.get_attribute('src') or ''
                    if '/Children-Programme' in src or 'children' in src.lower():
                        is_children = True
                    else:
                        is_children = any(kw in item_text for kw in children_keywords)
                else:
                    is_children = any(kw in item_text for kw in children_keywords)
                
                if not is_children:
                    continue
                
                # 提取標題
                title = ''
                for title_selector in ['h3', 'h4', '.title', 'strong', 'b']:
                    title_el = item.query_selector(title_selector)
                    if title_el:
                        title = title_el.inner_text().strip()
                        if title and len(title) > 5:
                            break
                
                if not title:
                    # 從文本第一行提取
                    lines = [l.strip() for l in item_text.split('\n') if l.strip()]
                    if lines:
                        title = lines[0][:50]
                
                # 提取日期
                date_str = ''
                for date_keyword in ['日期', 'Date', '時間', 'Time']:
                    if date_keyword in item_text:
                        # 嘗試從文本中提取日期
                        import re
                        date_match = re.search(r'(\d{4})年?(\d{1,2})月(\d{1,2})日?', item_text)
                        if date_match:
                            year, month, day = date_match.groups()
                            if len(year) == 2:
                                year = '20' + year
                            date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                            break
                
                start_date, end_date = self.parse_date(date_str)
                
                # 提取連結
                source_url = self.base_url
                link_el = item.query_selector('a')
                if link_el:
                    href = link_el.get_attribute('href') or ''
                    if href:
                        if href.startswith('http'):
                            source_url = href
                        else:
                            source_url = f"https://hk.science.museum{href}"
                
                # 提取圖片
                image_url = ''
                if img_src:
                    src = img_src.get_attribute('src') or ''
                    if src:
                        if src.startswith('http'):
                            image_url = src
                        else:
                            image_url = f"https://hk.science.museum{src}"
                
                event = Event(
                    name=title[:100] if title else '香港科學館活動',
                    description=item_text[:200],
                    start_date=start_date,
                    end_date=end_date,
                    location='香港科學館',
                    organizer='康文署',
                    source_url=source_url,
                    image_url=image_url,
                    is_free=False,  # 科學館通常收費
                    category='工作坊',
                    age_range='6-12歲'
                )
                events.append(event)
                
            except Exception as e:
                print(f"    解析錯誤: {e}")
                continue
        
        print(f"  ✅ 找到 {len(events)} 個親子活動")
        return events

if __name__ == '__main__':
    print("測試香港科學館爬蟲...")
    
    with ScienceMuseumCrawler() as crawler:
        events = crawler.crawl()
    
    print(f"\n總計: {len(events)} 個活動")
    for i, e in enumerate(events[:5], 1):
        print(f"{i}. {e.name} ({e.start_date})")
        print(f"   {e.description[:100]}...")
