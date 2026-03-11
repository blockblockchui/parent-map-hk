#!/usr/bin/env python3
"""
Event Image Sync - 從 Google Sheets 下載活動圖片並上傳到 Supabase Storage
"""

import os
import sys
import requests
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse

# Google Sheets
import gspread
from google.oauth2.service_account import Credentials

# Supabase
from supabase import create_client, Client

# 加載環境變數
from dotenv import load_dotenv
load_dotenv()

# ===== 配置 =====
GOOGLE_SHEETS_ID = os.getenv('GOOGLE_SHEETS_ID', '1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk')
WORKSHEET_NAME = '20_events'

SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # 需要 service_role key
SUPABASE_BUCKET = 'event-images'  # 請確認 bucket 名稱

# 圖片保存配置
LOCAL_DOWNLOAD_DIR = 'temp_event_images'

class EventImageSync:
    """活動圖片同步器"""
    
    def __init__(self):
        self.supabase: Optional[Client] = None
        self.google_client = None
        self.worksheet = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 確保臨時目錄存在
        Path(LOCAL_DOWNLOAD_DIR).mkdir(exist_ok=True)
        
    def init_supabase(self) -> bool:
        """初始化 Supabase 客戶端"""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                print("❌ 缺少 Supabase 環境變數")
                return False
                
            self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # 檢查 bucket 是否存在
            buckets = self.supabase.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            
            if SUPABASE_BUCKET not in bucket_names:
                print(f"⚠️ Bucket '{SUPABASE_BUCKET}' 不存在，嘗試創建...")
                try:
                    self.supabase.storage.create_bucket(
                        SUPABASE_BUCKET,
                        options={'public': True}
                    )
                    print(f"✅ 創建 bucket: {SUPABASE_BUCKET}")
                except Exception as e:
                    print(f"❌ 創建 bucket 失敗: {e}")
                    return False
            else:
                print(f"✅ 連接到 Supabase bucket: {SUPABASE_BUCKET}")
                
            return True
            
        except Exception as e:
            print(f"❌ Supabase 初始化失敗: {e}")
            return False
    
    def init_google_sheets(self) -> bool:
        """初始化 Google Sheets"""
        try:
            scope = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            
            # 尋找 credentials 文件
            cred_paths = [
                "credentials.json",
                "../pipeline/credentials.json",
                "../../pipeline/credentials.json",
                "/root/.openclaw/workspace/parent-map-hk/pipeline/credentials.json"
            ]
            
            creds = None
            for path in cred_paths:
                if os.path.exists(path):
                    creds = Credentials.from_service_account_file(path, scopes=scope)
                    print(f"✅ 使用憑證: {path}")
                    break
            
            if not creds:
                print("❌ 找不到 credentials.json")
                return False
            
            self.google_client = gspread.authorize(creds)
            sheet = self.google_client.open_by_key(GOOGLE_SHEETS_ID)
            self.worksheet = sheet.worksheet(WORKSHEET_NAME)
            
            print(f"✅ 連接到 Google Sheets: {WORKSHEET_NAME}")
            return True
            
        except Exception as e:
            print(f"❌ Google Sheets 初始化失敗: {e}")
            return False
    
    def get_events_with_images(self) -> List[Dict]:
        """從 Google Sheets 獲取有圖片的活動"""
        try:
            # 獲取所有數據
            data = self.worksheet.get_all_records()
            
            # 篩選有圖片 URL 的活動
            events_with_images = []
            for row in data:
                image_url = row.get('image_url', '').strip()
                event_id = row.get('event_id', '').strip()
                
                # 檢查是否有圖片 URL 且不是已上傳到 Supabase 的 URL
                if image_url and image_url.startswith('http') and not image_url.startswith(SUPABASE_URL):
                    events_with_images.append({
                        'event_id': event_id,
                        'name': row.get('name', ''),
                        'image_url': image_url,
                        'row_number': data.index(row) + 2  # +2 因為有標題行且索引從0開始
                    })
            
            print(f"📊 找到 {len(events_with_images)} 個有待處理圖片的活動")
            return events_with_images
            
        except Exception as e:
            print(f"❌ 獲取活動失敗: {e}")
            return []
    
    def download_image(self, image_url: str) -> Optional[bytes]:
        """下載圖片"""
        try:
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 檢查是否為圖片
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"⚠️ 不是圖片格式: {content_type}")
                return None
            
            return response.content
            
        except Exception as e:
            print(f"❌ 下載圖片失敗: {e}")
            return None
    
    def upload_to_supabase(self, event_id: str, image_data: bytes, original_url: str) -> Optional[str]:
        """上傳圖片到 Supabase Storage"""
        try:
            # 確定文件擴展名
            ext = self._get_extension(original_url)
            filename = f"poster{ext}"
            
            # 文件路徑: {event_id}/poster.jpg
            file_path = f"{event_id}/{filename}"
            
            # 上傳圖片
            result = self.supabase.storage.from_(SUPABASE_BUCKET).upload(
                file_path,
                image_data,
                file_options={'content-type': self._get_content_type(ext)}
            )
            
            # 獲取公開 URL
            public_url = self.supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
            
            print(f"✅ 上傳成功: {file_path}")
            return public_url
            
        except Exception as e:
            print(f"❌ 上傳到 Supabase 失敗: {e}")
            return None
    
    def _get_extension(self, url: str) -> str:
        """獲取文件擴展名"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if '.jpg' in path or '.jpeg' in path:
            return '.jpg'
        elif '.png' in path:
            return '.png'
        elif '.gif' in path:
            return '.gif'
        elif '.webp' in path:
            return '.webp'
        else:
            return '.jpg'  # 默認
    
    def _get_content_type(self, ext: str) -> str:
        """獲取 content type"""
        mapping = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        return mapping.get(ext, 'image/jpeg')
    
    def update_sheet_image_url(self, row_number: int, new_url: str):
        """更新 Google Sheets 中的圖片 URL"""
        try:
            # image_url 在第 I 欄 (第9列)
            self.worksheet.update_cell(row_number, 9, new_url)
            print(f"✅ 已更新 Sheet 第 {row_number} 行的圖片 URL")
            
        except Exception as e:
            print(f"❌ 更新 Sheet 失敗: {e}")
    
    def process_all_events(self):
        """處理所有活動"""
        print("=" * 60)
        print("Event Image Sync - 活動圖片同步")
        print("=" * 60)
        
        # 初始化
        if not self.init_supabase():
            return
        
        if not self.init_google_sheets():
            return
        
        # 獲取有待處理圖片的活動
        events = self.get_events_with_images()
        
        if not events:
            print("\n✅ 沒有需要處理的圖片")
            return
        
        # 處理每個活動
        success_count = 0
        failed_count = 0
        
        print(f"\n🚀 開始處理 {len(events)} 個活動...\n")
        
        for i, event in enumerate(events, 1):
            print(f"[{i}/{len(events)}] 處理: {event['name'][:40]}...")
            print(f"      Event ID: {event['event_id']}")
            print(f"      圖片 URL: {event['image_url'][:60]}...")
            
            # 下載圖片
            image_data = self.download_image(event['image_url'])
            if not image_data:
                failed_count += 1
                continue
            
            # 上傳到 Supabase
            new_url = self.upload_to_supabase(
                event['event_id'],
                image_data,
                event['image_url']
            )
            
            if new_url:
                # 更新 Google Sheets
                self.update_sheet_image_url(event['row_number'], new_url)
                success_count += 1
            else:
                failed_count += 1
            
            print()
        
        # 總結
        print("=" * 60)
        print("處理完成!")
        print(f"✅ 成功: {success_count}")
        print(f"❌ 失敗: {failed_count}")
        print("=" * 60)

def main():
    sync = EventImageSync()
    sync.process_all_events()

if __name__ == '__main__':
    main()
