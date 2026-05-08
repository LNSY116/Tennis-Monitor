import os
import time
import json
import google.generativeai as genai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# 初始化 Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

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

    # 優先模型與備援模型清單（根據環境實際可用模型更新）
    model_priority = [
        'gemini-2.5-flash',
        'gemini-2.0-flash',
        'gemini-pro-latest'
    ]

    for model_name in model_priority:
        # 每個模型嘗試重試 2 次
        for attempt in range(2):
            try:
                # 確保模型名稱正確，有些環境需要 models/ 前綴
                full_model_name = model_name if model_name.startswith("models/") else f"models/{model_name}"
                model = genai.GenerativeModel(full_model_name)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(temperature=0.3)
                )
                return response.text
            except Exception as e:
                error_msg = str(e)
                # 如果是忙線 (503) 或 配額問題 (429)
                if "503" in error_msg or "429" in error_msg:
                    wait_time = (attempt + 1) * 3  # 遞增等待時間
                    print(f"⚠️ 模型 {model_name} 忙碌中，{wait_time}秒後重試... (嘗試 {attempt+1}/2)")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ 模型 {model_name} 發生非預期錯誤: {e}")
                    break  # 跳到下一個模型
        
    return "😰 抱歉，目前 AI 服務端壓力過大，所有模型均暫時無法回應，請幾分鐘後再試！🎾"

def analyze_user_intent(user_text, history=None):
    """
    分析使用者自然語言的意圖，包含對話歷史。
    """
    current_date = datetime.now().strftime("%Y-%m-%d")
    history_context = ""
    if history:
        history_context = "\n".join([f"使用者: {msg}" for msg in history])
        history_context = f"\n對話歷史：\n{history_context}\n"

    prompt = f"""
你是網球場監控小助手的意圖與時間分析器。今天是 {current_date} (星期{datetime.now().strftime("%A")})。{history_context}
請分析使用者的最新輸入，並將其模糊的時間需求轉換為具體的日期清單。

任務：
1. 判斷意圖 ("check", "monitor", "chat")。
2. 將任何時間描述轉換為具體的 "MM/DD" 日期清單。

日期處理指南（極其重要）：
- **模糊時間推理**：
    - 「5/20以後」：展開為從 05/20 開始的連續 7 天。
    - 「這禮拜/這週」：展開為從今天到本週日的日期清單。
    - 「下週/下禮拜」：展開為下週一到下週日的日期清單。
    - 「週末」：展開為最近的一個週六與週日。
    - 「這兩天」：展開為今天與明天。
    - 「下個月」：展開為下個月的前 7 天。
- **各種格式相容**：
    - 支援 520, 0520, 5/20, 5月20, 五月二十。
    - 支援範圍：0518-20 展開為 05/18, 05/19, 05/20。
- **參考歷史**：如果使用者說「那明天呢」或「改為後天」，請結合對話歷史判斷正確的日期。

輸出規則：
- 輸出必須是純 JSON。
- "dates" 必須是具體的 "MM/DD" 字串陣列，不可為空（除非是純閒聊）。
- 即使使用者只給一個模糊的開頭，你也要負責幫他展開成合理的日期範圍（通常為 3-7 天）。

最新使用者輸入："{user_text}"

JSON 輸出：
"""

    model_priority = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-pro-latest']

    for model_name in model_priority:
        try:
            full_model_name = model_name if model_name.startswith("models/") else f"models/{model_name}"
            model = genai.GenerativeModel(full_model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            # 移除可能的 Markdown 標籤
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            print(f"⚠️ 意圖分析模型 {model_name} 失敗: {e}")
            continue

    return {"intent": "chat", "dates": [], "reply": "抱歉，我現在有點困惑，您可以試著用指令 `/check` 或 `/monitor` 來告訴我您想做什麼嗎？"}

def format_ai_response(user_request, scraped_data):
    """
    根據使用者的原始要求，將爬蟲抓到的資料格式化為自然語言回覆。
    """
    if not scraped_data:
        return "😰 抱歉，我沒能抓取到任何場地資訊，請稍後再試。"

    prompt = f"""
你是網球場監控小助手。
使用者剛才的要求是："{user_request}"

這是目前的場地即時資料（JSON 格式）：
{json.dumps(scraped_data, ensure_ascii=False)}

任務：
1. 根據使用者的「具體要求」來回覆。例如：如果使用者說「只列出空位」，就不要列出已預訂的。
2. 保持親切且精簡。
3. 如果有空位，請清楚列出日期與時段。
4. 使用繁體中文，並適當使用 Emoji (✅, ❌, 🎾, 📍)。
5. 回覆格式請參考使用者提供的範例，但要靈活變通。

請直接輸出回覆內容：
"""

    model_priority = ['gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-pro-latest']

    for model_name in model_priority:
        try:
            full_model_name = model_name if model_name.startswith("models/") else f"models/{model_name}"
            model = genai.GenerativeModel(full_model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=0.3)
            )
            return response.text.strip()
        except Exception as e:
            print(f"⚠️ 資料格式化模型 {model_name} 失敗: {e}")
            continue

    return "抱歉，我現在無法處理回覆格式，請稍後再試。"