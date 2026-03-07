#!/usr/bin/env python3
"""
Source: Hong Kong Palace Museum
URL: https://www.hkpm.org.hk/tc/event
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler import Event, BaseCrawler

class HKPMCrawler(BaseCrawler):
    """香港故宮文化博物館活動"""
    
    def __init__(self):
        super().__init__(
            name='香港故宮文化博物館',
            base_url='https://www.hkpm.org.hk/tc/event'
        )
    
    def crawl(self):
        events = []
        soup = self.fetch(self.base_url)
        if not soup:
            return events
        
        # 尋找活動項目
        event_items = soup.find_all('div', class_='event-item') or \
                     soup.find_all('article', class_='event') or \
                     soup.find_all('div', class_='card') or \
                     soup.find_all('article')
        
        print(f"  找到 {len(event_items)} 個活動項目")
        
        for item in event_items:
            try:
                # 提取標題
                title_tag = item.find('h2') or item.find('h3') or item.find('a', class_='title')
                if not title_tag:
                    continue
                title = title_tag.get_text(strip=True)
                
                # 檢查是否親子活動
                full_text = item.get_text()
                if not self.is_parent_child_event(title + ' ' + full_text):
                    # 故宮可能有「家庭」相關活動
                    if not any(kw in full_text.lower() for kw in ['家庭', '親子', '兒童', '工作坊']):
                        continue
                
                # 提取日期
                date_tag = item.find('span', class_='date') or \
                          item.find('div', class_='date') or \
                          item.find('time')
                date_str = date_tag.get_text(strip=True) if date_tag else ''
                start_date, end_date = self.parse_date(date_str)
                
                # 提取連結
                source_url = self.base_url
                link_tag = item.find('a')
                if link_tag:
                    href = link_tag.get('href', '')
                    if href:
                        if href.startswith('http'):
                            source_url = href
                        else:
                            source_url = f"https://www.hkpm.org.hk{href}"
                
                # 提取描述
                desc_tag = item.find('div', class_='description') or item.find('p')
                description = desc_tag.get_text(strip=True) if desc_tag else title
                
                # 提取圖片
                img_tag = item.find('img')
                image_url = ''
                if img_tag:
                    src = img_tag.get('src', '')
                    if src:
                        if src.startswith('http'):
                            image_url = src
                        else:
                            image_url = f"https://www.hkpm.org.hk{src}"
                
                event = Event(
                    name=title[:100],
                    description=description[:200],
                    start_date=start_date,
                    end_date=end_date,
                    location='香港故宮文化博物館',
                    organizer='香港故宮文化博物館',
                    source_url=source_url,
                    image_url=image_url,
                    is_free=False,  # 故宮通常收費
                    category='展覽',
                    age_range='6-12歲'
                )
                events.append(event)
                
            except Exception as e:
                print(f"    解析錯誤: {e}")
                continue
        
        print(f"  ✅ 找到 {len(events)} 個親子活動")
        return events

if __name__ == '__main__':
    crawler = HKPMCrawler()
    events = crawler.crawl()
    print(f"\\n總計: {len(events)} 個活動")
    for i, e in enumerate(events[:3], 1):
        print(f"{i}. {e.name} ({e.start_date})")
