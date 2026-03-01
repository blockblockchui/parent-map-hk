#!/usr/bin/env python3
"""
Google Sheet 自動座標查核工具
讀取 "99_pin_to_check" tab，使用 Google Places API 查核座標，並回填結果
"""

import os
import sys
import time
import json
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime

import requests

# Google API 設置
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
GOOGLE_SHEETS_API_KEY = os.environ.get('GOOGLE_SHEETS_API_KEY', '')

# Sheet 配置
SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')  # 你的 Google Sheet ID
TAB_NAME = "99_pin_to_check"

BASE_URL_PLACES = 'https://maps.googleapis.com/maps/api/place'
BASE_URL_SHEETS = 'https://sheets.googleapis.com/v4/spreadsheets'


@dataclass
class PlaceVerificationResult:
    """查核結果"""
    row_index: int  # Google Sheet 行號（1-based）
    place_name: str
    address: str
    original_lat: float
    original_lng: float
    google_lat: Optional[float] = None
    google_lng: Optional[float] = None
    google_name: Optional[str] = None
    distance_meters: Optional[float] = None
    status: str = 'pending'  # success, warning, error, not_found
    error_message: Optional[str] = None


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """計算兩點之間的距離（米）"""
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
    """使用 Google Places API 搜尋地點"""
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


def verify_single_place(
    row_index: int,
    place_name: str,
    address: str,
    original_lat: float,
    original_lng: float,
    district: str = ''
) -> PlaceVerificationResult:
    """查核單個地點"""
    result = PlaceVerificationResult(
        row_index=row_index,
        place_name=place_name,
        address=address,
        original_lat=original_lat,
        original_lng=original_lng
    )
    
    # 搜尋策略
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
        result.error_message = 'Google Places 找不到該地點'
        return result
    
    # 提取結果
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
        
        # 判斷狀態
        if result.distance_meters < 100:
            result.status = 'success'
        elif result.distance_meters < 500:
            result.status = 'warning'
        else:
            result.status = 'error'
    
    return result


class GoogleSheetsClient:
    """Google Sheets API 客戶端"""
    
    def __init__(self, sheet_id: str, api_key: str):
        self.sheet_id = sheet_id
        self.api_key = api_key
        self.base_url = f"{BASE_URL_SHEETS}/{sheet_id}"
    
    def read_tab(self, tab_name: str) -> List[Dict[str, Any]]:
        """讀取整個 tab 的數據"""
        url = f"{self.base_url}/values/{tab_name}"
        params = {'key': self.api_key}
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        
        if 'values' not in data:
            raise ValueError(f"無法讀取 tab: {data.get('error', {}).get('message', 'Unknown error')}")
        
        rows = data['values']
        if len(rows) < 2:
            return []
        
        # 第一行是標題
        headers = rows[0]
        
        # 轉換為字典列表
        results = []
        for i, row in enumerate(rows[1:], start=2):  # 從第2行開始（1-based）
            # 填充缺失的列
            while len(row) < len(headers):
                row.append('')
            
            row_data = dict(zip(headers, row))
            row_data['_row_index'] = i  # 保存行號用於後續更新
            results.append(row_data)
        
        return results
    
    def update_cells(self, tab_name: str, row: int, updates: Dict[str, str]):
        """
        更新指定行的單元格
        
        Args:
            tab_name: tab 名稱
            row: 行號（1-based）
            updates: {列名: 值} 的字典
        """
        # 先獲取標題行以確定列索引
        url = f"{self.base_url}/values/{tab_name}!1:1"
        params = {'key': self.api_key}
        
        response = requests.get(url, params=params, timeout=30)
        data = response.json()
        headers = data.get('values', [[]])[0]
        
        # 構建更新範圍和值
        ranges_and_values = []
        for col_name, value in updates.items():
            if col_name not in headers:
                print(f"    警告: 列 '{col_name}' 不存在")
                continue
            
            col_index = headers.index(col_name)
            col_letter = self._column_to_letter(col_index)
            cell_range = f"{tab_name}!{col_letter}{row}"
            
            ranges_and_values.append({
                'range': cell_range,
                'values': [[value]]
            })
        
        # 批量更新
        if ranges_and_values:
            url = f"{self.base_url}/values:batchUpdate"
            params = {'key': self.api_key}
            body = {
                'valueInputOption': 'RAW',
                'data': ranges_and_values
            }
            
            response = requests.post(url, params=params, json=body, timeout=30)
            if response.status_code != 200:
                print(f"    更新失敗: {response.json()}")
    
    def _column_to_letter(self, index: int) -> str:
        """將列索引轉換為字母（0 -> A, 1 -> B, ...）"""
        result = ""
        while index >= 0:
            result = chr(ord('A') + (index % 26)) + result
            index = index // 26 - 1
        return result or 'A'


