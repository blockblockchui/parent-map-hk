#!/usr/bin/env python3
"""
Add sample parent-child places to Google Sheets for testing
"""

import sys
import os
import uuid
from datetime import datetime
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("🚀 Adding Sample Places to Google Sheets")
print("=" * 70)

# Import gspread directly
from google.oauth2.service_account import Credentials
import gspread

sheet_id = os.getenv("GOOGLE_SHEETS_ID")
creds_path = Path(__file__).parent / "credentials.json"

# Authenticate
credentials = Credentials.from_service_account_file(
    str(creds_path),
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
)
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(sheet_id)

# Get or create worksheet
try:
    worksheet = spreadsheet.worksheet("Places")
    print(f"✓ Connected to worksheet: {worksheet.title}")
except gspread.WorksheetNotFound:
    print("Creating new worksheet...")
    worksheet = spreadsheet.add_worksheet("Places", rows=1000, cols=38)
    headers = [
        "place_id", "slug", "name", "name_en", "region", "district", "address",
        "lat", "lng", "geocode_confidence", "category", "indoor", "age_min",
        "age_max", "price_tier", "price_description", "description", "tips",
        "facilities", "opening_hours", "website_url", "facebook_url", "instagram_url",
        "status", "validation_stage", "confidence", "risk_tier", "evidence_urls",
        "evidence_snippets", "source_urls", "published_at", "updated_at",
        "last_checked_at", "next_check_at", "review_owner", "review_due_at",
        "resolution", "false_alarm_reason"
    ]
    worksheet.append_row(headers)
    print(f"✓ Created worksheet: {worksheet.title}")

# Sample parent-child places
from datetime import datetime

current_date = datetime.now().strftime("%Y-%m-%d")

sample_places = [
    {
        "name": "樹屋 Baumhaus",
        "name_en": "Baumhaus",
        "district": "灣仔",
        "region": "hk-island",
        "address": "灣仔灣仔道3號",
        "lat": 22.2755,
        "lng": 114.1708,
        "category": "playhouse",
        "indoor": True,
        "age_min": 0,
        "age_max": 6,
        "price_tier": "medium",
        "price_description": "$100-200",
        "description": "木製遊樂空間，提供創意藝術課程及探索樹屋。環境溫馨，適合幼兒自由探索。",
        "opening_hours": "09:30-18:00",
        "website_url": "https://www.baumhaus.com.hk/",
        "google_maps_url": "https://maps.google.com/?q=22.2755,114.1708",
        "status": "Open",
        "confidence": 90,
        "tips": "需預約；設有哺乳室",
        "source_urls": "https://www.baumhaus.com.hk/",
        "checked_at": current_date,
    },
    {
        "name": "香港兒童探索博物館",
        "name_en": "Hong Kong Children's Discovery Museum",
        "district": "西環",
        "region": "hk-island",
        "address": "西環皇后大道西550號",
        "lat": 22.2871,
        "lng": 114.1378,
        "category": "museum",
        "indoor": True,
        "age_min": 0,
        "age_max": 10,
        "price_tier": "medium",
        "price_description": "$50-100",
        "description": "互動式博物館，讓小朋友透過遊戲探索科學、藝術和文化。",
        "opening_hours": "10:00-18:00（周三休）",
        "website_url": "https://www.hkcdm.org/",
        "google_maps_url": "https://maps.google.com/?q=22.2871,114.1378",
        "status": "Open",
        "confidence": 95,
        "tips": "周三休館；建議預約時段",
        "source_urls": "https://www.hkcdm.org/",
        "checked_at": current_date,
    },
    {
        "name": "荃灣公園",
        "name_en": "Tsuen Wan Park",
        "district": "荃灣",
        "region": "nt",
        "address": "荃灣大河道",
        "lat": 22.3733,
        "lng": 114.1141,
        "category": "park",
        "indoor": False,
        "age_min": 0,
        "age_max": 12,
        "price_tier": "free",
        "price_description": "免費",
        "description": "大型公園設有兒童遊樂場、草坪同緩跑徑，適合家庭野餐同戶外活動。",
        "opening_hours": "全日開放",
        "website_url": "",
        "google_maps_url": "https://maps.google.com/?q=22.3733,114.1141",
        "status": "Open",
        "confidence": 100,
        "tips": "戶外地點；雨天留意安全",
        "source_urls": "https://www.lcsd.gov.hk/parks/twcp/",
        "checked_at": current_date,
    },
]

print(f"\n📝 Adding {len(sample_places)} sample places...")

added_count = 0
for place_data in sample_places:
    place_id = str(uuid.uuid4())[:8]
    
    # Build row data (matching NEW_HEADERS order)
    row = [
        place_id,  # place_id
        place_data["name"].lower().replace(" ", "-"),  # slug
        place_data["name"],  # name
        place_data["name_en"],  # name_en
        place_data["region"],  # region
        place_data["district"],  # district
        place_data["address"],  # address
        place_data["lat"],  # lat
        place_data["lng"],  # lng
        "manual",  # geocode_confidence
        place_data["category"],  # category
        "TRUE" if place_data["indoor"] else "FALSE",  # indoor
        place_data["age_min"],  # age_min
        place_data["age_max"],  # age_max
        place_data["price_tier"],  # price_tier
        place_data["price_description"],  # price_description
        place_data["description"],  # description
        place_data.get("tips", ""),  # tips
        "",  # facilities
        place_data["opening_hours"],  # opening_hours
        place_data["website_url"],  # website_url
        "",  # facebook_url
        "",  # instagram_url
        place_data.get("google_maps_url", ""),  # google_maps_url (NEW)
        place_data["status"],  # status
        "human_confirmed",  # validation_stage
        place_data["confidence"],  # confidence
        "low",  # risk_tier
        "",  # evidence_urls
        "",  # evidence_snippets
        place_data.get("source_urls", "manual_entry"),  # source_urls
        "",  # published_at
        datetime.now().isoformat(),  # updated_at
        datetime.now().isoformat(),  # last_checked_at
        "",  # next_check_at
        place_data.get("checked_at", ""),  # checked_at (NEW)
        "admin",  # review_owner
        "",  # review_due_at
        "",  # resolution
        "",  # false_alarm_reason
    ]
    
    try:
        worksheet.append_row(row)
        print(f"  ✓ Added: {place_data['name']} (ID: {place_id})")
        added_count += 1
    except Exception as e:
        print(f"  ❌ Error adding {place_data['name']}: {e}")

print(f"\n{'=' * 70}")
print(f"✅ Successfully added {added_count} places!")
print(f"{'=' * 70}")
print(f"\n📊 Sheet URL:")
print(f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
print(f"\n📝 Next steps:")
print(f"  1. Check the 'Places' worksheet in your Google Sheet")
print(f"  2. Run: python3 test_sheets.py (to verify)")
print(f"  3. Run: python3 export_json.py (to export to frontend)")
