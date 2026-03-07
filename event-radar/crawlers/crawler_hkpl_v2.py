#!/usr/bin/env python3
"""
Improved HKPL Crawler with Smart Element Detection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import PlaywrightCrawler, Event
from typing import List
import re

class HKPLCrawlerV2(PlaywrightCrawler):
    """改進版香港公共圖書館活動爬蟲"""
    
    def __init__(self, url: str = None):
        base_url = url or 'https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week'
        super().__init__(name='HKPL', base_url=base_url, headless=True)
    
    def crawl(self) -> List[Event]:
        events = []
        
        print("  導航到頁面...")
        if not self.navigate(self.base_url, timeout=60000):
            print("  ❌ 導航失敗")
            return events
        
        # 等待頁面加載
        import time
        time.sleep(5)
        
        print("  提取活動...")
        
        # 方法 1: 通過鏈接分析尋找活動
        events = self._extract_from_links()
        
        if not events:
            # 方法 2: 通過文本模式識別
            events = self._extract_from_text_patterns()
        
        if not events:
            # 方法 3: 通過結構分析
            events = self._extract_from_structure()
        
        print(f"  ✅ 找到 {len(events)} 個活動")
        return events
    
    def _extract_from_links(self) -> List[Event]:
        """通過活動鏈接提取"""
        events = []
        
        # 尋找所有可能活動的鏈接
        links = self.page.query_selector_all('a')
        print(f"    分析 {len(links)} 個鏈接...")
        
        for link in links:
            try:
                href = link.get_attribute('href') or ''
                text = link.inner_text().strip()
                
                # 過濾條件：鏈接包含 event/activity 且有有意義的文本
                if not text or len(text) < 5:
                    continue
                
                # 檢查是否為活動鏈接
                is_event_link = any(keyword in href.lower() for keyword in [
                    'event', 'activity', 'program', 'detail', 'info'
                ])
                
                # 檢查文本是否像活動名稱
                has_event_keywords = any(kw in text.lower() for kw in [
                    '工作坊', '講座', '活動', '故事', '閱讀', '親子', '兒童'
                ])
                
                if is_event_link or has_event_keywords:
                    # 嘗試獲取父元素中的更多信息
                    parent = link.query_selector('xpath=..')
                    parent_text = parent.inner_text() if parent else text
                    
                    # 提取日期
                    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', parent_text)
                    if not date_match:
                        date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', parent_text)
                    
                    if date_match:
                        start_date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
                    else:
                        start_date = self.parse_date('')[0]
                    
                    # 檢查是否親子活動
                    if not self.is_parent_child_event(text + ' ' + parent_text):
                        continue
                    
                    event = Event(
                        name=text[:100],
                        description=text[:200],
                        start_date=start_date,
                        end_date=start_date,
                        location='香港公共圖書館',
                        organizer='香港公共圖書館',
                        source_url=href if href.startswith('http') else f"https://www.hkpl.gov.hk{href}",
                        is_free=True,
                        category='工作坊'
                    )
                    events.append(event)
                    
            except Exception as e:
                continue
        
        # 去重
        unique_events = []
        seen = set()
        for e in events:
            key = f"{e.name}_{e.start_date}"
            if key not in seen:
                seen.add(key)
                unique_events.append(e)
        
        return unique_events
    
    def _extract_from_text_patterns(self) -> List[Event]:
        """通過文本模式識別活動"""
        events = []
        
        # 獲取頁面所有文本
        page_text = self.page.inner_text()
        
        # 尋找常見的活動模式
        # 模式 1: 活動名稱 + 日期
        pattern = r'([^\n]{10,50}(?:工作坊|講座|活動|故事|閱讀))[^\d]*(\d{4})年?(\d{1,2})月(\d{1,2})日?'
        matches = re.findall(pattern, page_text)
        
        for match in matches[:20]:  # 限制數量
            try:
                name = match[0].strip()
                year, month, day = match[1], match[2], match[3]
                date = f"{year}-{int(month):02d}-{int(day):02d}"
                
                if self.is_parent_child_event(name):
                    event = Event(
                        name=name[:100],
                        description=name[:200],
                        start_date=date,
                        end_date=date,
                        location='香港公共圖書館',
                        organizer='香港公共圖書館',
                        source_url=self.base_url,
                        is_free=True,
                        category='工作坊'
                    )
                    events.append(event)
            except:
                continue
        
        return events
    
    def _extract_from_structure(self) -> List[Event]:
        """通過 DOM 結構提取"""
        events = []
        
        # 尋找包含標題和日期的容器
        containers = self.page.query_selector_all('''
            div:has(h3):has(span:has-text("202")),
            div:has(h2):has(span:has-text("202")),
            li:has(a):has(span:has-text("202"))
        ''')
        
        print(f"    找到 {len(containers)} 個結構容器")
        
        for container in containers:
            try:
                # 提取標題
                title_el = container.query_selector('h3, h2, .title, a')
                if not title_el:
                    continue
                
                title = title_el.inner_text().strip()
                if len(title) < 5 or len(title) > 100:
                    continue
                
                # 檢查是否親子活動
                container_text = container.inner_text()
                if not self.is_parent_child_event(title + ' ' + container_text):
                    continue
                
                # 提取日期
                date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', container_text)
                if date_match:
                    date = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
                else:
                    date = self.parse_date('')[0]
                
                event = Event(
                    name=title[:100],
                    description=title[:200],
                    start_date=date,
                    end_date=date,
                    location='香港公共圖書館',
                    organizer='香港公共圖書館',
                    source_url=self.base_url,
                    is_free=True,
                    category='工作坊'
                )
                events.append(event)
                
            except Exception as e:
                continue
        
        return events

if __name__ == '__main__':
    print("="*60)
    print("🎯 HKPL Crawler V2 - 改進版")
    print("="*60)
    
    urls = [
        'https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week',
    ]
    
    all_events = []
    for url in urls:
        print(f"\n🔍 爬取: {url}")
        with HKPLCrawlerV2(url) as crawler:
            events = crawler.crawl()
            all_events.extend(events)
    
    print(f"\n{'='*60}")
    print(f"📊 總計: {len(all_events)} 個活動")
    print('='*60)
    
    for i, e in enumerate(all_events[:10], 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print()
