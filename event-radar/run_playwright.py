#!/usr/bin/env python3
"""
Playwright Event Crawler Master Runner
執行所有 Playwright 爬蟲並寫入 Google Sheets
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尋入所有爬蟲
from crawlers.crawler_hkpl import HKPLCrawler
from crawlers.crawler_science_museum import ScienceMuseumCrawler
from crawlers.crawler_lcsd import LCSDCrawler

from crawlers.base_playwright import Event
from typing import List

def run_all_crawlers() -> List[Event]:
    """執行所有 Playwright 爬蟲"""
    all_events = []
    
    crawlers_config = [
        {
            'name': '香港公共圖書館',
            'crawler_class': HKPLCrawler,
            'urls': [
                'https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week',
                'https://www.hkpl.gov.hk/tc/extension-activities/event-category/20414/other-talks-and-workshops',
                'https://www.hkpl.gov.hk/tc/extension-activities/event-category/23433/talks-workshops'
            ]
        },
        {
            'name': '香港科學館',
            'crawler_class': ScienceMuseumCrawler,
            'urls': [None]  # 使用默認 URL
        },
        {
            'name': '康文署',
            'crawler_class': LCSDCrawler,
            'urls': [None]
        },
    ]
    
    for config in crawlers_config:
        name = config['name']
        crawler_class = config['crawler_class']
        urls = config['urls']
        
        print(f"\n{'='*60}")
        print(f"🔍 [{name}] 開始爬取...")
        print('='*60)
        
        for url in urls:
            try:
                if url:
                    print(f"\n  URL: {url}")
                    crawler = crawler_class(url)
                else:
                    crawler = crawler_class()
                
                with crawler as c:
                    events = c.crawl()
                    all_events.extend(events)
                    print(f"  ✅ 成功: {len(events)} 個活動")
                    
            except Exception as e:
                print(f"  ❌ 錯誤: {e}")
                import traceback
                traceback.print_exc()
                continue
    
    # 去重
    seen = set()
    unique_events = []
    for event in all_events:
        key = f"{event.name}_{event.start_date}_{event.organizer}"
        if key not in seen:
            seen.add(key)
            unique_events.append(event)
    
    print(f"\n{'='*60}")
    print(f"📊 爬取完成!")
    print(f"   原始數據: {len(all_events)} 個")
    print(f"   去重後: {len(unique_events)} 個")
    print('='*60)
    
    return unique_events

def write_to_sheets(events: List[Event]):
    """寫入 Google Sheets"""
    if not events:
        print("\n❌ 沒有活動可寫入")
        return
    
    print(f"\n{'='*60}")
    print("📝 寫入 Google Sheets...")
    print('='*60)
    
    # 尋入寫入模組
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from write_to_sheets import main as write_main
    
    # 由於 write_to_sheets 需要修改以接受 events 參數
    # 這裡直接複制相關代碼
    
    import gspread
    from google.oauth2.service_account import Credentials
    import hashlib
    from datetime import datetime
    
    SHEET_ID = os.getenv('GOOGLE_SHEETS_ID', '1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk')
    WORKSHEET_NAME = '20_events'
    
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('pipeline/credentials.json', scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SHEET_ID)
    
    try:
        worksheet = sheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        print(f"❌ 找不到 {WORKSHEET_NAME} worksheet")
        return
    
    # 獲取現有 IDs 去重
    existing_ids = set()
    try:
        ids_col = worksheet.col_values(1)[1:]  # Skip header
        existing_ids = set(ids_col)
    except:
        pass
    
    added = 0
    skipped = 0
    
    for event in events:
        event_dict = event.to_dict()
        event_id = event_dict['event_id']
        
        if event_id in existing_ids:
            skipped += 1
            continue
        
        row = [
            event_dict['event_id'],
            event_dict['name'],
            event_dict['description'],
            event_dict['start_date'],
            event_dict['end_date'],
            event_dict['location'],
            event_dict['organizer'],
            event_dict['source_url'],
            event_dict['image_url'],
            event_dict['age_range'],
            event_dict['is_free'],
            event_dict['category'],
            event_dict['venue_slug'],
            event_dict['status'],
            event_dict['created_at'],
            event_dict['notes']
        ]
        
        worksheet.append_row(row)
        existing_ids.add(event_id)
        added += 1
    
    print(f"\n✅ 寫入完成!")
    print(f"   新增: {added} 個")
    print(f"   跳過（重複）: {skipped} 個")
    print('='*60)

if __name__ == '__main__':
    print("="*60)
    print("🎯 Playwright Event Crawler")
    print("   香港親子限時活動爬蟲系統")
    print("="*60)
    
    # 執行爬蟲
    events = run_all_crawlers()
    
    # 顯示結果
    print(f"\n{'='*60}")
    print("📋 活動預覽 (前 10 個):")
    print('='*60)
    for i, e in enumerate(events[:10], 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date} - {e.end_date}")
        print(f"   地點: {e.location}")
        print(f"   主辦: {e.organizer}")
        print()
    
    # 詢問是否寫入
    if events:
        confirm = input(f"\n確認寫入 {len(events)} 個活動到 Google Sheets? (yes/no): ")
        if confirm.lower() == 'yes':
            write_to_sheets(events)
        else:
            print("已取消寫入")
    else:
        print("\n❌ 沒有找到活動")
