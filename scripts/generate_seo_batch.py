#!/usr/bin/env python3
"""
批量更新 SEO Description - 更快版本
使用 update_cells 批量更新而非逐個 update_cell
"""

import gspread
import time
from google.oauth2.service_account import Credentials

SHEET_ID = "1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk"
WORKSHEET_NAME = "03_places"
SEO_COL = 33  # seo_description 欄位

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

def generate_seo_desc(row):
    """生成 SEO 描述"""
    district = row.get('district', row.get('district_id', ''))
    category = row.get('category', row.get('category_key', ''))
    
    # 檢查是否免費（通過 price_tier 字段）
    price_tier = row.get('price_tier', row.get('priceTier', ''))
    is_free = str(price_tier).lower() in ['free', '免費', '0']
    
    # 檢查是否室內
    indoor_val = row.get('indoor', row.get('indoor_raw', ''))
    is_indoor = str(indoor_val).lower() in ['yes', 'true', '是', '室內', 'indoor', '1']
    
    # 獲取年齡
    age_min = row.get('age_min', row.get('ageMin'))
    age_max = row.get('age_max', row.get('ageMax'))
    
    # 獲取交通
    mtr = row.get('mtr_station_name', row.get('mtrStationName', ''))
    
    # 構建描述
    location_type = "室內" if is_indoor else "戶外"
    price_tag = "免費" if is_free else "收費"
    features = CATEGORY_FEATURES.get(category, "設有親子友善設施")
    
    # 年齡描述
    if age_min and age_max:
        age_desc = f"{int(age_min)}-{int(age_max)}歲"
    elif age_min:
        age_desc = f"{int(age_min)}歲以上"
    else:
        age_desc = "各年齡"
    
    # 交通描述
    if mtr:
        transport = f"{mtr}港鐵站附近"
    else:
        transport = "交通便利"
    
    # 處理 district 可能為空的情況
    if district:
        desc = f"{district}親子{location_type}{category}，{features}，適合{age_desc}兒童放電，{price_tag}入場，{transport}。"
    else:
        desc = f"親子{location_type}{category}，{features}，適合{age_desc}兒童放電，{price_tag}入場，{transport}。"
    
    # 截斷到 120 字
    if len(desc) > 120:
        desc = desc[:117] + "..."
    
    return desc

def main():
    print("=" * 60)
    print("SEO Description Generator (批量更新版)")
    print("=" * 60)
    
    # 連接 Google Sheets
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("../pipeline/credentials.json", scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    
    print("\n讀取數據...")
    records = sheet.get_all_records()
    total = len(records)
    
    print(f"總計: {total} 筆記錄")
    print(f"目標欄位: 第 {SEO_COL} 列 (seo_description)")
    
    # 測試生成一個
    print(f"\n示例（第 1 筆）:")
    test = generate_seo_desc(records[0])
    print(f"  {test}")
    print(f"  長度: {len(test)} 字")
    
    print(f"\n開始生成所有描述並批量更新...")
    print("(每 100 筆批量更新一次，約需 2-3 分鐘)\n")
    
    # 生成所有描述
    descriptions = []
    for i, row in enumerate(records):
        desc = generate_seo_desc(row)
        descriptions.append(desc)
    
    print(f"✅ 已生成 {len(descriptions)} 個描述")
    print(f"開始批量更新到 Google Sheets...\n")
    
    # 批量更新
    batch_size = 100
    updated = 0
    
    for batch_start in range(0, len(descriptions), batch_size):
        batch_end = min(batch_start + batch_size, len(descriptions))
        batch = descriptions[batch_start:batch_end]
        
        # 準備 cell 列表
        cells = []
        for i, desc in enumerate(batch):
            row_num = batch_start + i + 2  # +2 因為第 1 行是 header
            cell = sheet.cell(row_num, SEO_COL)
            cell.value = desc
            cells.append(cell)
        
        # 批量更新
        try:
            sheet.update_cells(cells, value_input_option='RAW')
            updated += len(batch)
            print(f"  ✅ 已更新 {updated} / {total} 筆...")
            
            # 避免 API 限制，每批等待
            if batch_end < len(descriptions):
                time.sleep(2)
                
        except Exception as e:
            print(f"  ❌ 錯誤: {e}")
            print(f"     等待 10 秒後重試...")
            time.sleep(10)
            # 重試
            sheet.update_cells(cells, value_input_option='RAW')
            updated += len(batch)
            print(f"  ✅ 重試成功，已更新 {updated} / {total} 筆...")
    
    print(f"\n" + "=" * 60)
    print(f"✅ 完成! 共更新 {updated} 筆記錄")
    print("=" * 60)

if __name__ == "__main__":
    main()
