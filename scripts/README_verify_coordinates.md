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
