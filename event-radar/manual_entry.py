#!/usr/bin/env python3
"""
手動活動資料輸入模板
用於無法自動爬取的網站，人手複製貼上活動資料
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SHEET_ID = '1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk'
WORKSHEET_NAME = '20_events'

def add_manual_events():
    """
    手動添加活動資料
    格式：每個活動是一個字典
    """
    
    # 示例：手動添加的活動
    # 你可以複製這個模板添加更多活動
    manual_events = [
        {
            'name': '示例：親子工作坊',
            'description': '這是一個示例活動描述',
            'start_date': '2026-03-15',
            'end_date': '2026-03-15',
            'location': '香港中央圖書館',
            'organizer': '康文署',
            'source_url': 'https://example.com/event',
            'image_url': '',
            'age_range': '3-6歲',
            'is_free': True,
            'category': '工作坊',
            'venue_slug': 'hong-kong-central-library',
        },
        # 在此添加更多活動...
    ]
    
    return manual_events

def write_events_to_sheet(events):
    """將活動寫入 Google Sheets"""
    if not events:
        print("沒有活動可寫入")
        return
    
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('../pipeline/credentials.json', scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet(WORKSHEET_NAME)
    
    # 獲取現有 IDs 去重
    existing_ids = set()
    try:
        ids_col = worksheet.col_values(1)[1:]  # Skip header
        existing_ids = set(ids_col)
    except:
        pass
    
    import hashlib
    added = 0
    
    for event in events:
        # 生成 ID
        key = f"{event['name']}_{event['start_date']}_{event['organizer']}"
        event_id = hashlib.md5(key.encode()).hexdigest()[:12]
        
        if event_id in existing_ids:
            print(f"跳過重複: {event['name']}")
            continue
        
        row = [
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
            ''  # notes
        ]
        
        worksheet.append_row(row)
        added += 1
        print(f"✅ 添加: {event['name']}")
    
    print(f"\\n總計添加 {added} 個活動")

if __name__ == '__main__':
    print("手動活動輸入工具")
    print("="*60)
    print("\\n請編輯 manual_events 列表添加活動資料")
    print("然後運行此腳本寫入 Google Sheets")
    print()
    
    events = add_manual_events()
    print(f"準備寫入 {len(events)} 個活動")
    
    confirm = input("\\n確認寫入? (yes/no): ")
    if confirm.lower() == 'yes':
        write_events_to_sheet(events)
    else:
        print("已取消")
