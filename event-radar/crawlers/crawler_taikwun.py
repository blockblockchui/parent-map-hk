#!/usr/bin/env python3
"""
Source: Tai Kwun
URL: https://www.taikwun.hk/zh/taikwun/press/press_release
Remarks: press-article
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawlers.base_playwright import PlaywrightCrawler, Event
from typing import List
import re

class TaikwunCrawler(PlaywrightCrawler):
    """大館活動爬蟲"""
    
    def __init__(self):
        super().__init__(
            name='大館',
            base_url='https://www.taikwun.hk/zh/taikwun/press/press_release',
            headless=True
        )
    
    def crawl(self) -> List[Event]:
        events = []
        
        print("  導航到大館活動頁...")
        if not self.navigate(self.base_url, timeout=60000):
            print("  ❌ 導航失敗")
            return events
        
        import time
        time.sleep(3)
        
        # 滾動加載
        self.scroll_to_load(scroll_times=3)
        
        # 提取活動
        event_items = self._extract_events()
        
        print(f"  找到 {len(event_items)} 個活動")
        
        for i, item in enumerate(event_items[:8], 1):
            try:
                print(f"    [{i}/{len(event_items)}] {item['title'][:40]}...")
                
                self.page.goto(item['url'], wait_until="networkidle", timeout=30000)
                time.sleep(2)
                
                detail = self._extract_from_detail_page()
                
                event = Event(
                    name=item['title'],
                    description=detail.get('description') or item['title'],
                    start_date=detail.get('date') or item.get('date') or self.parse_date('')[0],
                    end_date=detail.get('date') or item.get('date') or self.parse_date('')[0],
                    location=detail.get('location') or '大館',
                    organizer='大館',
                    source_url=item['url'],
                    is_free=detail.get('is_free', True),
                    category='展覽',
                    age_range='6-12歲'
                )
                
                events.append(event)
                print(f"      ✅ {event.start_date}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"      ❌ 錯誤: {e}")
                continue
        
        print(f"  ✅ 總計找到 {len(events)} 個活動")
        return events
    
    def _extract_events(self) -> List[dict]:
        """提取活動列表"""
        events = []
        
        # 根據 remarks: press-article
        selectors = [
            '.press-article',
            '.article-item',
            '.press-item',
            '.event-item',
            'article'
        ]
        
        items = []
        for selector in selectors:
            items = self.page.query_selector_all(selector)
            if items:
                print(f"    使用選擇器: {selector} ({len(items)} 個)")
                break
        
        # 如果沒找到，嘗試通用方法
        if not items:
            items = self.page.query_selector_all('a[href*="press"], a[href*="event"]')
            print(f"    使用通用鏈接選擇器 ({len(items)} 個)")
        
        for item in items:
            try:
                # 提取標題
                title_el = item.query_selector('h2, h3, .title, .article-title')
                if not title_el:
                    title = item.inner_text().strip().split('\n')[0][:100]
                else:
                    title = title_el.inner_text().strip()
                
                if not title or len(title) < 5:
                    continue
                
                # 檢查是否親子/家庭相關
                if not self.is_parent_child_event(title + ' ' + item.inner_text()):
                    continue
                
                # 提取鏈接
                link_el = item if item.tag_name == 'a' else item.query_selector('a')
                if not link_el:
                    continue
                
                href = link_el.get_attribute('href') or ''
                if not href:
                    continue
                
                # 構建完整 URL
                if href.startswith('/'):
                    url = f"https://www.taikwun.hk{href}"
                elif href.startswith('http'):
                    url = href
                else:
                    url = f"https://www.taikwun.hk/zh/taikwun/{href}"
                
                # 嘗試提取日期
                date_str = ''
                item_text = item.inner_text()
                date_match = re.search(r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})', item_text)
                if date_match:
                    date_str = f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
                
                events.append({
                    'title': title[:100],
                    'url': url,
                    'date': date_str
                })
                
            except Exception as e:
                continue
        
        return events
    
    def _extract_from_detail_page(self) -> dict:
        """從詳情頁提取信息"""
        info = {}
        
        page_text = self.page.content()
        
        # 提取日期
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
        
        # 提取描述
        desc_el = self.page.query_selector('.article-content, .press-content, .description')
        if desc_el:
            info['description'] = desc_el.inner_text().strip()[:200]
        
        info['location'] = '大館'
        info['is_free'] = '免費' in page_text or 'free' in page_text.lower()
        
        return info

if __name__ == '__main__':
    print("="*60)
    print("🎭 Taikwun Crawler - 大館")
    print("="*60)
    
    with TaikwunCrawler() as crawler:
        events = crawler.crawl()
    
    print(f"\n{'='*60}")
    print(f"📊 總計: {len(events)} 個活動")
    print('='*60)
    
    for i, e in enumerate(events, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print(f"   URL: {e.source_url}")
        print()
