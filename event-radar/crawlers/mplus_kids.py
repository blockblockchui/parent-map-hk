#!/usr/bin/env python3
"""
Source: M+ Museum - Kids & Families Events
URL: https://www.mplus.org.hk/api/v2/events/?locale=tc&per_page=500&page=1&audience=kids-families&date_from=2026-03-07&date_to=2026-09-03
"""

import requests
import json
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler import Event

class MPlusKidsCrawler:
    """M+ 博物館親子活動"""
    
    def __init__(self):
        self.name = 'M+博物館'
        self.api_url = 'https://www.mplus.org.hk/api/v2/events/'
    
    def crawl(self):
        events = []
        
        # 構建 API 請求
        params = {
            'locale': 'tc',
            'per_page': 500,
            'page': 1,
            'audience': 'kids-families',
            'date_from': datetime.now().strftime('%Y-%m-%d'),
            'date_to': (datetime.now().replace(year=datetime.now().year + 1)).strftime('%Y-%m-%d')
        }
        
        try:
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # M+ API 返回的數據結構
            items = data.get('items', []) if isinstance(data, dict) else data
            
            print(f"  找到 {len(items)} 個活動")
            
            for item in items:
                try:
                    # 提取標題
                    title = item.get('title', '')
                    if isinstance(title, dict):
                        title = title.get('tc', '') or title.get('zh', '') or str(title)
                    
                    if not title:
                        continue
                    
                    # 提取描述
                    description = item.get('description', '')
                    if isinstance(description, dict):
                        description = description.get('tc', '') or description.get('zh', '') or ''
                    
                    # 提取日期
                    start_date = item.get('start_date', '')[:10]  # YYYY-MM-DD
                    end_date = item.get('end_date', '')[:10] or start_date
                    
                    # 如果沒有日期，跳過
                    if not start_date:
                        continue
                    
                    # 提取地點
                    location = 'M+博物館'
                    venue = item.get('venue', {})
                    if venue:
                        venue_name = venue.get('title', '') if isinstance(venue, dict) else str(venue)
                        if venue_name:
                            location = venue_name
                    
                    # 提取連結
                    slug = item.get('slug', '')
                    source_url = f"https://www.mplus.org.hk/tc/events/{slug}" if slug else 'https://www.mplus.org.hk/tc/events'
                    
                    # 提取圖片
                    image_url = ''
                    image = item.get('image', {})
                    if image:
                        image_url = image.get('url', '')
                    
                    # 提取年齡
                    age_range = ''
                    audience = item.get('audience', [])
                    if audience:
                        age_range = ', '.join([a.get('name', '') if isinstance(a, dict) else str(a) for a in audience])
                    
                    # 是否免費
                    is_free = item.get('is_free', True)
                    
                    event = Event(
                        name=title[:100],
                        description=description[:200],
                        start_date=start_date,
                        end_date=end_date,
                        location=location[:100],
                        organizer='M+博物館',
                        source_url=source_url,
                        image_url=image_url,
                        is_free=is_free,
                        category='展覽',
                        age_range=age_range[:50]
                    )
                    events.append(event)
                    
                except Exception as e:
                    print(f"    解析錯誤: {e}")
                    continue
            
        except Exception as e:
            print(f"  ❌ API 請求失敗: {e}")
        
        print(f"  ✅ 找到 {len(events)} 個親子活動")
        return events

if __name__ == '__main__':
    crawler = MPlusKidsCrawler()
    events = crawler.crawl()
    print(f"\\n總計: {len(events)} 個活動")
    for i, e in enumerate(events[:3], 1):
        print(f"{i}. {e.name} ({e.start_date}) - {e.location}")
