#!/usr/bin/env python3
"""
Parent Map HK - Auto Deploy
自動將驗證後嘅地點加入網站並部署
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace/parent-map-hk")
DATA_FILE = WORKSPACE / "data" / "locations.ts"
HTML_FILE = WORKSPACE / "index.html"

def log(message):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def load_ready_file():
    """讀取準備好嘅地點代碼"""
    today = datetime.now().strftime("%Y%m%d")
    ready_file = WORKSPACE / f"ready_to_add_{today}.txt"
    
    if not ready_file.exists():
        log(f"⚠️ 無準備好嘅檔案: {ready_file}")
        return None
    
    with open(ready_file, "r", encoding="utf-8") as f:
        return f.read()

def update_locations_ts(new_code):
    """更新 locations.ts"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 喺 // 繼續添加 之前插入新地點
        insert_marker = "// 繼續添加至50個..."
        if insert_marker in content:
            content = content.replace(insert_marker, new_code + "\n" + insert_marker)
        else:
            # 喺最後一個 }; 之前插入
            content = content.rstrip()
            if content.endswith("];"):
                content = content[:-2] + new_code + "];"
        
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        
        log("✅ 已更新 data/locations.ts")
        return True
    except Exception as e:
        log(f"❌ 更新 locations.ts 失敗: {e}")
        return False

def update_index_html():
    """更新 index.html 內嵌資料"""
    try:
        # 讀取 locations.ts 提取資料
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            ts_content = f.read()
        
        # 簡單提取 locations 陣列
        match = re.search(r'export const locations = (\[.*?\]);', ts_content, re.DOTALL)
        if not match:
            log("❌ 無法提取 locations 資料")
            return False
        
        locations_data = match.group(1)
        
        # 讀取 index.html
        with open(HTML_FILE, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        # 替換內嵌嘅 locations 資料
        pattern = r'(const locations = )\[.*?\](;)'
        new_html = re.sub(pattern, r'\1' + locations_data + r'\2', html_content, flags=re.DOTALL)
        
        with open(HTML_FILE, "w", encoding="utf-8") as f:
            f.write(new_html)
        
        log("✅ 已更新 index.html")
        return True
    except Exception as e:
        log(f"❌ 更新 index.html 失敗: {e}")
        return False

def git_commit_and_push():
    """Git 提交並推送"""
    try:
        os.chdir(WORKSPACE)
        
        # Add files
        subprocess.run(["git", "add", "data/locations.ts", "index.html"], check=True)
        
        # Commit
        today = datetime.now().strftime("%Y%m%d")
        subprocess.run(
            ["git", "commit", "-m", f"Auto: Add discovered locations {today}"],
            check=True
        )
        
        # Push
        subprocess.run(["git", "push", "origin", "main"], check=True)
        
        log("✅ Git push 完成")
        return True
    except subprocess.CalledProcessError as e:
        log(f"❌ Git 操作失敗: {e}")
        return False

def main():
    log("="*60)
    log("🚀 Parent Map Auto Deploy - 開始")
    log("="*60)
    
    # 檢查有無準備好嘅地點
    ready_code = load_ready_file()
    if not ready_code:
        log("📭 今日無新地點需要加入")
        return
    
    # 更新檔案
    if not update_locations_ts(ready_code):
        return
    
    if not update_index_html():
        return
    
    # Git 操作
    if not git_commit_and_push():
        return
    
    # 生成報告
    report = f"""
🎉 自動部署完成！

📅 時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}
✅ 狀態: 新地點已加入並部署

🌐 網站將喺 1-2 分鐘內自動更新:
https://blockblockchui.github.io/parent-map-hk/

⚠️ 注意: 新地點標記為「未驗證」，
    建議人手檢查後再移除標記。
"""
    log(report)
    print(report)
    
    log("="*60)
    log("✅ Auto Deploy 完成")
    log("="*60)

if __name__ == "__main__":
    main()
