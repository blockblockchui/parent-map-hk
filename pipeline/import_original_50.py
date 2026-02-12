#!/usr/bin/env python3
"""
Import all original locations from multiple TS files to Google Sheets
"""

import os
import sys
import re
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from google.oauth2.service_account import Credentials
import gspread

print("=" * 70)
print("📥 Importing All Original Locations to Google Sheets")
print("=" * 70)

# Files to process
DATA_DIR = Path(__file__).parent.parent / "data"
FILES = [
    "locations.ts",
    "locations50.ts", 
    "locations_021_050.ts"
]

all_locations = []

for filename in FILES:
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"⚠️  File not found: {filename}")
        continue
    
    print(f"\n📖 Reading: {filename}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse locations
    loc_blocks = re.findall(r'\{\s*id:[^}]+\}', content, re.DOTALL)
    print(f"  Found {len(loc_blocks)} location blocks")
    
    for block in loc_blocks:
        try:
            loc = {}
            
            id_match = re.search(r'id:\s*"([^"]+)"', block)
            name_match = re.search(r'name:\s*"([^"]+)"', block)
            district_match = re.search(r'district:\s*"([^"]+)"', block)
            region_match = re.search(r'region:\s*"([^"]+)"', block)
            lat_match = re.search(r'lat:\s*([\d.]+)', block)
            lng_match = re.search(r'lng:\s*([\d.]+)', block)
            category_match = re.search(r'category:\s*"([^"]+)"', block)
            indoor_match = re.search(r'indoor:\s*(\w+)', block)
            age_match = re.search(r'ageRange:\s*\[(\d+),\s*(\d+)\]', block)
            price_type_match = re.search(r'priceType:\s*"([^"]+)"', block)
            price_desc_match = re.search(r'priceDescription:\s*"([^"]+)"', block)
            desc_match = re.search(r'description:\s*"([^"]+)"', block)
            website_match = re.search(r'website:\s*"([^"]*)"', block)
            tips_match = re.search(r'tips:\s*"([^"]*)"', block)
            opening_match = re.search(r'openingHours:\s*"([^"]*)"', block)
            address_match = re.search(r'address:\s*"([^"]+)"', block)
            
            if name_match:
                loc['id'] = id_match.group(1) if id_match else ''
                loc['name'] = name_match.group(1)
                loc['district'] = district_match.group(1) if district_match else ''
                loc['region'] = region_match.group(1) if region_match else 'hk-island'
                loc['lat'] = lat_match.group(1) if lat_match else ''
                loc['lng'] = lng_match.group(1) if lng_match else ''
                loc['category'] = category_match.group(1) if category_match else 'playhouse'
                loc['indoor'] = 'TRUE' if (indoor_match and indoor_match.group(1) == 'true') else 'FALSE'
                loc['age_min'] = age_match.group(1) if age_match else '0'
                loc['age_max'] = age_match.group(2) if age_match else '6'
                loc['price_tier'] = price_type_match.group(1) if price_type_match else 'medium'
                loc['price_description'] = price_desc_match.group(1) if price_desc_match else ''
                loc['description'] = desc_match.group(1) if desc_match else ''
                loc['website'] = website_match.group(1) if website_match else ''
                loc['tips'] = tips_match.group(1) if tips_match else ''
                loc['opening_hours'] = opening_match.group(1) if opening_match else ''
                loc['address'] = address_match.group(1) if address_match else ''
                
                all_locations.append(loc)
        except Exception as e:
            continue

print(f"\n{'=' * 70}")
print(f"✓ Total parsed: {len(all_locations)} locations")
print(f"{'=' * 70}")

# Show sample
if all_locations:
    print("\n📍 Sample locations:")
    for i, loc in enumerate(all_locations[:5], 1):
        print(f"  {i}. {loc['name']} ({loc['district']})")

# Connect to Google Sheets
print("\n📝 Connecting to Google Sheets...")
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
print(f"\n📝 Importing {len(all_locations)} locations...")
imported = 0
skipped = 0

for loc in all_locations:
    try:
        # Check for duplicates
        existing = worksheet.findall(loc['name'])
        is_dup = False
        for cell in existing:
            row_vals = worksheet.row_values(cell.row)
            if len(row_vals) > 5 and row_vals[5] == loc['district']:
                is_dup = True
                break
        
        if is_dup:
            print(f"  ⚠️  Skipped: {loc['name']}")
            skipped += 1
            continue
        
        # Build row
        data = {
            'place_id': loc['id'] or str(uuid.uuid4())[:8],
            'slug': loc['name'].lower().replace(' ', '-')[:50],
            'name': loc['name'],
            'name_en': '',
            'region': loc['region'],
            'district': loc['district'],
            'address': loc['address'],
            'lat': loc['lat'],
            'lng': loc['lng'],
            'geocode_confidence': 'manual',
            'category': loc['category'],
            'indoor': loc['indoor'],
            'age_min': loc['age_min'],
            'age_max': loc['age_max'],
            'price_tier': loc['price_tier'],
            'price_description': loc['price_description'],
            'description': loc['description'],
            'tips': loc['tips'],
            'facilities': '',
            'opening_hours': loc['opening_hours'],
            'website_url': loc['website'],
            'facebook_url': '',
            'instagram_url': '',
            'google_maps_url': '',
            'status': 'Open',
            'validation_stage': 'human_confirmed',
            'confidence': 90,
            'risk_tier': 'low',
            'evidence_urls': '',
            'evidence_snippets': '',
            'source_urls': 'original_50_locations',
            'published_at': '',
            'updated_at': datetime.now().isoformat(),
            'last_checked_at': '',
            'next_check_at': '',
            'checked_at': datetime.now().strftime('%Y-%m-%d'),
            'review_owner': '',
            'review_due_at': '',
            'resolution': '',
            'false_alarm_reason': '',
        }
        
        row_data = [data.get(col, '') for col in SHEET_COLUMNS]
        worksheet.append_row(row_data)
        imported += 1
        print(f"  ✓ {loc['name']}")
        
    except Exception as e:
        print(f"  ❌ {loc['name']}: {e}")

print(f"\n{'=' * 70}")
print(f"✅ Import complete!")
print(f"   Imported: {imported}")
print(f"   Skipped (duplicates): {skipped}")
print(f"{'=' * 70}")

print(f"\n📊 Sheet URL:")
print(f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit")