def process_sheet():
    """主程序：處理 Google Sheet"""
    
    # 檢查配置
    if not GOOGLE_PLACES_API_KEY:
        print("❌ 請設置環境變數 GOOGLE_PLACES_API_KEY")
        return
    
    if not GOOGLE_SHEETS_API_KEY:
        print("❌ 請設置環境變數 GOOGLE_SHEETS_API_KEY")
        return
    
    if not SHEET_ID:
        print("❌ 請設置環境變數 GOOGLE_SHEET_ID")
        return
    
    print("="*70)
    print("Google Sheet 自動座標查核工具")
    print("="*70)
    print(f"Sheet ID: {SHEET_ID}")
    print(f"Tab: {TAB_NAME}")
    print("="*70)
    
    # 連接 Google Sheets
    sheets = GoogleSheetsClient(SHEET_ID, GOOGLE_SHEETS_API_KEY)
    
    # 讀取數據
    print(f"\n📖 正在讀取 '{TAB_NAME}'...")
    try:
        rows = sheets.read_tab(TAB_NAME)
        print(f"   找到 {len(rows)} 行數據")
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")
        return
    
    # 篩選未查核的行
    unchecked_rows = [
        r for r in rows 
        if str(r.get('checked', '')).lower() in ['false', '0', '', 'no']
    ]
    
    print(f"   其中 {len(unchecked_rows)} 行需要查核")
    
    if not unchecked_rows:
        print("\n✅ 所有地點都已查核完成！")
        return
    
    # 處理每個未查核的地點
    print(f"\n🔍 開始查核 {len(unchecked_rows)} 個地點...\n")
    
    success_count = 0
    warning_count = 0
    error_count = 0
    not_found_count = 0
    
    for i, row in enumerate(unchecked_rows, 1):
        row_index = row['_row_index']
        place_name = row.get('place_name', '')
        address = row.get('address', '')
        district = row.get('district', '')
        
        print(f"[{i}/{len(unchecked_rows)}] 查核: {place_name}")
        
        try:
            # 解析座標
            lat_str = row.get('lat', '0').replace(',', '.')
            lng_str = row.get('lng', '0').replace(',', '.')
            original_lat = float(lat_str) if lat_str else 0
            original_lng = float(lng_str) if lng_str else 0
            
            # 查核
            result = verify_single_place(
                row_index=row_index,
                place_name=place_name,
                address=address,
                original_lat=original_lat,
                original_lng=original_lng,
                district=district
            )
            
            # 準備更新數據
            updates = {
                'google_place_lat': str(result.google_lat) if result.google_lat else '',
                'google_place_lng': str(result.google_lng) if result.google_lng else '',
                'google_result': result.status,
                'checked': 'TRUE'
            }
            
            # 更新 Google Sheet
            sheets.update_cells(TAB_NAME, row_index, updates)
            
            # 統計
            if result.status == 'success':
                success_count += 1
                print(f"   ✅ {place_name} - 正確 (偏差 {result.distance_meters:.1f}m)")
            elif result.status == 'warning':
                warning_count += 1
                print(f"   ⚠️  {place_name} - 警告 (偏差 {result.distance_meters:.1f}m)")
            elif result.status == 'error':
                error_count += 1
                print(f"   ❌ {place_name} - 錯誤 (偏差 {result.distance_meters:.1f}m)")
            else:
                not_found_count += 1
                print(f"   ❓ {place_name} - 未找到")
            
        except Exception as e:
            print(f"   💥 {place_name} - 處理失敗: {e}")
            error_count += 1
        
        # 避免速率限制
        time.sleep(0.5)
    
    # 輸出統計
    print("\n" + "="*70)
    print("查核完成！")
    print("="*70)
    print(f"✅ 正確:   {success_count}")
    print(f"⚠️  警告:   {warning_count}")
    print(f"❌ 錯誤:   {error_count}")
    print(f"❓ 未找到: {not_found_count}")
    print("="*70)


if __name__ == '__main__':
    process_sheet()
