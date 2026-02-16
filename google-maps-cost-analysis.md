# Google Maps vs OpenStreetMap 成本評估 - Parent Map HK

## 現狀：OpenStreetMap + Leaflet

**成本：$0**
- 完全免費，無使用限制
- 使用 Leaflet 作為 map library
- 使用 OpenStreetMap tiles (免費 tier)

---

## Google Maps Platform 定價 (2025)

### 1. Maps JavaScript API (Dynamic Maps)
| 使用量 | 價格 |
|--------|------|
| 0 - 28,000 loads/月 | **免費** (在$200 credit內) |
| 28,001 - 100,000 | $7.00 per 1,000 |
| 100,001 - 500,000 | $5.60 per 1,000 |

### 2. Places API (Place Details)
| 數據類型 | 價格 |
|----------|------|
| Basic Data | $17.00 per 1,000 |
| Advanced Data | $20.00 per 1,000 |
| Preferred Data | $25.00 per 1,000 |

### 3. Geocoding API
- $5.00 per 1,000 requests

### 4. Directions API
- $5.00 per 1,000 requests

---

## 使用量估算

### 現階段 (30地點，新網站)
| 項目 | 估算月用量 | 成本 |
|------|-----------|------|
| Map loads | 1,000 - 5,000 | **$0** (在free tier內) |
| Place details | 500 - 2,000 | **$0** (在free tier內) |
| **總計** | | **$0/月** |

### 成長階段 (100地點，中等流量)
| 項目 | 估算月用量 | 成本 |
|------|-----------|------|
| Map loads | 50,000 | $154 (超過28k的部分) |
| Place details | 10,000 | $170 |
| **總計** | | **~$124/月** (扣除$200 credit) |

### 高流量階段 (500地點，熱門網站)
| 項目 | 估算月用量 | 成本 |
|------|-----------|------|
| Map loads | 200,000 | $952 |
| Place details | 50,000 | $850 |
| **總計** | | **~$1,602/月** |

---

## 免費額度

Google 提供 **每月 $200 USD credit**，直至另行通知。

這相當於：
- 約 **28,000** Dynamic Maps loads
- 或約 **11,700** Place Details requests

---

## 實施成本

### 技術成本
| 項目 | 工時估算 |
|------|---------|
| 安裝 @react-google-maps/api | 2小時 |
| 替換 Leaflet 組件 | 4-6小時 |
| 整合 Places API | 2-4小時 |
| 測試及 Bug fix | 2-4小時 |
| **總計** | **10-16小時** |

### 持續維護
- 需要監控 API 使用量
- 需要設置 billing alerts
- 可能需要實施 usage quotas

---

## 優缺點比較

### Google Maps

**優點：**
- 香港地區數據更準確
- Street View 功能
- Place details, 照片, 評論
- 用戶熟悉度高
- 路線規劃準確
- 載入速度快

**缺點：**
- 高流量時成本可觀
- 需要信用卡設定 billing
- 有潛在的 vendor lock-in

### OpenStreetMap (現狀)

**優點：**
- 完全免費
- 開源，無 lock-in
- 可 self-host tiles 若需要

**缺點：**
- 香港地區數據可能不完整
- 無 Street View
- 無內置地點詳情
- 路線規劃準確度較低
- 載入速度較慢

---

## 建議

### 短期 (現階段)
**維持 OpenStreetMap**
- 成本為 $0
- 流量低，OSM 已足夠
- 專注內容及功能開發

### 中期 (流量成長)
**考慮混合方案**
- 保留 OSM 作為預設
- Google Maps 作為進階選項
- 只在需要 Place details 時呼叫 Places API

### 長期 (高流量)
**評估轉用 Google Maps**
- 若網站有收入 (廣告/會員/預訂佣金)
- 成本可攤分至每用戶成本
- 或用 Mapbox (價格較低)

---

## 替代方案：Mapbox

若將來需要升級但想控制成本：

| 項目 | Mapbox | Google Maps |
|------|--------|-------------|
| 免費額度 | 50,000 loads/月 | 28,000 loads/月 |
| 超額價格 | $5 per 1,000 | $7 per 1,000 |
| 香港數據 | 良好 | 最佳 |

---

## 總結

| 階段 | 建議 | 預計月成本 |
|------|------|-----------|
| 現階段 (0-5k visits) | **維持 OSM** | $0 |
| 成長期 (5k-20k visits) | **維持 OSM** 或 **Mapbox** | $0-50 |
| 成熟期 (20k+ visits) | **Google Maps** | $100-500+ |

**關鍵指標**：當月活躍用戶超過 10,000 時，才認真考慮轉用 Google Maps。