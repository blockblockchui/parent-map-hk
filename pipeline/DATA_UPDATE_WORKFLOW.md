# Parent Map HK - 資料更新流程

## 🔄 完整工作流程

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Google Sheets  │────▶│  export_json.py │────▶│ data/locations  │
│   (CMS/數據庫)   │     │   (匯出腳本)     │     │     .json       │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                   ┌─────────────────┐
                                                   │   index.html    │
                                                   │ (自動讀取JSON)   │
                                                   └─────────────────┘
```

## 📋 更新地點資料步驟

### 方法 1：手動喺 Google Sheets 更新

1. **開啟 Google Sheets**
   ```
   https://docs.google.com/spreadsheets/d/1L_8FfQ_dC4ty53KbrCIvEAlKJwLH_Vl5U_2V0_m78kA/edit
   ```

2. **直接編輯「Places」worksheet**
   - 修改現有地點資料
   - 新增地點（喺最尾加 row）
   - 必填欄位：name, district, lat, lng

3. **匯出到 JSON**
   ```bash
   cd pipeline
   python3 export_json.py
   ```

4. **推送更新到 GitHub**
   ```bash
   git add data/locations.json
   git commit -m "Update locations data"
   git push origin main
   ```

5. **完成！** 網站會自動顯示最新資料（GitHub Pages 可能需要 1-2 分鐘更新）

---

### 方法 2：用 AI 搜集資料（CSV 匯入）

1. **用 Prompt 俾 AI（Grok/ChatGPT/Gemini）**
   - 使用檔案：`pipeline/PROMPT_FOR_AI_RESEARCH.md`

2. **AI 輸出 CSV 格式**
   ```csv
   place_id,name,name_en,region,district,address,lat,lng,category,indoor,age_min,age_max,price_tier,price_description,description,opening_hours,website_url,facebook_url,instagram_url,google_maps_url,status,tips,source_urls,checked_at
   ```

3. **儲存為 .txt 檔案**

4. **匯入 Google Sheets**
   ```bash
   cd pipeline
   python3 import_csv_to_sheets.py /path/to/file.txt
   ```

5. **驗證後匯出 JSON**
   ```bash
   python3 export_json.py
   git add data/locations.json
   git commit -m "Add new places from AI research"
   git push origin main
   ```

---

### 方法 3：從舊資料檔案匯入

如果 `data/locations.ts` 或 `data/locations50.ts` 有未匯入嘅地點：

```bash
cd pipeline
python3 import_original_50.py
python3 export_json.py
git add data/locations.json
git commit -m "Import additional places from TS files"
git push origin main
```

---

## 📁 重要檔案位置

| 檔案 | 用途 | 更新頻率 |
|------|------|---------|
| `data/locations.json` | 前端讀取嘅資料 | 每次 Sheets 更新後 |
| `pipeline/export_json.py` | 從 Sheets 匯出 JSON | 按需執行 |
| `pipeline/import_csv_to_sheets.py` | CSV 匯入 Sheets | 有新 CSV 時 |
| `pipeline/PROMPT_FOR_AI_RESEARCH.md` | AI 搜集用 Prompt | 參考用 |

---

## ⚠️ 注意事項

### Google Sheets API 限制
- **每分鐘 100 次請求**
- 大量匯入時可能會遇到限制
- 解决方法：等 1-2 分鐘後重試

### 必填欄位
- `name` - 地點名稱
- `district` - 地區
- `lat` / `lng` - 座標
- `status` - Open / SuspectedClosed / Closed

### 重複檢查
- 系統會自動檢查同名同區地點
- 重複地點會被跳過（不會覆蓋）

---

## 🧪 測試指令

```bash
# 檢查 Google Sheets 連線
cd pipeline
python3 test_sheets.py

# 比較 JSON 差異（dry-run）
python3 export_json.py --compare

# 匯出並預覽
cat ../data/locations.json | head -50
```

---

## 📊 現時狀態

- **Google Sheets**: ~60+ 地點
- **前端顯示**: 自動同步 JSON
- **更新延遲**: GitHub Pages 約 1-2 分鐘

---

## ❓ 常見問題

**Q: 為咩網站冇顯示新地點？**
A: 檢查以下步驟：
1. 確認已執行 `export_json.py`
2. 確認已 `git push`
3. 等 2-3 分鐘讓 GitHub Pages 更新
4. 清除瀏覽器快取 (Ctrl+Shift+R)

**Q: 可以同時匯入幾多個 CSV？**
A: 可以一次過指定多個檔案：
```bash
python3 import_csv_to_sheets.py 1.txt 2.txt 3.txt
```

**Q: 點樣刪除地點？**
A: 直接喺 Google Sheets 刪除該 row，然後重新匯出 JSON。

---

*最後更新：2026-02-13*
