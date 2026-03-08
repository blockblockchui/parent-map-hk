#!/usr/bin/env python3
"""
Source: Hong Kong Youth Arts Foundation (HKYAF)
URL: https://www.hkyaf.com/events
Method: Playwright + Stealth mode (bypass Cloudflare)
Language: Force Traditional Chinese (zh-HK)
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
    """香港青年藝術協會活動爬蟲 - 使用 Playwright + Stealth 模式繞過 Cloudflare，強制繁體中文"""
    
    def __init__(self):
        self.name = '香港青年藝術協會'
        # 使用繁體中文 URL (zh_tw)
        self.base_url = 'https://www.hkyaf.com/zh_tw/events?action=filter'
        # 繁體中文關鍵字
        self.keywords = ['親子', '兒童', '家庭', '工作坊', '小小', '家長', '學生', '青少年', '藝術', '招募', 'kid', 'children', 'family', 'art']
    
    def crawl(self) -> List[Event]:
        events = []
        
        print(f"  🚀 啟動 Stealth 模式訪問 (繁體中文): {self.base_url}")
        
        try:
            with sync_playwright() as p:
                # 啟動 Chromium (headless 模式)
                browser = p.chromium.launch(headless=True)
                
                # ✨ 關鍵：設置 locale 為 zh-HK，確保請求繁體中文內容
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    locale="zh-HK",  # 強制繁體中文
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
                        
                        # 從列表頁提取日期 (格式: DD/MM/YYYY-DD/MM/YYYY)
                        date_str = item.get('date_str', '')
                        start_date = self._extract_date(date_str, is_end_date=False)
                        end_date = self._extract_date(date_str, is_end_date=True)
                        
                        # 進入內頁抓取詳細資訊
                        details = self._get_inner_details(context, item['url'])
                        
                        event = Event(
                            name=item['title'],
                            description=details.get('description', item['title']),
                            start_date=start_date,
                            end_date=end_date,
                            location=details.get('location', '香港青年藝術協會'),
                            organizer='香港青年藝術協會',
                            source_url=item['url'].replace('/en/', '/zh_tw/'),
                            image_url=details.get('image_url', ''),
                            is_free=details.get('is_free', True),
                            category=details.get('category', '工作坊'),
                            age_range=details.get('age_range', '6-18歲')
                        )
                        
                        events.append(event)
                        print(f"      ✅ {event.start_date} ~ {event.end_date} | {event.location}")
                        
                    except Exception as e:
                        print(f"      ❌ 錯誤: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            print(f"  ❌ Stealth 模式失敗: {e}")
        
        print(f"  ✅ 總計找到 {len(events)} 個活動")
        return events
    
    def _get_inner_details(self, context, url: str) -> dict:
        """進入內頁抓取繁中詳細資訊"""
        # 強制將連結轉向繁體中文路徑 (使用 zh_tw)
        zh_url = url.replace('/en/', '/zh_tw/').replace('/events/', '/zh_tw/events/')
        
        details = {
            "description": "",
            "date_str": "",
            "age_range": "未註明",
            "is_free": True,
            "location": "見官網",
            "image_url": "",
            "category": "藝術工作坊"
        }
        
        try:
            page = context.new_page()
            
            # 啟用 Stealth
            stealth_obj = Stealth()
            stealth_obj.apply_stealth_sync(page)
            
            page.goto(zh_url, wait_until="networkidle", timeout=30000)
            time.sleep(1.5)
            
            soup = BeautifulSoup(page.content(), 'html.parser')
            
            # 1. Description (繁中內容)
            content_div = soup.select_one('.field-name-body, .node-event .content, .description')
            if content_div:
                details["description"] = content_div.get_text(separator=" ", strip=True)[:500]
            
            # 2. Image URL
            img_tag = soup.select_one('.field-name-field-image img, .field-name-field-event-image img, .event-image img')
            if img_tag:
                img_src = img_tag.get('src', '')
                if img_src.startswith('/'):
                    details["image_url"] = f"https://www.hkyaf.com{img_src}"
                else:
                    details["image_url"] = img_src
            
            # 3. 邏輯判斷: 是否免費
            full_text = soup.get_text()
            details["is_free"] = any(x in full_text for x in ["免費", "費用全免", "Free", "free"])
            
            # 4. 年齡層提取
            age_match = re.search(r'(\d+\s*至\s*\d+歲|\d+\s*-\s*\d+歲|\d+歲或以上|適合\d+.*歲)', full_text)
            if age_match:
                details["age_range"] = age_match.group()
            
            # 5. 地點提取
            loc_tag = soup.select_one('.field-name-field-event-venue, .venue, .location')
            if loc_tag:
                details["location"] = loc_tag.get_text(strip=True)
            
            # 6. 日期提取
            date_tag = soup.select_one('.field-name-field-event-date, .date, .event-date')
            if date_tag:
                details["date_str"] = date_tag.get_text(strip=True)
            
            page.close()
            
        except Exception as e:
            print(f"      ⚠️ 內頁解析失敗: {e}")
        
        return details
    
    def _extract_events(self, soup) -> List[dict]:
        """從 HTML 提取活動"""
        events = []
        
        # HKYAF 使用簡單 HTML 結構，查找 h2 標題和相關鏈接
        h2_tags = soup.find_all('h2')
        
        print(f"    找到 {len(h2_tags)} 個 h2 標題")
        
        for h2 in h2_tags:
            try:
                title = h2.get_text(strip=True)
                
                if not title or len(title) < 5:
                    continue
                
                # 檢查是否包含關鍵字（繁中 + 英文）
                if not any(kw in title.lower() for kw in self.keywords):
                    continue
                
                # 查找相關鏈接（通常在標題附近）
                url = self.base_url
                link_tag = h2.find_parent('a') or h2.find_next('a')
                if link_tag:
                    href = link_tag.get('href', '')
                    if href and href != '#':
                        if href.startswith('/'):
                            url = f"https://www.hkyaf.com{href}"
                        elif href.startswith('http'):
                            url = href
                
                # ✨ 關鍵：從列表頁提取日期（格式: 01/12/2023-31/03/2026）
                date_str = ''
                parent = h2.find_parent(['div', 'section', 'article'])
                if parent:
                    # 查找日期元素
                    date_el = parent.select_one('.field-name-field-event-date, .date, .event-date')
                    if date_el:
                        date_str = date_el.get_text(strip=True)
                    else:
                        # 從文本中提取日期
                        text = parent.get_text()
                        date_match = re.search(r'(\d{2}/\d{2}/\d{4})-(\d{2}/\d{2}/\d{4})', text)
                        if date_match:
                            date_str = date_match.group(0)
                
                events.append({
                    'title': title[:100],
                    'url': url,
                    'date_str': date_str
                })
                print(f"      找到: {title[:50]} | 日期: {date_str}")
                
            except Exception as e:
                continue
        
        return events
    
    def _extract_date(self, text: str, is_end_date: bool = False) -> str:
        """從文本提取日期
        支持格式:
        - DD/MM/YYYY-DD/MM/YYYY (HKYAF 格式)
        - 2026年3月15日
        - 2026-03-15
        - 15/03/2026
        """
        if not text or text == "詳情見連結":
            return datetime.now().strftime('%Y-%m-%d')
        
        # ✨ HKYAF 格式: 01/12/2023-31/03/2026 (DD/MM/YYYY-DD/MM/YYYY)
        range_match = re.search(r'(\d{2})/(\d{2})/(\d{4})-(\d{2})/(\d{2})/(\d{4})', text)
        if range_match:
            start_day, start_month, start_year = range_match.group(1), range_match.group(2), range_match.group(3)
            end_day, end_month, end_year = range_match.group(4), range_match.group(5), range_match.group(6)
            
            if is_end_date:
                return f"{end_year}-{end_month}-{end_day}"
            else:
                return f"{start_year}-{start_month}-{start_day}"
        
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
        
        return datetime.now().strftime('%Y-%m-%d')

if __name__ == '__main__':
    print("="*60)
    print("🎨 HKYAF Crawler (Stealth + 繁體中文) - 香港青年藝術協會")
    print("="*60)
    
    crawler = HKYAFStealthCrawler()
    events = crawler.crawl()
    
    print(f"\n{'='*60}")
    print(f"📊 總計: {len(events)} 個活動")
    print('='*60)
    
    for i, e in enumerate(events, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print(f"   地點: {e.location}")
        print(f"   描述: {e.description[:100]}...")
        print(f"   URL: {e.source_url}")
        print()
