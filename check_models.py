import os
from google import genai
from dotenv import load_dotenv

# 1. 載入 .env
load_dotenv()

# 2. 初始化 Client
client = genai.Client()

print("🔍 正在查詢你的 API Key 可使用的模型清單...")

try:
    # 這裡直接列出名稱，避免屬性名稱版本衝突
    models = client.models.list()
    for model in models:
        print(f"✅ 可用模型名稱: {model.name}")
except Exception as e:
    print(f"❌ 查詢失敗，錯誤訊息：{e}")