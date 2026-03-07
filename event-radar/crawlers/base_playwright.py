#!/usr/bin/env python3
"""
Base Playwright Crawler for Event Radar
Handles JavaScript-rendered pages
"""

from playwright.sync_api import sync_playwright, Page, Browser
from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime
import time
import hashlib

@dataclass
class Event:
    """活動資料結構"""
    name: str
    description: str
    start_date: str  # ISO format: 2026-03-15
    end_date: str    # ISO format: 2026-03-20
    location: str
    organizer: str
    source_url: str
    image_url: Optional[str] = None
    age_range: Optional[str] = None
    is_free: bool = True
    category: str = "其他"
    venue_slug: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'event_id': hashlib.md5(f"{self.name}_{self.start_date}_{self.organizer}".encode()).hexdigest()[:12],
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'location': self.location,
            'organizer': self.organizer,
            'source_url': self.source_url,
            'image_url': self.image_url or '',
            'age_range': self.age_range or '',
            'is_free': '是' if self.is_free else '否',
            'category': self.category,
            'venue_slug': self.venue_slug or '',
            'status': '待審核',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'notes': ''
        }

class PlaywrightCrawler:
    """基礎 Playwright 爬蟲類別"""
    
    def __init__(self, name: str, base_url: str, headless: bool = True):
        self.name = name
        self.base_url = base_url
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def __enter__(self):
        """Context manager entry"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def navigate(self, url: str, wait_for: Optional[str] = None, timeout: int = 30000) -> bool:
        """
        導航到網頁並等待元素
        
        Args:
            url: 目標 URL
            wait_for: 等待的 CSS selector
            timeout: 超時時間（毫秒）
        """
        try:
            print(f"  導航到: {url[:80]}...")
            self.page.goto(url, wait_until='networkidle', timeout=timeout)
            
            if wait_for:
                print(f"  等待元素: {wait_for}")
                self.page.wait_for_selector(wait_for, timeout=timeout)
            
            # 額外等待 JS 渲染
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"  ❌ 導航失敗: {e}")
            return False
    
    def scroll_to_load(self, scroll_times: int = 3, delay: float = 1.0):
        """滾動頁面加載更多內容（無限滾動）"""
        for i in range(scroll_times):
            self.page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(delay)
            print(f"  滾動 {i+1}/{scroll_times}")
    
    def click_load_more(self, selector: str, max_clicks: int = 5, delay: float = 2.0):
        """點擊「加載更多」按鈕"""
        for i in range(max_clicks):
            try:
                button = self.page.query_selector(selector)
                if not button or not button.is_visible():
                    break
                
                print(f"  點擊加載更多 {i+1}/{max_clicks}")
                button.click()
                time.sleep(delay)
                
            except Exception as e:
                print(f"  無法點擊: {e}")
                break
    
    def extract_text(self, selector: str, default: str = '') -> str:
        """提取元素的文本內容"""
        try:
            element = self.page.query_selector(selector)
            if element:
                return element.inner_text().strip()
        except:
            pass
        return default
    
    def extract_attribute(self, selector: str, attribute: str, default: str = '') -> str:
        """提取元素的屬性值"""
        try:
            element = self.page.query_selector(selector)
            if element:
                return element.get_attribute(attribute) or default
        except:
            pass
        return default
    
    def parse_date(self, date_str: str) -> tuple:
        """
        解析各種日期格式
        返回: (start_date, end_date) 格式: YYYY-MM-DD
        """
        import re
        
        date_str = date_str.strip()
        today = datetime.now()
        
        # 嘗試匹配 "2026年3月15日"
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if match:
            year, month, day = match.groups()
            date = f"{year}-{int(month):02d}-{int(day):02d}"
            return date, date
        
        # 嘗試匹配 "15/3/2026"
        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
        if match:
            day, month, year = match.groups()
            date = f"{year}-{int(month):02d}-{int(day):02d}"
            return date, date
        
        # 嘗試匹配 "2026-03-15"
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
        if match:
            return date_str[:10], date_str[:10]
        
        # 嘗試匹配日期範圍 "2026年3月15日至20日"
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日[\s至-]+(\d{1,2})日', date_str)
        if match:
            year, month, start_day, end_day = match.groups()
            start = f"{year}-{int(month):02d}-{int(start_day):02d}"
            end = f"{year}-{int(month):02d}-{int(end_day):02d}"
            return start, end
        
        # 默認返回今天
        return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')
    
    def is_parent_child_event(self, text: str) -> bool:
        """檢查是否為親子活動"""
        keywords = [
            '親子', '兒童', 'kids', 'children', 'family', '親子活動',
            '小朋友', '幼兒', '學前', '小學', '親子工作坊', '家庭'
        ]
        text_lower = text.lower()
        return any(kw in text_lower for kw in keywords)
    
    def crawl(self) -> List[Event]:
        """子類別需要實作此方法"""
        raise NotImplementedError("子類別必須實作 crawl() 方法")

if __name__ == '__main__':
    # 測試基礎功能
    print("測試 Playwright 基礎功能...")
    
    with PlaywrightCrawler('測試', 'https://example.com') as crawler:
        if crawler.navigate('https://www.google.com', wait_for='input[name="q"]'):
            print("✅ Playwright 工作正常")
        else:
            print("❌ Playwright 測試失敗")
