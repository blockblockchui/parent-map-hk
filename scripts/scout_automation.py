#!/usr/bin/env python3
"""
Parent Map HK - Auto Scout Workflow
每日自動搜集親子地點資訊
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
import requests

# API Keys (從環境變數讀取)
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "")

# 現有地點資料（用於比對重覆）
EXISTING_LOCATIONS_FILE = "/root/.openclaw/workspace/parent-map-hk/data/locations.ts"
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
            content = f.read()
            # 簡單提取 name 欄位
            names = re.findall(r'name:\s*"([^"]+)"', content)
            existing_names.update(names)
    except Exception as e:
        log(f"讀取現有地點錯誤: {e}")
    return existing_names

def search_google_places(query, location="Hong Kong"):
    """使用 Google Places API 搜尋"""
    if not GOOGLE_PLACES_API_KEY:
        log("⚠️ Google Places API Key 未設定")
        return []
    
    try:
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{query} {location}",
            "key": GOOGLE_PLACES_API_KEY,
            "language": "zh-HK"
        }
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        
        if data.get("status") != "OK":
            log(f"Google Places API 錯誤: {data.get('status')}")
            return []
        
        results = []
        for place in data.get("results", [])[:5]:  # 只取前 5 個
            results.append({
                "name": place.get("name"),
                "address": place.get("formatted_address"),
                "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                "lng": place.get("geometry", {}).get("location", {}).get("lng"),
                "place_id": place.get("place_id"),
                "rating": place.get("rating"),
                "types": place.get("types", [])
            })
        return results
    except Exception as e:
        log(f"Google Places 搜尋錯誤: {e}")
        return []

def search_brave(query):
    """使用 Brave Search 搜集資訊"""
    if not BRAVE_API_KEY:
        log("⚠️ Brave API Key 未設定")
        return []
    
    try:
        url = "https://api.search.brave.com/res/v1/web/search"
        headers = {
            "X-Subscription-Token": BRAVE_API_KEY,
            "Accept": "application/json"
        }
        params = {"q": query, "count": 5, "search_lang": "zh"}
        
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        data = resp.json()
        
        results = []
        for result in data.get("web", {}).get("results", []):
            results.append({
                "title": result.get("title"),
                "url": result.get("url"),
                "description": result.get("description")
            })
        return results
    except Exception as e:
        log(f"Brave Search 錯誤: {e}")
        return []

def classify_category(types, name):
    """根據 Google Places types 分類"""
    type_mapping = {
        "museum": ["museum", "art_gallery"],
        "park": ["park", "amusement_park", "zoo"],
        "playhouse": ["playground", "shopping_mall", "store"],
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
    elif any(kw in name_lower for kw in ["park", "公園", "park"]):
        return "park"
    
    return "playhouse"  # 默認

def estimate_price_level(price_level):
    """估計價格類型"""
    if price_level is None:
        return "medium"
    mapping = {
        0: "free",
        1: "low",
        2: "medium",
        3: "high",
        4: "high"
    }
    return mapping.get(price_level, "medium")

def format_location_data(place_data, source="google"):
    """格式化為標準地點資料"""
    return {
        "id": f"auto_{datetime.now().strftime('%Y%m%d')}_{hash(place_data['name']) % 10000:04d}",
        "name": place_data["name"],
        "nameEn": "",  # 可選
        "category": classify_category(place_data.get("types", []), place_data["name"]),
        "district": "待確認",  # 需要人手或進一步處理
        "region": "hk-island",  # 默認，需要驗證
        "address": place_data.get("address", ""),
        "lat": place_data.get("lat", 0),
        "lng": place_data.get("lng", 0),
        "ageRange": [0, 12],  # 默認，需要驗證
        "indoor": True,  # 默認，需要驗證
        "priceType": estimate_price_level(place_data.get("price_level")),
        "hasBabyRoom": False,  # 未知
        "hasStrollerAccess": True,  # 默認
        "hasRestaurant": False,  # 未知
        "rainyDaySuitable": True,  # 默認室內
        "openingHours": "請查詢官網",
        "priceDescription": "請查詢官網",
        "phone": "",
        "website": f"https://www.google.com/maps/place/?q=place_id:{place_data.get('place_id', '')}",
        "description": f"從 {source} 自動搜集",
        "tips": "⚠️ 此資料未經人手確認，請自行驗證",
        "verified": False,  # ⭐ 標記為未驗證
        "autoDiscovered": True,  # ⭐ 標記為自動發現
        "discoveredAt": datetime.now().isoformat()
    }

def main():
    """主執行函數"""
    log("="*60)
    log("🚀 Parent Map Scout - 開始搜集")
    log("="*60)
    
    existing_names = load_existing_locations()
    log(f"📊 現有地點數量: {len(existing_names)}")
    
    # 搜尋關鍵字
    search_queries = [
        "kids playground indoor Hong Kong",
        "children museum Hong Kong",
        "親子餐廳 香港",
        "兒童遊樂場 室內",
        "playhouse Hong Kong"
    ]
    
    new_locations = []
    
    for query in search_queries[:2]:  # 每日只搜 2 個關鍵字（避免太多）
        log(f"\n🔍 搜尋: {query}")
        
        # Google Places 搜尋
        places = search_google_places(query)
        log(f"   找到 {len(places)} 個地點")
        
        for place in places:
            # 檢查是否已存在
            if place["name"] in existing_names:
                log(f"   ⏭️ 已存在: {place['name']}")
                continue
            
            # 格式化資料
            location = format_location_data(place, "Google Places")
            new_locations.append(location)
            log(f"   ✅ 新地點: {place['name']}")
    
    # 儲存結果
    if new_locations:
        output_file = WORKSPACE / f"auto_discovered_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(new_locations, f, ensure_ascii=False, indent=2)
        
        log(f"\n📁 已儲存 {len(new_locations)} 個新地點到: {output_file}")
        
        # 生成報告
        report = f"""
🎯 Parent Map Scout - 每日報告

📅 日期: {datetime.now().strftime('%Y-%m-%d %H:%M')}
🔍 搜尋關鍵字: {len(search_queries[:2])} 個
✅ 發現新地點: {len(new_locations)} 個

⚠️ 重要提醒:
這些地點資料來自自動搜集，標記為「未經人手確認」。
請檢查後再決定是否加入正式資料庫。

📁 檔案位置: {output_file}

下一步:
1. 檢視 {output_file}
2. 人手驗證資料準確性
3. 確認後加入 data/locations.ts
        """
        log(report)
        
        # 發送通知俾用戶（如果係 cron job 執行）
        print(report)
    else:
        log("\n📭 今日無發現新地點")
    
    log("="*60)
    log("✅ Scout 完成")
    log("="*60)

if __name__ == "__main__":
    main()
