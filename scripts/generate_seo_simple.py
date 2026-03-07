#!/usr/bin/env python3
"""
簡化版 SEO Description Generator - 分批執行
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
    district = row.get('district', '')
    category = row.get('category', '')
    
    # 檢查是否免費（通過 price_tier 或 price_tier_raw）
    price_tier = row.get('price_tier', row.get('priceTier', ''))
    is_free = str(price_tier).lower() in ['free', '免費', '0']
    
    # 檢查室內字段
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
    
    desc = f"{district}親子{location_type}{category}，{features}，適合{age_desc}兒童放電，{price_tag}入場，{transport}。"
    
    # 截斷到 120 字
    if len(desc) > 120:
        desc = desc[:117] + "..."
    
    return desc

def main():
    print("=" * 60)
    print("SEO Description Generator (簡化版)")
    print("=" * 60)
    
    # 連接 Google Sheets
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file("../pipeline/credentials.json", scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    
    # 只讀取需要的列（提高速度）
    print("\n讀取數據...")
    
    # 讀取所有記錄
    records = sheet.get_all_records()
    total = len(records)
    
    print(f"總計: {total} 筆記錄")
    print(f"目標欄位: 第 {SEO_COL} 列 (seo_description)")
    
    # 測試生成一個
    print(f"\n示例（第 1 筆）:")
    test = generate_seo_desc(records[0])
    print(f"  {test}")
    print(f"  長度: {len(test)} 字\n")
    
    # 確認繼續
    confirm = input("確認更新所有記錄? (yes/no): ")
    if confirm.lower() != 'yes':
        print("已取消")
        return
    
    # 開始更新
    print(f"\n開始更新...")
    updated = 0
    
    for i, row in enumerate(records, start=2):
        try:
            desc = generate_seo_desc(row)
            sheet.update_cell(i, SEO_COL, desc)
            updated += 1
            
            if updated % 10 == 0:
                print(f"  已更新 {updated} / {total} 筆...")
            
            # 每 10 筆暫停 1 秒避免 API 限制
            if updated % 10 == 0:
                time.sleep(1)
                
        except Exception as e:
            print(f"  錯誤第 {i} 行: {e}")
            time.sleep(5)
    
    print(f"\n✅ 完成! 共更新 {updated} 筆記錄")

if __name__ == "__main__":
    main()
