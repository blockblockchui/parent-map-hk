#!/usr/bin/env python3
"""
Event Radar - Final Playwright Runner with Google Sheets Export
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawlers.crawler_hkpl_final import HKPLCrawlerFinal
from crawlers.crawler_science_museum_final import ScienceMuseumCrawler
from crawlers.crawler_hkpm import HKPMCrawler
# from crawlers.crawler_hkyaf import HKYAFCrawler  # Cloudflare protected
# from crawlers.crawler_hkyaf_requests import HKYAFRequestsCrawler  # Cloudflare protected
from crawlers.crawler_lcsd_final import LCSDCrawler
from crawlers.crawler_taikwun import TaikwunCrawler
from crawlers.crawler_taikwun_requests import TaikwunRequestsCrawler
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
    print("   Multi-Source Version with Google Sheets Export")
    print("="*60)
    
    all_events = []
    
    # HKPL Crawler
    print("\n📚 Running HKPL Crawler...")
    try:
        with HKPLCrawlerFinal() as crawler:
            events = crawler.crawl()
            for e in events:
                all_events.append((e, 'crawler_hkpl_final.py'))
    except Exception as e:
        print(f"   ❌ HKPL 錯誤: {e}")
    
    # Science Museum Crawler
    print("\n🔬 Running Science Museum Crawler...")
    try:
        with ScienceMuseumCrawler() as crawler:
            events = crawler.crawl()
            for e in events:
                all_events.append((e, 'crawler_science_museum_final.py'))
    except Exception as e:
        print(f"   ❌ Science Museum 錯誤: {e}")
    
    # HKPM Crawler
    print("\n🏛️  Running HKPM Crawler...")
    try:
        with HKPMCrawler() as crawler:
            events = crawler.crawl()
            for e in events:
                all_events.append((e, 'crawler_hkpm.py'))
    except Exception as e:
        print(f"   ❌ HKPM 錯誤: {e}")
    
    # HKYAF Crawler (Cloudflare protected, skipped for now)
    print("\n🎨 Running HKYAF Crawler...")
    print("   ⚠️  HKYAF 網站有 Cloudflare 保護，暫時跳過")
    # Uncomment below when Cloudflare bypass is implemented
    # try:
    #     crawler = HKYAFRequestsCrawler()
    #     events = crawler.crawl()
    #     for e in events:
    #         all_events.append((e, 'crawler_hkyaf_requests.py'))
    # except Exception as e:
    #     print(f"   ❌ HKYAF 錯誤: {e}")
    
    # LCSD Crawler
    print("\n🏛️  Running LCSD Crawler...")
    try:
        with LCSDCrawler() as crawler:
            events = crawler.crawl()
            for e in events:
                all_events.append((e, 'crawler_lcsd_final.py'))
    except Exception as e:
        print(f"   ❌ LCSD 錯誤: {e}")
    
    # Taikwun Crawler (Requests-based, more reliable)
    print("\n🎭 Running Taikwun Crawler (Requests)...")
    try:
        crawler = TaikwunRequestsCrawler()
        events = crawler.crawl()
        for e in events:
            all_events.append((e, 'crawler_taikwun_requests.py'))
    except Exception as e:
        print(f"   ❌ Taikwun 錯誤: {e}")
    
    print(f"\n📊 總共找到 {len(all_events)} 個活動")
    return all_events

def write_to_sheets(events_with_source):
    """寫入 Google Sheets"""
    if not events_with_source:
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
    
    for event, crawler_source in events_with_source:
        event_dict = event.to_dict(crawler_source)
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
            event_dict['notes'],
            event_dict.get('crawler_source', '')
        ]
        
        worksheet.append_row(row)
        existing_ids.add(event_id)
        added += 1
        print(f"   ✅ 添加: {event.name[:40]}... [{crawler_source}]")
    
    print(f"\n✅ 寫入完成!")
    print(f"   新增: {added}")
    print(f"   跳過: {skipped}")
    print('='*60)
    
    return added, skipped

if __name__ == '__main__':
    # 執行爬蟲
    events_with_source = run_crawler()
    
    # 顯示結果
    print(f"\n{'='*60}")
    print("📋 活動列表:")
    print('='*60)
    for i, (e, source) in enumerate(events_with_source, 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date}")
        print(f"   地點: {e.location}")
        print(f"   來源: {source}")
        print()
    
    # 寫入 Google Sheets
    if events_with_source:
        added, skipped = write_to_sheets(events_with_source)
        print(f"\n🎉 完成! 共 {added} 個新活動已寫入 Google Sheets")
    else:
        print("\n❌ 沒有找到活動")
