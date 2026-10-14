#!/usr/bin/env bash
set -e

echo "==================================================="
echo "  🎾 網球場時段監控小助手 - 自動啟動程序"
echo "==================================================="

# 1. 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "[❌ 錯誤] 找不到 python3，請先安裝 Python 3.10+！"
    exit 1
fi

# 2. 檢查 .env
if [ ! -f ".env" ]; then
    echo "[⚠️ 提示] 正在從 .env.example 建立 .env ..."
    cp .env.example .env
    echo "請編輯 .env 填入你的 TELEGRAM_BOT_TOKEN 與 GOOGLE_API_KEY 後再重新執行此腳本。"
    exit 1
fi

# 3. 虛擬環境
if [ ! -d "venv" ]; then
    echo "[📦 建立] 正在建立 Python 虛擬環境..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "[🔄 檢查] 正在檢查相依套件..."
pip install -r requirements.txt --quiet

echo "==================================================="
echo "  🚀 正在啟動機器人 (按 Ctrl+C 可停止)..."
echo "==================================================="
python3 main.py
