# Event Radar - 手動工作流程指南

使用瀏覽器插件快速抓取活動資料，然後導入 Google Sheets。

## 🛠️ 你需要安裝的工具

### 1. Chrome 插件：Instant Data Scraper

**安裝網址：**
```
https://chrome.google.com/webstore/detail/instant-data-scraper/ofaokhiedipichpaobibbnahnbeodieace
```

**為什麼選這個？**
- ✅ 免費
- ✅ 無需編程知識
- ✅ 自動識別表格和列表
- ✅ 一鍵導出 CSV
- ✅ 支持分頁

---

## 📋 工作流程

### 步驟 1：打開活動網頁

例如：
- https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week
- https://hk.science.museum/tc/web/scm/event-calendar.html
- https://www.hkpm.org.hk/tc/event

### 步驟 2：啟動 Instant Data Scraper

1. 點擊 Chrome 工具欄的插件圖標
2. 插件會自動分析頁面
3. 識別出活動列表後，會顯示預覽

### 步驟 3：調整選擇器（如有需要）

如果自動識別不準確：
1. 點擊 "Try another table"
2. 手動選擇活動區域
3. 使用 Parent/Child 按鈕調整範圍

### 步驟 4：導出 CSV

1. 點擊 "CSV" 按鈕
2. 下載檔案
3. 命名格式：`{來源}_{日期}.csv`
   - 例如：`hkpl_2026-03-07.csv`

### 步驟 5：導入 Google Sheets

有兩種方法：

#### 方法 A：使用腳本（推薦）

```bash
cd event-radar
source venv/bin/activate

# 導入 CSV
python import_csv.py hkpl_2026-03-07.csv "HKPL"
```

#### 方法 B：直接貼上

1. 打開 Google Sheets `20_events`
2. 選擇 CSV 內容（Ctrl+A, Ctrl+C）
3. 貼上到 Sheets（Ctrl+V）
4. 調整欄位對應關係

---

## 📝 CSV 欄位對應

Instant Data Scraper 抓取的欄位會自動映射：

| CSV 欄位 | Google Sheets | 說明 |
|---------|--------------|------|
| Name / Title | name | 活動名稱 |
| Date / 日期 | start_date, end_date | 自動解析 |
| Location / Venue | location | 地點 |
| Description / 描述 | description | 描述 |
| URL / Link | source_url | 來源 |

---

## 🎯 各來源抓取技巧

### HKPL 圖書館

**網址：** https://www.hkpl.gov.hk/tc/extension-activities/all-events/this-week

**技巧：**
1. 先用「進階搜索」篩選「親子」
2. 再使用插件抓取
3. 可能需要抓取 3 個分類頁：
   - this-week
   - other-talks-and-workshops
   - talks-workshops

### 香港科學館

**網址：** https://hk.science.museum/tc/web/scm/event-calendar.html

**技巧：**
1. 選擇「兒童節目」篩選
2. 插件可能只能抓到標題，需要手動點擊進入詳情頁獲取完整信息

### 康文署

**網址：** https://www.lcsd.gov.hk/clpss/tc/search/culture/GeneralSearchForm.do

**技巧：**
1. 在搜尋框輸入「親子」
2. 提交搜尋
3. 在結果頁使用插件
4. 注意分頁處理

### 故宮博物館

**網址：** https://www.hkpm.org.hk/tc/event

**技巧：**
1. 可能需要滾動加載更多
2. 使用插件的「延遲」功能等待內容加載

---

## ⏰ 建議時間表

| 頻率 | 任務 | 估計時間 |
|------|------|---------|
| **每週日** | 抓取本週活動 | 30 分鐘 |
| **每月 1 日** | 抓取下月活動 | 45 分鐘 |
| **每季度** | 更新所有來源 | 2 小時 |

---

## 💡 提高效率的技巧

### 1. 批量處理

一次打開多個分頁：
```
頁籤 1: HKPL 本週
頁籤 2: HKPL 講座
頁籤 3: HKPL 工作坊
```

### 2. 模板保存

Instant Data Scraper 可以保存選擇器配置，下次直接使用。

### 3. 使用快捷鍵

- `Ctrl+Shift+X`：啟動插件
- `Ctrl+S`：導出 CSV

---

## 📊 數據清理檢查清單

導入前檢查：

- [ ] 活動名稱是否完整
- [ ] 日期格式是否正確（YYYY-MM-DD）
- [ ] 地點是否具體（不只是「香港」）
- [ ] 是否為親子/兒童活動
- [ ] 連結是否可點擊
- [ ] 是否有重複活動

---

## 🐛 常見問題

### Q: 插件抓不到數據
**A:** 嘗試：
1. 滾動頁面讓所有內容加載
2. 點擊 "Locate Next Button" 設置分頁
3. 手動調整 Parent 選擇器

### Q: CSV 亂碼
**A:** 確保保存為 UTF-8 編碼。

### Q: 日期格式錯誤
**A:** 腳本會自動嘗試解析多種格式，但建議在 CSV 中統一為 YYYY-MM-DD。

---

## 📞 支援

如有問題，可以：
1. 查看 Instant Data Scraper 官方教程
2. 在 GitHub Issues 提問
3. 直接編輯 CSV 手動修復

---

**祝你抓取愉快！** 🎯
