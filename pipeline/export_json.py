#!/usr/bin/env python3
"""
Export places from Google Sheets to JSON (standalone)
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("📤 Exporting Places to JSON")
print("=" * 70)

# Import gspread
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
worksheet = spreadsheet.worksheet("Places")

# Get all records
records = worksheet.get_all_records()
print(f"\n📊 Found {len(records)} places in Google Sheets")

# Convert to frontend format
locations = []
for record in records:
    # Only export Open places with location data
    if record.get('status') != 'Open':
        continue
    if not record.get('lat') or not record.get('lng'):
        continue
    
    # Safely parse coordinates
    try:
        lat = float(record['lat']) if record.get('lat') else None
    except (ValueError, TypeError):
        lat = None
    try:
        lng = float(record['lng']) if record.get('lng') else None
    except (ValueError, TypeError):
        lng = None
    
    location = {
        "id": record.get('place_id', ''),
        "name": record.get('name', ''),
        "nameEn": record.get('name_en') or None,
        "district": record.get('district', ''),
        "region": record.get('region', 'hk-island'),
        "lat": lat,
        "lng": lng,
        "category": record.get('category', 'playhouse'),
        "indoor": str(record.get('indoor', '')).upper() == 'TRUE',
        "ageRange": [
            int(record['age_min']) if record.get('age_min') and str(record['age_min']).strip().isdigit() else 0,
            int(record['age_max']) if record.get('age_max') and str(record['age_max']).strip().isdigit() else 6
        ],
        "priceType": record.get('price_tier', 'medium'),
        "priceDescription": record.get('price_description', '$100-200'),
        "description": record.get('description', ''),
        "website": record.get('website_url') or None,
        "googleMapsUrl": record.get('google_maps_url') or None,  # NEW
        "tips": record.get('tips') or None,
        "openingHours": record.get('opening_hours', '請查詢官網'),
        "address": record.get('address', ''),
        "hasBabyRoom": False,
        "hasStrollerAccess": True,
        "hasRestaurant": False,
        "rainyDaySuitable": True,
        "verified": record.get('validation_stage') == 'human_confirmed',
        "updatedAt": record.get('updated_at'),
        "checkedAt": record.get('checked_at'),  # NEW
        "sourceUrls": record.get('source_urls'),  # NEW
    }
    locations.append(location)

print(f"✓ {len(locations)} places ready for export")

# Build output
output = {
    "metadata": {
        "exported_at": datetime.now().isoformat(),
        "total_count": len(locations),
        "version": "1.0",
        "source": "Google Sheets",
    },
    "locations": locations,
}

# Write JSON
output_path = Path(__file__).parent.parent / "data" / "locations.json"
output_path.parent.mkdir(exist_ok=True)

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2, default=str)

print(f"\n✅ Exported to: {output_path}")
print(f"\n📋 Sample data:")
if locations:
    print(json.dumps(locations[0], ensure_ascii=False, indent=2))

print(f"\n{'=' * 70}")
print("🎉 Export complete!")
print(f"{'=' * 70}")
