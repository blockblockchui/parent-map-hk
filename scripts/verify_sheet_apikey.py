#!/usr/bin/env python3
"""
Google Sheet 自動座標查核工具（API Key 版本 - 需要 Sheet 公開）
"""

import os
import sys
import time
import json
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# 從環境變數讀取
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
GOOGLE_SHEETS_API_KEY = os.environ.get('GOOGLE_SHEETS_API_KEY', GOOGLE_PLACES_API_KEY)  # 使用同一個 Key
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')

TAB_NAME = "99_pin_to_check"
BASE_URL_PLACES = 'https://maps.googleapis.com/maps/api/place'
SHEETS_API_BASE = 'https://sheets.googleapis.com/v4'


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
    if not GOOGLE_PLACES_API_KEY:
        raise ValueError("請設置 GOOGLE_PLACES_API_KEY")
    
    endpoint = f"{BASE_URL_PLACES}/findplacefromtext/json"
    params = {
        'input': query,
        'inputtype': 'textquery',
        'fields': 'place_id,name,formatted_address,geometry',
        'key': GOOGLE_PLACES_API_KEY,
        'language': 'zh-HK',
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('candidates'):
            return data['candidates'][0]
        elif data.get('status') == 'ZERO_RESULTS':
            return None
        else:
            print(f"    API 錯誤: {data.get('status')}")
            return None
    except Exception as e:
        print(f"    請求失敗: {e}")
        return None


def verify_single_place(row_index, place_name, address, original_lat, original_lng, district=''):
    result = PlaceVerificationResult(
        row_index=row_index,
        place_name=place_name,
        address=address,
        original_lat=original_lat,
        original_lng=original_lng
    )
    
    search_queries = [
        f"{place_name} {district}".strip(),
        f"{place_name} 香港",
        place_name,
        address,
    ]
    
    google_place = None
    
    for query in search_queries:
        if not query.strip():
            continue
        
        print(f"    嘗試搜尋: {query}")
        google_place = find_place_by_text(query)
        
        if google_place:
            break
        
        time.sleep(0.2)
    
    if not google_place:
        result.status = 'not_found'
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


def read_sheet_with_retry(sheet_id, tab_name, api_key, max_retries=3):
    """帶重試的 Sheet 讀取"""
    url = f"{SHEETS_API_BASE}/spreadsheets/{sheet_id}/values/{tab_name}"
    params = {'key': api_key}
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if 'values' in data:
                return data['values']
            
            error = data.get('error', {})
            error_msg = error.get('message', 'Unknown error')
            
            if 'Quota exceeded' in error_msg:
                wait_time = (attempt + 1) * 30
                print(f"    配額限制，等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
                continue
            else:
                raise ValueError(f"無法讀取 tab: {error_msg}")
                
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"    錯誤: {e}，等待 {wait_time} 秒後重試...")
                time.sleep(wait_time)
            else:
                raise
    
    raise ValueError("超過最大重試次數")


def process_sheet():
    if not GOOGLE_PLACES_API_KEY:
        print("❌ 請設置環境變數 GOOGLE_PLACES_API_KEY")
        return
    
    if not GOOGLE_SHEET_ID:
        print("❌ 請設置環境變數 GOOGLE_SHEET_ID")
        return
    
    print("="*70)
    print("Google Sheet 自動座標查核工具（API Key）")
    print("="*70)
    print(f"Sheet ID: {GOOGLE_SHEET_ID}")
    print(f"Tab: {TAB_NAME}")
    print("="*70)
    print("\n⚠️  注意：此版本需要 Google Sheet 設為「任何人可檢視」")
    print("="*70)
    
    # 讀取數據
    print(f"\n📖 正在讀取 '{TAB_NAME}'...")
    try:
        rows = read_sheet_with_retry(GOOGLE_SHEET_ID, TAB_NAME, GOOGLE_SHEETS_API_KEY)
        print(f"   找到 {len(rows)} 行數據")
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")
        print("\n可能原因：")
        print("  1. Sheet 未設為公開（需要「任何人可檢視」）")
        print("  2. API Key 無權限訪問 Sheets API")
        print("  3. Sheet ID 錯誤")
        return
    
    if len(rows) < 2:
        print("❌ Sheet 數據不足")
        return
    
    # 解析標題行
    headers = rows[0]
    print(f"   列名: {', '.join(headers)}")
    
    # 轉換為字典
    data_rows = []
    for i, row in enumerate(rows[1:], start=2):
        while len(row) < len(headers):
            row.append('')
        row_data = dict(zip(headers, row))
        row_data['_row_index'] = i
        data_rows.append(row_data)
    
    # 篩選未查核的行
    unchecked_rows = [
        r for r in data_rows 
        if str(r.get('checked', '')).lower() in ['false', '0', '', 'no']
    ]
    
    print(f"   其中 {len(unchecked_rows)} 行需要查核")
    
    if not unchecked_rows:
        print("\n✅ 所有地點都已查核完成！")
        return
    
    # 處理
    print(f"\n🔍 開始查核 {len(unchecked_rows)} 個地點...")
    print("   （結果將保存到本地 JSON，不會自動回填 Sheet）\n")
    
    results = []
    success_count = warning_count = error_count = not_found_count = 0
    
    for i, row in enumerate(unchecked_rows, 1):
        row_index = row['_row_index']
        place_name = row.get('place_name', '')
        address = row.get('address', '')
        district = row.get('district', '')
        
        print(f"[{i}/{len(unchecked_rows)}] 查核: {place_name}")
        
        try:
            lat_str = row.get('lat', '0').replace(',', '.')
            lng_str = row.get('lng', '0').replace(',', '.')
            original_lat = float(lat_str) if lat_str else 0
            original_lng = float(lng_str) if lng_str else 0
            
            result = verify_single_place(
                row_index=row_index,
                place_name=place_name,
                address=address,
                original_lat=original_lat,
                original_lng=original_lng,
                district=district
            )
            
            results.append({
                'row_index': result.row_index,
                'place_name': result.place_name,
                'address': result.address,
                'original_lat': result.original_lat,
                'original_lng': result.original_lng,
                'google_lat': result.google_lat,
                'google_lng': result.google_lng,
                'distance_meters': result.distance_meters,
                'status': result.status,
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
    
    # 保存結果
    output_file = 'sheet_verification_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 統計
    print("\n" + "="*70)
    print("查核完成！")
    print("="*70)
    print(f"✅ 正確:   {success_count}")
    print(f"⚠️  警告:   {warning_count}")
    print(f"❌ 錯誤:   {error_count}")
    print(f"❓ 未找到: {not_found_count}")
    print("="*70)
    print(f"\n📄 詳細結果已保存至: {output_file}")
    print("\n請手動將結果回填到 Google Sheet：")
    print("  - google_place_lat")
    print("  - google_place_lng")
    print("  - google_result")
    print("  - checked (設為 TRUE)")


if __name__ == '__main__':
    process_sheet()
