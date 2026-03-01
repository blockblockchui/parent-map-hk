#!/usr/bin/env python3
"""
Google Places API 地址座標查核工具
用於驗證 Parent Map HK 地點的地址和座標是否正確
"""

import os
import sys
import json
import time
import requests
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from urllib.parse import quote

# 請在環境變數中設置 GOOGLE_PLACES_API_KEY
# export GOOGLE_PLACES_API_KEY="your_api_key_here"

GOOGLE_PLACES_API_KEY = os.environ.get('GOOGLE_PLACES_API_KEY', '')
BASE_URL = 'https://maps.googleapis.com/maps/api/place'


@dataclass
class PlaceVerificationResult:
    """查核結果"""
    place_name: str
    address: str
    original_lat: float
    original_lng: float
    google_lat: Optional[float] = None
    google_lng: Optional[float] = None
    google_name: Optional[str] = None
    google_address: Optional[str] = None
    distance_meters: Optional[float] = None
    status: str = 'pending'  # pending, success, not_found, error
    error_message: Optional[str] = None


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """計算兩點之間的距離（米）"""
    from math import radians, sin, cos, sqrt, atan2
    
    R = 6371000  # 地球半徑（米）
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c


def find_place_by_text(query: str) -> Optional[Dict[str, Any]]:
    """
    使用 Find Place API 根據文字搜尋地點
    https://developers.google.com/maps/documentation/places/web-service/search-find-place
    """
    if not GOOGLE_PLACES_API_KEY:
        raise ValueError("請設置 GOOGLE_PLACES_API_KEY 環境變數")
    
    endpoint = f"{BASE_URL}/findplacefromtext/json"
    params = {
        'input': query,
        'inputtype': 'textquery',
        'fields': 'place_id,name,formatted_address,geometry',
        'key': GOOGLE_PLACES_API_KEY,
        'language': 'zh-HK',  # 返回繁體中文
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK' and data.get('candidates'):
            return data['candidates'][0]
        elif data.get('status') == 'ZERO_RESULTS':
            return None
        else:
            print(f"API 錯誤: {data.get('status')} - {data.get('error_message', '')}")
            return None
            
    except Exception as e:
        print(f"請求失敗: {e}")
        return None


def get_place_details(place_id: str) -> Optional[Dict[str, Any]]:
    """
    使用 Place Details API 獲取詳細資訊
    https://developers.google.com/maps/documentation/places/web-service/details
    """
    if not GOOGLE_PLACES_API_KEY:
        raise ValueError("請設置 GOOGLE_PLACES_API_KEY 環境變數")
    
    endpoint = f"{BASE_URL}/details/json"
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,geometry,url',
        'key': GOOGLE_PLACES_API_KEY,
        'language': 'zh-HK',
    }
    
    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK':
            return data.get('result')
        else:
            print(f"API 錯誤: {data.get('status')}")
            return None
            
    except Exception as e:
        print(f"請求失敗: {e}")
        return None


def verify_place(
    place_name: str,
    address: str,
    original_lat: float,
    original_lng: float,
    district: str = ''
) -> PlaceVerificationResult:
    """
    查核單個地點的座標
    
    Args:
        place_name: 地點名稱（如：大美督燒烤場）
        address: 地址（如：大埔大美督路）
        original_lat: 原始緯度
        original_lng: 原始經度
        district: 地區（可選，如：大埔）
    
    Returns:
        PlaceVerificationResult 查核結果
    """
    result = PlaceVerificationResult(
        place_name=place_name,
        address=address,
        original_lat=original_lat,
        original_lng=original_lng
    )
    
    # 構建搜尋查詢：優先使用「地點名稱 + 地區」
    search_queries = [
        f"{place_name} {district}",
        f"{place_name} 香港",
        place_name,
        address,
    ]
    
    google_place = None
    used_query = ''
    
    for query in search_queries:
        if not query.strip():
            continue
        
        print(f"  嘗試搜尋: {query}")
        google_place = find_place_by_text(query)
        
        if google_place:
            used_query = query
            break
        
        time.sleep(0.2)  # 避免速率限制
    
    if not google_place:
        result.status = 'not_found'
        result.error_message = 'Google Places 找不到該地點'
        return result
    
    # 獲取詳細資訊
    place_id = google_place.get('place_id')
    if place_id:
        details = get_place_details(place_id)
        if details:
            google_place.update(details)
    
    # 提取座標
    geometry = google_place.get('geometry', {})
    location = geometry.get('location', {})
    
    result.google_lat = location.get('lat')
    result.google_lng = location.get('lng')
    result.google_name = google_place.get('name')
    result.google_address = google_place.get('formatted_address')
    
    # 計算距離差異
    if result.google_lat and result.google_lng:
        result.distance_meters = calculate_distance(
            original_lat, original_lng,
            result.google_lat, result.google_lng
        )
        
        # 判斷狀態
        if result.distance_meters < 100:
            result.status = 'success'  # 100米內視為正確
        elif result.distance_meters < 500:
            result.status = 'warning'  # 500米內視為警告
        else:
            result.status = 'error'    # 超過500米視為錯誤
    
    return result


