#!/usr/bin/env python3
"""
Event Radar - 圖片下載器
下載活動海報並上傳到 Cloudinary 或保存本地
"""

import requests
import os
import hashlib
from pathlib import Path
from typing import Optional
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

# Cloudinary 配置（可選）
CLOUDINARY_ENABLED = all([
    os.getenv('CLOUDINARY_CLOUD_NAME'),
    os.getenv('CLOUDINARY_API_KEY'),
    os.getenv('CLOUDINARY_API_SECRET')
])

if CLOUDINARY_ENABLED:
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    print("✅ Cloudinary 已啟用")
else:
    print("⚠️ Cloudinary 未配置，圖片將保存到本地")

class ImageDownloader:
    """圖片下載器"""
    
    def __init__(self, local_dir: str = 'event_images'):
        self.local_dir = Path(local_dir)
        self.local_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_image(self, image_url: str, event_name: str) -> Optional[str]:
        """
        下載圖片並返回 URL（Cloudinary 或本地路徑）
        """
        if not image_url:
            return None
        
        try:
            # 下載圖片
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            # 檢查是否為圖片
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"⚠️ 不是圖片格式: {image_url}")
                return None
            
            # 生成文件名
            file_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            ext = self._get_extension(content_type, image_url)
            filename = f"event_{file_hash}{ext}"
            
            if CLOUDINARY_ENABLED:
                # 上傳到 Cloudinary
                return self._upload_to_cloudinary(response.content, filename, event_name)
            else:
                # 保存到本地
                return self._save_local(response.content, filename)
                
        except Exception as e:
            print(f"❌ 下載圖片失敗: {image_url} - {e}")
            return None
    
    def _get_extension(self, content_type: str, url: str) -> str:
        """獲取文件擴展名"""
        # 從 content-type 判斷
        ext_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
        }
        
        for mime, ext in ext_map.items():
            if mime in content_type:
                return ext
        
        # 從 URL 判斷
        if '.jpg' in url.lower() or '.jpeg' in url.lower():
            return '.jpg'
        elif '.png' in url.lower():
            return '.png'
        elif '.gif' in url.lower():
            return '.gif'
        
        return '.jpg'  # 默認
    
    def _upload_to_cloudinary(self, image_data: bytes, filename: str, event_name: str) -> Optional[str]:
        """上傳到 Cloudinary"""
        try:
            result = cloudinary.uploader.upload(
                image_data,
                public_id=f"event-radar/{filename}",
                folder="parent-map-hk",
                overwrite=True,
                resource_type="image"
            )
            print(f"✅ 上傳到 Cloudinary: {result['secure_url']}")
            return result['secure_url']
        except Exception as e:
            print(f"❌ Cloudinary 上傳失敗: {e}")
            # 降級到本地保存
            return self._save_local(image_data, filename)
    
    def _save_local(self, image_data: bytes, filename: str) -> str:
        """保存到本地"""
        filepath = self.local_dir / filename
        with open(filepath, 'wb') as f:
            f.write(image_data)
        print(f"✅ 保存本地: {filepath}")
        return str(filepath)

def process_event_images(events):
    """處理所有活動的圖片"""
    downloader = ImageDownloader()
    
    updated = 0
    failed = 0
    
    print(f"\n🖼️ 開始下載 {len(events)} 個活動的圖片...")
    
    for event in events:
        if event.image_url:
            new_url = downloader.download_image(event.image_url, event.name)
            if new_url:
                event.image_url = new_url
                updated += 1
            else:
                failed += 1
    
    print(f"\n✅ 圖片處理完成: {updated} 成功, {failed} 失敗")
    return events

if __name__ == '__main__':
    # 測試下載
    test_url = "https://www.lcsd.gov.hk/tc/whats-on/image.jpg"  # 替換為真實 URL
    downloader = ImageDownloader()
    result = downloader.download_image(test_url, "測試活動")
    print(f"結果: {result}")
