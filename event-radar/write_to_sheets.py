#!/usr/bin/env python3
"""
Event Radar - 將活動寫入 Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import sys

# 確保能尋入 crawler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from crawler import run_crawlers

# Google Sheets 配置
SHEET_ID = os.getenv('GOOGLE_SHEETS_ID', '1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk')
WORKSHEET_NAME = '20_events'  # 新的事件 tab

# 欄位定義
COLUMNS = [
    'event_id',           # A: 唯一ID
    'name',               # B: 活動名稱
    'description',        # C: 描述
    'start_date',         # D: 開始日期
    'end_date',           # E: 結束日期
    'location',           # F: 地點
    'organizer',          # G: 主辦機構
    'source_url',         # H: 來源網址
    'image_url',          # I: 圖片網址
    'age_range',          # J: 適合年齡
    'is_free',            # K: 是否免費
    'category',           # L: 類別
    'venue_slug',         # M: 關聯地點 slug
    'status',             # N: 狀態（待審核/已審核/已結束）
    'created_at',         # O: 創建時間
    'notes',              # P: 備註（人手填寫）
]

def init_worksheet(sheet):
    """初始化 worksheet，如果不存在則創建"""
    try:
        worksheet = sheet.worksheet(WORKSHEET_NAME)
        print(f"✅ 找到現有 worksheet: {WORKSHEET_NAME}")
    except gspread.WorksheetNotFound:
        print(f"🆕 創建新 worksheet: {WORKSHEET_NAME}")
        worksheet = sheet.add_worksheet(title=WORKSHEET_NAME, rows=1000, cols=20)
        
        # 設置標題行
        worksheet.append_row(COLUMNS)
        
        # 設置欄寬
        worksheet.set_column_width(1, 120)   # event_id
        worksheet.set_column_width(2, 250)   # name
        worksheet.set_column_width(3, 350)   # description
        worksheet.set_column_width(4, 100)   # start_date
        worksheet.set_column_width(5, 100)   # end_date
        worksheet.set_column_width(6, 200)   # location
        worksheet.set_column_width(7, 150)   # organizer
        worksheet.set_column_width(8, 250)   # source_url
        worksheet.set_column_width(9, 250)   # image_url
        worksheet.set_column_width(10, 100)  # age_range
        worksheet.set_column_width(11, 80)   # is_free
        worksheet.set_column_width(12, 100)  # category
        worksheet.set_column_width(13, 150)  # venue_slug
        worksheet.set_column_width(14, 100)  # status
        worksheet.set_column_width(15, 120)  # created_at
        worksheet.set_column_width(16, 200)  # notes
        
        # 設置標題行格式
        worksheet.format('A1:P1', {
            'backgroundColor': {'red': 1, 'green': 0.8, 'blue': 0.4},
            'textFormat': {'bold': True}
        })
    
    return worksheet

def get_existing_event_ids(worksheet) -> set:
    """獲取已存在的活動 ID，用於去重"""
    try:
        # 獲取 A 欄所有值（跳過標題）
        ids = worksheet.col_values(1)[1:]
        return set(ids)
    except:
        return set()

def generate_event_id(event) -> str:
    """生成唯一活動 ID"""
    key = f"{event.name}_{event.start_date}_{event.organizer}"
    return hashlib.md5(key.encode()).hexdigest()[:12]

def append_events_to_sheet(worksheet, events):
    """將活動追加到 sheet"""
    existing_ids = get_existing_event_ids(worksheet)
    
    new_count = 0
    duplicate_count = 0
    
    for event in events:
        event_id = generate_event_id(event)
        
        # 檢查是否已存在
        if event_id in existing_ids:
            duplicate_count += 1
            continue
        
        # 準備行數據
        row = [
            event_id,
            event.name,
            event.description,
            event.start_date,
            event.end_date,
            event.location,
            event.organizer,
            event.source_url,
            event.image_url or '',
            event.age_range or '',
            '是' if event.is_free else '否',
            event.category,
            event.venue_slug or '',
            '待審核',
            datetime.now().strftime('%Y-%m-%d %H:%M'),
            ''  # notes
        ]
        
        worksheet.append_row(row)
        existing_ids.add(event_id)
        new_count += 1
    
    return new_count, duplicate_count

def main():
    print("=" * 60)
    print("Event Radar - 寫入 Google Sheets")
    print("=" * 60)
    
    # 連接 Google Sheets
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # 尋找 credentials 文件
    cred_paths = [
        "credentials.json",
        "../pipeline/credentials.json",
        "../../pipeline/credentials.json"
    ]
    
    creds = None
    for path in cred_paths:
        if os.path.exists(path):
            creds = Credentials.from_service_account_file(path, scopes=scope)
            print(f"✅ 使用憑證: {path}")
            break
    
    if not creds:
        print("❌ 找不到 credentials.json")
        return
    
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    
    # 初始化 worksheet
    worksheet = init_worksheet(sheet)
    
    # 執行爬蟲
    print("\n🔍 開始爬取活動...")
    events = run_crawlers()
    
    if not events:
        print("❌ 沒有找到活動")
        return
    
    # 寫入 sheet
    print(f"\n📝 寫入 {len(events)} 個活動到 Google Sheets...")
    new_count, duplicate_count = append_events_to_sheet(worksheet, events)
    
    print(f"\n✅ 完成!")
    print(f"   新增: {new_count} 個活動")
    print(f"   重複: {duplicate_count} 個活動（已跳過）")
    print(f"\n📊 請查看 Google Sheets: {WORKSHEET_NAME}")

if __name__ == '__main__':
    main()
