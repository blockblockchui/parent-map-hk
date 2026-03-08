#!/usr/bin/env python3
"""
Source: Hong Kong Youth Arts Foundation (HKYAF)
URL: https://www.hkyaf.com/events
Method: Requests + BeautifulSoup
Filter URL: ?from_d=&from_m=&from_y=&to_d=&to_m=&to_y=&so=&tags=&pf=&et=&action=filter
Remarks: Drupal system with .views-row
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import Event
from typing import List
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

class HKYAFRequestsCrawler:
    """香港青年藝術協會活動爬蟲 - 使用 Requests + BeautifulSoup"""
    
    def __init__(self):
        self.name = '香港青年藝術協會'
        # 使用過濾後的 URL
        self.base_url = 'https://www.hkyaf.com/events?from_d=&from_m=&from_y=&to_d=&to_m=&to_y=&so=&tags=&pf=&et=&action=filter'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-HK,zh-TW;q=0.9,zh;q=0.8,en-US;q=0.7,en;q=0.6',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.keywords = ['親子', '兒童', '家庭', '工作坊', '學生', '青少年', 'kid', 'children', 'family']
    
    def crawl(self) -> List[Event]:
        events = []
        
        print(f"  獲取頁面: {self.base_url}...")
        
        try:
            # 使用 session 和延遲
            import time
            session = requests.Session()
            
            # 先訪問主頁獲取 cookie
            print("    訪問主頁...")
            session.get('https://www.hkyaf.com/', headers=self.headers, timeout=10)
            time.sleep(2)
            
            # 再訪問活動頁
            print("    訪問活動頁...")
            response = session.get(self.base_url, headers=self.headers, timeout=15)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                print(f"  ❌ HTTP 錯誤: {response.status_code}")
                # 嘗試不使用過濾參數
                print("    嘗試不使用過濾參數...")
                simple_url = 'https://www.hkyaf.com/events'
                response = session.get(simple_url, headers=self.headers, timeout=15)
                response.encoding = 'utf-8'
                
                if response.status_code != 200:
                    print(f"    ❌ 仍然失敗: {response.status_code}")
                    return events
            
            print(f"  ✅ 成功獲取頁面 ({len(response.text)} 字符)")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找活動項目 - Drupal 系統使用 .views-row
            event_items = self._extract_events(soup)
            
            print(f"  找到 {len(event_items)} 個潛在活動")
            
            for i, item in enumerate(event_items[:10], 1):
                try:
                    print(f"    [{i}] {item['title'][:50]}...")
                    
                    event = Event(
                        name=item['title'],
                        description=item.get('description', item['title']),
                        start_date=self._extract_date(item.get('date_str', '')),
                        end_date=self._extract_date(item.get('date_str', '')),
                        location='香港青年藝術協會',
                        organizer='香港青年藝術協會',
                        source_url=item['url'],
                        is_free=True,  # HKYAF 活動通常免費
                        category='工作坊',
                        age_range='6-18歲'
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
        
        # 使用 .views-row 選擇器（Drupal 系統）
        items = soup.select('.views-row')
        
        print(f"    找到 {len(items)} 個 .views-row 元素")
        
        for item in items:
            try:
                # 提取標題
                title = ''
                title_selectors = [
                    '.field-name-title-field h2',
                    '.title',
                    'h2',
                    'h3',
                    '.event-title'
                ]
                
                for selector in title_selectors:
                    title_tag = item.select_one(selector)
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        break
                
                if not title:
                    # 嘗試從整個元素獲取第一行文本
                    title = item.get_text(strip=True).split('\n')[0][:100]
                
                if not title or len(title) < 5:
                    continue
                
                # 提取鏈接
                url = self.base_url
                link_tag = item.select_one('a')
                if link_tag:
                    href = link_tag.get('href', '')
                    if href:
                        if href.startswith('/'):
                            url = f"https://www.hkyaf.com{href}"
                        elif href.startswith('http'):
                            url = href
                
                # 提取日期
                date_str = ''
                date_selectors = [
                    '.field-name-field-event-date',
                    '.date',
                    '.event-date'
                ]
                
                for selector in date_selectors:
                    date_tag = item.select_one(selector)
                    if date_tag:
                        date_str = date_tag.get_text(strip=True)
                        break
                
                # 檢查是否包含關鍵字
                item_text = title + ' ' + date_str + ' ' + item.get_text()
                if not any(kw in item_text.lower() for kw in self.keywords):
                    continue
                
                # 提取描述（如果有）
                description = ''
                desc_tag = item.select_one('.field-name-body, .description, .summary')
                if desc_tag:
                    description = desc_tag.get_text(strip=True)[:200]
                
                events.append({
                    'title': title[:100],
                    'url': url,
                    'date_str': date_str,
                    'description': description
                })
                print(f"      找到: {title[:50]}")
                
            except Exception as e:
                continue
        
        return events
    
    def _extract_date(self, text: str) -> str:
        """從文本提取日期"""
        if not text or text == "日期見內頁":
            return datetime.now().strftime('%Y-%m-%d')
        
        # 嘗試匹配各種日期格式
        # 2026年3月15日
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 2026-03-15
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
        if match:
            return match.group(0)
        
        # 15/03/2026
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
        if match:
            day, month, year = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        # 默認返回今天
        return datetime.now().strftime('%Y-%m-%d')

if __name__ == '__main__':
    print("="*60)
    print("🎨 HKYAF Crawler (Requests) - 香港青年藝術協會")
    print("="*60)
    
    crawler = HKYAFRequestsCrawler()
    events = crawler.crawl()
    
    print(f"\n{'='*60}")
    print(f"📊 總計: {len(events)} 個活動")
    print('='*60)
    
    for i, e in enumerate(events, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print(f"   URL: {e.source_url}")
        print()
