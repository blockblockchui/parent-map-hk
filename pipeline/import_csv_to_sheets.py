#!/usr/bin/env python3
"""
Import CSV/TXT files to Google Sheets (Robust version with better CSV parsing)
Usage: python3 import_csv_to_sheets.py /path/to/1.txt /path/to/2.txt [--dry-run]
"""

import os
import sys
import csv
import io
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from google.oauth2.service_account import Credentials
import gspread

print("=" * 70)
print("📥 CSV to Google Sheets Importer (Robust)")
print("=" * 70)

# Check arguments
if len(sys.argv) < 2:
    print("\nUsage: python3 import_csv_to_sheets.py <file1.txt> [file2.txt] [--dry-run]")
    print("\nExample:")
    print("  python3 import_csv_to_sheets.py /home/helsinki/Desktop/1.txt /home/helsinki/Desktop/2.txt")
    sys.exit(1)

files = []
dry_run = False

for arg in sys.argv[1:]:
    if arg == "--dry-run":
        dry_run = True
    else:
        files.append(arg)

print(f"\n📁 Files to import: {len(files)}")
for f in files:
    print(f"  • {f}")

if dry_run:
    print("\n🔍 DRY RUN MODE - No data will be written to Google Sheets")

# All columns in Google Sheets (40 columns)
SHEET_COLUMNS = [
    "place_id", "slug", "name", "name_en", "region", "district", "address", "lat", "lng",
    "geocode_confidence", "category", "indoor", "age_min", "age_max", "price_tier",
    "price_description", "description", "tips", "facilities", "opening_hours",
    "website_url", "facebook_url", "instagram_url", "google_maps_url", "status",
    "validation_stage", "confidence", "risk_tier", "evidence_urls", "evidence_snippets",
    "source_urls", "published_at", "updated_at", "last_checked_at", "next_check_at",
    "checked_at", "review_owner", "review_due_at", "resolution", "false_alarm_reason"
]

# Expected input columns
INPUT_COLUMNS = [
    "place_id", "name", "name_en", "region", "district", "address", "lat", "lng",
    "category", "indoor", "age_min", "age_max", "price_tier", "price_description",
    "description", "opening_hours", "website_url", "facebook_url", "instagram_url",
    "google_maps_url", "status", "tips", "source_urls", "checked_at"
]

# Read and parse CSV files
all_places = []
errors = []

for file_path in files:
    print(f"\n📖 Reading: {file_path}")
    
    if not os.path.exists(file_path):
        errors.append(f"File not found: {file_path}")
        continue
    
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse CSV
        reader = csv.DictReader(io.StringIO(content))
        headers = reader.fieldnames
        
        print(f"  Columns found: {len(headers)}")
        print(f"  Headers: {headers[:5]}...")
        
        # Read rows
        row_count = 0
        for row in reader:
            row_count += 1
            
            # Skip empty rows
            if not row.get('name'):
                continue
            
            # Validate coordinates
            lat = row.get('lat', '').strip()
            lng = row.get('lng', '').strip()
            
            if not lat or not lng:
                errors.append(f"Row {row_count} ({row.get('name', 'N/A')}): Missing coordinates")
                continue
            
            try:
                float(lat)
                float(lng)
            except ValueError:
                errors.append(f"Row {row_count} ({row.get('name', 'N/A')}): Invalid coordinates")
                continue
            
            # Clean and prepare data
            place = {}
            
            # Map input columns to sheet columns
            place['place_id'] = row.get('place_id', '').strip() or str(uuid.uuid4())[:8]
            place['slug'] = row.get('name', '').lower().replace(' ', '-').replace(',', '')[:50]
            place['name'] = row.get('name', '').strip()
            place['name_en'] = row.get('name_en', '').strip()
            place['region'] = row.get('region', 'hk-island').strip()
            place['district'] = row.get('district', '').strip()
            place['address'] = row.get('address', '').strip()
            place['lat'] = lat
            place['lng'] = lng
            place['geocode_confidence'] = 'ai_research'
            place['category'] = row.get('category', 'playhouse').strip()
            place['indoor'] = 'TRUE' if row.get('indoor', '').upper() == 'TRUE' else 'FALSE'
            place['age_min'] = row.get('age_min', '').strip()
            place['age_max'] = row.get('age_max', '').strip()
            place['price_tier'] = row.get('price_tier', '').strip()
            place['price_description'] = row.get('price_description', '').strip()
            place['description'] = row.get('description', '').strip()[:500]  # Limit length
            place['tips'] = row.get('tips', '').strip()[:200]
            place['facilities'] = ''
            place['opening_hours'] = row.get('opening_hours', '').strip()
            place['website_url'] = row.get('website_url', '').strip()
            place['facebook_url'] = row.get('facebook_url', '').strip()
            place['instagram_url'] = row.get('instagram_url', '').strip()
            place['google_maps_url'] = row.get('google_maps_url', '').strip()
            
            # Status handling
            status = row.get('status', '').strip()
            if status not in ['Open', 'SuspectedClosed', 'Closed']:
                status = 'Open'
            place['status'] = status
            
            place['validation_stage'] = 'ai_extracted'
            place['confidence'] = 75 if row.get('source_urls') else 50
            place['risk_tier'] = 'medium'
            place['evidence_urls'] = ''
            place['evidence_snippets'] = ''
            
            # Clean up source_urls (remove newlines)
            source_urls = row.get('source_urls', '').strip()
            source_urls = source_urls.replace('\n', ' ').replace('\r', ' ')
            place['source_urls'] = source_urls
            
            place['published_at'] = ''
            place['updated_at'] = datetime.now().isoformat()
            place['last_checked_at'] = ''
            place['next_check_at'] = ''
            place['checked_at'] = row.get('checked_at', datetime.now().strftime('%Y-%m-%d')).strip()
            place['review_owner'] = ''
            place['review_due_at'] = ''
            place['resolution'] = ''
            place['false_alarm_reason'] = ''
            
            all_places.append(place)
        
        print(f"  ✓ Parsed {row_count} rows, {len([p for p in all_places if p['source_urls']])} with sources")
            
    except Exception as e:
        errors.append(f"Error reading {file_path}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'=' * 70}")
