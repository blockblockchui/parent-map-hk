#!/usr/bin/env python3
"""
Source: Tai Kwun
URL: https://www.taikwun.hk/zh/taikwun/press/press_release
Remarks: press-article
Method: Requests + BeautifulSoup (no JavaScript needed)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import Event
from typing import List
import requests
from bs4 import BeautifulSoup
import re

class TaikwunRequestsCrawler:
    """大館活動爬蟲 - 使用 Requests + BeautifulSoup"""
    
    def __init__(self):
        self.name = '大館'
        self.base_url = 'https://www.taikwun.hk/zh/taikwun/press/press_release'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        }
        self.keywords = ['親子', '兒童', '家庭', '工作坊', '小小', '家長', '馬', 'pony', 'kid', 'family']
    
    def crawl(self) -> List[Event]:
        events = []
        
        print(f"  獲取頁面: {self.base_url}...")
        
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"  ❌ HTTP 錯誤: {response.status_code}")
                return events
            
            print(f"  ✅ 成功獲取頁面 ({len(response.text)} 字符)")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找活動項目
            event_items = self._extract_events(soup)
            
            print(f"  找到 {len(event_items)} 個潛在活動")
            
            for i, item in enumerate(event_items[:10], 1):
                try:
                    print(f"    [{i}] {item['title'][:50]}...")
                    
                    event = Event(
                        name=item['title'],
                        description=item['title'],
                        start_date=self._extract_date(item.get('date_text', '')),
                        end_date=self._extract_date(item.get('date_text', '')),
                        location='大館',
                        organizer='大館',
                        source_url=item['url'],
                        is_free=True,
                        category='展覽',
                        age_range='6-12歲'
                    )
                    
                    events.append(event)
                    print(f"      ✅ {event.start_date}")
                    
                except Exception as e:
                    print(f"      ❌ 錯誤: {e}")
                    continue
            
        except Exception as e:
            print(f"  ❌ 請求失敗: {e}")
        
        print(f"  ✅ 總計找到 {len(events)} 個活動")
        return events
    
    def _extract_events(self, soup) -> List[dict]:
        """從 HTML 提取活動"""
        events = []
        
        # 嘗試多種選擇器
        selectors = [
            ('div', 'content'),
            ('div', 'press-release-item'),
            ('article', None),
            ('div', 'card'),
            ('a', None)
        ]
        
        items = []
        for tag, class_name in selectors:
            if class_name:
                items = soup.find_all(tag, class_=class_name)
            else:
                items = soup.find_all(tag)
            if items:
                print(f"    使用選擇器: {tag}.{class_name} ({len(items)} 個)")
                break
        
        for item in items:
            try:
                # 提取標題
                title = ''
                title_tag = item.find('h4') or item.find('h3') or item.find('h2') or item.find('a')
                if title_tag:
                    title = title_tag.get_text(strip=True)
                else:
                    title = item.get_text(strip=True).split('\n')[0][:100]
                
                if not title or len(title) < 5:
                    continue
                
                # 檢查是否包含關鍵字
                if not any(kw in title.lower() for kw in self.keywords):
                    continue
                
                # 提取鏈接
                url = self.base_url
                if title_tag and title_tag.name == 'a':
                    href = title_tag.get('href', '')
                else:
                    link_tag = item.find_parent('a') or item.find('a')
                    href = link_tag.get('href', '') if link_tag else ''
                
                if href:
                    if href.startswith('/'):
                        url = f"https://www.taikwun.hk{href}"
                    elif href.startswith('http'):
                        url = href
                
                # 嘗試提取日期
                date_text = ''
                item_text = item.get_text()
                date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', item_text)
                if date_match:
                    date_text = item_text
                
                events.append({
                    'title': title[:100],
                    'url': url,
                    'date_text': date_text
                })
                print(f"      找到: {title[:50]}")
                
            except Exception as e:
                continue
        
        return events
    
    def _extract_date(self, text: str) -> str:
        """從文本提取日期"""
        import re
        from datetime import datetime
        
        # 嘗試匹配 "2026年3月15日"
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 嘗試匹配 "2026-03-15"
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
        if match:
            return match.group(0)
        
        # 默認返回今天
        return datetime.now().strftime('%Y-%m-%d')

if __name__ == '__main__':
    print("="*60)
    print("🎭 Taikwun Crawler (Requests) - 大館")
    print("="*60)
    
    crawler = TaikwunRequestsCrawler()
    events = crawler.crawl()
    
    print(f"\n{'='*60}")
    print(f"📊 總計: {len(events)} 個活動")
    print('='*60)
    
    for i, e in enumerate(events, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print(f"   URL: {e.source_url}")
        print()
