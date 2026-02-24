#!/usr/bin/env python3
"""
Export places from Google Sheets to JSON (standalone)
Updated for new schema with 03_places sheet
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

# Load districts lookup
districts_ws = spreadsheet.worksheet("02_districts")
districts_records = districts_ws.get_all_records()
districts_map = {d['district_id']: d for d in districts_records}

# Load places
worksheet = spreadsheet.worksheet("03_places")
records = worksheet.get_all_records()
print(f"\n📊 Found {len(records)} places in Google Sheets")

# Load place links (for website, facebook, instagram)
try:
    links_ws = spreadsheet.worksheet("08_place_links")
    links_records = links_ws.get_all_records()
    # Build lookup: place_id -> {link_type: url}
    links_map = {}
    for link in links_records:
        pid = link.get('place_id')
        if pid:
            if pid not in links_map:
                links_map[pid] = {}
            links_map[pid][link.get('link_type')] = link.get('url')
except Exception as e:
    print(f"⚠️ Could not load place_links: {e}")
    links_map = {}

# Load opening hours mapping from 13_opening_hours_mapping
try:
    oh_ws = spreadsheet.worksheet("13_opening_hours_mapping")
    oh_records = oh_ws.get_all_records()
    # Build lookup: id -> opening_hours_mapping (id matches opening_hours_json_mapping in places)
    opening_hours_map = {}
    for oh in oh_records:
        oh_id = oh.get('id')
        if oh_id:
            # Parse opening_hours_json which contains the full mapping
            oh_json = oh.get('opening_hours_json')
            if oh_json and isinstance(oh_json, str):
                try:
                    import json
                    parsed = json.loads(oh_json)
                    opening_hours_map[oh_id] = {
                        'default_hours': parsed.get('default_hours', ''),
                        'has_override': parsed.get('has_override', False),
                        'override_rule': parsed.get('override_rule'),
                    }
                except:
                    pass
            elif oh_json and isinstance(oh_json, dict):
                opening_hours_map[oh_id] = {
                    'default_hours': oh_json.get('default_hours', ''),
                    'has_override': oh_json.get('has_override', False),
                    'override_rule': oh_json.get('override_rule'),
                }
    print(f"✓ Loaded {len(opening_hours_map)} opening hours mappings")
except Exception as e:
    print(f"⚠️ Could not load opening_hours_mapping: {e}")
    opening_hours_map = {}

# Convert to frontend format
locations = []
for record in records:
    # Only export active places with location data
    status = record.get('status', '').lower()
    if status not in ['active', 'open', '']:
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
    
    if lat is None or lng is None:
        continue
    
    # Lookup district and region
    district_id = record.get('district_id', '')
    district_info = districts_map.get(district_id, {})
    district_name = district_info.get('name_zh', district_id)
    region = district_info.get('region', 'hk-island')
    
    # Get place links
    pid = record.get('place_id', '')
    place_links = links_map.get(pid, {})
    
    # Parse age range
    age_min = 0
    age_max = 12
    try:
        if record.get('age_min') and str(record['age_min']).strip().isdigit():
            age_min = int(record['age_min'])
    except:
        pass
    try:
        if record.get('age_max') and str(record['age_max']).strip().isdigit():
            age_max = int(record['age_max'])
    except:
        pass
    
    # Parse indoor (yes/no/mixed -> boolean for backward compat)
    indoor_val = str(record.get('indoor', '')).lower()
    indoor = indoor_val == 'yes'
    
    location = {
        "id": pid,
        "slug": record.get('slug') or None,
        "name": record.get('name_zh', ''),
        "nameEn": record.get('name_en') or None,
        "district": district_name,
        "region": region,
        "lat": lat,
        "lng": lng,
        "category": record.get('category_key', 'playhouse'),
        "indoor": indoor,
        "ageRange": [age_min, age_max],
        "priceType": record.get('price_tier', 'medium'),
        "priceDescription": record.get('price_desc') or None,
        "description": record.get('description_short') or '',
        "website": place_links.get('website') or None,
        "facebook_url": place_links.get('facebook') or None,
        "instagram_url": place_links.get('instagram') or None,
        "googleMapsUrl": None,  # Not in new schema
        "tips": record.get('tips') or None,
        "openingHours": record.get('opening_hours_short') or '請查詢官網',
        "address": record.get('address_zh', ''),
        "hasBabyRoom": False,
        "hasStrollerAccess": str(record.get('stroller_friendly', '')).lower() == 'yes',
        "hasRestaurant": False,
        "rainyDaySuitable": str(record.get('rainy_day_ok', '')).lower() == 'yes',
        "verified": str(record.get('verified', '')).lower() == 'true',
        "updatedAt": record.get('updated_at'),
        "stay_duration_min": int(record['stay_duration_min']) if record.get('stay_duration_min') and str(record['stay_duration_min']).strip().isdigit() else None,
    }
    
    # Add opening hours mapping if exists
    oh_mapping_id = record.get('opening_hours_json_mapping')
    if oh_mapping_id:
        try:
            oh_id = int(oh_mapping_id)
            location["opening_hours_mapping"] = opening_hours_map.get(oh_id)
        except (ValueError, TypeError):
            pass
    
    locations.append(location)

print(f"✓ {len(locations)} places ready for export")

# Build output
output = {
    "metadata": {
        "exported_at": datetime.now().isoformat(),
        "total_count": len(locations),
        "version": "1.1",
        "source": "Google Sheets (03_places)",
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
