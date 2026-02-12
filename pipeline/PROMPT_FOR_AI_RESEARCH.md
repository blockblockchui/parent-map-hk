# Parent Map HK - 地點資料收集 Prompt

## 任務

請幫我收集香港親子地點（playhouse/室內遊樂場/親子餐廳）嘅詳細資料，並按以下格式輸出。

## 輸出格式（CSV 格式）

請以 **CSV 格式** 輸出，方便我直接複製到 Google Sheets：

```csv
place_id,name,name_en,region,district,address,lat,lng,category,indoor,age_min,age_max,price_tier,price_description,description,opening_hours,website_url,facebook_url,instagram_url,status,tips
```

## 欄位說明

| 欄位 | 必填 | 說明 | 示例 |
|------|------|------|------|
| place_id | ✓ | 自動生成 8 位英數字 | 系統自動生成 |
| name | ✓ | 中文名稱 | 樹屋 Baumhaus |
| name_en | | 英文名稱 | Baumhaus |
| region | ✓ | hk-island/kowloon/nt | hk-island |
| district | ✓ | 十八區之一 | 灣仔 |
| address | ✓ | 完整地址 | 灣仔灣仔道3號 |
| lat | ✓ | 緯度 | 22.2755 |
| lng | ✓ | 經度 | 114.1708 |
| category | ✓ | playhouse/park/museum/restaurant | playhouse |
| indoor | ✓ | TRUE/FALSE | TRUE |
| age_min | ✓ | 最小適合年齡 | 0 |
| age_max | ✓ | 最大適合年齡 | 6 |
| price_tier | ✓ | free/low/medium/high | medium |
| price_description | ✓ | 價格描述 | $100-200/位 |
| description | ✓ | 100-150字介紹 | 木製遊樂空間... |
| opening_hours | ✓ | 營業時間 | 09:30-18:00 |
| website_url | | 官網 | https://... |
| facebook_url | | FB 專頁 | https://facebook.com/... |
| instagram_url | | IG 帳號 | @baumhaus |
| status | ✓ | 固定填 Open | Open |
| tips | | 貼士/備註 | 需預約、有儲奶室等 |

## 重要規則

### 1. 資料來源要求（Evidence-first）
- 每個地點必須提供 **至少 1 個來源 URL**
- 優先使用：官方網站、官方社交媒體、可信媒體報導
- 避免：討論區傳言、無日期來源

### 2. 結業檢查（必做）
搜尋時請檢查：
- 是否有「結業」「停止營業」「closed」等關鍵字
- Google Maps 是否顯示「永久結業」
- 官方網站是否 404/顯示結業公告

**如發現疑似結業，請標記：**
```csv
status,notes
SuspectedClosed,網站無法訪問/最後貼文為2024年X月
```

### 3. 座標獲取
請提供準確座標：
- 方法 1：Google Maps 搜地點名，右鍵「複製經緯度」
- 方法 2：搜地址後睇 URL 入面嘅 @lat,lng

### 4. 價格分級
- **free**: 完全免費
- **low**: $0-100
- **medium**: $100-300
- **high**: $300+

## 輸出示例

```csv
place_id,name,name_en,region,district,address,lat,lng,category,indoor,age_min,age_max,price_tier,price_description,description,opening_hours,website_url,facebook_url,instagram_url,status,tips
auto-gen,樹屋 Baumhaus,Baumhaus,hk-island,灣仔,灣仔灣仔道3號,22.2755,114.1708,playhouse,TRUE,0,6,medium,$100-200/位,木製遊樂空間，提供創意藝術課程及探索樹屋。環境溫馨，設有嬰兒換片室，適合0-6歲幼兒自由探索。,09:30-18:00,https://www.baumhaus.com.hk/,https://facebook.com/baumhaus,baumhaus_hk,Open,需網上預約；設有哺乳室
auto-gen,香港兒童探索博物館,Hong Kong Children's Discovery Museum,hk-island,西環,西環皇后大道西550號,22.2871,114.1378,museum,TRUE,0,10,medium,$50-100/位,互動式博物館，讓小朋友透過遊戲探索科學、藝術和文化。設有多個主題展區，適合不同年齡層。,10:00-18:00（周三休）,https://www.hkcdm.org/,https://facebook.com/hkcdm,,Open,周三休館；建議預約時段
```

## 請提供

1. **地點名稱**（我可以幫你搜尋）
2. **或地區**（例如：「灣仔有咩新 playhouse？」）
3. **或主題**（例如：「有咩適合 2歲以下嘅室內遊樂場？」）

## 我會幫你

- ✅ 搜尋最新資料
- ✅ 檢查是否結業
- ✅ 獲取準確座標
- ✅ 按 CSV 格式整理
- ✅ 提供來源 URL

請告訴我你想搜尋咩地點或地區？
