# 香港親子地圖 - MVP 開發指南

## 🚀 快速啟動

```bash
cd parent-map-hk
npm install
npm run dev
```

開啟 http://localhost:3000

---

## 📋 待完成清單

### Week 1: 基礎功能 ✅
- [x] Next.js + TypeScript 專案結構
- [x] Tailwind CSS 配置
- [x] 資料結構定義
- [x] 篩選功能
- [x] 地點卡片 UI
- [ ] Mapbox 地圖整合
- [ ] 詳情頁面

### Week 2: 內容 + 優化
- [ ] 搜集 100 個地點資料
- [ ] 圖片處理
- [ ] SEO 優化
- [ ] 手機適配

### Week 3: 部署
- [ ] Vercel 部署
- [ ] Google Search Console
- [ ] 社交媒體專頁

---

## 🗺 地圖整合 (下一步)

需要 Mapbox access token:
1. 去 https://www.mapbox.com/ 註冊
2. 獲取 free tier token (50,000 loads/月)
3. 加入 `.env.local`:
```
NEXT_PUBLIC_MAPBOX_TOKEN=your_token_here
```

---

## 📝 新增地點資料

編輯 `data/locations.ts`，加入新地點:

```typescript
{
  id: "006",
  name: "新地點名稱",
  nameEn: "English Name",
  category: "playhouse", // museum/park/playhouse/restaurant/library
  district: "中環",
  region: "hk-island", // hk-island/kowloon/nt
  address: "詳細地址",
  lat: 22.2783,
  lng: 114.1555,
  ageRange: [0, 8],
  indoor: true,
  priceType: "low", // free/low/medium/high
  hasBabyRoom: true,
  hasStrollerAccess: true,
  hasRestaurant: false,
  rainyDaySuitable: true,
  openingHours: "10:00-18:00",
  priceDescription: "$100（1大1小）",
  phone: "1234 5678",
  website: "https://example.com",
  description: "簡短描述...",
  tips: "貼士..."
}
```

---

## 🎨 分類系統

### 地區
- 港島 (hk-island)
- 九龍 (kowloon)  
- 新界 (nt)

### 類型
- museum: 博物館/展覽
- park: 公園/戶外
- playhouse: 室內遊樂場
- restaurant: 親子餐廳
- library: 圖書館

### 價格
- free: 免費
- low: 低消費 ( <$50)
- medium: 中消費 ($50-200)
- high: 高消費 (>$200)

---

## 💡 內容搜集建議

優先加入:
1. 你已經去過的（有真實體驗）
2. 高知名度地點（科學館、海洋公園等）
3. 有特色的小眾地點

資料來源:
- OpenRice 親子標籤
- Klook 親子活動
- 康文署網站
- 親子 Facebook 群組

---

## 🏗 專案結構

```
app/
├── layout.tsx          # 全域布局 + SEO
├── page.tsx            # 主頁（地圖+列表）
├── globals.css         # 全局樣式
└── location/
    └── [id]/           # 地點詳情頁（待做）
        └── page.tsx

data/
└── locations.ts        # 所有地點資料

components/
├── Map.tsx             # Mapbox 地圖（待做）
├── FilterBar.tsx       # 篩選器
├── LocationCard.tsx    # 地點卡片
└── LocationDetail.tsx  # 詳情組件（待做）

public/
└── images/             # 地點圖片（待加入）
```

---

## 🔧 開發指令

```bash
# 本地開發
npm run dev

# 建構（測試）
npm run build

# 建構（生產，輸出到 dist/）
npm run build
# 輸出: dist/ 文件夾（可上傳任何 static hosting）
```

---

## 🌐 部署到 Vercel

```bash
# 安裝 Vercel CLI
npm i -g vercel

# 部署
vercel --prod
```

或連結 GitHub repo 自動部署。

---

## 📊 成功指標

- [ ] 100 個地點資料
- [ ] Google 收錄
- [ ] 月流量 1000+ visits
- [ ] Affiliate 首筆收入

---

**下一步你想先做邊樣？**
1. 加地圖功能
2. 搜集更多地點
3. 部署上線睇效果
