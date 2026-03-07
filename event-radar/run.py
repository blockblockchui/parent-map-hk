#!/usr/bin/env python3
"""
Event Radar - 主執行腳本
運行完整 pipeline: 爬取 → 下載圖片 → 寫入 Google Sheets
"""

import os
import sys
import argparse
from datetime import datetime

# 添加當前目錄到路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crawler import run_crawlers
from image_downloader import process_event_images
from write_to_sheets import main as write_to_sheets_main

def run_pipeline(download_images=False):
    """執行完整 pipeline"""
    print("=" * 70)
    print("🎯 Event Radar - 香港親子限時活動雷達")
    print("=" * 70)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 步驟 1: 爬取活動
    print("📡 步驟 1/3: 爬取活動...")
    events = run_crawlers()
    
    if not events:
        print("❌ 沒有找到活動，結束")
        return
    
    print(f"✅ 找到 {len(events)} 個活動")
    print()
    
    # 步驟 2: 下載圖片（可選）
    if download_images:
        print("🖼️ 步驟 2/3: 下載活動圖片...")
        events = process_event_images(events)
        print()
    else:
        print("⏭️ 步驟 2/3: 跳過圖片下載")
        print()
    
    # 步驟 3: 寫入 Google Sheets
    print("📝 步驟 3/3: 寫入 Google Sheets...")
    write_to_sheets_main()
    
    print()
    print("=" * 70)
    print("✅ Pipeline 完成!")
    print(f"結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Event Radar - 香港親子活動爬蟲')
    parser.add_argument(
        '--download-images', 
        action='store_true',
        help='下載活動圖片（需要 Cloudinary 配置或保存到本地）'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='測試模式：只爬取不寫入 Sheets'
    )
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 測試模式：只爬取不寫入")
        events = run_crawlers()
        for i, e in enumerate(events[:5], 1):
            print(f"\n{i}. {e.name}")
            print(f"   日期: {e.start_date} - {e.end_date}")
            print(f"   地點: {e.location}")
            print(f"   來源: {e.source_url}")
    else:
        run_pipeline(download_images=args.download_images)

if __name__ == '__main__':
    main()