print(f"📊 Summary: {len(all_places)} places ready to import")
print(f"{'=' * 70}")

# Show samples
if all_places:
    print("\n📍 First 3 places:")
    for i, place in enumerate(all_places[:3], 1):
        print(f"\n  {i}. {place['name']}")
        print(f"     District: {place['district']}")
        print(f"     Coords: {place['lat']}, {place['lng']}")
        print(f"     Status: {place['status']}")
        source_preview = place['source_urls'][:50] + "..." if len(place['source_urls']) > 50 else place['source_urls']
        print(f"     Source: {source_preview or 'None'}")

# Report errors
if errors:
    print(f"\n⚠️  Errors ({len(errors)}):")
    for err in errors[:5]:
        print(f"  • {err}")
    if len(errors) > 5:
        print(f"  ... and {len(errors) - 5} more")

# Import to Google Sheets
if not dry_run and all_places:
    print("\n📝 Importing to Google Sheets...")
    
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
        print(f"  Connected to: {worksheet.title}")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet("Places", rows=1000, cols=40)
        worksheet.append_row(SHEET_COLUMNS)
        print(f"  Created new worksheet: Places")
    
    # Import rows
    imported = 0
    skipped = 0
    
    for place in all_places:
        try:
            # Check if place already exists (by name + district)
            existing = worksheet.findall(place['name'])
            if existing:
                # Check if same district
                for cell in existing:
                    row = worksheet.row_values(cell.row)
                    if len(row) > 5 and row[5] == place['district']:  # district is column 6
                        print(f"  ⚠️  Skipped (duplicate): {place['name']} ({place['district']})")
                        skipped += 1
                        break
                else:
                    # Same name but different district
                    row = [place.get(col, '') for col in SHEET_COLUMNS]
                    worksheet.append_row(row)
                    imported += 1
                    print(f"  ✓ {place['name']}")
            else:
                row = [place.get(col, '') for col in SHEET_COLUMNS]
                worksheet.append_row(row)
                imported += 1
                print(f"  ✓ {place['name']}")
                
        except Exception as e:
            print(f"  ❌ {place['name']}: {e}")
    
    print(f"\n✅ Import complete!")
    print(f"   Imported: {imported}")
    print(f"   Skipped (duplicates): {skipped}")
    
elif dry_run:
    print(f"\n🔍 DRY RUN - Would import {len(all_places)} places")
    print("Run without --dry-run to actually import")

print(f"\n{'=' * 70}")
print("🎉 Done!")
print(f"{'=' * 70}")

if not dry_run and all_places:
    print(f"\n📊 Sheet URL:")
    print(f"https://docs.google.com/spreadsheets/d/{os.getenv('GOOGLE_SHEETS_ID')}/edit")
    print(f"\n📝 Next: Run python3 export_json.py to update frontend")
