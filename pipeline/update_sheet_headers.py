#!/usr/bin/env python3
"""
Update Google Sheets headers to match latest format
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from google.oauth2.service_account import Credentials
import gspread

print("=" * 70)
print("📝 Updating Google Sheets Headers")
print("=" * 70)

# New headers matching the improved prompt
NEW_HEADERS = [
    "place_id",
    "slug",
    "name",
    "name_en",
    "region",
    "district",
    "address",
    "lat",
    "lng",
    "geocode_confidence",
    "category",
    "indoor",
    "age_min",
    "age_max",
    "price_tier",
    "price_description",
    "description",
    "tips",
    "facilities",
    "opening_hours",
    "website_url",
    "facebook_url",
    "instagram_url",
    "google_maps_url",  # NEW
    "status",
    "validation_stage",
    "confidence",
    "risk_tier",
    "evidence_urls",
    "evidence_snippets",
    "source_urls",
    "published_at",
    "updated_at",
    "last_checked_at",
    "next_check_at",
    "checked_at",  # NEW
    "review_owner",
    "review_due_at",
    "resolution",
    "false_alarm_reason",
]

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

# Get or create worksheet
try:
    worksheet = spreadsheet.worksheet("Places")
    print(f"✓ Found worksheet: {worksheet.title}")
except gspread.WorksheetNotFound:
    print("Creating new worksheet...")
    worksheet = spreadsheet.add_worksheet("Places", rows=1000, cols=len(NEW_HEADERS))
    print(f"✓ Created worksheet: {worksheet.title}")

# Check current headers
current_headers = worksheet.row_values(1)
print(f"\n📊 Current columns: {len(current_headers)}")
print(f"📊 New columns: {len(NEW_HEADERS)}")

# Compare headers
if current_headers == NEW_HEADERS:
    print("\n✅ Headers already up to date!")
else:
    print("\n📝 Updating headers...")
    
    # Show differences
    print("\nChanges:")
    added = [h for h in NEW_HEADERS if h not in current_headers]
    removed = [h for h in current_headers if h not in NEW_HEADERS]
    
    if added:
        print(f"  + Added: {', '.join(added)}")
    if removed:
        print(f"  - Removed: {', '.join(removed)}")
    
    # Update first row with new headers
    worksheet.update([NEW_HEADERS], "A1")
    print("\n✅ Headers updated successfully!")

# Verify
print("\n📋 Current headers:")
for i, header in enumerate(worksheet.row_values(1), 1):
    print(f"  {i:2}. {header}")

print(f"\n{'=' * 70}")
print("🎉 Google Sheets headers are now up to date!")
print(f"{'=' * 70}")
