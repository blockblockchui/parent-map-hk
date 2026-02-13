#!/usr/bin/env python3
"""
低成本地點搜集腳本 - 不使用 LLM，只用 RSS + HTTP 檢查
Usage: python3 ingest_lowcost.py [--dry-run]
"""

import os
import sys
import asyncio
import uuid
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from dotenv import load_dotenv

load_dotenv()

# Check required packages
try:
    import feedparser
    import httpx
    import yaml
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"❌ 缺少套件: {e}")
    print("請執行: pip3 install --break-system-packages feedparser httpx pyyaml beautifulsoup4")
    sys.exit(1)

print("=" * 70)
print("🚀 低成本地點搜集 (Low Cost Pipeline)")
print("=" * 70)

# Load config
config_path = Path(__file__).parent / "config" / "sources_lowcost.yaml"
if not config_path.exists():
    print(f"❌ Config file not found: {config_path}")
    sys.exit(1)

with open(config_path) as f:
    config = yaml.safe_load(f)

# Parse arguments
dry_run = "--dry-run" in sys.argv

if dry_run:
    print("\n🔍 DRY RUN 模式 - 不會寫入 Google Sheets")

# Load sources
sources = [s for s in config.get('sources', []) if s.get('enabled', True)]
print(f"\n📡 啟用嘅來源: {len(sources)}")
for s in sources:
    print(f"  • {s['name']} ({s['type']})")

# Google Sheets setup
print("\n📋 連接 Google Sheets...")
from google.oauth2.service_account import Credentials
import gspread

sheet_id = os.getenv("GOOGLE_SHEETS_ID")
creds_path = Path(__file__).parent / "credentials.json"

credentials = Credentials.from_service_account_file(
    str(creds_path),
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(sheet_id)

try:
    worksheet = spreadsheet.worksheet("Places")
    print(f"✓ 已連接: {worksheet.title}")
except gspread.WorksheetNotFound:
    worksheet = spreadsheet.add_worksheet("Places", rows=1000, cols=40)
    print(f"✓ 已創建: Places")

# Get existing places for deduplication
print("\n📊 獲取現有地點...")
existing = worksheet.get_all_records()
existing_names = {(row.get('name', ''), row.get('district', '')) for row in existing}
print(f"  現有: {len(existing)} 個地點")

# Results
found_places = []

def extract_real_url_from_bing(url):
    """Extract real URL from Bing redirect URL"""
    if 'bing.com/news/apiclick.aspx' in url:
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        params = urllib.parse.parse_qs(parsed.query)
        if 'url' in params:
            return urllib.parse.unquote(params['url'][0])
    return url

async def fetch_url(url, timeout=10):
    """Fetch URL with timeout"""
    try:
        # Handle Bing redirect URLs
        url = extract_real_url_from_bing(url)
        
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (compatible; ParentMapBot/1.0)"
            })
            return response
    except Exception as e:
        return None

def extract_place_info(title, summary, url):
    """Extract place info from title and summary (without LLM)"""
    text = f"{title} {summary}"
    
    # Handle Bing redirect URLs
    real_url = extract_real_url_from_bing(url)
    
    # Pattern matching for common formats
    place = {
        'name': title.split('|')[0].split('–')[0].split('-')[0].strip()[:50],
        'category': 'playhouse',
        'indoor': True,
        'district': '',
        'address': '',
        'description': summary[:200] if summary else title[:200],
        'website_url': real_url,
        'source_url': real_url,
    }
    
    # Try to extract district
    districts = ['灣仔', '銅鑼灣', '中環', '尖沙咀', '旺角', '沙田', '荃灣', '九龍城', 
                 '將軍澳', '大埔', '屯門', '元朗', '天水圍', '青衣', '葵涌', '觀塘']
    for d in districts:
        if d in text:
            place['district'] = d
            break
    
    # Detect category
    if any(k in text for k in ['博物館', '科學館', '太空館']):
        place['category'] = 'museum'
    elif any(k in text for k in ['公園', '濕地']):
        place['category'] = 'park'
        place['indoor'] = False
    elif any(k in text for k in ['餐廳', 'café', 'Cafe']):
        place['category'] = 'restaurant'
    
    # Detect indoor/outdoor
    if any(k in text for k in ['室外', '戶外', '公園']):
        place['indoor'] = False
    
    return place

def check_already_exists(name, district):
    """Check if place already exists"""
    return (name, district) in existing_names