def print_result(result: PlaceVerificationResult):
    """打印查核結果"""
    print("\n" + "="*60)
    print(f"地點: {result.place_name}")
    print(f"地址: {result.address}")
    print("-"*60)
    
    if result.status == 'not_found':
        print("❌ 狀態: Google Places 找不到該地點")
        return
    
    print(f"原始座標: {result.original_lat:.6f}, {result.original_lng:.6f}")
    print(f"Google座標: {result.google_lat:.6f}, {result.google_lng:.6f}")
    print(f"距離差異: {result.distance_meters:.1f} 米")
    print("-"*60)
    print(f"Google名稱: {result.google_name}")
    print(f"Google地址: {result.google_address}")
    
    if result.status == 'success':
        print("✅ 狀態: 座標正確（<100米）")
    elif result.status == 'warning':
        print("⚠️  狀態: 座標有偏差（100-500米）")
    elif result.status == 'error':
        print("❌ 狀態: 座標錯誤（>500米）")


def verify_from_csv(csv_file: str, output_file: str = 'verification_results.json'):
    """
    從 CSV 文件批量查核地點
    
    CSV 格式：name,address,lat,lng,district
    """
    import csv
    
    results = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        places = list(reader)
    
    print(f"開始查核 {len(places)} 個地點...\n")
    
    for i, place in enumerate(places, 1):
        print(f"[{i}/{len(places)}] 查核: {place.get('name', 'Unknown')}")
        
        try:
            result = verify_place(
                place_name=place.get('name', ''),
                address=place.get('address', ''),
                original_lat=float(place.get('lat', 0)),
                original_lng=float(place.get('lng', 0)),
                district=place.get('district', '')
            )
            results.append(result)
            print_result(result)
            
        except Exception as e:
            print(f"  ❌ 查核失敗: {e}")
        
        # 避免速率限制（每秒 10 次請求）
        time.sleep(0.3)
    
    # 保存結果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([r.__dict__ for r in results], f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 查核完成！結果已保存至: {output_file}")
    
    # 統計
    success = sum(1 for r in results if r.status == 'success')
    warning = sum(1 for r in results if r.status == 'warning')
    error = sum(1 for r in results if r.status == 'error')
    not_found = sum(1 for r in results if r.status == 'not_found')
    
    print("\n統計：")
    print(f"  ✅ 正確: {success}")
    print(f"  ⚠️  警告: {warning}")
    print(f"  ❌ 錯誤: {error}")
    print(f"  ❓ 未找到: {not_found}")


# ============ 使用範例 ============

if __name__ == '__main__':
    
    # 檢查 API Key
    if not GOOGLE_PLACES_API_KEY:
        print("❌ 請先設置環境變數:")
        print("   export GOOGLE_PLACES_API_KEY='你的API密鑰'")
        print("\n獲取 API Key: https://developers.google.com/maps/documentation/places/web-service/get-api-key")
        sys.exit(1)
    
    # 範例 1：單個地點查核
    print("="*60)
    print("範例 1：單個地點查核")
    print("="*60)
    
    result = verify_place(
        place_name="大美督燒烤場",
        address="大埔大美督路",
        original_lat=22.471384,
        original_lng=114.232780,
        district="大埔"
    )
    print_result(result)
    
    # 範例 2：從 CSV 批量查核
    # verify_from_csv('places_to_verify.csv', 'results.json')
