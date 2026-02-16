#!/usr/bin/env python3
"""
Generate random place IDs for Parent Map HK
Format: 8 characters, alphanumeric (uppercase letters + numbers)
Example: K7X2M9P4, R5N8W3Q1
"""

import random
import string

def generate_place_id():
    """Generate a random 8-character place ID"""
    # Use uppercase letters and numbers, exclude confusing characters (0, O, I, 1)
    chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
    return ''.join(random.choices(chars, k=8))

def generate_unique_ids(count, existing_ids=None):
    """Generate multiple unique place IDs"""
    if existing_ids is None:
        existing_ids = set()
    
    ids = set()
    while len(ids) < count:
        new_id = generate_place_id()
        if new_id not in existing_ids:
            ids.add(new_id)
    
    return list(ids)

if __name__ == "__main__":
    # Example: Generate 10 new IDs
    print("Generated Place IDs:")
    for i, pid in enumerate(generate_unique_ids(10), 1):
        print(f"{i}. {pid}")
