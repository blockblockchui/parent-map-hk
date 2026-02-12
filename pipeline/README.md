# Parent Map HK - Data Pipeline

自動化 Data Pipeline 用於收集、驗證、更新香港親子地點資料。

## 🎯 核心功能

1. **自動收集** - 從 RSS/Sitemap/網頁抽取新地點
2. **智能驗證** - HTTP 檢查 → 內容 Hash → 搜尋證據 → LLM 分析
3. **人工覆核** - Google Sheets 作為工作台
4. **定期校驗** - 自動檢測結業/搬遷/資料更新
5. **輸出發佈** - 乾淨 JSON 供前端使用

## 🏗️ 系統架構

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Sources   │────▶│  Extractor  │────▶│  Validator  │
│ (RSS/Web)   │     │  (Parser)   │     │(Cheap→LLM)  │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                 │
┌─────────────┐     ┌─────────────┐            │
│  Frontend   │◀────│    JSON     │◀───────────┘
│  (GitHub    │     │   Export    │
│   Pages)    │     └─────────────┘
└─────────────┘            ▲
                           │
┌─────────────┐     ┌─────────────┐
│   Sheets    │────▶│   Staging   │
│   (CMS)     │     │  (Review)   │
└─────────────┘     └─────────────┘
```

## 🚀 快速開始

### 1. 安裝

```bash
cd pipeline
python3 -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. 設定

```bash
cp .env.example .env
# 編輯 .env，填入你的 API Keys
```

必需：
- `GOOGLE_SHEETS_ID` - 你的 Google Sheet ID
- `credentials.json` - Google Service Account 憑證

### 3. 初始化 Google Sheet

1. 建立新 Google Sheet
2. 分享畀 Service Account (Editor 權限)
3. 複製 Sheet ID 到 `.env`
4. 執行初始化：

```bash
python3 -c "from src.sheets_client import SheetsClient; SheetsClient().get_worksheet()"
```

### 4. 執行

```bash
# 收集新地點
python -m pipeline ingest --dry-run

# 校驗舊資料
python -m pipeline check --dry-run

# 輸出到 JSON
python -m pipeline export --dry-run
```

## 📋 詳細說明

### 收集新地點 (Ingest)

```bash
# 測試模式（唔會寫入 Sheets）
python -m pipeline ingest --dry-run

# 指定來源
python -m pipeline ingest --source "U Lifestyle"

# 正式執行
python -m pipeline ingest
```

流程：
1. 讀取 `config/sources.yaml` 定義嘅來源
2. 抽取候選地點
3. 檢查重複
4. 執行驗證（HTTP → Hash → Search → LLM）
5. 寫入 Sheets（status=PendingReview）

### 校驗舊資料 (Freshness Check)

```bash
# 測試模式
python -m pipeline check --dry-run

# 輸出需覆核清單
python -m pipeline check --export-flagged review_queue.csv

# 正式執行
python -m pipeline check
```

只會處理 `next_check_at <= now` 嘅地點，根據 risk_tier 決定檢查頻率：
- high: 7 日
- medium: 14-30 日
- low: 60-90 日

### 輸出 JSON (Export)

```bash
# 比較現有檔案
python -m pipeline export --compare

# 包含待審核地點
python -m pipeline export --include-pending

# Git commit + push
python -m pipeline export --git-commit --git-push
```

輸出欄位只包含前端需要嘅資訊，debug/evidence 欄位會移除。

## ⚙️ 設定檔

### `config/sources.yaml`

定義資料來源：

```yaml
sources:
  - name: "U Lifestyle 親子"
    type: rss
    url: "https://www.ulifestyle.com.hk/rss/..."
    recency_window_days: 30
    category_keywords: ["playhouse", "室內遊樂場"]
    enabled: true

  - name: "Oh!爸媽"
    type: sitemap
    url: "https://www.ohmykids.hk/sitemap.xml"
    selectors:
      title_selector: "h1.entry-title"
      content_selector: "div.entry-content"
```

支援類型：
- `rss` - RSS feed
- `sitemap` - XML sitemap
- `tag_page` - 分類/標籤頁面
- `manual` - 手工輸入

### `.env`

環境變數：

```bash
GOOGLE_SHEETS_ID=your_sheet_id
OPENAI_API_KEY=sk-...  # 可選
BING_API_KEY=...       # 可選

# Pipeline 設定
LOG_LEVEL=INFO
CACHE_TTL_HOURS=24
MAX_CONCURRENT_REQUESTS=5
RATE_LIMIT_REQUESTS_PER_MINUTE=30
```

## 📊 Google Sheets 結構

主要欄位：

| 欄位 | 說明 |
|-----|------|
| place_id | UUID，永恆主鍵 |
| name | 地點名稱 |
| district | 地區（十八區） |
| lat/lng | 座標 |
| category | 類別（playhouse/park/museum） |
| status | Open/PendingReview/NeedsReview/Alert/SuspectedClosed/Closed |
| validation_stage | 驗證階段 |
| confidence | 信心分數（0-100） |
| evidence_urls | 證據 URL |
| last_checked_at | 上次檢查時間 |
| next_check_at | 下次檢查時間 |

Filter Views 建議：
- **待審新地點** - status = PendingReview
- **需覆核** - status in (NeedsReview, Alert, SuspectedClosed)
- **到期檢查** - next_check_at <= today

## 🔒 安全注意

1. **credentials.json** - 唔好提交到 Git，已加入 .gitignore
2. **.env** - 包含 API keys，唔好分享
3. **Service Account** - 只授權必要嘅 Sheets，唔好畀佢睇晒你個 Drive

## 🐛 故障排除

### Module not found
```bash
cd pipeline
python3 -m src.ingest_sources  # 正確
# 唔好：python3 src/ingest_sources.py
```

### Google Sheets 權限錯誤
- 確認已分享 Sheet 畀 Service Account email
- 確認 API 已啟用（Sheets API + Drive API）

### Rate limit
- 降低 `MAX_CONCURRENT_REQUESTS`
- 增加 `RATE_LIMIT_REQUESTS_PER_MINUTE`

## 📝 開發

### 新增來源

1. 編輯 `config/sources.yaml`
2. 測試抽取：`python3 -m src.ingest_sources --source "你的來源" --dry-run`
3. 調整 selectors 直到成功
4. 正式執行

### 新增驗證規則

1. 編輯 `src/validate_places.py`
2. 喺 `CheapValidator` 或 `LLMValidator` 加規則
3. 測試：`python3 -m src.validate_places --place-id xxx`

## 🗓️ 排程建議

### 使用 cron (Linux/macOS)

```bash
# 每日早上 9 點收集新地點
0 9 * * * cd /path/to/pipeline && /path/to/venv/bin/python -m pipeline ingest

# 每周一早上 10 點校驗舊資料
0 10 * * 1 cd /path/to/pipeline && /path/to/venv/bin/python -m pipeline check

# 每日下午 6 點輸出 JSON
0 18 * * * cd /path/to/pipeline && /path/to/venv/bin/python -m pipeline export --git-commit
```

### 使用 Task Scheduler (Windows)

1. 開啟 Task Scheduler
2. 建立新任務
3. 觸發器：每日 9:00
4. 動作：啟動程式
5. 程式：`C:\path\to\pipeline\venv\Scripts\python.exe`
6. 參數：`-m pipeline ingest`
7. 開始位置：`C:\path\to\pipeline`

## 📄 License

MIT

## 🙏 貢獻

歡迎 Issue 同 PR！請確保：
- 通過測試
- 更新文件
- 遵循現有 code style
