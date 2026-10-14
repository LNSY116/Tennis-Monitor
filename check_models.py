import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 1. 載入 .env
load_dotenv()

# 2. 初始化 API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ 找不到 GOOGLE_API_KEY，請確認 .env 檔案")
    exit(1)

genai.configure(api_key=api_key)

print("🔍 正在查詢你的 API Key 可使用的模型清單...")

try:
    models = genai.list_models()
    count = 0
    for model in models:
        if "generateContent" in model.supported_generation_methods:
            print(f"✅ 可用模型: {model.name}")
            count += 1
    print(f"\n✨ 共找到 {count} 個可用模型")
except Exception as e:
    print(f"❌ 查詢失敗，錯誤訊息：{e}")
