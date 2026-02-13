#!/usr/bin/env python3
"""
Parent Map HK - Google Alerts Ingestion via Gmail API
Reads Google Alerts emails and extracts new place information
"""

import os
import re
import base64
import json
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Gmail API
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

# Load env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
WORKSPACE = Path("/root/.openclaw/workspace/parent-map-hk")

# Alert keywords to monitor (for reference)
ALERT_KEYWORDS = [
    "香港 親子活動 室內",
    "playhouse 香港 新開",
    "兒童遊樂場 開幕",
    "親子好去處 推介",
    "indoor playground Hong Kong",
    "博物館 香港 親子"
]

def get_gmail_service():
    """Authenticate and return Gmail API service"""
    creds = None
    token_path = WORKSPACE / "pipeline" / "gmail_token.pickle"
    
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Need credentials.json from Google Cloud Console
            creds_path = WORKSPACE / "pipeline" / "gmail_credentials.json"
            if not creds_path.exists():
                print("❌ gmail_credentials.json not found")
                print("   Please create one at https://console.cloud.google.com/")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def extract_links_from_html(html_content):
    """Extract article links from Google Alert email HTML"""
    links = []
    
    # Google Alerts format: <a href="URL">Title</a>
    # Pattern for alert links
    patterns = [
        r'<a[^>]+href="(https://www\.google\.com/url\?[^"]+)"[^>]*>(.*?)</a>',
        r'<a[^>]+href="(https?://[^"]+)"[^>]*>([^<]+(?:playhouse|遊樂場|博物館|親子|兒童)[^<]*)</a>',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        for url, title in matches:
            # Clean Google redirect URLs
            if 'google.com/url' in url:
                # Extract real URL from ?url= parameter
                url_match = re.search(r'[?&]url=([^&]+)', url)
                if url_match:
                    from urllib.parse import unquote
                    url = unquote(url_match.group(1))
            
            # Clean title
            title = re.sub(r'<[^>]+>', '', title).strip()
            
            if title and len(title) > 5:
                links.append({
                    'url': url,
                    'title': title,
                    'source': 'google_alerts'
                })
    
    return links

def fetch_alert_emails(service, max_results=10):
    """Fetch recent Google Alert emails"""
    # Search for Google Alerts emails from last 24 hours
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y/%m/%d')
    query = f'from:googlealerts-noreply@google.com after:{yesterday}'
    
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        print(f"📧 Found {len(messages)} alert emails")
        return messages
    except Exception as e:
        print(f"❌ Error fetching emails: {e}")
        return []

def parse_email(service, msg_id):
    """Parse a Gmail message and extract content"""
    try:
        message = service.users().messages().get(
            userId='me',
            id=msg_id,
            format='full'
        ).execute()
        
        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        # Extract body
        parts = message['payload'].get('parts', [message['payload']])
        html_content = ''
        
        for part in parts:
            if part.get('mimeType') == 'text/html':
                data = part['body'].get('data', '')
                if data:
                    html_content = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
        
        return {
            'subject': subject,
            'date': date,
            'html': html_content
        }
    except Exception as e:
        print(f"❌ Error parsing email {msg_id}: {e}")
        return None

def filter_place_links(links):
    """Filter links that are likely about places/venues"""
    venue_keywords = [
        'playhouse', 'playroom', '遊樂場', '室內', '親子', 
        'museum', '博物館', '科學館', '公園', 'park',
        'kiztopia', 'nobi nobi', 'epicland', 'legoland'
    ]
    
    filtered = []
    for link in links:
        title_lower = link['title'].lower()
        if any(kw in title_lower for kw in venue_keywords):
            filtered.append(link)
    
    return filtered

def main():
    """Main entry point"""
    print("=" * 60)
    print("📧 Google Alerts Ingestion")
    print("=" * 60)
    
    # Get Gmail service
    service = get_gmail_service()
    if not service:
        print("❌ Failed to authenticate Gmail")
        return
    
    print("✅ Gmail authenticated")
    
    # Fetch alert emails
    messages = fetch_alert_emails(service)
    if not messages:
        print("📭 No new alerts")
        return
    
    # Process each email
    all_links = []
    for msg in messages:
        email_data = parse_email(service, msg['id'])
        if email_data:
            print(f"\n📰 {email_data['subject'][:60]}")
            links = extract_links_from_html(email_data['html'])
            print(f"   Found {len(links)} links")
            all_links.extend(links)
    
    # Filter for place-related content
    place_links = filter_place_links(all_links)
    print(f"\n📍 Place-related links: {len(place_links)}")
    
    # Display results
    for link in place_links[:10]:
        print(f"  • {link['title'][:50]}")
        print(f"    {link['url'][:70]}")
    
    # Save for manual review
    if place_links:
        output_file = WORKSPACE / f"alerts_discovered_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(place_links, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Saved to: {output_file}")
    
    print("\n✅ Done")

if __name__ == "__main__":
    main()
