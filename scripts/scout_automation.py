#!/usr/bin/env python3
"""
Parent Map HK - Auto Scout Workflow (Updated for Places API New)
每日自動搜集親子地點資訊
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
import requests

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# API Keys (從環境變數讀取)
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")

# 現有地點資料（用於比對重覆）
EXISTING_LOCATIONS_FILE = "/root/.openclaw/workspace/parent-map-hk/data/locations.json"
WORKSPACE = Path("/root/.openclaw/workspace/parent-map-hk")
LOG_FILE = WORKSPACE / "scout_log.txt"

def log(message):
    """記錄日誌"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def load_existing_locations():
    """讀取現有地點名稱（用於比對重覆）"""
    existing_names = set()
    try:
        with open(EXISTING_LOCATIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for loc in data.get("locations", []):
                existing_names.add(loc.get("name", ""))
    except Exception as e:
        log(f"讀取現有地點錯誤: {e}")
    return existing_names

def search_google_places_new(query, location="Hong Kong"):
    """使用 Google Places API (New) 搜尋"""
    if not GOOGLE_PLACES_API_KEY:
        log("⚠️ Google Places API Key 未設定")
        return []
    
    try:
        # New Places API endpoint
        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.types,places.rating,places.priceLevel"
        }
        body = {
            "textQuery": f"{query} in {location}",
            "pageSize": 10,
            "languageCode": "zh-HK"
        }
        
        resp = requests.post(url, headers=headers, json=body, timeout=30)
        data = resp.json()
        
        if "error" in data:
            log(f"Google Places API 錯誤: {data['error'].get('message', 'Unknown error')}")
            return []
        
        results = []
        for place in data.get("places", []):
            location_data = place.get("location", {})
            results.append({
                "name": place.get("displayName", {}).get("text", ""),
                "address": place.get("formattedAddress", ""),
                "lat": location_data.get("latitude", 0),
                "lng": location_data.get("longitude", 0),
                "place_id": place.get("id", ""),
                "rating": place.get("rating"),
                "types": place.get("types", [])
            })
        return results
    except Exception as e:
        log(f"Google Places 搜尋錯誤: {e}")
        return []

def classify_category(types, name):
    """根據 Google Places types 分類"""
    type_mapping = {
        "museum": ["museum", "art_gallery"],
        "park": ["park", "amusement_park", "zoo"],
        "playhouse": ["playground", "shopping_mall", "store", "tourist_attraction"],
        "restaurant": ["restaurant", "food", "cafe", "meal_takeaway"],
        "library": ["library"]
    }
    
    for category, keywords in type_mapping.items():
        for t in types:
            if any(kw in t.lower() for kw in keywords):
                return category
    
    # 根據名稱關鍵字判斷
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["playhouse", "playroom", "遊樂", "play"]):
        return "playhouse"
    elif any(kw in name_lower for kw in ["museum", "館", "gallery"]):
        return "museum"
    elif any(kw in name_lower for kw in ["park", "公園"]):
        return "park"
    
    return "playhouse"  # 默認

def format_location_data(place_data):
    """格式化為標準地點資料"""
    return {
        "id": f"auto_{datetime.now().strftime('%Y%m%d')}_{abs(hash(place_data['name'])) % 10000:04d}",
        "name": place_data["name"],
        "nameEn": "",
        "category": classify_category(place_data.get("types", []), place_data["name"]),
        "district": "",
        "region": "hk-island",
        "address": place_data.get("address", ""),
        "lat": place_data.get("lat", 0),
        "lng": place_data.get("lng", 0),
        "ageRange": [0, 12],
        "indoor": True,
        "priceType": "medium",
        "hasBabyRoom": False,
        "hasStrollerAccess": True,
        "hasRestaurant": False,
        "rainyDaySuitable": True,
        "openingHours": "請查詢官網",
        "priceDescription": "請查詢官網",
        "description": f"從 Google Places 自動搜集",
        "tips": "⚠️ 此資料未經人手確認，請自行驗證",
        "website": f"https://www.google.com/maps/place/?q=place_id:{place_data.get('place_id', '')}",
        "verified": False,
        "autoDiscovered": True
    }

def main():
    """主執行函數"""
    log("="*60)
    log("🚀 Parent Map Scout - 開始搜集")
    log(f"API Key 狀態: {'✅ 已設定' if GOOGLE_PLACES_API_KEY else '❌ 未設定'}")
    log("="*60)
    
    if not GOOGLE_PLACES_API_KEY:
        log("❌ 請先設定 GOOGLE_PLACES_API_KEY 環境變數")
        return
    
    existing_names = load_existing_locations()
    log(f"📊 現有地點數量: {len(existing_names)}")
    
    # 搜尋關鍵字
    search_queries = [
        "kids playground indoor",
        "children museum",
        "親子活動中心",
        "indoor playroom",
        "family entertainment center"
    ]
    
    new_locations = []
    
    for query in search_queries:
        if len(new_locations) >= 3:  # 每日最多 3 個
            log(f"⏹️ 已達每日上限 (3個)，停止搜集")
            break
        
        log(f"\n🔍 搜尋: {query}")
        
        places = search_google_places_new(query)
        log(f"   找到 {len(places)} 個地點")
        
        for place in places:
            if place["name"] in existing_names:
                log(f"   ⏭️ 已存在: {place['name']}")
                continue
            
            location = format_location_data(place)
            new_locations.append(location)
            log(f"   ✅ 新地點: {place['name']}")
            
            if len(new_locations) >= 3:
                break
    
    # 儲存結果
    if new_locations:
        output_file = WORKSPACE / f"ready_to_add_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(new_locations, f, ensure_ascii=False, indent=2)
        
        log(f"\n📁 已儲存 {len(new_locations)} 個新地點")
        log(f"📁 檔案: {output_file}")
        
        report = f"""
🎯 Parent Map Scout - 報告

📅 日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}
✅ 發現新地點: {len(new_locations)} 個

⚠️ 請檢查 ready_to_add_*.json 後人手加入 Google Sheets
        """
        log(report)
        print(report)
    else:
        log("\n📭 今日無發現新地點")
    
    log("="*60)
    log("✅ Scout 完成")
    log("="*60)

if __name__ == "__main__":
    main()
