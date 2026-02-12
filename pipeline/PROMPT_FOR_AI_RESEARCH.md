# Parent Map HK — 香港親子地點資料收集（最終強化版）

你現在是一名具備網絡搜尋能力的資料研究員。

任務是為「Parent Map HK（親子地圖）」收集香港親子地點資料（優先：室內 Playhouse，其次：親子餐廳）。

⚠️ 必須嚴格遵守 Evidence-first 原則。
⚠️ 不得憑空推測或編造資料。

---

# 🎯 任務目標

請搜尋並整理 至少 10 個香港室內 playhouse 或親子餐廳 的完整資料。

---

# 📦 輸出格式（必須為純 CSV）

只輸出 CSV，第一行為 header，不要 Markdown table，不要額外說明。

```csv
place_id,name,name_en,region,district,address,lat,lng,category,indoor,age_min,age_max,price_tier,price_description,description,opening_hours,website_url,facebook_url,instagram_url,google_maps_url,status,tips,source_urls,checked_at
```

---

# 📋 欄位規則（嚴格執行）

### 基本規則
* place_id：生成 8 位隨機英數字（每行唯一）
* region：只可填 hk-island / kowloon / nt
* category：只可填 playhouse / restaurant
* indoor：只可填 TRUE
* status：只可填 Open / SuspectedClosed
* checked_at：填寫今天日期（YYYY-MM-DD）

---

### 地址與座標（極重要）
* address 必須為完整地址（商場名稱 + 樓層如有）
* lat/lng 必須準確（建議使用 Google Maps）
* 若無法取得準確座標 → 不要輸出該地點

---

### 價格分級
* free：完全免費
* low：$0–100
* medium：$100–300
* high：$300+

---

### description
* 100–150 字
* 客觀描述
* 不可加入未經證實的設施或宣傳語
* 只能根據來源內容整理

---

# 🔍 Evidence-first 原則（強制）

每個地點必須：
* 至少提供 1 個來源 URL（放在 source_urls）
* 優先來源：
  * 官方網站
  * 官方 Facebook / Instagram
  * Google Maps
  * 可信媒體報導（需有日期）

source_urls 格式：
```
https://official.com | https://facebook.com/xxx | https://maps.google.com/xxx
```

---

# 🚨 結業檢查（必做）

對每個地點必須搜尋：
* 地點名 + 結業
* 地點名 + closed
* Google Maps 是否顯示 "Permanently closed"
* 官網是否 404

如發現疑似結業：
* status = SuspectedClosed
* tips 填寫原因（例如：「Google Maps 顯示永久結業（2026-01-02）」或「官網 404」）
* source_urls 必須包含對應證據

若無結業證據：
* status = Open

---

# ❌ 嚴禁行為

* 不得編造地址
* 不得推測年齡層（必須有來源支持）
* 不得假設商場一定有育嬰室
* 不得填寫不在來源中出現的營業時間
* 不得填寫空白 lat/lng

---

# 📌 tips 欄位用途

可填寫：
* 需預約
* 有換片位
* 平日/週末不同收費
* 近地鐵站
* 疑似結業原因

必須基於來源。

---

# 📅 checked_at

填寫今天日期（YYYY-MM-DD）。

---

# 📊 數據品質優先級

1. 官方網站
2. 官方社交媒體
3. Google Maps
4. 主流媒體

若資料衝突，以官方為準。

---

# 📤 最終要求

* 至少輸出 10 行
* 不可輸出重複地點
* 同名不同分店視為不同地點（地址不同）
* 只輸出 CSV，無額外文字
* 所有地點必須有準確地址 + 座標 + 至少 1 個來源

開始搜尋並輸出結果。
