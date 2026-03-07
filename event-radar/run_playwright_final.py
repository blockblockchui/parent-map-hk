#!/usr/bin/env python3
"""
Event Radar - Final Playwright Runner with Google Sheets Export
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawlers.crawler_hkpl_final import HKPLCrawlerFinal
from crawlers.base_playwright import Event
from typing import List

import gspread
from google.oauth2.service_account import Credentials

SHEET_ID = os.getenv('GOOGLE_SHEETS_ID', '1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk')
WORKSHEET_NAME = '20_events'

def run_crawler():
    """執行爬蟲"""
    print("="*60)
    print("🎯 Event Radar - Playwright Crawler")
    print("   Final Version with Google Sheets Export")
    print("="*60)
    
    with HKPLCrawlerFinal() as crawler:
        events = crawler.crawl()
    
    return events

def write_to_sheets(events: List[Event]):
    """寫入 Google Sheets"""
    if not events:
        print("\n❌ 沒有活動可寫入")
        return 0, 0
    
    print(f"\n{'='*60}")
    print("📝 寫入 Google Sheets...")
    print('='*60)
    
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    
    # 尋找 credentials
    cred_paths = [
        '../pipeline/credentials.json',
        'pipeline/credentials.json',
        '../../pipeline/credentials.json'
    ]
    
    creds = None
    for path in cred_paths:
        if os.path.exists(path):
            creds = Credentials.from_service_account_file(path, scopes=scope)
            print(f"✅ 使用憑證: {path}")
            break
    
    if not creds:
        print("❌ 找不到 credentials.json")
        return 0, 0
    
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    
    try:
        worksheet = sheet.worksheet(WORKSHEET_NAME)
        print(f"✅ 找到 worksheet: {WORKSHEET_NAME}")
    except gspread.WorksheetNotFound:
        print(f"❌ 找不到 {WORKSHEET_NAME}")
        return 0, 0
    
    # 獲取現有 IDs
    existing_ids = set()
    try:
        ids_col = worksheet.col_values(1)[1:]  # Skip header
        existing_ids = set(ids_col)
        print(f"   現有活動: {len(existing_ids)} 個")
    except:
        pass
    
    added = 0
    skipped = 0
    
    for event in events:
        event_dict = event.to_dict()
        event_id = event_dict['event_id']
        
        if event_id in existing_ids:
            skipped += 1
            print(f"   ⏭️  跳過（已存在）: {event.name[:40]}...")
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
        print(f"   ✅ 添加: {event.name[:40]}...")
    
    print(f"\n✅ 寫入完成!")
    print(f"   新增: {added}")
    print(f"   跳過: {skipped}")
    print('='*60)
    
    return added, skipped

if __name__ == '__main__':
    # 執行爬蟲
    events = run_crawler()
    
    # 顯示結果
    print(f"\n{'='*60}")
    print("📋 活動列表:")
    print('='*60)
    for i, e in enumerate(events, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print(f"   地點: {e.location}")
        print()
    
    # 寫入 Google Sheets
    if events:
        added, skipped = write_to_sheets(events)
        print(f"\n🎉 完成! 共 {added} 個新活動已寫入 Google Sheets")
    else:
        print("\n❌ 沒有找到活動")
