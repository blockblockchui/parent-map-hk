#!/usr/bin/env python3
"""
Google Sheet 座標查核工具 - 名稱搜尋版本
使用地點名稱搜尋 Google Places API（保留地址搜尋版本獨立運行）
"""

import os
import sys
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import requests
import gspread
from google.oauth2.service_account import Credentials

# 配置
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', './service-account.json')

TAB_NAME = "99_pin_to_check"
BASE_URL_PLACES = 'https://maps.googleapis.com/maps/api/place'

# OAuth 範圍
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.readonly'
]


@dataclass
class PlaceVerificationResult:
    row_index: int
    place_name: str
    address: str
    original_lat: float
    original_lng: float
    google_lat: Optional[float] = None
    google_lng: Optional[float] = None
    google_name: Optional[str] = None
    distance_meters: Optional[float] = None
    status: str = 'pending'
    error_message: Optional[str] = None


def get_gspread_client():
    """創建 gspread 客戶端"""
    if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(f"找不到 Service Account 文件: {GOOGLE_SERVICE_ACCOUNT_FILE}")
    
    creds = Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_FILE,
        scopes=SCOPES
    )
    
    return gspread.authorize(creds)


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    from math import radians, sin, cos, sqrt, atan2
    R = 6371000
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def find_place_by_text(query: str) -> Optional[Dict[str, Any]]:
    """使用 Places API (New) - Text Search 搜尋地點"""
    if not GOOGLE_PLACES_API_KEY:
        raise ValueError("請設置 GOOGLE_PLACES_API_KEY")
    
    endpoint = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': GOOGLE_PLACES_API_KEY,
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location',
    }
    body = {
        'textQuery': query,
        'languageCode': 'zh-HK',
        'maxResultCount': 1,
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=body, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and data.get('places'):
            place = data['places'][0]
            return {
                'place_id': place.get('id'),
                'name': place.get('displayName', {}).get('text'),
                'formatted_address': place.get('formattedAddress'),
                'geometry': {
                    'location': {
                        'lat': place.get('location', {}).get('latitude'),
                        'lng': place.get('location', {}).get('longitude'),
                    }
                }
            }
        elif 'error' in data:
            error_msg = data['error'].get('message', 'Unknown error')
            print(f"    API 錯誤: {error_msg}")
            return None
        else:
            return None
    except Exception as e:
        print(f"    請求失敗: {e}")
        return None


def verify_single_place(row_index, place_name, address, original_lat, original_lng, district=''):
    """使用名稱搜尋查核單一地點"""
    result = PlaceVerificationResult(
        row_index=row_index,
        place_name=place_name,
        address=address,
        original_lat=original_lat,
        original_lng=original_lng
    )
    
    # 搜尋策略（優先使用地點名稱）
    search_queries = [
        place_name,  # 優先使用地點名稱
        f"{place_name} {district}".strip() if district else '',
        f"{place_name} 香港",
        address,  # 最後嘗試地址
    ]
    
    # 過濾空查詢
    search_queries = [q for q in search_queries if q.strip()]
    
    google_place = None
    
    for query in search_queries:
        print(f"    嘗試搜尋: {query}")
        google_place = find_place_by_text(query)
        
        if google_place:
            break
        
        time.sleep(0.2)
    
    if not google_place:
        result.status = 'not_found'
        result.error_message = 'Google Places 找不到該地點'
        return result
    
    geometry = google_place.get('geometry', {})
    location = geometry.get('location', {})
    
    result.google_lat = location.get('lat')
    result.google_lng = location.get('lng')
    result.google_name = google_place.get('name')
    
    if result.google_lat and result.google_lng:
        result.distance_meters = calculate_distance(
            original_lat, original_lng,
            result.google_lat, result.google_lng
        )
        
        if result.distance_meters < 100:
            result.status = 'success'
        elif result.distance_meters < 500:
            result.status = 'warning'
        else:
            result.status = 'error'
    
    return result


def process_sheet():
    """主程序"""
    
    if not GOOGLE_PLACES_API_KEY:
        print("❌ 請設置環境變數 GOOGLE_PLACES_API_KEY")
        return
    
    if not GOOGLE_SHEET_ID:
        print("❌ 請設置環境變數 GOOGLE_SHEET_ID")
        return
    
    print("="*70)
    print("Google Sheet 座標查核工具 - 名稱搜尋版本")
    print("="*70)
    print(f"Sheet ID: {GOOGLE_SHEET_ID}")
    print(f"Tab: {TAB_NAME}")
    print("搜尋策略: 名稱優先")
    print("="*70)
    
    # 連接 Sheets
    print("\n🔌 正在連接 Google Sheets...")
    try:
        client = get_gspread_client()
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        worksheet = spreadsheet.worksheet(TAB_NAME)
        print("   ✅ 連接成功")
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        print("\n請確認：")
        print("  1. Service Account 文件正確")
        print("  2. Sheet ID 正確")
        print("  3. 已將 Service Account 分享給該 Sheet 作為編輯者")
        return
    
    # 讀取所有數據
    print(f"\n📖 正在讀取 '{TAB_NAME}'...")
    try:
        all_values = worksheet.get_all_values()
        print(f"   找到 {len(all_values)} 行數據")
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")
        return
    
    if len(all_values) < 2:
        print("❌ Sheet 數據不足")
        return
    
    # 解析標題行
    headers = all_values[0]
    print(f"   列名: {', '.join(headers[:5])}...")
    
    # 獲取列索引
    try:
        col_checked = headers.index('checked')
        col_place_name = headers.index('Name')
        col_address = headers.index('Address')
        try:
            col_district = headers.index('district')
        except ValueError:
            col_district = -1
        col_lat = headers.index('lat')
        col_lng = headers.index('lng')
        col_google_lat = headers.index('google_place_lat')
        col_google_lng = headers.index('google_place_lng')
        col_google_result = headers.index('google_result')
    except ValueError as e:
        print(f"❌ 找不到必要的列: {e}")
        print(f"   可用列: {headers}")
        return
    
    # 篩選未查核的行
    force_all = os.environ.get('FORCE_ALL', '').lower() == 'true'
    
    if force_all:
        unchecked_indices = list(range(2, len(all_values) + 1))
        print(f"   ⚠️  強制模式：檢查所有 {len(unchecked_indices)} 行")
    else:
        unchecked_indices = []
        for i, row in enumerate(all_values[1:], start=2):
            if len(row) > col_checked:
                checked_value = str(row[col_checked]).lower()
                if checked_value in ['false', '0', '', 'no']:
                    unchecked_indices.append(i)
        print(f"   其中 {len(unchecked_indices)} 行需要查核")
    
    if not unchecked_indices:
        print("\n✅ 所有地點都已查核完成！")
        return
    
    # 處理
    print(f"\n🔍 開始查核 {len(unchecked_indices)} 個地點（名稱搜尋）...\n")
    
    success_count = warning_count = error_count = not_found_count = 0
    batch_updates = []
    
    for idx, row_num in enumerate(unchecked_indices, 1):
        row = all_values[row_num - 1]
        
        place_name = row[col_place_name] if len(row) > col_place_name else ''
        address = row[col_address] if len(row) > col_address else ''
        district = row[col_district] if col_district >= 0 and len(row) > col_district else ''
        
        print(f"[{idx}/{len(unchecked_indices)}] 查核: {place_name}")
        
        try:
            lat_str = row[col_lat].replace(',', '.') if len(row) > col_lat else '0'
            lng_str = row[col_lng].replace(',', '.') if len(row) > col_lng else '0'
            original_lat = float(lat_str) if lat_str else 0
            original_lng = float(lng_str) if lng_str else 0
            
            result = verify_single_place(
                row_index=row_num,
                place_name=place_name,
                address=address,
                original_lat=original_lat,
                original_lng=original_lng,
                district=district
            )
            
            batch_updates.append({
                'row': row_num,
                'google_lat': str(result.google_lat) if result.google_lat else '',
                'google_lng': str(result.google_lng) if result.google_lng else '',
                'google_result': result.status,
                'checked': 'TRUE',
            })
            
            if result.status == 'success':
                success_count += 1
                print(f"   ✅ {place_name} - 正確 ({result.distance_meters:.1f}m)")
            elif result.status == 'warning':
                warning_count += 1
                print(f"   ⚠️  {place_name} - 警告 ({result.distance_meters:.1f}m)")
            elif result.status == 'error':
                error_count += 1
                print(f"   ❌ {place_name} - 錯誤 ({result.distance_meters:.1f}m)")
            else:
                not_found_count += 1
                print(f"   ❓ {place_name} - 未找到")
            
        except Exception as e:
            print(f"   💥 {place_name} - 處理失敗: {e}")
            error_count += 1
        
        time.sleep(0.5)
    
    # 批量更新 Sheet
    if batch_updates:
        print(f"\n💾 正在批量更新 {len(batch_updates)} 行到 Google Sheet...")
        try:
            cells_to_update = []
            for update in batch_updates:
                row = update['row']
                cells_to_update.extend([
                    gspread.Cell(row, col_google_lat + 1, update['google_lat']),
                    gspread.Cell(row, col_google_lng + 1, update['google_lng']),
                    gspread.Cell(row, col_google_result + 1, update['google_result']),
                    gspread.Cell(row, col_checked + 1, update['checked']),
                ])
            
            batch_size = 100
            for i in range(0, len(cells_to_update), batch_size):
                batch = cells_to_update[i:i+batch_size]
                worksheet.update_cells(batch)
                print(f"   已更新 {len(batch)} 個單元格...")
                time.sleep(1)
            
            print("   ✅ 批量更新完成")
        except Exception as e:
            print(f"   ❌ 批量更新失敗: {e}")
    
    # 統計
    print("\n" + "="*70)
    print("查核完成！（名稱搜尋版本）")
    print("="*70)
    print(f"✅ 正確:   {success_count}")
    print(f"⚠️  警告:   {warning_count}")
    print(f"❌ 錯誤:   {error_count}")
    print(f"❓ 未找到: {not_found_count}")
    print("="*70)
    print("\n✅ 所有結果已自動回填到 Google Sheet！")
    print("\n💡 提示：如需使用地址搜尋，請運行 verify_sheet_gspread.py")


if __name__ == '__main__':
    process_sheet()
