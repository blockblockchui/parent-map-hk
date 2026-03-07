#!/bin/bash
# Playwright Event Crawler Setup Script

set -e

echo "=============================================="
echo "🎯 Playwright Event Crawler 安裝腳本"
echo "=============================================="
echo ""

# 檢查 Python
echo "📋 檢查環境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到 Python3，請先安裝 Python 3.9+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python 版本: $PYTHON_VERSION"

# 創建虛擬環境（可選）
echo ""
echo "📦 安裝依賴..."

if [ -d "venv" ]; then
    echo "虛擬環境已存在，跳過創建"
else
    echo "創建虛擬環境..."
    python3 -m venv venv
fi

# 啟動虛擬環境
echo "啟動虛擬環境..."
source venv/bin/activate

# 升級 pip
echo "升級 pip..."
pip install --upgrade pip

# 安裝 Python 依賴
echo "安裝 Python 套件..."
pip install -r requirements-playwright.txt

# 安裝 Playwright 瀏覽器
echo ""
echo "🌐 安裝 Playwright 瀏覽器..."
playwright install chromium

echo ""
echo "=============================================="
echo "✅ 安裝完成!"
echo "=============================================="
echo ""
echo "使用方法:"
echo "  1. 啟動虛擬環境: source venv/bin/activate"
echo "  2. 執行爬蟲: python run_playwright.py"
echo ""
echo "測試單個爬蟲:"
echo "  python crawlers/crawler_hkpl.py"
echo ""
echo "📖 詳細文檔: README_PLAYWRIGHT.md"
echo ""
