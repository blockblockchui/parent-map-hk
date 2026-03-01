# Google Places API 座標查核工具

用於驗證 Parent Map HK 地點的地址和座標是否與 Google Maps 一致。

## 設置步驟

### 1. 獲取 Google Places API Key

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 創建或選擇現有專案
3. 啟用 **Places API**（New）
4. 前往「憑證」頁面創建 API 密鑰
5. 限制密鑰僅允許 Places API 使用（安全建議）

### 2. 安裝依賴

```bash
cd /root/.openclaw/workspace/parent-map-hk/scripts
pip install requests
```

### 3. 設置環境變數

```bash
export GOOGLE_PLACES_API_KEY="你的API密鑰"
```

或在 `.bashrc` / `.zshrc` 中添加以上行，然後運行 `source ~/.bashrc`

## 使用方法

### 方法一：單個地點查核

編輯 `verify_coordinates.py` 底部的範例代碼，或直接運行：

```python
from verify_coordinates import verify_place, print_result

result = verify_place(
    place_name="大美督燒烤場",
    address="大埔大美督路",
    original_lat=22.471384,
    original_lng=114.232780,
    district="大埔"
)

print_result(result)
```

### 方法二：批量查核（CSV）

創建 CSV 文件 `places_to_verify.csv`：

```csv
name,address,lat,lng,district
大美督燒烤場,大埔大美督路,22.471384,114.232780,大埔
瀑布灣公園,香港仔華富邨瀑布灣道,22.252080,114.133761,南區
石澳海角郊遊區,石澳山仔路,22.230043,114.257496,南區
```

然後運行：

```bash
cd /root/.openclaw/workspace/parent-map-hk/scripts
python verify_coordinates.py
```

取消註釋這行：
```python
verify_from_csv('places_to_verify.csv', 'results.json')
```

### 方法三：直接從 Supabase 查核

```python
import json
from verify_coordinates import verify_place
from supabase import create_client

# 連接 Supabase
supabase = create_client(
    "你的SUPABASE_URL",
    "你的SUPABASE_KEY"
)

# 獲取所有地點
response = supabase.table('places').select('*').execute()
places = response.data

# 查核每個地點
results = []
for place in places[:10]:  # 先測試前10個
    result = verify_place(
        place_name=place['name_zh'],
        address=place['address_zh'],
        original_lat=place['lat'],
        original_lng=place['lng'],
        district=place['district_id']
    )
    results.append(result)

# 保存結果
with open('verification_results.json', 'w') as f:
    json.dump([r.__dict__ for r in results], f, ensure_ascii=False, indent=2)
```

## 結果判讀

| 狀態 | 距離差異 | 說明 |
|------|---------|------|
| ✅ success | < 100米 | 座標正確 |
| ⚠️ warning | 100-500米 | 座標有偏差，建議複查 |
| ❌ error | > 500米 | 座標錯誤，需要修正 |
| ❓ not_found | N/A | Google Places 找不到該地點 |

## 輸出範例

```
============================================================
地點: 大美督燒烤場
地址: 大埔大美督路
------------------------------------------------------------
原始座標: 22.471384, 114.232780
Google座標: 22.471450, 114.232850
距離差異: 12.5 米
------------------------------------------------------------
Google名稱: 大美督燒烤場
Google地址: 大埔大美督路香港
✅ 狀態: 座標正確（<100米）
```

## 注意事項

1. **API 配額**：Google Places API 有免費配額限制（每月 5,000 次請求）
2. **速率限制**：代碼已內置 0.3 秒延遲，避免超過每秒 10 次限制
3. **中文支援**：設置 `language=zh-HK` 確保返回繁體中文結果
4. **搜尋策略**：優先使用「地點名+地區」，其次「地點名+香港」

## 常見問題

### Q: API 返回 "REQUEST_DENIED"
A: 確保已啟用 Places API，且密鑰正確無誤。

### Q: 某些地點找不到
A: 嘗試簡化地點名稱（如「香港迪士尼樂園」→「迪士尼樂園」），或直接使用地址搜尋。

### Q: 座標偏差很大怎麼辦？
A: 檢查原始數據是否混淆了緯度/經度順序。香港地區的緯度約 22.x，經度約 114.x。

