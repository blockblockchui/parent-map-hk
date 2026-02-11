#!/usr/bin/env python3
"""
Parent Map HK - Auto Quill + Observer
處理 Scout 搜集嘅資料，驗證後準備加入網站
"""

import json
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace/parent-map-hk")
DATA_FILE = WORKSPACE / "data" / "locations.ts"
LOG_FILE = WORKSPACE / "process_log.txt"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {message}"
    print(msg)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def load_json_file(filepath):
    """讀取自動搜集嘅 JSON 檔案"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"❌ 讀取檔案錯誤: {e}")
        return []

def validate_location(location):
    """Observer: 驗證資料完整性"""
    errors = []
    warnings = []
    
    # 必填欄位檢查
    required_fields = ["name", "lat", "lng", "category"]
    for field in required_fields:
        if not location.get(field):
            errors.append(f"缺少必要欄位: {field}")
    
    # 座標檢查
    lat = location.get("lat", 0)
    lng = location.get("lng", 0)
    if not (22.1 <= lat <= 22.6):
        errors.append(f"緯度異常: {lat}（應該喺香港範圍）")
    if not (113.7 <= lng <= 114.5):
        errors.append(f"經度異常: {lng}（應該喺香港範圍）")
    
    # 地址檢查
    address = location.get("address", "")
    if not address or address == "待確認":
        warnings.append("地址需要確認")
    
    # 價錢檢查
    if location.get("priceDescription") == "請查詢官網":
        warnings.append("價錢需要確認")
    
    # 年齡範圍檢查
    age_range = location.get("ageRange", [0, 12])
    if age_range[0] < 0 or age_range[1] > 18:
        errors.append("年齡範圍異常")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

def generate_location_code(location):
    """Quill: 生成 TypeScript 代碼"""
    return f'''  {{
    id: "{location['id']}",
    name: "{location['name']}",
    district: "{location.get('district', '待確認')}",
    region: "{location.get('region', 'hk-island')}",
    lat: {location['lat']},
    lng: {location['lng']},
    category: "{location['category']}",
    indoor: {str(location.get('indoor', True)).lower()},
    ageRange: {location.get('ageRange', [0, 12])},
    priceType: "{location.get('priceType', 'medium')}",
    priceDescription: "{location.get('priceDescription', '請查詢官網')}",
    description: "{location.get('description', '')}",
    address: "{location.get('address', '')}",
    website: "{location.get('website', '')}",
    tips: "{location.get('tips', '⚠️ 此資料未經人手確認')}",
    verified: false,
    autoDiscovered: true,
    hasBabyRoom: {str(location.get('hasBabyRoom', False)).lower()},
    hasStrollerAccess: {str(location.get('hasStrollerAccess', True)).lower()},
    hasRestaurant: {str(location.get('hasRestaurant', False)).lower()},
    rainyDaySuitable: {str(location.get('rainyDaySuitable', True)).lower()},
    openingHours: "{location.get('openingHours', '請查詢官網')}"
  }}'''

def main():
    log("="*60)
    log("📝 Parent Map Quill + Observer - 開始處理")
    log("="*60)
    
    # 尋找今日搜集嘅檔案
    today = datetime.now().strftime("%Y%m%d")
    scout_file = WORKSPACE / f"auto_discovered_{today}.json"
    
    if not scout_file.exists():
        log(f"⚠️ 今日無搜集檔案: {scout_file}")
        return
    
    # 讀取新地點
    new_locations = load_json_file(scout_file)
    log(f"📂 讀取到 {len(new_locations)} 個新地點")
    
    # 驗證每個地點
    validated = []
    rejected = []
    
    for loc in new_locations:
        log(f"\n🔍 驗證: {loc['name']}")
        result = validate_location(loc)
        
        if result["valid"]:
            log("   ✅ 通過驗證")
            validated.append(loc)
        else:
            log(f"   ❌ 驗證失敗: {', '.join(result['errors'])}")
            rejected.append({"location": loc, "errors": result["errors"]})
        
        if result["warnings"]:
            log(f"   ⚠️ 警告: {', '.join(result['warnings'])}")
    
    # 生成報告
    report = f"""
📊 處理報告

✅ 通過驗證: {len(validated)} 個
❌ 驗證失敗: {len(rejected)} 個

⚠️ 注意: 通過驗證只代表資料格式正確，
    並不保證內容準確性。

建議人手檢查項目:
1. 地址正確性
2. 價錢準確性
3. 開放時間
4. 適合年齡

下一步:
- 檢視下方生成嘅代碼
- 人手確認後再更新網站
- 或保持 autoDiscovered 標記上綫
"""
    log(report)
    
    # 生成準備加入嘅代碼
    if validated:
        output_file = WORKSPACE / f"ready_to_add_{today}.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("// 準備加入嘅新地點\n")
            f.write("// 複製以下內容到 data/locations.ts\n\n")
            
            for loc in validated:
                f.write(generate_location_code(loc))
                f.write(",\n\n")
        
        log(f"📁 已生成代碼檔案: {output_file}")
    
    # 儲存拒絕嘅地點（俾人手審查）
    if rejected:
        reject_file = WORKSPACE / f"rejected_{today}.json"
        with open(reject_file, "w", encoding="utf-8") as f:
            json.dump(rejected, f, ensure_ascii=False, indent=2)
        log(f"📁 拒絕地點已儲存: {reject_file}")
    
    log("="*60)
    log("✅ Quill + Observer 完成")
    log("="*60)
    
    # 輸出俾 cron job 捕捉
    print(f"\n🎯 總結: {len(validated)} 個地點準備就緒")

if __name__ == "__main__":
    main()
