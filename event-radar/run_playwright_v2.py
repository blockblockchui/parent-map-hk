#!/usr/bin/env python3
"""
Event Radar - Playwright Crawler Runner (Improved Version)
執行所有改進版爬蟲並寫入 Google Sheets
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尋入改進版爬蟲
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'crawlers'))
from crawler_hkpl_v2 import HKPLCrawlerV2
from base_playwright import Event

from typing import List
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import hashlib

SHEET_ID = os.getenv('GOOGLE_SHEETS_ID', '1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk')
WORKSHEET_NAME = '20_events'

def run_all_crawlers() -> List[Event]:
    """執行所有爬蟲"""
    all_events = []
    
    crawlers_config = [
        {
            'name': 'HKPL 本週活動',
            'crawler_class': HKPLCrawlerV2,
            'urls': [
                'https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week',
            ]
        },
    ]
    
    for config in crawlers_config:
        name = config['name']
        crawler_class = config['crawler_class']
        urls = config['urls']
        
        print(f"\n{'='*60}")
        print(f"🔍 [{name}]")
        print('='*60)
        
        for url in urls:
            try:
                print(f"\n  URL: {url}")
                crawler = crawler_class(url)
                
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
    print(f"   原始: {len(all_events)} 個")
    print(f"   去重: {len(unique_events)} 個")
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
            break
    
    if not creds:
        print("❌ 找不到 credentials.json")
        return
    
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    
    try:
        worksheet = sheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        print(f"❌ 找不到 {WORKSHEET_NAME}")
        return
    
    # 獲取現有 IDs
    existing_ids = set()
    try:
        ids_col = worksheet.col_values(1)[1:]
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
    print(f"   新增: {added}")
    print(f"   跳過: {skipped}")
    print('='*60)

if __name__ == '__main__':
    print("="*60)
    print("🎯 Event Radar - Playwright Crawler")
    print("   改進版 - 智能選擇器")
    print("="*60)
    
    # 執行爬蟲
    events = run_all_crawlers()
    
    # 顯示結果
    print(f"\n{'='*60}")
    print("📋 活動預覽:")
    print('='*60)
    for i, e in enumerate(events, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date} - {e.end_date}")
        print(f"   地點: {e.location}")
        print(f"   主辦: {e.organizer}")
        print()
    
    # 自動寫入
    if events:
        write_to_sheets(events)
        print(f"\n🎉 完成! 共 {len(events)} 個活動已寫入 Google Sheets")
    else:
        print("\n❌ 沒有找到活動")
