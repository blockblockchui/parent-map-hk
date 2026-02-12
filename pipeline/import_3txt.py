#!/usr/bin/env python3
"""
Quick import for 3.txt with better CSV handling
"""

import os
import sys
import csv
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from google.oauth2.service_account import Credentials
import gspread

print("=" * 70)
print("📥 Importing 3.txt to Google Sheets")
print("=" * 70)

# Authenticate
sheet_id = os.getenv("GOOGLE_SHEETS_ID")
creds_path = Path(__file__).parent / "credentials.json"

credentials = Credentials.from_service_account_file(
    str(creds_path),
    scopes=[
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
)
client = gspread.authorize(credentials)
spreadsheet = client.open_by_key(sheet_id)

try:
    worksheet = spreadsheet.worksheet("Places")
    print(f"✓ Connected to: {worksheet.title}")
except gspread.WorksheetNotFound:
    print("❌ Places worksheet not found")
    sys.exit(1)

# Read CSV with proper handling
file_path = "/home/helsinki/Desktop/3.txt"
print(f"\n📖 Reading: {file_path}")

places = []
with open(file_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if not row.get('name'):
            continue
        places.append(row)

print(f"✓ Found {len(places)} places")

# Show first few
print("\n📍 Sample:")
for i, p in enumerate(places[:3], 1):
    print(f"  {i}. {p.get('name')} ({p.get('district')})")

# Sheet columns
SHEET_COLUMNS = [
    "place_id", "slug", "name", "name_en", "region", "district", "address", "lat", "lng",
    "geocode_confidence", "category", "indoor", "age_min", "age_max", "price_tier",
    "price_description", "description", "tips", "facilities", "opening_hours",
    "website_url", "facebook_url", "instagram_url", "google_maps_url", "status",
    "validation_stage", "confidence", "risk_tier", "evidence_urls", "evidence_snippets",
    "source_urls", "published_at", "updated_at", "last_checked_at", "next_check_at",
    "checked_at", "review_owner", "review_due_at", "resolution", "false_alarm_reason"
]

# Import
print(f"\n📝 Importing...")
imported = 0

for row in places:
    # Build data
    data = {
        'place_id': row.get('place_id') or str(uuid.uuid4())[:8],
        'slug': row.get('name', '').lower().replace(' ', '-')[:50],
        'name': row.get('name', ''),
        'name_en': row.get('name_en', ''),
        'region': row.get('region', 'hk-island'),
        'district': row.get('district', ''),
        'address': row.get('address', ''),
        'lat': row.get('lat', ''),
        'lng': row.get('lng', ''),
        'geocode_confidence': 'ai_research',
        'category': row.get('category', 'playhouse'),
        'indoor': row.get('indoor', 'TRUE'),
        'age_min': row.get('age_min', ''),
        'age_max': row.get('age_max', ''),
        'price_tier': row.get('price_tier', ''),
        'price_description': row.get('price_description', '')[:100],
        'description': row.get('description', '')[:500],
        'tips': row.get('tips', '')[:200],
        'facilities': '',
        'opening_hours': row.get('opening_hours', ''),
        'website_url': row.get('website_url', ''),
        'facebook_url': row.get('facebook_url', ''),
        'instagram_url': row.get('instagram_url', ''),
        'google_maps_url': row.get('google_maps_url', ''),
        'status': row.get('status', 'Open'),
        'validation_stage': 'ai_extracted',
        'confidence': 75 if row.get('source_urls') else 50,
        'risk_tier': 'medium',
        'evidence_urls': '',
        'evidence_snippets': '',
        'source_urls': row.get('source_urls', '').replace('\n', ' '),
        'published_at': '',
        'updated_at': datetime.now().isoformat(),
        'last_checked_at': '',
        'next_check_at': '',
        'checked_at': row.get('checked_at', datetime.now().strftime('%Y-%m-%d')),
        'review_owner': '',
        'review_due_at': '',
        'resolution': '',
        'false_alarm_reason': '',
    }
    
    # Check for duplicates
    try:
        existing = worksheet.findall(data['name'])
        is_dup = False
        for cell in existing:
            row_vals = worksheet.row_values(cell.row)
            if len(row_vals) > 5 and row_vals[5] == data['district']:
                is_dup = True
                break
        
        if is_dup:
            print(f"  ⚠️  Skipped (duplicate): {data['name']}")
            continue
    except:
        pass
    
    # Add row
    row_data = [data.get(col, '') for col in SHEET_COLUMNS]
    try:
        worksheet.append_row(row_data)
        imported += 1
        print(f"  ✓ {data['name']}")
    except Exception as e:
        print(f"  ❌ {data['name']}: {e}")

print(f"\n{'=' * 70}")
print(f"✅ Import complete!")
print(f"   Imported: {imported}")
print(f"{'=' * 70}")

print(f"\n📊 Sheet URL:")
print(f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
