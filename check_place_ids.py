#!/usr/bin/env python3
"""
Read Google Sheets and show rows needing place_ids
"""

import sys
import random
import string
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent / "pipeline"))

from pipeline.src.sheets_client import SheetsClient

def generate_place_id():
    """Generate a random 8-character place ID"""
    chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
    return ''.join(random.choices(chars, k=8))

def main():
    print("Connecting to Google Sheets...")
    client = SheetsClient()
    
    # Get the Places worksheet
    try:
        ws = client.get_worksheet("Places")
    except Exception as e:
        print(f"Error accessing sheet: {e}")
        return
    
    # Get all records
    print("Reading sheet data...")
    records = ws.get_all_records()
    
    print(f"\nTotal rows: {len(records)}")
    
    # Find rows without place_id
    rows_needing_ids = []
    existing_ids = set()
    
    for i, row in enumerate(records, start=2):
        place_id = str(row.get('place_id', '')).strip()
        name = row.get('name', '')
        
        if place_id:
            existing_ids.add(place_id)
        else:
            rows_needing_ids.append({
                'row': i,
                'name': name,
                'district': row.get('district', '')
            })
    
    print(f"\nExisting IDs: {len(existing_ids)}")
    print(f"Rows needing IDs: {len(rows_needing_ids)}")
    
    if not rows_needing_ids:
        print("\n✅ All rows have place_ids!")
        return [], existing_ids
    
    # Show which rows need IDs
    print("\n📋 First 20 rows needing place_id:")
    for item in rows_needing_ids[:20]:
        print(f"  Row {item['row']}: {item['name']} ({item['district']})")
    
    if len(rows_needing_ids) > 20:
        print(f"  ... and {len(rows_needing_ids) - 20} more rows")
    
    return rows_needing_ids, existing_ids

if __name__ == "__main__":
    rows_needing_ids, existing_ids = main()
    
    if rows_needing_ids:
        print(f"\n🎲 Generating {len(rows_needing_ids)} unique place_ids...")
        new_ids = set()
        while len(new_ids) < len(rows_needing_ids):
            new_id = generate_place_id()
            if new_id not in existing_ids and new_id not in new_ids:
                new_ids.add(new_id)
        
        print("\n✅ Generated IDs (ready to fill in):")
        for item, new_id in zip(rows_needing_ids, new_ids):
            print(f"  Row {item['row']}: {new_id} → {item['name']}")
