# SEO Description 生成腳本

自動為 Google Sheets 的 `03_places` 表生成 SEO 優化的描述，並新增 `seo_description` 欄位。

## 功能

- 根據地點屬性（地區、分類、是否免費、是否室內、年齡、交通）自動生成描述
- 插入關鍵詞：「親子」「放電」「免費」「室內」「港鐵」
- 自動在 `description_short` 旁邊新增 `seo_description` 欄位
- 零成本（無需 AI API）

## 安裝依賴

```bash
pip install gspread google-auth
```

## 配置

### 1. 確保有 Google Sheets API 憑證

需要 `credentials.json` 檔案（服務帳戶金鑰）。如果沒有：

1. 前往 https://console.cloud.google.com/
2. 啟用 Google Sheets API 和 Google Drive API
3. 建立服務帳戶並下載 JSON 金鑰
4. 將金鑰重新命名為 `credentials.json` 放在此目錄

### 2. 設定 Google Sheet 分享權限

將服務帳戶 email（在 credentials.json 中的 `client_email`）
分享給你的 Google Sheet（檢視者權限即可）。

### 3. 更新 Sheet ID

編輯腳本中的 `SHEET_ID`：
```python
SHEET_ID = "你的_Google_Sheet_ID"
```

> Sheet ID 在網址中：
> `https://docs.google.com/spreadsheets/d/`**`1wZo1WGSZ-BP4jVv-TQJMH5G9lG4H7oZh1d9N1--E8eM`**`/edit`

## 使用

```bash
cd /path/to/parent-map-hk/scripts
python3 generate_seo_descriptions.py
```

## 輸出示例

```
沙田親子室內遊樂場，設有滑梯、波波池及互動遊戲區，適合2-6歲兒童放電，收費入場，沙田港鐵站5分鐘即達。

旺角免費親子公園，設有遊樂設施、草地及休憩空間，適合各年齡兒童放電，免費入場，旺角東港鐵站3分鐘即達。
```

## 描述模板規則

```
{地區}親子{室內/戶外}{分類}，{設施描述}，適合{年齡}兒童放電，{免費/收費}入場，{交通資訊}。
```

### 關鍵詞自動插入

- **地區名**：提升本地搜尋排名
- **親子**：核心關鍵詞
- **室內/戶外**：天氣相關搜尋
- **免費**：高轉化關鍵詞
- **放電**：目標用戶語言
- **港鐵**：交通便利性

## 後續步驟

1. 在 Google Sheets 人工審核生成的描述
2. 手動調整不準確的描述
3. 同步到 Supabase（透過現有的 sync pipeline）
4. 更新網站抓取最新數據

## 更新網站數據

```bash
cd parent-map-next
npm run prebuild  # 重新抓取 places 數據
npm run build     # 構建並部署
```
