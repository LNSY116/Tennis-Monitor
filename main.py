"""
Tennis Court Monitor - 專案唯一主程式入口
執行方式：python main.py
"""
import sys
from pathlib import Path

# 將 src 目錄加入 Python 模組搜尋路徑
ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Windows 終端 UTF-8 編碼支援
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from bot import run_bot

if __name__ == "__main__":
    run_bot()
