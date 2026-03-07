#!/usr/bin/env python3
"""
SEO Description Generator for Parent Map HK
自動生成 seo_description 並寫入 Google Sheets
"""

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Google Sheets 配置
import os
SHEET_ID = os.getenv("GOOGLE_SHEETS_ID", "")  # 從環境變數讀取，或手動填入
WORKSHEET_NAME = "03_places"

if not SHEET_ID:
    print("❌ 錯誤：請設定 GOOGLE_SHEETS_ID 環境變數，或編輯腳本中的 SHEET_ID")
    print("   例如：export GOOGLE_SHEETS_ID='1wZo1WGSZ...'")
    exit(1)

# 分類對應的設施描述
CATEGORY_FEATURES = {
    "室內遊樂場": "設有滑梯、波波池及互動遊戲區",
    "親子餐廳": "設有兒童遊戲區及親子友善設施",
    "公園": "設有遊樂設施、草地及休憩空間",
    "圖書館": "設有兒童閱讀區及互動學習設施",
    "博物館": "設有互動展覽及兒童教育活動",
    "體育館": "設有兒童遊戲室及運動設施",
    "游泳池": "設有兒童池及嬉水設施",
    "商場": "設有親子設施及兒童遊戲區",
    "戲院": "設有親子場次及兒童友善設施",
    "Party Room": "設有派對設施及私人空間",
}

# 年齡範圍描述
def get_age_description(age_min, age_max):
    if not age_min and not age_max:
        return "各年齡"
    if age_min == 0 and age_max and age_max <= 3:
        return "幼兒"
    if age_min and age_min >= 6:
        return "兒童"
    if age_max and age_max >= 12:
        return f"{int(age_min)}歲以上" if age_min else "各年齡"
    if age_min and age_max:
        return f"{int(age_min)}-{int(age_max)}歲"
    return "各年齡"

# 交通描述
def get_transport_description(mtr_station, mtr_access):
    if mtr_station and mtr_access:
        return f"{mtr_station}港鐵站{mtr_access}分鐘即達"
    elif mtr_station:
        return f"鄰近{mtr_station}港鐵站"
    return "交通便利"

# 生成 SEO 描述模板
def generate_seo_description(row):
    """
    根據地點屬性生成 SEO 優化描述
    """
    district = row.get('district', '')
    category = row.get('category', '')
    name = row.get('name_zh', '')
    free_entry = row.get('free_entry', '').lower() in ['yes', 'true', '是', '免費']
    indoor = row.get('indoor', '').lower() in ['yes', 'true', '是', '室內']
    age_min = row.get('age_min')
    age_max = row.get('age_max')
    mtr_station = row.get('mtr_station_name', '')
    mtr_access = row.get('mtr_access_minutes', '')
    
    # 獲取設施描述
    features = CATEGORY_FEATURES.get(category, "設有親子友善設施")
    
    # 獲取年齡描述
    age_desc = get_age_description(age_min, age_max)
    
    # 獲取交通描述
    transport = get_transport_description(mtr_station, mtr_access)
    
    # 室內/室外標籤
    location_type = "室內" if indoor else "戶外"
    
    # 收費標籤
    price_tag = "免費" if free_entry else "收費"
    
    # 構建描述（控制在 60-100 字）
    parts = []
    
    # 開頭：地區 + 類型 + 親子
    parts.append(f"{district}親子{location_type}{category}")
    
    # 設施
    parts.append(f"，{features}")
    
    # 適合年齡 + 活動
    parts.append(f"，適合{age_desc}兒童放電")
    
    # 收費
    parts.append(f"，{price_tag}入場")
    
    # 交通
    parts.append(f"，{transport}。")
    
    description = "".join(parts)
    
    # 截斷到 120 字以內
    if len(description) > 120:
        description = description[:117] + "..."
    
    return description

