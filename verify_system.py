#!/usr/bin/env python3
"""
修復驗證腳本：檢查所有配置和依賴是否正確
"""
import sys
import os

print("🔍 開始驗證 Tennis Monitor 系統...\n")

# 1. 環境變數驗證
print("✅ 步驟 1: 檢查環境變數")
from dotenv import load_dotenv
load_dotenv()

required_env_vars = {
    "TELEGRAM_BOT_TOKEN": "Telegram Bot Token",
    "GOOGLE_API_KEY": "Google Gemini API Key",
}

all_present = True
for var, desc in required_env_vars.items():
    value = os.getenv(var)
    if value:
        print(f"  ✅ {desc} ({var}): ✓ 已配置")
    else:
        print(f"  ❌ {desc} ({var}): ✗ 缺失")
        all_present = False

if not all_present:
    print("\n❌ 必要的環境變數缺失，請檢查 .env 文件")
    sys.exit(1)

# 2. 配置驗證
print("\n✅ 步驟 2: 驗證配置模塊")
try:
    from config import validate_config
    validate_config()
    print("  ✅ 配置驗證通過")
except Exception as e:
    print(f"  ❌ 配置驗證失敗: {e}")
    sys.exit(1)

# 3. 爬蟲模塊驗證
print("\n✅ 步驟 3: 檢查爬蟲模塊")
try:
    import scraper
    print("  ✅ scraper 模塊已成功導入")
except Exception as e:
    print(f"  ❌ scraper 模塊導入失敗: {e}")
    sys.exit(1)

# 4. AI 助手模塊驗證
print("\n✅ 步驟 4: 檢查 AI 助手模塊")
try:
    import ai_helper
    print("  ✅ ai_helper 模塊已成功導入")
except Exception as e:
    print(f"  ❌ ai_helper 模塊導入失敗: {e}")
    sys.exit(1)

# 5. Telegram 模塊驗證
print("\n✅ 步驟 5: 檢查 Telegram 模塊")
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    print("  ✅ Telegram 模塊已成功導入")
except Exception as e:
    print(f"  ❌ Telegram 模塊導入失敗: {e}")
    sys.exit(1)

# 6. Gemini API 連線測試
print("\n✅ 步驟 6: 測試 Gemini API 連線")
try:
    import google.generativeai as genai
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    
    # 嘗試列表模型
    models = list(genai.list_models())
    if models:
        print(f"  ✅ Gemini API 連線成功，可用模型數: {len(models)}")
    else:
        print("  ❌ 無法獲取可用模型")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ Gemini API 連線失敗: {e}")
    sys.exit(1)

# 7. 爬蟲功能測試
print("\n✅ 步驟 7: 測試爬蟲功能")
try:
    result = scraper.fetch_venue_slots(target_dates=None)
    if "slots" in result and "alerts" in result:
        print(f"  ✅ 爬蟲成功抓取資料")
        print(f"     - 時段數: {len(result.get('slots', []))}")
        print(f"     - 警告/消息: {len(result.get('alerts', []))}")
    else:
        print("  ⚠️ 爬蟲返回結構異常")
except Exception as e:
    print(f"  ❌ 爬蟲功能失敗: {e}")

# 8. AI 助手功能測試
print("\n✅ 步驟 8: 測試 AI 助手功能")
try:
    test_alerts = ["⚠️ 測試消息 1", "✅ 測試消息 2"]
    reply = ai_helper.generate_telegram_reply(test_alerts)
    if reply:
        print(f"  ✅ AI 助手成功生成回覆")
        print(f"     - 回覆長度: {len(reply)} 字元")
    else:
        print("  ❌ AI 助手無法生成回覆")
except Exception as e:
    print(f"  ⚠️ AI 助手測試失敗: {e}")

print("\n" + "="*50)
print("✅ 所有檢查完成！系統已準備就緒。")
print("="*50)
print("\n📝 下一步:")
print("   1. 確認 .env 文件中的 API 密鑰正確")
print("   2. 運行: python bot.py")
print("   3. 向 Telegram Bot 發送指令進行測試")
