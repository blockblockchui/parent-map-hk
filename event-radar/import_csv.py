#!/usr/bin/env python3
"""
CSV 導入工具 - 將 Instant Data Scraper 導出的 CSV 導入 Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
import csv
import io
import os
import hashlib
from datetime import datetime

SHEET_ID = os.getenv('GOOGLE_SHEETS_ID', '1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk')
WORKSHEET_NAME = '20_events'

def import_csv_to_sheets(csv_file_path: str, source_name: str = 'Manual'):
    """
    將 CSV 檔案導入 Google Sheets
    
    Args:
        csv_file_path: CSV 檔案路徑
        source_name: 來源名稱（用於記錄）
    """
    print(f"📥 導入 CSV: {csv_file_path}")
    print(f"   來源: {source_name}")
    
    # 讀取 CSV
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"   CSV 行數: {len(rows)}")
    
    if not rows:
        print("❌ CSV 為空")
        return
    
    # 顯示欄位
    print(f"   CSV 欄位: {list(rows[0].keys())}")
    
    # 連接 Google Sheets
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('../pipeline/credentials.json', scopes=scope)
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
        ids_col = worksheet.col_values(1)[1:]  # Skip header
        existing_ids = set(ids_col)
    except:
        pass
    
    # 處理每一行
    added = 0
    skipped = 0
    
    for row in rows:
        # 嘗試提取活動信息
        event = extract_event_from_row(row, source_name)
        
        if not event:
            continue
        
        # 生成 ID
        event_id = hashlib.md5(f"{event['name']}_{event['start_date']}_{event['organizer']}".encode()).hexdigest()[:12]
        
        if event_id in existing_ids:
            skipped += 1
            continue
        
        # 準備行數據
        sheet_row = [
            event_id,
            event['name'],
            event['description'],
            event['start_date'],
            event['end_date'],
            event['location'],
            event['organizer'],
            event['source_url'],
            event.get('image_url', ''),
            event.get('age_range', ''),
            '是' if event.get('is_free', True) else '否',
            event.get('category', '其他'),
            event.get('venue_slug', ''),
            '待審核',
            datetime.now().strftime('%Y-%m-%d %H:%M'),
            f"Source: {source_name}"
        ]
        
        worksheet.append_row(sheet_row)
        existing_ids.add(event_id)
        added += 1
    
    print(f"\n✅ 導入完成!")
    print(f"   新增: {added}")
    print(f"   跳過（重複）: {skipped}")

def extract_event_from_row(row: dict, source_name: str) -> dict:
    """從 CSV 行提取活動信息"""
    
    # 標準化欄位名（轉小寫，移除空格）
    normalized = {k.lower().replace(' ', '_').replace('-', '_'): v for k, v in row.items()}
    
    # 嘗試提取名稱
    name = (normalized.get('name') or 
            normalized.get('title') or 
            normalized.get('event_name') or 
            normalized.get('活動名稱') or 
            normalized.get('名稱') or
            '')
    
    if not name:
        return None
    
    # 嘗試提取日期
    date_str = (normalized.get('date') or 
                normalized.get('start_date') or 
                normalized.get('event_date') or 
                normalized.get('日期') or
                '')
    
    # 解析日期
    start_date, end_date = parse_date(date_str)
    
    # 嘗試提取地點
    location = (normalized.get('location') or 
                normalized.get('venue') or 
                normalized.get('place') or 
                normalized.get('地點') or 
                normalized.get('場地') or
                source_name)
    
    # 嘗試提取描述
    description = (normalized.get('description') or 
                   normalized.get('desc') or 
                   normalized.get('details') or 
                   normalized.get('描述') or 
                   normalized.get('詳情') or
                   name)
    
    # 嘗試提取連結
    source_url = (normalized.get('url') or 
                  normalized.get('link') or 
                  normalized.get('source_url') or 
                  normalized.get('網址') or 
                  normalized.get('連結') or
                  '')
    
    return {
        'name': name[:100],
        'description': description[:200],
        'start_date': start_date,
        'end_date': end_date,
        'location': location[:100],
        'organizer': source_name,
        'source_url': source_url,
        'is_free': True,  # 默認免費
        'category': '其他'
    }

def parse_date(date_str: str) -> tuple:
    """解析日期"""
    import re
    
    if not date_str:
        today = datetime.now().strftime('%Y-%m-%d')
        return today, today
    
    # 嘗試匹配 YYYY-MM-DD
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_str)
    if match:
        d = match.group(0)
        return d, d
    
    # 嘗試匹配 YYYY/MM/DD
    match = re.search(r'(\d{4})/(\d{2})/(\d{2})', date_str)
    if match:
        d = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
        return d, d
    
    # 嘗試匹配中文日期
    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
    if match:
        d = f"{match.group(1)}-{int(match.group(2)):02d}-{int(match.group(3)):02d}"
        return d, d
    
    today = datetime.now().strftime('%Y-%m-%d')
    return today, today

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print(f"  python {sys.argv[0]} <csv_file> [source_name]")
        print()
        print("示例:")
        print(f"  python {sys.argv[0]} hkpl_events.csv 'HKPL'")
        print(f"  python {sys.argv[0]} science_museum.csv 'Science Museum'")
        return
    
    csv_file = sys.argv[1]
    source = sys.argv[2] if len(sys.argv) > 2 else 'Manual'
    
    import_csv_to_sheets(csv_file, source)

if __name__ == '__main__':
    main()
