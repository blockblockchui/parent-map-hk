# 🎯 Event Radar - 香港親子限時活動雷達

自動爬取香港各機構的限時親子活動（工作坊、展覽、表演等），並整理到 Google Sheets 供人手審核。

## ✨ 功能特點

- 🔍 **自動爬取**：支援康文署、圖書館等多個來源
- 🖼️ **圖片抓取**：自動下載活動海報（可選 Cloudinary 託管）
- 📝 **Google Sheets 整合**：直接寫入 `20_events` tab
- 🔗 **地點關聯**：可關聯到現有放電地圖地點
- ♻️ **去重機制**：避免重複記錄
- ✅ **人手工審**：所有活動默認為「待審核」狀態

## 📁 檔案結構

```
event-radar/
├── crawler.py              # 爬蟲核心（BeautifulSoup + Requests）
├── write_to_sheets.py      # 寫入 Google Sheets
├── image_downloader.py     # 圖片下載器
├── run.py                  # 主執行腳本
├── requirements.txt        # 依賴套件
├── .env.example            # 環境變數範例
└── README.md               # 本檔案
```

## 🚀 快速開始

### 1. 安裝依賴

```bash
cd event-radar
pip install -r requirements.txt
```

### 2. 配置環境變數

```bash
cp .env.example .env
# 編輯 .env 檔案，填入你的設定
```

必要設定：
- `GOOGLE_SHEETS_ID`: 你的 Google Sheets ID

可選設定（圖片託管）：
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

### 3. 確保 Google Sheets API 權限

需要 `credentials.json` 檔案（服務帳戶金鑰）。

### 4. 執行爬蟲

```bash
# 基本執行（不抓圖片）
python run.py

# 包含圖片下載
python run.py --download-images

# 測試模式（只爬取不寫入）
python run.py --test
```

## 📊 Google Sheets 結構

新創建的 `20_events` tab 包含以下欄位：

| 欄位 | 說明 | 示例 |
|------|------|------|
| event_id | 唯一ID | a1b2c3d4e5f6 |
| name | 活動名稱 | 親子故事工作坊 |
| description | 描述 | 適合3-6歲兒童... |
| start_date | 開始日期 | 2026-03-15 |
| end_date | 結束日期 | 2026-03-15 |
| location | 地點 | 香港中央圖書館 |
| organizer | 主辦機構 | 康文署 |
| source_url | 來源網址 | https://... |
| image_url | 圖片網址 | https://... |
| age_range | 適合年齡 | 3-6歲 |
| is_free | 是否免費 | 是 |
| category | 類別 | 工作坊 |
| venue_slug | 關聯地點 slug | hong-kong-central-library |
| status | 狀態 | 待審核 |
| created_at | 創建時間 | 2026-03-07 10:30 |
| notes | 備註 | 人手填寫 |

## 🔗 與現有系統整合

### 關聯地點

在 `venue_slug` 欄位填入現有地點的 slug，例如：
- `hong-kong-central-library` → 香港中央圖書館
- `taikwun` → 大館

### 同步到 Supabase

審核後的活動可以批量導入 Supabase：

```sql
-- 從 Google Sheets 導出 CSV，然後導入
COPY events FROM 'events.csv' CSV HEADER;
```

## 🕐 自動化建議

### GitHub Actions（推薦）

創建 `.github/workflows/event-radar.yml`：

```yaml
name: Event Radar Crawler

on:
  schedule:
    # 每週一早上 9 點執行
    - cron: '0 1 * * 1'  # UTC 時間
  workflow_dispatch:  # 手動觸發

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r event-radar/requirements.txt
      - run: python event-radar/run.py
        env:
          GOOGLE_SHEETS_ID: ${{ secrets.GOOGLE_SHEETS_ID }}
```

### 本地 Cron

```bash
# 編輯 crontab
crontab -e

# 每週一早上 9 點執行
0 9 * * 1 cd /path/to/parent-map-hk/event-radar && python run.py >> /var/log/event-radar.log 2>&1
```

## 🛠️ 擴展新來源

要添加新的爬蟲來源，繼承 `BaseCrawler` 類別：

```python
from crawler import BaseCrawler, Event

class MyNewCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(name='新來源', base_url='https://example.com')
    
    def crawl(self) -> List[Event]:
        soup = self.fetch(self.base_url)
        # 解析邏輯...
        return events
```

然後在 `crawler.py` 的 `run_crawlers()` 中添加：

```python
crawlers = [
    LCSDCrawler(),
    HKPLCrawler(),
    MyNewCrawler(),  # 新增
]
```

## 💡 注意事項

1. **爬蟲禮儀**：已設置 2 秒延遲，避免對目標網站造成壓力
2. **圖片版權**：抓取的圖片僅供個人使用，請遵守各機構的使用條款
3. **數據準確性**：自動抓取的資料可能有誤，請人手審核後再發佈
4. **API 配額**：Google Sheets API 有配額限制，大量寫入時請注意

## 📞 支援

如有問題，請檢查：
1. `credentials.json` 是否存在且有正確權限
2. Google Sheet 是否已分享給服務帳戶
3. 環境變數是否正確設置

## 📝 License

與 parent-map-hk 專案相同
