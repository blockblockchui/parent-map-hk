#!/usr/bin/env python3
"""
Source: LCSD Cultural Activities Search
URL: https://www.lcsd.gov.hk/clpss/tc/search/common/searchResult.do
Remarks: POST request with search parameters
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import PlaywrightCrawler, Event
from typing import List
import re

class LCSDCrawler(PlaywrightCrawler):
    """康文署文化活動爬蟲"""
    
    def __init__(self):
        super().__init__(
            name='康文署',
            base_url='https://www.lcsd.gov.hk/clpss/tc/search/culture/GeneralSearchForm.do',
            headless=True
        )
    
    def crawl(self) -> List[Event]:
        events = []
        
        print("  導航到康文署搜尋頁...")
        if not self.navigate(self.base_url, timeout=60000):
            print("  ❌ 導航失敗")
            return events
        
        import time
        time.sleep(3)
        
        # 搜索「親子」活動
        if not self._search_parent_child_events():
            print("  ⚠️ 搜索失敗，嘗試直接獲取列表...")
        
        # 提取活動列表
        event_items = self._extract_events()
        
        print(f"  找到 {len(event_items)} 個活動")
        
        for i, item in enumerate(event_items[:8], 1):
            try:
                print(f"    [{i}/{len(event_items)}] {item['title'][:40]}...")
                
                # 康文署的活動詳情通常在搜尋結果中已經有完整信息
                # 如果需要更多詳情才進入詳情頁
                event = Event(
                    name=item['title'],
                    description=item.get('description') or item['title'],
                    start_date=item.get('date') or self.parse_date('')[0],
                    end_date=item.get('date') or self.parse_date('')[0],
                    location=item.get('location') or '康文署場地',
                    organizer='康文署',
                    source_url=item['url'],
                    is_free=True,  # 康文署活動通常免費
                    category='其他',
                    age_range='3-12歲'
                )
                
                events.append(event)
                print(f"      ✅ {event.start_date} @ {event.location}")
                
            except Exception as e:
                print(f"      ❌ 錯誤: {e}")
                continue
        
        print(f"  ✅ 總計找到 {len(events)} 個活動")
        return events
    
    def _search_parent_child_events(self) -> bool:
        """搜索親子活動"""
        try:
            print("    填寫搜索關鍵字...")
            
            # 查找關鍵字輸入框
            keyword_input = self.page.query_selector('input[name="keyword"], #keyword, input[placeholder*="關鍵"]')
            if not keyword_input:
                print("    找不到搜索框")
                return False
            
            # 填寫「親子」
            keyword_input.fill('親子')
            
            # 查找提交按鈕
            submit_btn = self.page.query_selector('input[type="submit"], button[type="submit"], .search-btn, input[value*="搜索"]')
            if submit_btn:
                print("    提交搜索...")
                submit_btn.click()
                time.sleep(5)  # 等待結果加載
                return True
            else:
                # 嘗試按 Enter
                keyword_input.press('Enter')
                time.sleep(5)
                return True
                
        except Exception as e:
            print(f"    搜索錯誤: {e}")
            return False
    
    def _extract_events(self) -> List[dict]:
        """提取搜尋結果中的活動"""
        events = []
        
        # 查找搜尋結果表格或列表
        selectors = [
            '.search-result',
            '.result-item',
            'tr[data-row]',
            '.event-item',
            'table tr'
        ]
        
        items = []
        for selector in selectors:
            items = self.page.query_selector_all(selector)
            if len(items) > 0:
                print(f"    使用選擇器: {selector} ({len(items)} 個)")
                break
        
        for item in items:
            try:
                # 獲取文本內容
                item_text = item.inner_text()
                
                # 跳過標題行
                if '活動名稱' in item_text or '日期' in item_text:
                    continue
                
                # 提取標題
                title = ''
                title_el = item.query_selector('a, .title, td:nth-child(1)')
                if title_el:
                    title = title_el.inner_text().strip()
                else:
                    # 從文本第一行提取
                    lines = [l.strip() for l in item_text.split('\n') if l.strip()]
                    if lines:
                        title = lines[0][:100]
                
                if not title or len(title) < 5:
                    continue
                
                # 檢查是否親子活動
                if not self.is_parent_child_event(title + ' ' + item_text):
                    continue
                
                # 提取日期
                date_str = ''
                date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', item_text)
                if date_match:
                    date_str = date_match.group(0)
                else:
                    date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', item_text)
                    if date_match:
                        date_str = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
                
                # 提取地點
                location = '康文署場地'
                # 嘗試從文本中提取地點信息
                for line in item_text.split('\n'):
                    if any(x in line for x in ['體育館', '圖書館', '會堂', '中心', '場地']):
                        location = line.strip()[:100]
                        break
                
                # 提取鏈接
                url = self.base_url
                link_el = item.query_selector('a')
                if link_el:
                    href = link_el.get_attribute('href') or ''
                    if href:
                        if href.startswith('/'):
                            url = f"https://www.lcsd.gov.hk{href}"
                        elif href.startswith('http'):
                            url = href
                        elif 'event' in href or 'activity' in href:
                            url = f"https://www.lcsd.gov.hk/clpss/tc/{href}"
                
                events.append({
                    'title': title[:100],
                    'url': url,
                    'date': date_str,
                    'location': location,
                    'description': item_text[:200]
                })
                
            except Exception as e:
                continue
        
        return events

if __name__ == '__main__':
    print("="*60)
    print("🏛️  LCSD Crawler - 康文署文化活動")
    print("="*60)
    
    with LCSDCrawler() as crawler:
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
