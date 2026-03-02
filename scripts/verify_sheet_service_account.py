#!/usr/bin/env python3
"""
Google Sheet 自動座標查核工具（Service Account 版本）
使用 Service Account 認證，支援 Private Google Sheets
"""

import os
import sys
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

import requests

# 從環境變數讀取配置
GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID', '')

# Service Account 配置
# 請將 service account JSON 文件路徑設置在環境變數中
# 或將 JSON 內容直接設置在環境變數 GOOGLE_SERVICE_ACCOUNT_JSON 中
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE', '')
GOOGLE_SERVICE_ACCOUNT_JSON = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '')

TAB_NAME = "99_pin_to_check"

BASE_URL_PLACES = 'https://maps.googleapis.com/maps/api/place'
SHEETS_API_BASE = 'https://sheets.googleapis.com/v4'


@dataclass
class PlaceVerificationResult:
    """查核結果"""
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


class ServiceAccountAuth:
    """Service Account OAuth 認證"""
    
    def __init__(self):
        self.access_token = None
        self.token_expiry = 0
        
    def get_credentials(self):
        """獲取 Service Account 憑證"""
        # 優先從環境變數讀取 JSON
        if GOOGLE_SERVICE_ACCOUNT_JSON:
            return json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        
        # 其次從文件讀取
        if GOOGLE_SERVICE_ACCOUNT_FILE and os.path.exists(GOOGLE_SERVICE_ACCOUNT_FILE):
            with open(GOOGLE_SERVICE_ACCOUNT_FILE, 'r') as f:
                return json.load(f)
        
        raise ValueError("找不到 Service Account 憑證。請設置 GOOGLE_SERVICE_ACCOUNT_JSON 或 GOOGLE_SERVICE_ACCOUNT_FILE")
    
    def get_access_token(self) -> str:
        """獲取或刷新 Access Token"""
        if self.access_token and time.time() < self.token_expiry - 60:
            return self.access_token
        
        import jwt
        
        creds = self.get_credentials()
        
        # 構建 JWT
        now = int(time.time())
        payload = {
            'iss': creds['client_email'],
            'sub': creds['client_email'],
            'scope': 'https://www.googleapis.com/auth/spreadsheets',
            'aud': 'https://oauth2.googleapis.com/token',
            'iat': now,
            'exp': now + 3600,
        }
        
        # 簽名
        private_key = creds['private_key']
        assertion = jwt.encode(payload, private_key, algorithm='RS256')
        
        # 交換 Access Token
        response = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'assertion': assertion,
            },
            timeout=30
        )
        
        if response.status_code != 200:
            raise ValueError(f"獲取 Access Token 失敗: {response.text}")
        
        data = response.json()
        self.access_token = data['access_token']
        self.token_expiry = now + data['expires_in']
        
        return self.access_token


class GoogleSheetsClient:
    """Google Sheets API 客戶端（Service Account 版本）"""
    
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
        self.auth = ServiceAccountAuth()
    
    def _get_headers(self) -> Dict[str, str]:
        """獲取請求頭"""
        return {
            'Authorization': f'Bearer {self.auth.get_access_token()}',
            'Content-Type': 'application/json',
        }
    
    def read_tab(self, tab_name: str) -> List[Dict[str, Any]]:
        """讀取整個 tab"""
        url = f"{SHEETS_API_BASE}/spreadsheets/{self.sheet_id}/values/{tab_name}"
        
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        data = response.json()
        
        if 'values' not in data:
            error_msg = data.get('error', {}).get('message', 'Unknown error')
            raise ValueError(f"無法讀取 tab: {error_msg}")
        
        rows = data['values']
        if len(rows) < 2:
            return []
        
        headers = rows[0]
        
        results = []
        for i, row in enumerate(rows[1:], start=2):
            while len(row) < len(headers):
                row.append('')
            
            row_data = dict(zip(headers, row))
            row_data['_row_index'] = i
            results.append(row_data)
        
        return results
    
    def update_cells(self, tab_name: str, row: int, updates: Dict[str, str]):
        """更新單元格"""
        # 獲取標題行
        url = f"{SHEETS_API_BASE}/spreadsheets/{self.sheet_id}/values/{tab_name}!1:1"
        response = requests.get(url, headers=self._get_headers(), timeout=30)
        data = response.json()
        headers = data.get('values', [[]])[0]
        
        # 構建批量更新數據
        data_entries = []
        for col_name, value in updates.items():
            if col_name not in headers:
                print(f"    警告: 列 '{col_name}' 不存在")
                continue
            
            col_index = headers.index(col_name)
            col_letter = self._column_to_letter(col_index)
            
            data_entries.append({
                'range': f"{tab_name}!{col_letter}{row}",
                'values': [[value]]
            })
        
        if not data_entries:
            return
        
        # 批量更新
        url = f"{SHEETS_API_BASE}/spreadsheets/{self.sheet_id}/values:batchUpdate"
        body = {
            'valueInputOption': 'RAW',
            'data': data_entries
        }
        
        response = requests.post(
            url, 
            headers=self._get_headers(),
            json=body,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"    更新失敗: {response.text}")
    
    def _column_to_letter(self, index: int) -> str:
        """列索引轉字母"""
        result = ""
        while index >= 0:
            result = chr(ord('A') + (index % 26)) + result
            index = index // 26 - 1
        return result or 'A'


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """計算距離（米）"""
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
    """Google Places API 搜尋"""
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
    
    # 檢查配置
    if not GOOGLE_PLACES_API_KEY:
        print("❌ 請設置環境變數 GOOGLE_PLACES_API_KEY")
        return
    
    if not GOOGLE_SHEET_ID:
        print("❌ 請設置環境變數 GOOGLE_SHEET_ID")
        return
    
    try:
        # 測試獲取 Service Account
        auth = ServiceAccountAuth()
        auth.get_credentials()
    except ValueError as e:
        print(f"❌ {e}")
        print("\n請設置以下環境變數之一：")
        print("  1. GOOGLE_SERVICE_ACCOUNT_JSON - 直接貼上 JSON 內容")
        print("  2. GOOGLE_SERVICE_ACCOUNT_FILE - JSON 文件路徑")
        return
    
    print("="*70)
    print("Google Sheet 自動座標查核工具（Service Account）")
    print("="*70)
    print(f"Sheet ID: {GOOGLE_SHEET_ID}")
    print(f"Tab: {TAB_NAME}")
    print("="*70)
    
    # 連接 Sheets
    sheets = GoogleSheetsClient(GOOGLE_SHEET_ID)
    
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
    
    # 處理
    print(f"\n🔍 開始查核 {len(unchecked_rows)} 個地點...\n")
    
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
            
            # 回填
            updates = {
                'google_place_lat': str(result.google_lat) if result.google_lat else '',
                'google_place_lng': str(result.google_lng) if result.google_lng else '',
                'google_result': result.status,
                'checked': 'TRUE'
            }
            
            sheets.update_cells(TAB_NAME, row_index, updates)
            
            # 統計
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
    
    # 統計
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
