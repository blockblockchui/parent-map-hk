# Event Radar - Source Analysis Report

## 📊 21_event_sources 分析結果

從你的 Google Sheets `21_event_sources` tab 中找到 **11 個活動來源**：

### 來源列表

| # | 來源名稱 | URL | 技術方案 |
|---|---------|-----|---------|
| 1 | 香港科學館 | hk.science.museum | JavaScript 渲染 |
| 2 | 藝發局 | hkac.org.hk | 靜態 HTML |
| 3 | 旅發局 | discoverhongkong.com | JSON API |
| 4 | H2OPE | h2opecentre.gov.hk | JavaScript 渲染 |
| 5 | HKPL 本週 | hkpl.gov.hk | JavaScript 渲染 |
| 6 | HKPL 講座 | hkpl.gov.hk | JavaScript 渲染 |
| 7 | HKPL 工作坊 | hkpl.gov.hk | JavaScript 渲染 |
| 8 | 故宮 | hkpm.org.hk | JavaScript 渲染 |
| 9 | 青年藝術 | hkyaf.com | JavaScript 渲染 |
| 10 | 康文署 | lcsd.gov.hk | 搜尋結果頁 |
| 11 | M+ | mplus.org.hk | API (400 錯誤) |

---

## ⚠️ 技術挑戰

### 問題：JavaScript 渲染

**70% 的來源**使用 React/Vue/Angular 等前端框架，活動數據通過 JavaScript 動態加載：

```
網頁 HTML → 加載 JavaScript → JavaScript 請求 API → 渲染活動列表
```

BeautifulSoup 只能獲取第一步的 HTML，看不到最終渲染的活動數據。

### 影響的來源
- ❌ 香港科學館
- ❌ H2OPE
- ❌ HKPL 所有來源
- ❌ 故宮
- ❌ 青年藝術
- ❌ M+ (API 限制)

---

## 💡 解決方案

### 方案 A：使用 Puppeteer/Playwright（推薦，但有成本）

使用真正的瀏覽器自動化工具：

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(url)
    page.wait_for_selector('.event-item')  # 等待 JS 渲染
    html = page.content()
```

**優點：** 能處理所有 JavaScript 網站
**缺點：** 需要安裝 Chromium，執行時間長，可能有 memory 問題

---

### 方案 B：尋找隱藏 API（零成本，需分析）

很多網站雖然前端用 JavaScript，但會調用後端 API：

```javascript
// 在瀏覽器 DevTools Network tab 查看
fetch('/api/events?category=kids')
```

**優點：** 零成本，速度快
**缺點：** 每個網站需單獨分析，API 可能隨時改變

---

### 方案 C：手動輸入 + 瀏覽器插件（當前推薦）

使用瀏覽器插件快速複製活動資料：

**推薦工具：**
1. **Web Scraper** (Chrome Extension) - 可視化爬蟲
2. **Instant Data Scraper** (Chrome Extension) - 一鍵提取表格
3. **Data Miner** (Chrome Extension) - 進階數據提取

**工作流程：**
1. 打開活動網頁
2. 用插件選擇活動區域
3. 導出 CSV
4. 上傳到 Google Sheets

---

### 方案 D：RSS / Newsletter（自動化替代）

很多機構提供：
- RSS feed
- Email newsletter
- Telegram 頻道

可以：
1. 訂閱這些渠道的更新
2. 用 Gmail API 自動抓取郵件
3. 用 LLM 解析郵件內容

---

## 🛠️ 已創建的工具

為你準備了以下腳本：

| 腳本 | 用途 |
|------|------|
| `crawlers/hkpl_thisweek.py` | HKPL 爬蟲模板 |
| `crawlers/mplus_kids.py` | M+ API 爬蟲模板 |
| `crawlers/hkpm_events.py` | 故宮爬蟲模板 |
| `run_all_crawlers.py` | 執行所有爬蟲 |
| `get_sources.py` | 讀取 21_event_sources |
| `manual_entry.py` | 手動輸入工具 |

---

## 📋 建議的實施路徑

### 短期（本週）：手動輸入

1. 用 **Instant Data Scraper** 從每個網站提取活動
2. 整理成 CSV
3. 上傳到 Google Sheets `20_events`

預計時間：2-3 小時，可獲得 50-100 個活動

### 中期（下週）：API 分析

1. 對每個網站，打開瀏覽器 DevTools
2. 查看 Network tab，尋找 XHR/Fetch 請求
3. 如果能找到穩定的 API，更新對應的爬蟲腳本

### 長期（月內）：自動化

1. 如果有預算，部署 Playwright 版本的爬蟲
2. 設置 GitHub Actions 每週自動執行
3. Telegram 通知新活動

---

## 🎯 下一步行動

請選擇你想先嘗試的方案：

**A.** 我幫你寫一個 **Playwright 版本** 的爬蟲（可以處理 JavaScript，但需要安裝瀏覽器）

**B.** 我們先 **手動輸入 20-30 個活動** 作為測試數據，驗證整個流程

**C.** 我幫你分析 **哪幾個網站有隱藏的 API** 可以用

**D.** 提供 **Web Scraper 的詳細配置指南**，你自己操作

你想先試哪個？
