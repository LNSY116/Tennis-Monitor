import os
import time
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client()

def generate_telegram_reply(alerts):
    """產生回覆，具備自動重試與模型備援機制"""
    alerts = [alert.strip() for alert in (alerts or []) if alert and alert.strip()]

    if not alerts:
        return "✅ 目前沒有需要通知的異常或更新。"

    alert_text = "\n".join(f"- {alert}" for alert in alerts)

    prompt = f"""
你是網球場監控小助手，只能根據提供的 alerts 回覆，不可自行推測場地時段、日期、預訂者或其他未提供的資訊。

任務：把 alerts 整理成適合 Telegram 的繁體中文回覆。

輸入 alerts：
{alert_text}

輸出規則：
1. 先給 1 行簡短標題。
2. 再用 2-4 點條列整理目前狀況。
3. 若 alerts 顯示沒有資料、抓取失敗或網頁異常，請清楚說明原因與建議。
4. 語氣親切、精簡，總長度盡量控制在 4096 字元內。
5. 不要輸出你沒有根據的額外資訊。
"""

    # 優先模型與備援模型清單 (來自你剛才的 check_models 结果)
    model_priority = [
        'gemini-2.5-flash', 
        'gemini-2.0-flash-lite', 
        'gemini-flash-latest'
    ]

    for model_name in model_priority:
        # 每個模型嘗試重試 2 次
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.3)
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                # 如果是忙線 (503) 或 配額問題
                if "503" in error_msg or "429" in error_msg:
                    wait_time = (attempt + 1) * 3 # 遞增等待時間
                    print(f"⚠️ 模型 {model_name} 忙碌中，{wait_time}秒後重試... (嘗試 {attempt+1}/2)")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ 模型 {model_name} 發生非預期錯誤: {e}")
                    break # 跳到下一個模型
        
    return "😰 抱歉，目前 AI 服務端壓力過大，所有模型均暫時無法回應，請幾分鐘後再試！🎾"