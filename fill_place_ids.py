#!/usr/bin/env python3
"""
Read Google Sheets and fill in missing place_ids
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
    # Use uppercase letters and numbers, exclude confusing characters
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
    
    for i, row in enumerate(records, start=2):  # start=2 because row 1 is header
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
    
    # Show which rows need IDs
    print("\n📋 Rows needing place_id:")
    for item in rows_needing_ids[:20]:  # Show first 20
        print(f"  Row {item['row']}: {item['name']} ({item['district']})")
    
    if len(rows_needing_ids) > 20:
        print(f"  ... and {len(rows_needing_ids) - 20} more")
    
    # Generate unique IDs
    print(f"\n🎲 Generating {len(rows_needing_ids)} unique place_ids...")
    new_ids = set()
    while len(new_ids) < len(rows_needing_ids):
        new_id = generate_place_id()
        if new_id not in existing_ids and new_id not in new_ids:
            new_ids.add(new_id)
    
    new_ids = list(new_ids)
    
    # Ask for confirmation
    print("\n⚠️  Ready to fill in place_ids to Google Sheets")
    print("   This will update the 'place_id' column for empty rows")
    response = input("\nProceed? (yes/no): ")
    
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Update sheet
    print("\n📝 Updating Google Sheets...")
    place_id_col = 1  # Column A (place_id is first column)
    
    for i, item in enumerate(rows_needing_ids):
        new_id = new_ids[i]
        row_num = item['row']
        
        try:
            ws.update_cell(row_num, place_id_col, new_id)
            print(f"  Row {row_num}: {item['name']} → {new_id}")
        except Exception as e:
            print(f"  ❌ Error updating row {row_num}: {e}")
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
