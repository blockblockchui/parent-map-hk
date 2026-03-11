# Event Image Sync - 活動圖片同步工具

自動從 Google Sheets 下載活動圖片並上傳到 Supabase Storage。

## 功能

1. 從 Google Sheets (`20_events` worksheet) 讀取活動資料
2. 檢查每個活動的 `image_url` 欄位
3. 下載外部圖片（HTTP URL）
4. 在 Supabase Storage 按活動 ID 創建文件夾
5. 上傳圖片到對應文件夾
6. 更新 Google Sheets 中的圖片 URL 為 Supabase URL

## 前置需求

### 1. 安裝依賴

```bash
pip install supabase gspread google-auth-httplib2 google-auth-oauthlib python-dotenv requests
```

或

```bash
pip install -r requirements-image-sync.txt
```

### 2. 配置環境變數

複製範例文件並填入實際值：

```bash
cp .env.image-sync.example .env
```

編輯 `.env` 文件：

```env
# Google Sheets ID (已預填)
GOOGLE_SHEETS_ID=1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk

# Supabase 配置
NEXT_PUBLIC_SUPABASE_URL=https://krlqzkxqlxoetxxjqamh.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here  # 需要 service_role key

# Storage Bucket 名稱
SUPABASE_BUCKET=event-images
```

**注意：** 上傳文件到 Storage 需要使用 `service_role` key，而不是 `anon` key。
在 Supabase Dashboard → Project Settings → API → Project API keys 中獲取。

### 3. 確保 Google Sheets API 憑證

確保 `credentials.json` 存在於以下位置之一：
- `event-radar/credentials.json`
- `pipeline/credentials.json`

## 使用方法

### 單次執行

```bash
cd /root/.openclaw/workspace/parent-map-hk/event-radar
python sync_event_images.py
```

### 自動化執行（推薦）

設置定時任務（cron job）每小時執行一次：

```bash
# 編輯 crontab
crontab -e

# 添加以下行（每小時執行）
0 * * * * cd /root/.openclaw/workspace/parent-map-hk/event-radar && python sync_event_images.py >> /var/log/event-image-sync.log 2>&1
```

或每 30 分鐘執行：

```bash
*/30 * * * * cd /root/.openclaw/workspace/parent-map-hk/event-radar && python sync_event_images.py >> /var/log/event-image-sync.log 2>&1
```

## 圖片存儲結構

上傳到 Supabase Storage 的圖片會按以下結構組織：

```
event-images/  (bucket)
├── {event_id_1}/
│   └── poster.jpg
├── {event_id_2}/
│   └── poster.png
└── {event_id_3}/
    └── poster.jpg
```

## 處理邏輯

1. **篩選條件**：只處理 `image_url` 以 `http` 開頭且不是 Supabase URL 的活動
2. **去重**：如果活動已有 Supabase URL，會跳過不重複處理
3. **文件命名**：統一命名為 `poster.{ext}`（保留原始擴展名）
4. **錯誤處理**：下載或上傳失敗的活動會記錯誤但繼續處理其他活動

## 日誌輸出

腳本會輸出處理進度：

```
============================================================
Event Image Sync - 活動圖片同步
============================================================
✅ 使用憑證: ../pipeline/credentials.json
✅ 連接到 Supabase bucket: event-images
✅ 連接到 Google Sheets: 20_events
📊 找到 12 個有待處理圖片的活動

🚀 開始處理 12 個活動...

[1/12] 處理: 兒童故事時間...
      Event ID: d8d69b2effa6
      圖片 URL: https://www.hkpl.gov.hk/images/...
✅ 上傳成功: d8d69b2effa6/poster.jpg
✅ 已更新 Sheet 第 3 行的圖片 URL

...

============================================================
處理完成!
✅ 成功: 10
❌ 失敗: 2
============================================================
```

## 常見問題

### Q: 為什麼需要使用 service_role key？
A: 因為上傳文件到 Storage 需要繞過 RLS (Row Level Security) 策略，service_role key 擁有完整權限。

### Q: 同一活動會重複上傳嗎？
A: 不會。腳本會檢查 `image_url` 是否已經是 Supabase URL，如果是則跳過。

### Q: 如果活動有多張圖片怎麼辦？
A: 目前設計是每個活動只有一張主要圖片（poster）。如需支持多圖，需要修改腳本邏輯。

### Q: 如何檢查執行結果？
A: 可以在 Supabase Dashboard → Storage → event-images 中查看上傳的圖片。

## 安全注意事項

1. **保護 service_role key**：不要將其提交到 Git 或公開分享
2. **設置 RLS 策略**：建議為 Storage bucket 設置適當的訪問控制
3. **定期輪轉密鑰**：定期更新 service_role key

## 故障排除

### 問題："找不到 credentials.json"
**解決**：確保 Google Sheets API 憑證文件存在於正確位置

### 問題："Supabase 初始化失敗"
**解決**：檢查 SUPABASE_SERVICE_ROLE_KEY 是否正確設置

### 問題："Bucket 不存在"
**解決**：腳本會自動嘗試創建 bucket，如果失敗請手動在 Supabase Dashboard 創建