def main():
    """主函數：連接 Google Sheets 並更新 seo_description"""
    
    # 設置 Google Sheets API 認證
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        # 嘗試多個可能的 credentials 路徑
        cred_paths = [
            "credentials.json",
            "../pipeline/credentials.json",
            "../credentials.json",
            "../../credentials.json"
        ]
        
        creds = None
        for path in cred_paths:
            try:
                creds = Credentials.from_service_account_file(path, scopes=scope)
                print(f"使用憑證: {path}")
                break
            except FileNotFoundError:
                continue
        
        if not creds:
            raise FileNotFoundError("找不到 credentials.json，請確保服務帳戶憑證存在")
        client = gspread.authorize(creds)
        
        # 打開工作表
        sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
        
        # 獲取所有記錄
        print("正在讀取 Google Sheets 數據...")
        print(f"  工作表: {WORKSHEET_NAME}")
        records = sheet.get_all_records()
        print(f"  成功讀取 {len(records)} 筆記錄")
        
        # 找到 header row
        headers = sheet.row_values(1)
        
        # 檢查是否已有 seo_description 欄位
        if 'seo_description' not in headers:
            # 找到 description_short 的位置並在旁邊插入
            try:
                desc_short_idx = headers.index('description_short')
                new_col = desc_short_idx + 2  # +2 因為 gspread 是 1-based
                sheet.update_cell(1, new_col, 'seo_description')
                print(f"已新增 'seo_description' 欄位在第 {new_col} 列")
            except ValueError:
                # 如果找不到，加到最後
                new_col = len(headers) + 1
                sheet.update_cell(1, new_col, 'seo_description')
                print(f"已新增 'seo_description' 欄位在最後（第 {new_col} 列）")
        else:
            new_col = headers.index('seo_description') + 1
            print(f"'seo_description' 欄位已存在（第 {new_col} 列）")
        
        # 生成並更新 seo_description
        print(f"\n開始生成 SEO 描述（共 {len(records)} 筆記錄）...")
        print("（每 50 筆批量更新，API 限制時會自動等待）\n")
        
        updates = []
        for i, row in enumerate(records, start=2):  # start=2 因為第 1 行是 header
            try:
                seo_desc = generate_seo_description(row)
                updates.append({
                    'row': i,
                    'col': new_col,
                    'value': seo_desc
                })
                
                if len(updates) >= 50:  # 每 50 筆批量更新
                    _batch_update(sheet, updates)
                    print(f"  ✅ 已更新 {i-1} / {len(records)} 筆...")
                    updates = []
                    time.sleep(2)  # 每次批量更新後等待 2 秒
                    
            except Exception as e:
                print(f"  ❌ 錯誤：第 {i} 行 - {e}")
                time.sleep(5)  # 錯誤後等待更長時間
        
        # 更新剩餘的
        if updates:
            _batch_update(sheet, updates)
        
        print(f"\n✅ 完成！共更新 {len(records)} 筆記錄的 seo_description")
        
        # 顯示幾個示例
        print("\n示例輸出：")
        for i in range(min(5, len(records))):
            row = records[i]
            print(f"  {row.get('name_zh', 'N/A')}: {generate_seo_description(row)[:60]}...")
        
    except Exception as e:
        print(f"錯誤：{e}")
        raise

import time

def _batch_update(sheet, updates, max_retries=3):
    """批量更新單元格，帶重試機制"""
    cells = []
    for update in updates:
        cell = sheet.cell(update['row'], update['col'])
        cell.value = update['value']
        cells.append(cell)
    
    for attempt in range(max_retries):
        try:
            sheet.update_cells(cells, value_input_option='RAW')
            return True
        except Exception as e:
            if '429' in str(e):
                wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                print(f"    API 配額限制，等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                raise
    
    # 如果還是失敗，逐個更新
    print("    批量更新失敗，改用逐個更新...")
    for update in updates:
        try:
            sheet.update_cell(update['row'], update['col'], update['value'])
            time.sleep(0.5)  # 每個請求間隔 0.5 秒
        except Exception as e:
            if '429' in str(e):
                time.sleep(5)
                sheet.update_cell(update['row'], update['col'], update['value'])
    return True

if __name__ == "__main__":
    main()