---

## 方法四：自動化 Google Sheet 查核（推薦）

使用 `verify_sheet_coordinates.py` 直接讀取 Google Sheet 的 "99_pin_to_check" tab，自動查核並回填結果。

### Sheet 結構要求

Tab 名稱：`99_pin_to_check`

| 列名 | 說明 |
|------|------|
| `place_name` | 地點名稱（如：大美督燒烤場） |
| `address` | 地址（如：大埔大美督路） |
| `district` | 地區（如：大埔） |
| `lat` | 原始緯度 |
| `lng` | 原始經度 |
| `checked` | 是否已查核（TRUE/FALSE） |
| `google_place_lat` | Google 緯度（自動填充） |
| `google_place_lng` | Google 經度（自動填充） |
| `google_result` | 查核結果（自動填充） |

### 設置步驟

#### 1. 獲取 Google Sheets API Key

1. 前往 [Google Cloud Console](https://console.cloud.google.com/)
2. 確保已啟用 **Google Sheets API**
3. 使用相同的 API Key（或創建新的）

#### 2. 設置環境變數

```bash
# Google Places API
export GOOGLE_PLACES_API_KEY="你的API密鑰"

# Google Sheets API（可以是同一個密鑰）
export GOOGLE_SHEETS_API_KEY="你的API密鑰"

# 你的 Google Sheet ID
# 從 Sheet URL 獲取：https://docs.google.com/spreadsheets/d/{這裡是ID}/edit
export GOOGLE_SHEET_ID="你的SheetID"
```

#### 3. 分享 Sheet

確保 Sheet 已設置為「任何人都可以查看」：
1. 在 Google Sheets 點擊「分享」
2. 將權限設為「知道連結的任何人」
3. 選擇「檢視者」

### 運行

```bash
cd /root/.openclaw/workspace/parent-map-hk/scripts
python verify_sheet_coordinates.py
```

### 運作流程

1. **讀取**：讀取 "99_pin_to_check" tab 中所有 `checked` = FALSE 的行
2. **查核**：對每個地點使用 Google Places API 搜尋
3. **計算**：比對原始座標與 Google 座標的距離
4. **回填**：自動填充以下列：
   - `google_place_lat`：Google 提供的緯度
   - `google_place_lng`：Google 提供的經度
   - `google_result`：查核結果（success/warning/error/not_found）
   - `checked`：設為 TRUE

### 輸出範例

```
======================================================================
Google Sheet 自動座標查核工具
======================================================================
Sheet ID: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
Tab: 99_pin_to_check
======================================================================

📖 正在讀取 '99_pin_to_check'...
   找到 50 行數據
   其中 10 行需要查核

🔍 開始查核 10 個地點...

[1/10] 查核: 大美督燒烤場
    嘗試搜尋: 大美督燒烤場 大埔
   ✅ 大美督燒烤場 - 正確 (偏差 12.5m)

[2/10] 查核: 瀑布灣公園
    嘗試搜尋: 瀑布灣公園 南區
   ⚠️  瀑布灣公園 - 警告 (偏差 150.3m)

[3/10] 查核: 某某遊樂場
    嘗試搜尋: 某某遊樂場 香港
    嘗試搜尋: 某某遊樂場
   ❓ 某某遊樂場 - 未找到

======================================================================
查核完成！
======================================================================
✅ 正確:   7
⚠️  警告:   2
❌ 錯誤:   0
❓ 未找到: 1
======================================================================
```

### 注意事項

1. **API 配額**：每次查核消耗 1 次 Places API 請求，免費版每月限額 5,000 次
2. **速率限制**：腳本已內置 0.5 秒延遲，避免觸發限制
3. **數據安全**：API Key 請保存在環境變數中，不要硬編碼在代碼裡
4. **錯誤處理**：如果某行處理失敗，腳本會繼續處理下一行，不會中斷

### 定時自動運行（可選）

可以設置 cron job 每天自動查核：

```bash
# 編輯 crontab
crontab -e

# 添加以下行（每天早上 9 點運行）
0 9 * * * cd /root/.openclaw/workspace/parent-map-hk/scripts && /usr/bin/python3 verify_sheet_coordinates.py >> /var/log/pin_check.log 2>&1
```
