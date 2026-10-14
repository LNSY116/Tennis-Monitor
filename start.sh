#!/usr/bin/env bash
set -e

echo "==================================================="
echo "  Tennis-Monitor | 服務啟動程序"
echo "==================================================="

# 1. 檢查 Python 執行環境
if ! command -v python3 &> /dev/null; then
    echo "[錯誤] 未偵測到 Python 3 執行環境，請先安裝 Python 3.10 或以上版本。"
    exit 1
fi

# 2. 檢查設定檔
if [ ! -f ".env" ]; then
    echo "[資訊] 首次執行：正在自 .env.example 建立 .env 設定檔..."
    cp .env.example .env
    echo "請編輯 .env 填入 TELEGRAM_BOT_TOKEN 與 GOOGLE_API_KEY 後重新執行此腳本。"
    exit 1
fi

# 3. 檢查並建立虛擬環境
if [ ! -d "venv" ]; then
    echo "[資訊] 正在建立 Python 虛擬環境 (venv)..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "[資訊] 正在檢查相依套件..."
pip install -r requirements.txt --quiet

echo "==================================================="
echo "  服務啟動中 (按 Ctrl+C 可停止服務)"
echo "==================================================="
python3 main.py
