#!/usr/bin/env python3
"""
Final HKPL Crawler - Working Version
Uses link titles from list page and extracts accurate info from detail pages
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import PlaywrightCrawler, Event
from typing import List
import re

class HKPLCrawlerFinal(PlaywrightCrawler):
    """最終版 HKPL 爬蟲"""
    
    def __init__(self, url: str = None):
        base_url = url or 'https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week'
        super().__init__(name='HKPL', base_url=base_url, headless=True)
    
    def crawl(self) -> List[Event]:
        events = []
        
        print("  導航到活動列表頁...")
        if not self.navigate(self.base_url, timeout=60000):
            print("  ❌ 導航失敗")
            return events
        
        import time
        time.sleep(3)
        
        # 獲取列表頁的所有信息
        print("  從列表頁提取活動信息...")
        event_infos = self._extract_from_list_page()
        
        print(f"  找到 {len(event_infos)} 個活動")
        
        # 進入每個詳情頁獲取更準確的信息
        for i, info in enumerate(event_infos[:10], 1):  # 限制10個避免太長
            try:
                print(f"    [{i}/{len(event_infos)}] {info['title'][:50]}...")
                
                # 導航到詳情頁
                self.page.goto(info['url'], wait_until="networkidle", timeout=30000)
                time.sleep(2)
                
                # 從詳情頁提取準確信息
                detail_info = self._extract_from_detail_page()
                
                # 合並信息（優先使用詳情頁的日期和地點）
                event = Event(
                    name=info['title'],  # 使用列表頁的標題（準確）
                    description=info['title'],
                    start_date=detail_info.get('date') or info.get('date') or self.parse_date('')[0],
                    end_date=detail_info.get('date') or info.get('date') or self.parse_date('')[0],
                    location=detail_info.get('location') or info.get('location') or '香港公共圖書館',
                    organizer='香港公共圖書館',
                    source_url=info['url'],
                    is_free=True,
                    category='工作坊',
                    age_range='3-12歲'
                )
                
                events.append(event)
                print(f"      ✅ {event.start_date} @ {event.location[:30]}...")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"      ❌ 錯誤: {e}")
                continue
        
        print(f"  ✅ 總計找到 {len(events)} 個活動")
        return events
    
    def _extract_from_list_page(self) -> List[dict]:
        """從列表頁提取活動基本信息"""
        events = []
        
        # 獲取頁面 HTML 內容
        html = self.page.content()
        
        # 方法：查找所有活動鏈接和標題
        # HKPL 的活動通常在 .event_title 中
        event_elements = self.page.query_selector_all('.event_title, .event-item, .touchcarousel-item')
        
        for el in event_elements:
            try:
                # 提取標題
                title_el = el.query_selector('a, h3, h4')
                if not title_el:
                    continue
                
                title = title_el.inner_text().strip()
                if not title or len(title) < 5:
                    continue
                
                # 檢查是否親子活動
                if not self.is_parent_child_event(title):
                    continue
                
                # 提取鏈接
                href = title_el.get_attribute('href') or ''
                if not href:
                    continue
                
                # 構建完整 URL
                if href.startswith('/'):
                    url = f"https://www.hkpl.gov.hk{href}"
                elif href.startswith('http'):
                    url = href
                else:
                    url = f"https://www.hkpl.gov.hk/tc/extension-activities/{href}"
                
                # 嘗試從附近元素提取日期
                date = ''
                parent = el.query_selector('xpath=..')
                if parent:
                    parent_text = parent.inner_text()
                    date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', parent_text)
                    if date_match:
                        date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
                
                events.append({
                    'title': title[:100],
                    'url': url,
                    'date': date
                })
                
            except Exception as e:
                continue
        
        return events
    
    def _extract_from_detail_page(self) -> dict:
        """從詳情頁提取準確信息"""
        info = {}
        
        # 獲取頁面文本
        page_text = self.page.content()
        
        # 提取日期 - 查找多種模式
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
        
        # 提取地點 - 香港公共圖書館分館列表
        # 按優先級排序：更具體的地區名優先於「香港中央」
        hkpl_branches = [
            # 港島區（優先具體分館）
            '大會堂公共圖書館', '士美非路公共圖書館',
            '石塘咀公共圖書館', '駱克道公共圖書館', '黃泥涌公共圖書館',
            '柴灣公共圖書館', '鰂魚涌公共圖書館', '西灣河公共圖書館',
            '香港仔公共圖書館', '薄扶林公共圖書館', '鴨脷洲公共圖書館',
            '石排灣公共圖書館',
            # 九龍區
            '大角咀公共圖書館', '深水埗公共圖書館',
            '長沙灣公共圖書館', '荔枝角公共圖書館', '美孚公共圖書館',
            '牛頭角公共圖書館', '觀塘公共圖書館', '藍田公共圖書館',
            '油蔴地公共圖書館', '尖沙咀公共圖書館', '土瓜灣公共圖書館',
            '新蒲崗公共圖書館', '黃大仙公共圖書館', '慈雲山公共圖書館',
            '樂富公共圖書館', '石硤尾公共圖書館', '啟德公共圖書館',
            '九龍公共圖書館',
            # 新界東
            '沙田公共圖書館', '大埔公共圖書館', '馬鞍山公共圖書館',
            '將軍澳公共圖書館', '上水公共圖書館', '粉嶺公共圖書館',
            '荃灣公共圖書館', '葵涌公共圖書館', '青衣公共圖書館',
            '東涌公共圖書館', '天水圍公共圖書館', '元朗公共圖書館',
            '屯門公共圖書館', '沙頭角公共圖書館',
            # 最後才檢查中央/總館
            '香港中央圖書館', '香港公共圖書館'
        ]
        
        # 方法1: 直接查找完整分館名稱（按優先級順序）
        for branch in hkpl_branches:
            if branch in page_text:
                info['location'] = branch
                break
        
        # 方法2: 如果沒找到，嘗試正則匹配
        if 'location' not in info:
            lib_match = re.search(r'([\u4e00-\u9fa5]{2,6}公共圖書館)', page_text)
            if lib_match:
                info['location'] = lib_match.group(1)
        
        # 方法3: 查找「地點」欄位附近的文字
        if 'location' not in info:
            # 嘗試找到「地點」標籤後面的文字
            loc_patterns = [
                r'地點[:\s]*([^<\n]{5,30}?)(?:<|\n|$)',
                r'venue[:\s]*([^<\n]{5,30}?)(?:<|\n|$)',
                r'location[:\s]*([^<\n]{5,30}?)(?:<|\n|$)'
            ]
            for pattern in loc_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    loc = match.group(1).strip()
                    if '圖書館' in loc or '會堂' in loc or '中心' in loc:
                        info['location'] = loc
                        break
        
        return info

if __name__ == '__main__':
    print("="*60)
    print("🎯 HKPL Crawler - Final Version")
    print("="*60)
    
    with HKPLCrawlerFinal() as crawler:
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
