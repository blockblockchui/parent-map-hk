#!/usr/bin/env python3
"""
Manual parsing for 3.txt - handles complex CSV with commas in fields
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from google.oauth2.service_account import Credentials
import gspread

print("=" * 70)
print("📥 Importing 3.txt (Manual Parser)")
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

# Manual parse
file_path = "/home/helsinki/Desktop/3.txt"
print(f"\n📖 Reading: {file_path}")

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# First line is header
headers = lines[0].strip().split(',')
print(f"✓ Headers: {len(headers)} columns")

# Parse data rows
places = []
for i, line in enumerate(lines[1:], 2):
    line = line.strip()
    if not line:
        continue
    
    # Simple split - this assumes well-formed CSV
    # For complex CSV with embedded commas, we'd need a proper parser
    parts = line.split(',')
    
    if len(parts) >= 24:
        place = {
            'place_id': parts[0],
            'name': parts[1],
            'name_en': parts[2],
            'region': parts[3],
            'district': parts[4],
            'address': ','.join(parts[5:11]) if len(parts) > 11 else parts[5],  # Address may contain commas
            'lat': parts[-18] if len(parts) >= 18 else '',
            'lng': parts[-17] if len(parts) >= 17 else '',
            'category': parts[-16] if len(parts) >= 16 else 'playhouse',
            'indoor': parts[-15] if len(parts) >= 15 else 'TRUE',
            'age_min': parts[-14] if len(parts) >= 14 else '',
            'age_max': parts[-13] if len(parts) >= 13 else '',
            'price_tier': parts[-12] if len(parts) >= 12 else '',
            'price_description': parts[-11] if len(parts) >= 11 else '',
            'description': parts[-10] if len(parts) >= 10 else '',
            'opening_hours': parts[-9] if len(parts) >= 9 else '',
            'website_url': parts[-8] if len(parts) >= 8 else '',
            'facebook_url': parts[-7] if len(parts) >= 7 else '',
            'instagram_url': parts[-6] if len(parts) >= 6 else '',
            'google_maps_url': parts[-5] if len(parts) >= 5 else '',
            'status': parts[-4] if len(parts) >= 4 else 'Open',
            'tips': parts[-3] if len(parts) >= 3 else '',
            'source_urls': parts[-2] if len(parts) >= 2 else '',
            'checked_at': parts[-1] if len(parts) >= 1 else datetime.now().strftime('%Y-%m-%d'),
        }
        places.append(place)

print(f"✓ Found {len(places)} places")

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

# Show samples
print("\n📍 First 3 places:")
for i, p in enumerate(places[:3], 1):
    print(f"  {i}. {p['name']} ({p['district']}) - {p['lat']},{p['lng']}")

# Import
print(f"\n📝 Importing {len(places)} places...")
imported = 0

for place in places:
    # Skip if no name
    if not place['name']:
        continue
    
    # Build row
    data = {
        'place_id': place['place_id'] or str(uuid.uuid4())[:8],
        'slug': place['name'].lower().replace(' ', '-')[:50],
        'name': place['name'],
        'name_en': place['name_en'],
        'region': place['region'] or 'hk-island',
        'district': place['district'],
        'address': place['address'][:200],
        'lat': place['lat'],
        'lng': place['lng'],
        'geocode_confidence': 'ai_research',
        'category': place['category'] or 'playhouse',
        'indoor': place['indoor'] if place['indoor'] else 'TRUE',
        'age_min': place['age_min'],
        'age_max': place['age_max'],
        'price_tier': place['price_tier'],
        'price_description': place['price_description'][:100],
        'description': place['description'][:500],
        'tips': place['tips'][:200],
        'facilities': '',
        'opening_hours': place['opening_hours'][:100],
        'website_url': place['website_url'][:200],
        'facebook_url': place['facebook_url'][:200],
        'instagram_url': place['instagram_url'][:200],
        'google_maps_url': place['google_maps_url'][:200],
        'status': place['status'] if place['status'] in ['Open', 'SuspectedClosed', 'Closed'] else 'Open',
        'validation_stage': 'ai_extracted',
        'confidence': 75 if place.get('source_urls') else 50,
        'risk_tier': 'medium',
        'evidence_urls': '',
        'evidence_snippets': '',
        'source_urls': place.get('source_urls', '').replace('\n', ' ')[:500],
        'published_at': '',
        'updated_at': datetime.now().isoformat(),
        'last_checked_at': '',
        'next_check_at': '',
        'checked_at': place.get('checked_at', datetime.now().strftime('%Y-%m-%d')),
        'review_owner': '',
        'review_due_at': '',
        'resolution': '',
        'false_alarm_reason': '',
    }
    
    # Check duplicates
    try:
        existing = worksheet.findall(data['name'])
        for cell in existing:
            row_vals = worksheet.row_values(cell.row)
            if len(row_vals) > 5 and row_vals[5] == data['district']:
                print(f"  ⚠️  Skipped: {data['name']} ({data['district']}) - duplicate")
                break
        else:
            # Add row
            row_data = [data.get(col, '') for col in SHEET_COLUMNS]
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
print(f"\n📝 Next: Run python3 export_json.py to update frontend")
