# 更新工作流程

## 網站資料更新流程（2024-02-13 更新）

### 自動同步架構

```
Google Sheets (CMS)
       ↓
  export_json.py
       ↓
data/locations.json
       ↓
GitHub Pages (自動讀取)
```

### 更新步驟

#### 1. 新增地點

**方法 A：AI 搜集 → CSV → Sheets**
```bash
# 1. 用 AI (Grok/ChatGPT) 生成 CSV
# 2. 匯入 Google Sheets
cd pipeline
python3 import_csv_to_sheets.py /path/to/data.csv

# 3. 輸出 JSON
python3 export_json.py

# 4. Git commit & push
git add data/locations.json
git commit -m "Update locations"
git push
```

**方法 B：直接喺 Google Sheets 編輯**
```
1. 開啟 https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
2. 喺 "Places" worksheet 加/改資料
3. 執行 export_json.py
4. Git commit & push
```

#### 2. 前端自動讀取

網站已改成 **Fetch JSON** 模式：
- `index.html` 會自動從 `data/locations.json` 讀取資料
- 唔再使用 hardcode 資料
- 更新 JSON 後，網站會自動顯示最新資料

#### 3. 驗證更新

```bash
# 本地測試（可選）
cd parent-map-hk
python3 -m http.server 8000
# 開啟 http://localhost:8000

# 線上驗證
open https://blockblockchui.github.io/parent-map-hk/
```

### 重要檔案

| 檔案 | 用途 |
|------|------|
| `data/locations.json` | 前端讀取嘅資料檔 |
| `pipeline/export_json.py` | 從 Sheets 輸出 JSON |
| `pipeline/import_csv_to_sheets.py` | 匯入 CSV 到 Sheets |
| `pipeline/PROMPT_FOR_AI_RESEARCH.md` | AI 搜集 Prompt |

### 注意事項

1. **Google Sheets API 配額限制**
   - 每分鐘 100 次讀取
   - 大量匯入時會遇到限制，需要等 1-2 分鐘

2. **資料格式**
   - 必需欄位：`name`, `district`, `lat`, `lng`
   - 座標必須準確，否則會被過濾

3. **GitHub Pages 更新時間**
   - Push 後約 1-2 分鐘自動更新
   - 可用 `Ctrl+F5` 強制刷新瀏覽器

### 常用指令

```bash
# 輸出最新資料
cd pipeline && python3 export_json.py

# 測試 Sheets 連線
cd pipeline && python3 test_sheets.py

# 完整更新流程
cd pipeline && python3 export_json.py && cd .. && git add data/ && git commit -m "Update locations" && git push
```
