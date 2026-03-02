#!/usr/bin/env python3
"""
重置 Google Sheet 的 checked 列為 FALSE
"""

import os
import gspread
from google.oauth2.service_account import Credentials

GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', './service-account.json')
TAB_NAME = "99_pin_to_check"

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def reset_checked():
    if not GOOGLE_SHEET_ID:
        print("❌ 請設置 GOOGLE_SHEET_ID")
        return
    
    print("="*70)
    print("重置 Google Sheet - 將所有 checked 設為 FALSE")
    print("="*70)
    
    # 連接 Sheets
    creds = Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
    worksheet = spreadsheet.worksheet(TAB_NAME)
    
    # 讀取所有數據
    all_values = worksheet.get_all_values()
    headers = all_values[0]
    
    # 找到 checked 列索引
    try:
        col_checked = headers.index('checked')
    except ValueError:
        print("❌ 找不到 'checked' 列")
        return
    
    print(f"找到 {len(all_values) - 1} 行數據")
    print(f"正在重置所有行的 checked 為 FALSE...")
    
    # 批量重置所有行
    cells_to_update = []
    for row_num in range(2, len(all_values) + 1):
        cells_to_update.append(gspread.Cell(row_num, col_checked + 1, 'FALSE'))
    
    # 分批更新（每批 100 個）
    batch_size = 100
    for i in range(0, len(cells_to_update), batch_size):
        batch = cells_to_update[i:i+batch_size]
        worksheet.update_cells(batch)
        print(f"  已更新 {len(batch)} 行...")
    
    print(f"\n✅ 已重置 {len(cells_to_update)} 行的 checked 為 FALSE")
    print("現在可以重新運行查核腳本了！")

if __name__ == '__main__':
    reset_checked()
