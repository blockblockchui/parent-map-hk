#!/usr/bin/env python3
"""Add discovered places to Google Sheets"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from google.oauth2.service_account import Credentials
import gspread

# Connect
sheet_id = "1L_8FfQ_dC4ty53KbrCIvEAlKJwLH_Vl5U_2V0_m78kA"
creds_path = Path(__file__).parent.parent / "pipeline" / "credentials.json"

credentials = Credentials.from_service_account_file(
    str(creds_path),
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)
client = gspread.authorize(credentials)
worksheet = client.open_by_key(sheet_id).worksheet("Places")

# Load discovered places
with open("/root/.openclaw/workspace/parent-map-hk/ready_to_add_20260213.json") as f:
    places = json.load(f)

SHEET_COLUMNS = [
    "place_id", "slug", "name", "name_en", "region", "district", "address", "lat", "lng",
    "geocode_confidence", "category", "indoor", "age_min", "age_max", "price_tier",
    "price_description", "description", "tips", "facilities", "opening_hours",
    "website_url", "facebook_url", "instagram_url", "google_maps_url", "status",
    "validation_stage", "confidence", "risk_tier", "evidence_urls", "evidence_snippets",
    "source_urls", "published_at", "updated_at", "last_checked_at", "next_check_at",
    "checked_at", "review_owner", "review_due_at", "resolution", "false_alarm_reason"
]

print(f"Adding {len(places)} places...")

for p in places:
    # Extract district from address
    address = p.get("address", "")
    district = ""
    if "Wan Chai" in address or "灣仔" in address:
        district = "灣仔"
    elif "Tseung Kwan O" in address or "將軍澳" in address:
        district = "將軍澳"
    elif "Sha Tin" in address or "沙田" in address:
        district = "沙田"
    
    # Determine region
    region = "hk-island" if district == "灣仔" else ("kowloon" if district in [] else "nt")
    
    row = [
        str(uuid.uuid4())[:8],
        p["name"].lower().replace(" ", "-").replace("(", "").replace(")", ""),
        p["name"],
        p.get("nameEn", ""),
        region,
        district,
        address,
        p["lat"],
        p["lng"],
        "google_places",
        p["category"],
        "TRUE" if p["indoor"] else "FALSE",
        p["ageRange"][0],
        p["ageRange"][1],
        p["priceType"],
        "",
        "室內親子遊樂場，從 Google Places 自動搜集",
        p["tips"],
        "",
        "請查詢官網",
        "https://kiztopia.com.hk/",
        "",
        "",
        p["website"],
        "Open",
        "google_places_extracted",
        80,
        "low",
        "",
        "",
        "Google Places API",
        datetime.now().isoformat(),
        datetime.now().isoformat(),
        "",
        "",
        datetime.now().strftime("%Y-%m-%d"),
        "",
        "",
        "",
        ""
    ]
    
    worksheet.append_row(row)
    print(f"✓ Added: {p['name']} ({district})")

print(f"\n✅ Added {len(places)} places to Google Sheets!")
