@echo off
chcp 65001 >nul
title 🎾 網球場時段監控小助手 (Tennis-Monitor)

echo ===================================================
echo   🎾 網球場時段監控小助手 - 自動啟動程序
echo ===================================================
echo.

:: 1. 檢查 Python 環境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [❌ 錯誤] 系統未偵測到 Python，請先安裝 Python 3.10 以上版本！
    echo 下載網址: https://www.python.org/downloads/
    echo 注意：安裝時請務必勾選 "Add Python to PATH"！
    echo.
    pause
    exit /b 1
)

:: 2. 檢查 .env 設定檔
if not exist ".env" (
    echo [⚠️ 提示] 尚未找到 .env 設定檔，正在自動從 .env.example 建立...
    copy .env.example .env >nul
    echo.
    echo ===================================================
    echo   已為您建立 .env 檔案！
    echo   請先用記事本開啟專案目錄下的 .env 填入：
    echo   1. TELEGRAM_BOT_TOKEN (向 @BotFather 取得)
    echo   2. GOOGLE_API_KEY (向 Google AI Studio 取得)
    echo ===================================================
    echo.
    notepad .env
    echo 編輯完成並存檔後，請按任意鍵繼續啟動...
    pause >nul
)

:: 3. 檢查並建立虛擬環境
if not exist "venv\Scripts\activate.bat" (
    echo [📦 建立] 正在建立 Python 虛擬環境 (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [❌ 錯誤] 建立虛擬環境失敗。
        pause
        exit /b 1
    )
)

:: 4. 啟用虛擬環境並安裝依賴
call venv\Scripts\activate.bat

echo [🔄 檢查] 正在檢查並安裝所需套件...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [❌ 錯誤] 套件安裝失敗，請檢查網路連線。
    pause
    exit /b 1
)

:: 5. 啟動主程式
echo.
echo ===================================================
echo   🚀 正在啟動機器人...
echo   (如需停止運行，請直接按鍵盤 Ctrl + C 或關閉視窗)
echo ===================================================
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo [❌ 異常] 程式意外退出。
    pause
)
