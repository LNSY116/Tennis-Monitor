@echo off
chcp 65001 >nul
title Tennis-Monitor Launcher

echo ===================================================
echo   Tennis-Monitor ^| 服務啟動程序
echo ===================================================
echo.

:: 1. 檢查 Python 執行環境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 未偵測到 Python 執行環境，請先安裝 Python 3.10 或以上版本。
    echo 下載位置: https://www.python.org/downloads/
    echo 注意事項：安裝時請務必勾選 "Add Python to PATH"。
    echo.
    pause
    exit /b 1
)

:: 2. 檢查設定檔
if not exist ".env" (
    echo [資訊] 首次執行：正在自 .env.example 建立 .env 設定檔...
    copy .env.example .env >nul
    echo.
    echo ===================================================
    echo   已建立 .env 設定檔，請填入必要參數：
    echo   - TELEGRAM_BOT_TOKEN
    echo   - GOOGLE_API_KEY
    echo ===================================================
    echo.
    notepad .env
    echo 設定完成並存檔後，請按任意鍵繼續啟動...
    pause >nul
)

:: 3. 檢查並建立虛擬環境
if not exist "venv\Scripts\activate.bat" (
    echo [資訊] 正在建立 Python 虛擬環境 (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [錯誤] 虛擬環境建立失敗。
        pause
        exit /b 1
    )
)

:: 4. 安裝或更新相依套件
call venv\Scripts\activate.bat
echo [資訊] 正在檢查相依套件...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [錯誤] 相依套件安裝失敗，請檢查網路連線。
    pause
    exit /b 1
)

:: 5. 啟動主程式
echo.
echo ===================================================
echo   服務啟動中 (按 Ctrl+C 可停止服務)
echo ===================================================
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo [警告] 程式異常終止。
    pause
)
