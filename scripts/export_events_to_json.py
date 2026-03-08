#!/usr/bin/env python3
"""
Script to export events from Google Sheets to JSON for the website
"""

import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime

def export_events_to_json():
    print("🚀 Exporting events from Google Sheets to JSON...")
    
    # Google Sheets setup
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    creds = Credentials.from_service_account_file('../pipeline/credentials.json', scopes=scope)
    client = gspread.authorize(creds)
    
    SHEET_ID = '1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk'
    sheet = client.open_by_key(SHEET_ID)
    worksheet = sheet.worksheet('20_events')
    
    # Get all data
    data = worksheet.get_all_records()
    
    # Process events
    events = []
    for row in data:
        event = {
            'event_id': row.get('event_id', ''),
            'name': row.get('name', ''),
            'description': row.get('description', ''),
            'start_date': row.get('start_date', ''),
            'end_date': row.get('end_date', ''),
            'location': row.get('location', ''),
            'organizer': row.get('organizer', ''),
            'source_url': row.get('source_url', ''),
            'image_url': row.get('image_url', ''),
            'age_range': row.get('age_range', ''),
            'is_free': row.get('is_free', False),
            'category': row.get('category', ''),
            'venue_slug': row.get('venue_slug', ''),
            'status': row.get('status', ''),
            'created_at': row.get('created_at', ''),
            'notes': row.get('notes', ''),
            'crawler_source': row.get('crawler_source', '')
        }
        events.append(event)
    
    # Save to JSON
    output_path = '../src/data/events.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Exported {len(events)} events to {output_path}")
    
    # Print summary
    today = datetime.now().strftime('%Y-%m-%d')
    active_events = [e for e in events if e.get('end_date', '') >= today]
    print(f"📊 Active events: {len(active_events)}")

if __name__ == '__main__':
    export_events_to_json()
