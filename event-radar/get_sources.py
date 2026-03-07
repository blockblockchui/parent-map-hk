#!/usr/bin/env python3
"""
Event Sources - 21_event_sources 數據讀取器
讀取 Google Sheets 中的 source list
"""

import gspread
from google.oauth2.service_account import Credentials
from urllib.parse import urlparse

SHEET_ID = '1xUL8jiJckSTe3ScThsh-USNWb2DqpGnkroGdarafJgk'

def get_event_sources():
    """從 Google Sheets 獲取所有 event sources"""
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file('../pipeline/credentials.json', scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SHEET_ID)
    
    try:
        worksheet = sheet.worksheet('21_event_sources')
    except gspread.WorksheetNotFound:
        print("❌ 找不到 21_event_sources worksheet")
        return []
    
    # 獲取所有行（第一行可能是 header 或 URL）
    all_values = worksheet.get_all_values()
    
    sources = []
    for i, row in enumerate(all_values):
        if not row:
            continue
        
        # 假設 URL 在第一欄
        url = row[0].strip() if row[0] else ''
        
        # 跳過 header 或無效 URL
        if not url or not url.startswith('http'):
            continue
        
        # 提取域名作為名稱
        domain = urlparse(url).netloc
        name = domain.replace('www.', '').split('.')[0]
        
        sources.append({
            'id': i,
            'name': name,
            'url': url,
            'domain': domain
        })
    
    return sources

if __name__ == '__main__':
    sources = get_event_sources()
    
    print(f"找到 {len(sources)} 個 event sources:\n")
    
    for i, s in enumerate(sources, 1):
        print(f"{i}. {s['name']}")
        print(f"   URL: {s['url'][:80]}..." if len(s['url']) > 80 else f"   URL: {s['url']}")
        print()