async def process_rss_source(source):
    """Process RSS source"""
    print(f"\n📰 處理: {source['name']}")
    
    try:
        feed = feedparser.parse(source['url'])
        print(f"  找到 {len(feed.entries)} 篇文章")
        
        new_count = 0
        for entry in feed.entries[:10]:  # 只處理最近 10 篇
            title = entry.get('title', '')
            summary = entry.get('summary', entry.get('description', ''))
            link = entry.get('link', '')
            
            # Check keywords - must contain venue-related terms
            text = f"{title} {summary}".lower()
            
            # Must contain at least one venue indicator
            venue_terms = ['樂園', '遊樂場', 'playhouse', 'playroom', '博物館', '科學館', '太空館', '公園', '探索館', '親子館', '兒童', '放電']
            if not any(term in title for term in venue_terms):
                continue
            
            # Skip news articles about parenting advice, celebrity news, etc.
            skip_terms = ['鬧仔', '湊仔', '教養', '專訪', '明星', '藝人', '夫妻', '婚姻', '懷孕', '生仔', '分娩', '湊B']
            if any(term in title for term in skip_terms):
                print(f"  ⏭️  跳過非地點文章: {title[:40]}...")
                continue
            
            # Extract place info
            place = extract_place_info(title, summary, link)
            
            if not place['name']:
                continue
            
            # Check duplicate
            if check_already_exists(place['name'], place['district']):
                print(f"  ⚠️  已存在: {place['name']}")
                continue
            
            # HTTP check (cheap validation)
            print(f"  🔍 檢查: {place['name']}")
            response = await fetch_url(link)
            if response and response.status_code == 200:
                place['http_ok'] = True
                new_count += 1
                found_places.append(place)
                print(f"  ✓ 有效: {place['name']}")
            else:
                print(f"  ❌ 無法訪問: {place['name']}")
            
            # Rate limiting
            await asyncio.sleep(1)
        
        print(f"  ✓ 新增: {new_count} 個")
        
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")

async def main():
    # Process all sources
    for source in sources:
        if source['type'] == 'rss':
            await process_rss_source(source)
        
        # Add delay between sources
        await asyncio.sleep(2)
    
    print(f"\n{'=' * 70}")
    print(f"📊 搜集完成: {len(found_places)} 個新地點")
    print(f"{'=' * 70}")
    
    if not found_places:
        print("\nℹ️ 沒有找到新地點")
        return
    
    # Show found places
    print("\n📍 找到嘅地點:")
    for i, p in enumerate(found_places[:5], 1):
        print(f"  {i}. {p['name']} ({p['district'] or '未知地區'})")
    if len(found_places) > 5:
        print(f"  ... 還有 {len(found_places) - 5} 個")
    
    if dry_run:
        print("\n🔍 DRY RUN - 不會寫入 Google Sheets")
        return
    
    # Import to Google Sheets
    print("\n📝 匯入 Google Sheets...")
    
    SHEET_COLUMNS = [
        "place_id", "slug", "name", "name_en", "region", "district", "address", "lat", "lng",
        "geocode_confidence", "category", "indoor", "age_min", "age_max", "price_tier",
        "price_description", "description", "tips", "facilities", "opening_hours",
        "website_url", "facebook_url", "instagram_url", "google_maps_url", "status",
        "validation_stage", "confidence", "risk_tier", "evidence_urls", "evidence_snippets",
        "source_urls", "published_at", "updated_at", "last_checked_at", "next_check_at",
        "checked_at", "review_owner", "review_due_at", "resolution", "false_alarm_reason"
    ]
    
    imported = 0
    for place in found_places:
        try:
            row_data = [
                str(uuid.uuid4())[:8],  # place_id
                place['name'].lower().replace(' ', '-')[:50],  # slug
                place['name'],  # name
                '',  # name_en
                'hk-island' if not place['district'] else ('kowloon' if place['district'] in ['尖沙咀', '旺角', '九龍城'] else 'nt'),  # region
                place['district'],  # district
                place.get('address', ''),  # address
                '',  # lat
                '',  # lng
                'rss_extracted',  # geocode_confidence
                place['category'],  # category
                'TRUE' if place['indoor'] else 'FALSE',  # indoor
                '',  # age_min
                '',  # age_max
                '',  # price_tier
                '',  # price_description
                place['description'],  # description
                '',  # tips
                '',  # facilities
                '請查詢官網',  # opening_hours
                place['website_url'],  # website_url
                '',  # facebook_url
                '',  # instagram_url
                '',  # google_maps_url
                'PendingReview',  # status
                'rss_extracted',  # validation_stage
                50,  # confidence
                'medium',  # risk_tier
                '',  # evidence_urls
                '',  # evidence_snippets
                place['source_url'],  # source_urls
                datetime.now().isoformat(),  # published_at
                datetime.now().isoformat(),  # updated_at
                '',  # last_checked_at
                '',  # next_check_at
                datetime.now().strftime('%Y-%m-%d'),  # checked_at
                '',  # review_owner
                '',  # review_due_at
                '',  # resolution
                '',  # false_alarm_reason
            ]
            
            worksheet.append_row(row_data)
            imported += 1
            print(f"  ✓ {place['name']}")
            
        except Exception as e:
            print(f"  ❌ {place['name']}: {e}")
    
    print(f"\n✅ 匯入完成: {imported} 個地點")
    print(f"\n📊 Sheet URL:")
    print(f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
    print(f"\n📝 下一步:")
    print(f"  1. 檢查 'PendingReview' 狀態嘅地點")
    print(f"  2. 手動補充座標同詳情")
    print(f"  3. 執行 export_json.py 更新前端")

# Run
if __name__ == "__main__":
    asyncio.run(main())
