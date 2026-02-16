#!/usr/bin/env python3
"""
Auto-fill all missing place_ids to Google Sheets
"""

import sys
import random
import string
import time
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
    
    # Update sheet in batches
    print(f"\n📝 Updating Google Sheets (batch mode)...")
    place_id_col = 1  # Column A
    
    # Prepare batch updates
    updates = []
    for i, item in enumerate(rows_needing_ids):
        new_id = new_ids[i]
        updates.append({
            'range': f'A{item["row"]}',
            'values': [[new_id]]
        })
    
    # Batch update (50 at a time to avoid rate limits)
    batch_size = 50
    total = len(updates)
    
    for i in range(0, total, batch_size):
        batch = updates[i:i+batch_size]
        try:
            # Use batch_update for efficiency
            for update in batch:
                ws.update(update['range'], update['values'])
            print(f"  Updated {min(i+batch_size, total)}/{total} rows...")
            time.sleep(1)  # Rate limit protection
        except Exception as e:
            print(f"  ❌ Error in batch {i//batch_size + 1}: {e}")
            time.sleep(2)
    
    print("\n✅ Done! All place_ids filled.")

if __name__ == "__main__":
    main()
