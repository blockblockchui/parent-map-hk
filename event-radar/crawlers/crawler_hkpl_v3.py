#!/usr/bin/env python3
"""
Improved HKPL Crawler - Extract detailed info from event pages
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import PlaywrightCrawler, Event
from typing import List
import re

class HKPLCrawlerV3(PlaywrightCrawler):
    """改進版 HKPL 爬蟲 - 進入詳情頁獲取準確信息"""
    
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
        
        # 從列表頁獲取所有活動鏈接
        print("  從列表頁提取活動鏈接...")
        event_links = self._extract_event_links_from_list()
        
        if not event_links:
            print("  ⚠️ 沒有找到活動鏈接，嘗試備用方法...")
            event_links = self._extract_links_fallback()
        
        print(f"  找到 {len(event_links)} 個活動鏈接")
        
        # 進入每個詳情頁獲取信息
        for i, link_info in enumerate(event_links[:15], 1):  # 限制前15個避免太長
            try:
                print(f"    [{i}/{len(event_links)}] 處理: {link_info['title'][:40]}...")
                
                event = self._extract_from_detail_page(link_info)
                if event:
                    events.append(event)
                    print(f"      ✅ 獲取成功: {event.start_date} @ {event.location}")
                
                # 短暫暫停，避免過快
                time.sleep(1)
                
            except Exception as e:
                print(f"      ❌ 錯誤: {e}")
                continue
        
        print(f"  ✅ 總計找到 {len(events)} 個活動")
        return events
    
    def _extract_event_links_from_list(self) -> List[dict]:
        """從列表頁提取活動鏈接"""
        links = []
        
        # 尋找所有活動標題鏈接
        # HKPL 的活動鏈接通常在 .event_title 中
        event_elements = self.page.query_selector_all('.event_title, .event_detail, .touchcarousel-item')
        
        for el in event_elements:
            try:
                link_el = el.query_selector('a')
                if not link_el:
                    continue
                
                href = link_el.get_attribute('href') or ''
                title = link_el.inner_text().strip()
                
                if not href or not title:
                    continue
                
                # 檢查是否為親子活動
                if not self.is_parent_child_event(title):
                    continue
                
                # 構建完整 URL
                if href.startswith('/'):
                    full_url = f"https://www.hkpl.gov.hk{href}"
                elif href.startswith('http'):
                    full_url = href
                else:
                    full_url = f"https://www.hkpl.gov.hk/tc/extension-activities/{href}"
                
                links.append({
                    'title': title,
                    'url': full_url
                })
                
            except Exception as e:
                continue
        
        return links
    
    def _extract_links_fallback(self) -> List[dict]:
        """備用方法提取鏈接"""
        links = []
        
        # 尋找所有包含 event-detail 的鏈接
        all_links = self.page.query_selector_all('a[href*="event-detail"]')
        
        for link in all_links:
            try:
                href = link.get_attribute('href') or ''
                title = link.inner_text().strip()
                
                if not href or not title or len(title) < 5:
                    continue
                
                if not self.is_parent_child_event(title):
                    continue
                
                if href.startswith('/'):
                    full_url = f"https://www.hkpl.gov.hk{href}"
                elif href.startswith('http'):
                    full_url = href
                else:
                    continue
                
                # 避免重複
                if not any(l['url'] == full_url for l in links):
                    links.append({
                        'title': title,
                        'url': full_url
                    })
                    
            except Exception as e:
                continue
        
        return links
    
    def _extract_from_detail_page(self, link_info: dict) -> Event:
        """從詳情頁提取活動信息"""
        import time
        
        # 導航到詳情頁
        detail_url = link_info['url']
        
        try:
            self.page.goto(detail_url, wait_until="networkidle", timeout=30000)
            time.sleep(2)
        except Exception as e:
            print(f"      ⚠️ 導航詳情頁失敗: {e}")
            return None
        
        # 提取活動名稱 - h1 通常是「全部活動」，真正的標題在 h2
        title = link_info['title']
        
        # 嘗試 h2 先（真正的活動標題）
        title_el = self.page.query_selector('h2')
        if title_el:
            title_text = title_el.inner_text().strip()
            if title_text and title_text != '全部活動':
                title = title_text[:100]
        
        # 如果 h2 沒有，再嘗試其他選擇器
        if not title or title == '全部活動':
            for title_selector in ['.event_title', '.activity-title', '.title', 'h3']:
                title_el = self.page.query_selector(title_selector)
                if title_el:
                    title_text = title_el.inner_text().strip()
                    if title_text and len(title_text) > 5:
                        title = title_text[:100]
                        break
        
        # 提取日期 - 改進版
        date_str = ''
        
        # 方法 1: 從頁面文本中查找日期模式
        page_text = self.page.inner_text()
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{2})-(\d{2})',
            r'(\d{4})/(\d{2})/(\d{2})',
            r'(\d{1,2})/(\d{1,2})/(\d{4})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, page_text)
            if date_match:
                if len(date_match.groups()) == 3:
                    if date_match.group(1) and len(date_match.group(1)) == 4:  # Year first
                        date_str = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
                    else:  # Day or month first
                        date_str = f"{date_match.group(3)}-{int(date_match.group(2)):02d}-{int(date_match.group(1)):02d}"
                    break
        
        # 方法 2: 通過選擇器查找
        if not date_str:
            for date_selector in ['.event_date', '.date', '[class*="date"]']:
                date_el = self.page.query_selector(date_selector)
                if date_el:
                    date_html = date_el.inner_html()
                    date_text = re.sub(r'<[^>]+>', '', date_html)
                    date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', date_text)
                    if date_match:
                        date_str = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
                        break
        
        if not date_str:
            date_str = self.parse_date('')[0]
        
        # 提取時間
        time_str = ''
        for time_selector in ['.event_time', '.time', '[class*="time"]']:
            time_el = self.page.query_selector(time_selector)
            if time_el:
                time_text = time_el.inner_text()
                time_match = re.search(r'(\d{1,2}):(\d{2})', time_text)
                if time_match:
                    time_str = f"{time_match.group(0)}"
                    break
        
        # 提取地點 - 改進版
        location = '香港公共圖書館'
        
        # 方法 1: 直接查找包含「公共圖書館」的元素
        page_text = self.page.inner_text()
        lib_match = re.search(r'([\u4e00-\u9fa5]+公共圖書館)', page_text)
        if lib_match:
            location = lib_match.group(1)
        else:
            # 方法 2: 通過標籤查找
            for loc_selector in ['.event_locat', '.location', '.venue', '[class*="locat"]']:
                loc_el = self.page.query_selector(loc_selector)
                if loc_el:
                    # 獲取元素的完整文本，包括子元素
                    loc_html = loc_el.inner_html()
                    # 移除 HTML 標籤獲取純文本
                    import re
                    loc_text = re.sub(r'<[^>]+>', '', loc_html)
                    loc_text = loc_text.strip()
                    # 清理前綴
                    loc_text = re.sub(r'^[地點場館]+[:\s]*', '', loc_text)
                    if loc_text and len(loc_text) > 3 and '圖書館' in loc_text:
                        location = loc_text[:100]
                        break
        
        # 提取描述
        description = title
        for desc_selector in ['.event_desc', '.description', '.content', '[class*="desc"]']:
            desc_el = self.page.query_selector(desc_selector)
            if desc_el:
                desc_text = desc_el.inner_text().strip()
                if len(desc_text) > 10:
                    description = desc_text[:200]
                    break
        
        # 提取報名狀態
        is_free = True
        page_content = self.page.content()
        if '費用' in page_content or '收費' in page_content:
            # 檢查是否免費
            if re.search(r'免費|Free', page_content, re.IGNORECASE):
                is_free = True
            elif re.search(r'\$\d+|HK\$\d+', page_content):
                is_free = False
        
        # 構建 Event 對象
        event = Event(
            name=title,
            description=description,
            start_date=date_str,
            end_date=date_str,
            location=location,
            organizer='香港公共圖書館',
            source_url=detail_url,
            is_free=is_free,
            category='工作坊',
            age_range='3-12歲'
        )
        
        return event

if __name__ == '__main__':
    print("="*60)
    print("🎯 HKPL Crawler V3 - 詳情頁提取版")
    print("="*60)
    
    with HKPLCrawlerV3() as crawler:
        events = crawler.crawl()
    
    print(f"\n{'='*60}")
    print(f"📊 總計: {len(events)} 個活動")
    print('='*60)
    
    for i, e in enumerate(events, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print(f"   時間: {e.location}")  # 这里显示地点
        print(f"   URL: {e.source_url}")
        print()
