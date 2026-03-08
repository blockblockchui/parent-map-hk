#!/usr/bin/env python3
"""
Source: Hong Kong Youth Arts Foundation (HKYAF)
URL: https://www.hkyaf.com/events
Method: Playwright + Stealth mode (bypass Cloudflare)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import Event
from typing import List
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import re
from datetime import datetime
import time

class HKYAFStealthCrawler:
    """香港青年藝術協會活動爬蟲 - 使用 Playwright + Stealth 模式繞過 Cloudflare"""
    
    def __init__(self):
        self.name = '香港青年藝術協會'
        self.base_url = 'https://www.hkyaf.com/events?action=filter'
        self.keywords = ['親子', '兒童', '家庭', '工作坊', '小小', '家長', '學生', '青少年', 'kid', 'children', 'family']
    
    def crawl(self) -> List[Event]:
        events = []
        
        print(f"  🚀 啟動 Stealth 模式訪問: {self.base_url}")
        
        try:
            with sync_playwright() as p:
                # 啟動 Chromium (headless 模式)
                browser = p.chromium.launch(headless=True)
                
                # 建立 context 並設置 User-Agent
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = context.new_page()
                
                # ✨ 關鍵步驟：啟用 Stealth 模式
                stealth_obj = Stealth()
                stealth_obj.apply_stealth_sync(page)
                
                # 訪問網頁
                page.goto(self.base_url, wait_until="networkidle", timeout=60000)
                
                # 模擬真人隨機滾動，觸發動態加載
                page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
                time.sleep(1.5)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)
                
                # 獲取 HTML 並解析
                html_content = page.content()
                print(f"  ✅ 成功獲取頁面 ({len(html_content)} 字符)")
                
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 提取活動
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
                            is_free=True,
                            category='工作坊',
                            age_range='6-18歲'
                        )
                        
                        events.append(event)
                        print(f"      ✅ {event.start_date}")
                        
                    except Exception as e:
                        print(f"      ❌ 錯誤: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            print(f"  ❌ Stealth 模式失敗: {e}")
        
        print(f"  ✅ 總計找到 {len(events)} 個活動")
        return events
    
    def _extract_events(self, soup) -> List[dict]:
        """從 HTML 提取活動"""
        events = []
        
        # HKYAF 使用簡單 HTML 結構，查找 h2 標題和相關鏈接
        # 查找所有 h2 標題
        h2_tags = soup.find_all('h2')
        
        print(f"    找到 {len(h2_tags)} 個 h2 標題")
        
        for h2 in h2_tags:
            try:
                title = h2.get_text(strip=True)
                
                if not title or len(title) < 5:
                    continue
                
                # 檢查是否包含關鍵字
                if not any(kw in title.lower() for kw in self.keywords):
                    continue
                
                # 查找相關鏈接（通常在標題附近）
                url = self.base_url
                link_tag = h2.find_parent('a') or h2.find_next('a')
                if link_tag:
                    href = link_tag.get('href', '')
                    if href:
                        if href.startswith('/'):
                            url = f"https://www.hkyaf.com{href}"
                        elif href.startswith('http'):
                            url = href
                
                # 查找日期（可能在標題後的 p 標籤中）
                date_str = ''
                next_p = h2.find_next_sibling('p')
                if next_p:
                    date_str = next_p.get_text(strip=True)
                
                # 查找描述（查找父元素中的段落）
                description = ''
                parent = h2.find_parent(['div', 'section', 'article'])
                if parent:
                    desc_p = parent.find('p')
                    if desc_p:
                        description = desc_p.get_text(strip=True)[:200]
                
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
        if not text or text == "詳情見連結":
            return datetime.now().strftime('%Y-%m-%d')
        
        # 嘗試匹配各種日期格式
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', text)
        if match:
            year, month, day = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', text)
        if match:
            return match.group(0)
        
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', text)
        if match:
            day, month, year = match.groups()
            return f"{year}-{int(month):02d}-{int(day):02d}"
        
        return datetime.now().strftime('%Y-%m-%d')

if __name__ == '__main__':
    print("="*60)
    print("🎨 HKYAF Crawler (Stealth) - 香港青年藝術協會")
    print("="*60)
    
    crawler = HKYAFStealthCrawler()
    events = crawler.crawl()
    
    print(f"\n{'='*60}")
    print(f"📊 總計: {len(events)} 個活動")
    print('='*60)
    
    for i, e in enumerate(events, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print(f"   URL: {e.source_url}")
        print()
