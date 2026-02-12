#!/usr/bin/env python3
"""
Standalone test for Google Sheets connection
(No relative imports)
"""

import sys
import os
import json
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

try:
    print("=" * 60)
    print("🧪 Testing Google Sheets Connection")
    print("=" * 60)
    
    # Test 1: Check environment
    print("\n1️⃣  Checking environment...")
    sheet_id = os.getenv("GOOGLE_SHEETS_ID")
    if not sheet_id:
        print("   ❌ GOOGLE_SHEETS_ID not found in .env")
        sys.exit(1)
    print(f"   ✓ Sheet ID: {sheet_id[:25]}...")
    
    # Test 2: Check credentials
    print("\n2️⃣  Checking credentials...")
    creds_path = Path(__file__).parent / "credentials.json"
    if not creds_path.exists():
        print(f"   ❌ credentials.json not found at {creds_path}")
        sys.exit(1)
    
    with open(creds_path) as f:
        creds = json.load(f)
    print(f"   ✓ credentials.json found")
    print(f"   ✓ Project: {creds.get('project_id', 'N/A')}")
    print(f"   ✓ Client Email: {creds.get('client_email', 'N/A')[:45]}...")
    
    # Test 3: Connect to Google Sheets
    print("\n3️⃣  Connecting to Google Sheets...")
    
    from google.oauth2.service_account import Credentials
    import gspread
    
    credentials = Credentials.from_service_account_file(
        str(creds_path),
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
    )
    
    client = gspread.authorize(credentials)
    print(f"   ✓ Authenticated successfully")
    
    # Test 4: Open spreadsheet
    print("\n4️⃣  Opening spreadsheet...")
    spreadsheet = client.open_by_key(sheet_id)
    print(f"   ✓ Spreadsheet: {spreadsheet.title}")
    
    # Test 5: Access/create worksheet
    print("\n5️⃣  Accessing 'Places' worksheet...")
    try:
        worksheet = spreadsheet.worksheet("Places")
        print(f"   ✓ Worksheet exists: {worksheet.title}")
    except gspread.WorksheetNotFound:
        print("   ℹ️  Worksheet not found, creating...")
        worksheet = spreadsheet.add_worksheet("Places", rows=1000, cols=38)
        # Add headers
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
        print(f"   ✓ Created worksheet: {worksheet.title}")
    
    print(f"   ✓ Rows: {worksheet.row_count}")
    print(f"   ✓ Cols: {worksheet.col_count}")
    
    # Test 6: Check data
    print("\n6️⃣  Checking data...")
    records = worksheet.get_all_records()
    print(f"   ✓ Found {len(records)} place records")
    
    if records:
        print(f"\n   Sample: {records[0].get('name', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("✅ All tests passed!")
    print("=" * 60)
    print("\n📝 Your Google Sheets setup is working correctly!")
    print("\nNext steps:")
    print("   1. Add place data to the 'Places' worksheet")
    print("   2. Run: python -m src.ingest_sources --dry-run")
    print("   3. Or run: python -m src.export_json --compare")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("Troubleshooting:")
    print("1. Check if Sheet is shared with:")
    print("   place-search@parent-map-hk.iam.gserviceaccount.com")
    print("2. Verify API is enabled at:")
    print("   https://console.cloud.google.com/apis/dashboard")
    print("3. Make sure the email has 'Editor' permission")
    print("=" * 60)
    sys.exit(1)
