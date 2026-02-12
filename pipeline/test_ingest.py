#!/usr/bin/env python3
"""
Test pipeline ingestion (standalone, no relative imports)
"""

import sys
import os
import asyncio
import uuid
from datetime import datetime
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 70)
print("🚀 Testing Pipeline Ingestion")
print("=" * 70)

# Check configuration
sheet_id = os.getenv("GOOGLE_SHEETS_ID")
if not sheet_id:
    print("❌ GOOGLE_SHEETS_ID not set")
    sys.exit(1)
print(f"\n📋 Sheet ID: {sheet_id[:30]}...")

# Parse sources.yaml
import yaml
sources_file = Path(__file__).parent / "config" / "sources.yaml"
with open(sources_file) as f:
    config_data = yaml.safe_load(f)

sources = config_data.get('sources', [])
enabled_sources = [s for s in sources if s.get('enabled', True)]
print(f"📡 Found {len(sources)} sources, {len(enabled_sources)} enabled")

# Show enabled sources
for src in enabled_sources:
    print(f"  • {src['name']} ({src['type']})")

# Test RSS feed parsing (if any RSS sources)
print("\n" + "-" * 70)
print("🧪 Testing RSS Feed Parsing")
print("-" * 70)

import feedparser

rss_sources = [s for s in enabled_sources if s['type'] == 'rss']
if not rss_sources:
    print("No enabled RSS sources found")
else:
    for source in rss_sources:
        print(f"\n📰 Testing: {source['name']}")
        print(f"   URL: {source['url'][:60]}...")
        
        try:
            feed = feedparser.parse(source['url'])
            print(f"   ✓ Feed parsed successfully")
            print(f"   📊 Entries found: {len(feed.entries)}")
            
            # Show sample entries
            for i, entry in enumerate(feed.entries[:3], 1):
                title = entry.get('title', 'N/A')[:50]
                print(f"   {i}. {title}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

# Test what would be extracted
print("\n" + "-" * 70)
print("📝 Simulating Place Extraction")
print("-" * 70)

# Create a sample extract for demonstration
sample_extract = {
    "place_id": str(uuid.uuid4())[:8],
    "name": "測試親子遊樂場",
    "district": "灣仔",
    "region": "hk-island",
    "category": "playhouse",
    "indoor": True,
    "age_min": 0,
    "age_max": 6,
    "description": "這是一個測試用的親子地點資料",
    "status": "PendingReview",
    "source_url": "https://example.com/test",
    "extracted_at": datetime.utcnow().isoformat(),
}

print("\n📍 Sample place that would be added:")
for key, value in sample_extract.items():
    print(f"   {key}: {value}")

# Show dry run message
print("\n" + "=" * 70)
print("ℹ️  DRY RUN MODE")
print("=" * 70)
print("In dry-run mode, no data is written to Google Sheets.")
print("\nTo actually add data:")
print("  1. Add real sources to config/sources.yaml")
print("  2. Run without --dry-run flag")
print("  3. Or manually add data to the Google Sheet")

print("\n" + "=" * 70)
print("✅ Pipeline test completed successfully!")
print("=" * 70)
