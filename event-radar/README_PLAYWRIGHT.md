# Playwright Event Crawler System

使用 Playwright 自動抓取 JavaScript 渲染的活動頁面。

## 📦 安裝

### 1. 安裝 Python 依賴

```bash
cd event-radar
pip install -r requirements-playwright.txt
```

### 2. 安裝 Playwright 瀏覽器

```bash
playwright install chromium
```

這會下載 Chromium 瀏覽器（約 130MB）。

## 🚀 使用

### 執行所有爬蟲

```bash
python run_playwright.py
```

### 執行單個爬蟲測試

```bash
# HKPL
python crawlers/crawler_hkpl.py

# 科學館
python crawlers/crawler_science_museum.py

# 康文署
python crawlers/crawler_lcsd.py
```

## 📁 檔案結構

```
event-radar/
├── crawlers/
│   ├── base_playwright.py          # 基礎 Playwright 類別
│   ├── crawler_hkpl.py             # HKPL 爬蟲
│   ├── crawler_science_museum.py   # 科學館爬蟲
│   └── crawler_lcsd.py             # 康文署爬蟲
├── run_playwright.py               # 主執行腳本
└── requirements-playwright.txt     # 依賴
```

## 🔧 技術細節

### 為什麼用 Playwright？

| 特性 | BeautifulSoup | Playwright |
|------|--------------|------------|
| 執行速度 | ⚡ 快 (1-2s) | 🐢 慢 (5-15s) |
| JavaScript 支援 | ❌ 無 | ✅ 有 |
| 記憶體佔用 | 💚 低 | 💛 中 (100-300MB) |
| 適合場景 | 靜態 HTML | 動態渲染 |

### 爬蟲流程

```
1. 啟動 Chromium 瀏覽器
2. 導航到目標 URL
3. 等待 JavaScript 渲染完成
4. 滾動加載更多內容
5. 提取活動數據
6. 關閉瀏覽器
```

## 📊 支援的來源

| 來源 | 網址 | 狀態 | 備註 |
|------|------|------|------|
| HKPL | hkpl.gov.hk | ✅ 已實作 | 3 個 URL |
| 科學館 | hk.science.museum | ✅ 已實作 | 兒童節目篩選 |
| 康文署 | lcsd.gov.hk | ✅ 已實作 | 分頁處理 |
| M+ | mplus.org.hk | ⏳ 待定 | API 限制 |
| 故宮 | hkpm.org.hk | ⏳ 待定 | JavaScript |
| 藝發局 | hkac.org.hk | ⏳ 待定 | calendar-event-item-title |
| 旅發局 | discoverhongkong.com | ⏳ 待定 | JSON API |
| H2OPE | h2opecentre.gov.hk | ⏳ 待定 | news-wrap |
| 青年藝術 | hkyaf.com | ⏳ 待定 | Box 3 |
| 大館 | taikwun.hk | ⏳ 待定 | press-article |

## 🛠️ 添加新爬蟲

```python
from crawlers.base_playwright import PlaywrightCrawler, Event

class MyNewCrawler(PlaywrightCrawler):
    def __init__(self):
        super().__init__(name='新來源', base_url='https://example.com')
    
    def crawl(self) -> List[Event]:
        events = []
        
        # 導航並等待渲染
        if not self.navigate(self.base_url, wait_for='.event-item'):
            return events
        
        # 提取活動
        items = self.page.query_selector_all('.event-item')
        for item in items:
            # 解析邏輯...
            event = Event(...)
            events.append(event)
        
        return events
```

## ⚠️ 注意事項

1. **執行時間**：每個爬蟲需要 10-30 秒（包含瀏覽器啟動）
2. **記憶體使用**：建議至少 4GB RAM
3. **網絡要求**：需要穩定的互聯網連接
4. **IP 限制**：頻繁爬取可能被封 IP，建議添加延遲

## 🐛 故障排除

### 瀏覽器啟動失敗

```bash
# 重新安裝瀏覽器
playwright install --force chromium
```

### 記憶體不足

```python
# 在 base_playwright.py 中減少並發
# 或增加 swap 空間
```

### 元素找不到

```python
# 嘗試不同的選擇器
wait_for='.event-item, [class*="event"], article'
```

## 📈 優化建議

1. **使用 headless=False 調試**：可以看到瀏覽器操作
2. **添加 screenshot**：保存錯誤時的頁面截圖
3. **設置合理的 timeout**：避免無限等待
4. **滾動加載**：處理無限滾動的頁面

## 📞 支援

如有問題，請檢查：
1. Playwright 瀏覽器是否正確安裝
2. 網址是否可訪問
3. 選擇器是否需要更新
