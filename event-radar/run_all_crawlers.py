#!/usr/bin/env python3
"""
Master crawler runner - 執行所有 event source 爬蟲
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 尋入所有爬蟲
from crawlers.hkpm_events import HKPMCrawler
from crawlers.mplus_kids import MPlusKidsCrawler
from crawlers.hkpl_thisweek import HKPLThisWeekCrawler

# 如果 BaseCrawler 不在路徑中，添加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crawler import run_crawlers as base_run_crawlers

def run_all_crawlers():
    """執行所有專用爬蟲"""
    all_events = []
    
    crawlers = [
        ('香港故宮文化博物館', HKPMCrawler()),
        ('M+博物館', MPlusKidsCrawler()),
        ('HKPL本週活動', HKPLThisWeekCrawler()),
    ]
    
    for name, crawler in crawlers:
        try:
            print(f"\\n🔍 [{name}] 開始爬取...")
            events = crawler.crawl()
            all_events.extend(events)
            print(f"   ✅ {name}: {len(events)} 個活動")
        except Exception as e:
            print(f"   ❌ {name} 錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\\n📊 總計: {len(all_events)} 個活動")
    return all_events

if __name__ == '__main__':
    events = run_all_crawlers()
    
    # 顯示結果
    print("\\n" + "="*60)
    print("爬取結果預覽 (前 10 個):")
    print("="*60)
    for i, e in enumerate(events[:10], 1):
        print(f"{i}. {e.name}")
        print(f"   日期: {e.start_date} - {e.end_date}")
        print(f"   地點: {e.location}")
        print(f"   主辦: {e.organizer}")
        print(f"   免費: {'是' if e.is_free else '否'}")
        print()
