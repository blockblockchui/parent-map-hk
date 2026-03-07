#!/usr/bin/env python3
"""
Source: LCSD Cultural Activities Search
URL: https://www.lcsd.gov.hk/clpss/tc/search/culture/GeneralSearchForm.do
Remarks: POST request searchFormPath=search%2Fculture%2FGeneralSearchForm&searchType=type&keyword=%E8%A6%AA%E5%AD%90
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import PlaywrightCrawler, Event
from typing import List

class LCSDCrawler(PlaywrightCrawler):
    """康文署文化活動爬蟲"""
    
    def __init__(self):
        super().__init__(
            name='康文署',
            base_url='https://www.lcsd.gov.hk/clpss/tc/search/culture/GeneralSearchForm.do'
        )
    
    def crawl(self) -> List[Event]:
        events = []
        
        # 直接導航到搜尋結果頁（已包含關鍵字「親子」）
        search_url = 'https://www.lcsd.gov.hk/clpss/tc/search/common/searchResult.do'
        
        if not self.navigate(search_url, wait_for='.search-result, .event-item, table', timeout=60000):
            print("  ⚠️ 嘗試從搜尋表單開始...")
            if not self._search_from_form():
                return events
        
        # 等待結果加載
        self.page.wait_for_timeout(3000)
        
        # 處理分頁
        page_num = 1
        max_pages = 5
        
        while page_num <= max_pages:
            print(f"  處理第 {page_num} 頁...")
            
            # 提取當前頁活動
            page_events = self._extract_events_from_page()
            events.extend(page_events)
            
            # 檢查是否有下一頁
            next_page = self.page.query_selector('a.next, .pagination a[title="下一頁"], a:has-text("下一頁")')
            if not next_page:
                # 嘗試其他分頁選擇器
                pagination_links = self.page.query_selector_all('.pagination a, .page-link')
                found_next = False
                for link in pagination_links:
                    if '下一頁' in (link.inner_text() or '') or 'next' in (link.get_attribute('class') or '').lower():
                        next_page = link
                        found_next = True
                        break
                
                if not found_next:
                    break
            
            if next_page:
                try:
                    next_page.click()
                    self.page.wait_for_timeout(3000)
                    page_num += 1
                except:
                    break
            else:
                break
        
        print(f"  ✅ 找到 {len(events)} 個親子活動")
        return events
    
    def _search_from_form(self) -> bool:
        """從搜尋表單開始"""
        if not self.navigate(self.base_url, wait_for='form', timeout=60000):
            return False
        
        try:
            # 填寫關鍵字
            keyword_input = self.page.query_selector('input[name="keyword"], #keyword, [name*="keyword"]')
            if keyword_input:
                keyword_input.fill('親子')
            
            # 提交表單
            submit_btn = self.page.query_selector('input[type="submit"], button[type="submit"], .search-btn')
            if submit_btn:
                submit_btn.click()
                self.page.wait_for_timeout(5000)
                return True
                
        except Exception as e:
            print(f"  表單填寫失敗: {e}")
        
        return False
    
    def _extract_events_from_page(self) -> List[Event]:
        """從當前頁提取活動"""
        events = []
        
        # 尋找結果項目
        result_selectors = [
            '.search-result',
            '.result-item',
            'tr',  # 表格行
            '.event-item'
        ]
        
        items = []
        for selector in result_selectors:
            items = self.page.query_selector_all(selector)
            if len(items) > 0:
                print(f"    找到 {len(items)} 個項目 (selector: {selector})")
                break
        
        for item in items:
            try:
                item_text = item.inner_text()
                
                # 跳過標題行
                if not item_text or '活動名稱' in item_text or '日期' in item_text:
                    continue
                
                # 提取標題
                title = ''
                title_el = item.query_selector('a, .title, h3, h4')
                if title_el:
                    title = title_el.inner_text().strip()
                
                if not title:
                    lines = [l.strip() for l in item_text.split('\n') if l.strip()]
                    if lines:
                        title = lines[0][:50]
                
                # 檢查是否親子活動
                if not self.is_parent_child_event(title + ' ' + item_text):
                    continue
                
                # 提取日期
                import re
                date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', item_text)
                if date_match:
                    start_date = date_match.group(0)
                    end_date = start_date
                else:
                    start_date, end_date = self.parse_date('')
                
                # 提取地點
                venue = '康文署場地'
                for line in item_text.split('\n'):
                    if '場地' in line or '地點' in line or '地區' in line:
                        venue = line.split('：')[-1].strip()[:50]
                        break
                
                # 提取連結
                source_url = self.base_url
                link_el = item.query_selector('a')
                if link_el:
                    href = link_el.get_attribute('href') or ''
                    if href:
                        if href.startswith('http'):
                            source_url = href
                        else:
                            source_url = f"https://www.lcsd.gov.hk{href}"
                
                event = Event(
                    name=title[:100] if title else '康文署活動',
                    description=item_text[:200],
                    start_date=start_date,
                    end_date=end_date,
                    location=venue,
                    organizer='康文署',
                    source_url=source_url,
                    is_free=True,
                    category='其他'
                )
                events.append(event)
                
            except Exception as e:
                print(f"    解析錯誤: {e}")
                continue
        
        return events

if __name__ == '__main__':
    print("測試康文署爬蟲...")
    
    with LCSDCrawler() as crawler:
        events = crawler.crawl()
    
    print(f"\n總計: {len(events)} 個活動")
    for i, e in enumerate(events[:10], 1):
        print(f"{i}. {e.name} ({e.start_date}) - {e.location}")
