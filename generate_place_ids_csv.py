#!/usr/bin/env python3
"""
Generate CSV with place_ids for Google Sheets
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
        return
    
    # Generate unique IDs
    print(f"\n🎲 Generating {len(rows_needing_ids)} unique place_ids...")
    new_ids = set()
    while len(new_ids) < len(rows_needing_ids):
        new_id = generate_place_id()
        if new_id not in existing_ids and new_id not in new_ids:
            new_ids.add(new_id)
    
    new_ids = list(new_ids)
    
    # Write to CSV
    output_file = "/root/.openclaw/workspace/parent-map-hk/place_ids_to_fill.csv"
    print(f"\n📝 Writing to CSV: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Row,place_id,Name,District\n")
        for item, new_id in zip(rows_needing_ids, new_ids):
            f.write(f"{item['row']},{new_id},{item['name']},{item['district']}\n")
    
    print(f"✅ CSV created with {len(rows_needing_ids)} entries")
    print(f"\n📋 First 10 entries:")
    for i, (item, new_id) in enumerate(zip(rows_needing_ids[:10], new_ids[:10]), 1):
        print(f"  Row {item['row']}: {new_id} → {item['name']}")

if __name__ == "__main__":
    main()
