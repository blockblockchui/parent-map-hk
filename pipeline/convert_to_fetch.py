#!/usr/bin/env python3
"""
Convert index.html from hardcoded locations to fetch JSON
"""

import re
from pathlib import Path

index_path = Path("/root/.openclaw/workspace/parent-map-hk/index.html")

with open(index_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the locations array
# Pattern: from "const locations = [" to the closing "];"
pattern = r'(    <script>\n)(        // Location data\n        const locations = \[.*?\n  // 繼續添加至50個\.\.\.\n\];)'

replacement = r'''\1        // Location data - loaded from JSON
        let locations = [];
        let isLoading = true;

        // Fetch locations from JSON
        async function loadLocations() {
            try {
                console.log('Loading locations from JSON...');
                const response = await fetch('data/locations.json');
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                locations = data.locations || [];
                console.log(`Loaded ${locations.length} locations`);
                
                // Update UI
                isLoading = false;
                document.getElementById('resultCount').textContent = `已加載 ${locations.length} 個地點`;
                
                // Initialize map and render
                initMap();
                renderLocations();
                
            } catch (error) {
                console.error('Error loading locations:', error);
                document.getElementById('resultCount').textContent = '載入失敗，請刷新重試';
                document.getElementById('locationList').innerHTML = `
                    <div class="col-span-full text-center py-8 text-gray-500">
                        <p>❌ 無法載入地點資料</p>
                        <p class="text-sm mt-2">錯誤: ${error.message}</p>
                        <button onclick="location.reload()" class="mt-4 px-4 py-2 bg-blue-500 text-white rounded">重新載入</button>
                    </div>
                `;
            }
        }

        // Start loading
        loadLocations();'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content == content:
    print("⚠️  Pattern not found, trying alternative method...")
    # Try a simpler approach
    lines = content.split('\n')
    new_lines = []
    skip_until = -1
    
    for i, line in enumerate(lines):
        if skip_until > 0:
            if i <= skip_until:
                continue
            skip_until = -1
        
        if '// Location data' in line and 'const locations' in lines[i+1]:
            # Replace this section
            new_lines.append('        // Location data - loaded from JSON')
            new_lines.append('        let locations = [];')
            new_lines.append('        let isLoading = true;')
            new_lines.append('')
            new_lines.append('        // Fetch locations from JSON')
            new_lines.append('        async function loadLocations() {')
            new_lines.append('            try {')
            new_lines.append("                console.log('Loading locations from JSON...');")
            new_lines.append("                const response = await fetch('data/locations.json');")
            new_lines.append('                if (!response.ok) {')
            new_lines.append('                    throw new Error(`HTTP error! status: ${response.status}`);')
            new_lines.append('                }')
            new_lines.append('                const data = await response.json();')
            new_lines.append('                locations = data.locations || [];')
            new_lines.append('                console.log(`Loaded ${locations.length} locations`);')
            new_lines.append('                ')
            new_lines.append('                // Update UI')
            new_lines.append('                isLoading = false;')
            new_lines.append("                document.getElementById('resultCount').textContent = `已加載 ${locations.length} 個地點`;")
            new_lines.append('                ')
            new_lines.append('                // Initialize map and render')
            new_lines.append('                initMap();')
            new_lines.append('                renderLocations();')
            new_lines.append('                ')
            new_lines.append('            } catch (error) {')
            new_lines.append("                console.error('Error loading locations:', error);")
            new_lines.append("                document.getElementById('resultCount').textContent = '載入失敗，請刷新重試';")
            new_lines.append("                document.getElementById('locationList').innerHTML = `")
            new_lines.append('                    <div class="col-span-full text-center py-8 text-gray-500">')
            new_lines.append('                        <p>❌ 無法載入地點資料</p>')
            new_lines.append('                        <p class="text-sm mt-2">錯誤: ${error.message}</p>')
            new_lines.append('                        <button onclick="location.reload()" class="mt-4 px-4 py-2 bg-blue-500 text-white rounded">重新載入</button>')
            new_lines.append('                    </div>')
            new_lines.append('                `;')
            new_lines.append('            }')
            new_lines.append('        }')
            new_lines.append('')
            new_lines.append('        // Start loading')
            new_lines.append('        loadLocations();')
            
            # Find the end of the array
            for j in range(i+2, len(lines)):
                if lines[j].strip() == '];' or '// 繼續添加' in lines[j]:
                    skip_until = j
                    break
        else:
            new_lines.append(line)
    
    new_content = '\n'.join(new_lines)

# Write the new content
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✅ index.html updated to fetch JSON!")
print("Changes:")
print("  - Removed hardcoded locations array")
print("  - Added async loadLocations() function")
print("  - Fetches from data/locations.json")
print("  - Added error handling")
