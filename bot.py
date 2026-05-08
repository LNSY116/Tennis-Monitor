from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import scraper, ai_helper
from config import validate_config, MONITOR_INTERVAL
from dotenv import load_dotenv
import os
import re
from collections import defaultdict
import logging
import asyncio
import json

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# 存儲監控訂閱：{chat_id: set(dates)}
subscriptions = defaultdict(set)
# 存儲上次檢查到的可用時段，用於比對變化：{(date, time): status}
last_available_slots = {}
# 存儲對話紀錄：{chat_id: list of messages}
chat_history = defaultdict(list)
MAX_HISTORY = 5  # 每個使用者保留最近 5 則對話

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_query_dates(user_query: str) -> list:
    """從指令提取日期，支援單日/區間/緊湊格式 (MMDD)/中文日期，統一轉為 MM/DD"""
    if not user_query:
        return []

    dates = set()
    
    # 0. 基礎中文數字轉換（簡單處理常見的）
    cn_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    
    def cn_to_int(s):
        if not s: return 0
        if s == '十': return 10
        if len(s) == 1: return cn_nums.get(s, 0)
        if len(s) == 2:
            if s[0] == '十': return 10 + cn_nums.get(s[1], 0)
            if s[1] == '十': return cn_nums.get(s[0], 0) * 10
        if len(s) == 3:
            return cn_nums.get(s[0], 0) * 10 + cn_nums.get(s[2], 0)
        return 0

    # 1. 處理 MM/DD 或 MM-DD 或 MM月DD
    pattern1 = re.findall(r'(\d{1,2})[月/-](\d{1,2})', user_query)
    for m, d in pattern1:
        dates.add(f"{int(m):02d}/{int(d):02d}")

    # 2. 處理 MMDD 或 MDD 緊湊格式 (例如 0520, 520)
    # 支援 4 位 (MMDD) 或 3 位 (MDD)
    # 4 位：0520 -> 05/20
    pattern4 = re.findall(r'(?<!\d)(\d{2})(\d{2})(?!\d)', user_query)
    for m, d in pattern4:
        month, day = int(m), int(d)
        if 1 <= month <= 12 and 1 <= day <= 31:
            dates.add(f"{month:02d}/{day:02d}")
            
    # 3 位：520 -> 05/20
    pattern3_digit = re.findall(r'(?<!\d)(\d{1})(\d{2})(?!\d)', user_query)
    for m, d in pattern3_digit:
        month, day = int(m), int(d)
        if 1 <= month <= 9 and 1 <= day <= 31:
            dates.add(f"{month:02d}/{day:02d}")

    # 3. 處理中文日期（例如 五月十八）
    pattern3 = re.findall(r'([一二三四五六七八九十]{1,3})月([一二三四五六七八九十]{1,3})', user_query)
    for m_str, d_str in pattern3:
        m, d = cn_to_int(m_str), cn_to_int(d_str)
        if 1 <= m <= 12 and 1 <= d <= 31:
            dates.add(f"{m:02d}/{d:02d}")

    # 4. 處理範圍格式 (例如 5/18-19, 5/18-5/20, 0518-20, 0518-0520)
    # 4.1 標準範圍 (帶分隔符)
    range_match = re.search(r'(\d{1,2})[月/-](\d{1,2})\s*-\s*(?:(\d{1,2})[月/-])?(\d{1,2})', user_query)
    # 4.2 緊湊範圍 (MMDD-DD 或 MMDD-MMDD)
    compact_range_match = re.search(r'(?<!\d)(\d{2})(\d{2})\s*-\s*(?:(\d{2}))?(\d{2})(?!\d)', user_query)
    
    if range_match or compact_range_match:
        if compact_range_match:
            m1, d1, m2, d2 = compact_range_match.groups()
        else:
            m1, d1, m2, d2 = range_match.groups()
            
        start_m, start_d = int(m1), int(d1)
        end_m = int(m2) if m2 else start_m
        end_d = int(d2)
        
        if end_m == start_m and end_d > start_d:
            for day in range(start_d, end_d + 1):
                dates.add(f"{start_m:02d}/{day:02d}")
        elif end_m > start_m:
            for day in range(start_d, 32): 
                dates.add(f"{start_m:02d}/{day:02d}")
            for day in range(1, end_d + 1):
                dates.add(f"{end_m:02d}/{day:02d}")

    return sorted(list(dates))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎾 *網球場監控小助手*\n\n"
        "我會幫您即時監控台北市網球場的租借情形。您可以直接用「自然語言」跟我對話，或是使用下方的指令：\n\n"
        "💬 *您可以這樣說：*\n"
        "「幫我查明天有沒有空位」\n"
        "「下週三如果有位子請通知我」\n"
        "「你好呀」\n\n"
        "🛠️ *可用指令：*\n"
        "🔍 `/check 5/15` - 查詢特定日期\n"
        "🔔 `/monitor 5/20` - 訂閱監控通知\n"
        "📋 `/list` - 查看監控清單\n"
        "🚫 `/stop` - 取消所有監控\n"
        "❓ `/help` - 顯示此幫助訊息\n\n"
        "_提示：監控任務每 2 分鐘會自動檢查一次。_",
        parse_mode="Markdown"
    )

async def monitor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    raw_query = ' '.join(context.args) if context.args else ""
    parsed_dates = parse_query_dates(raw_query)
    
    if not parsed_dates:
        await update.message.reply_text("請提供日期，例如：`/monitor 5/15` 或 `/monitor 5/15-5/20`", parse_mode="Markdown")
        return

    for d in parsed_dates:
        subscriptions[chat_id].add(d)
    
    await update.message.reply_text(f"✅ 已為您開啟監控日期：{', '.join(parsed_dates)}\n當這些日期出現空位時，我會立刻通知您！")
    logger.info("Chat %s subscribed to %s", chat_id, parsed_dates)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in subscriptions:
        del subscriptions[chat_id]
        await update.message.reply_text("🚫 已取消您的所有監控訂閱。")
    else:
        await update.message.reply_text("您目前沒有任何監控訂閱。")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    dates = sorted(list(subscriptions.get(chat_id, [])))
    if dates:
        await update.message.reply_text(f"📋 目前監控中的日期：\n{', '.join(dates)}")
    else:
        await update.message.reply_text("您目前沒有任何監控訂閱。")

async def monitor_job(context: ContextTypes.DEFAULT_TYPE):
    """背景監控任務：抓取所有被訂閱的日期，並通知相關使用者。"""
    if not subscriptions:
        return

    # 收集所有需要抓取的日期
    all_target_dates = set()
    for dates in subscriptions.values():
        all_target_dates.update(dates)
    
    if not all_target_dates:
        return

    logger.info("Running monitor_job for dates: %s", all_target_dates)
    
    try:
        # 抓取資料
        result = await asyncio.to_thread(scraper.fetch_venue_slots, target_dates=list(all_target_dates))
        slots = result.get("slots", [])
        
        # 整理目前的可用時段
        current_available = {}
        for slot in slots:
            if slot.get("status") == "available":
                key = (slot["date"], slot["time"])
                current_available[key] = True

        # 比對是否有「新出現」的空位
        new_slots_by_date = defaultdict(list)
        for key in current_available:
            if key not in last_available_slots:
                date, time_text = key
                new_slots_by_date[date].append(time_text)
        
        # 更新全域狀態
        last_available_slots.clear()
        last_available_slots.update(current_available)

        if not new_slots_by_date:
            return

        # 通知訂閱者
        for chat_id, subscribed_dates in subscriptions.items():
            relevant_new_slots = []
            for d in subscribed_dates:
                if d in new_slots_by_date:
                    for t in new_slots_by_date[d]:
                        relevant_new_slots.append(f"📍 {d} {t}")
            
            if relevant_new_slots:
                msg = "🔔 *偵測到新空位！*\n\n" + "\n".join(relevant_new_slots) + "\n\n快去預訂吧！"
                await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")
                logger.info("Sent notification to %s for %s", chat_id, relevant_new_slots)

    except Exception:
        logger.exception("monitor_job failed")

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_query = ' '.join(context.args) if context.args else ""
    parsed_dates = parse_query_dates(raw_query)
    await perform_check(update, context, parsed_dates)

async def perform_check(update: Update, context: ContextTypes.DEFAULT_TYPE, parsed_dates: list, user_request: str = None):
    """執行實際的查詢動作"""
    logger.info("Performing check for dates: %s", parsed_dates)
    
    try:
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id is not None:
            await context.bot.send_message(chat_id=chat_id, text="🔍 收到，查詢中，請稍候...")
            await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        result = await asyncio.to_thread(scraper.fetch_venue_slots, target_dates=parsed_dates or None)
        slots = result.get("slots", [])
        alerts = result.get("alerts", [])

        # 如果有使用者原始要求，交給 AI 進行自然語言格式化
        if user_request:
            reply = await asyncio.to_thread(ai_helper.format_ai_response, user_request, slots)
            # 檢查 AI 是否回覆失敗 (包含錯誤訊息字眼)
            error_keywords = ["抱歉", "無法處理", "困惑", "失敗", "error"]
            if any(kw in reply for kw in error_keywords) and len(reply) < 100:
                logger.warning("AI format failed, falling back to template")
                reply = format_slot_reply(slots, parsed_dates)
        else:
            # 否則使用預設的格式化 (例如指令查詢時)
            if slots:
                reply = format_slot_reply(slots, parsed_dates)
            else:
                reply = ai_helper.generate_telegram_reply(alerts)

        if chat_id is not None:
            await context.bot.send_message(chat_id=chat_id, text=reply, parse_mode="Markdown")
    except Exception:
        logger.exception("perform_check failed")
        if update.effective_chat:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="⚠️ 查詢時發生錯誤，請稍後再試一次。")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理自然語言訊息"""
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    logger.info("Received message from chat_id=%s text=%s", chat_id, user_text)
    
    # --- 增加：本地正則表達式快速檢測 (作為兜底) ---
    parsed_dates_fallback = parse_query_dates(user_text)
    
    # 使用 AI 分析意圖
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")
    analysis = await asyncio.to_thread(ai_helper.analyze_user_intent, user_text, history=chat_history[chat_id])
    intent = analysis.get("intent", "chat")
    dates = analysis.get("dates", [])
    
    # 更新對話紀錄
    chat_history[chat_id].append(user_text)
    if len(chat_history[chat_id]) > MAX_HISTORY:
        chat_history[chat_id].pop(0)

    # 如果 AI 沒抓到日期，但本地正則抓到了，則補上日期
    if not dates and parsed_dates_fallback:
        dates = parsed_dates_fallback
        if intent == "chat": # 如果原本是閒聊但有日期，改為查詢
            intent = "check"

    if intent == "check":
        if not dates:
            await update.message.reply_text("想查詢哪一天的場地呢？請告訴我日期（例如：明天、5/20）。")
        else:
            # 傳入 user_text，讓 AI 能根據要求回覆
            await perform_check(update, context, dates, user_request=user_text)
            
    elif intent == "monitor":
        if not dates:
            await update.message.reply_text("想監控哪一天的場地呢？請告訴我日期（例如：下週六、5/25）。")
        else:
            for d in dates:
                subscriptions[chat_id].add(d)
            await update.message.reply_text(f"✅ 沒問題！我已經為您開啟監控日期：{', '.join(dates)}\n一有空位會立刻通知您！")
            
    else:  # chat
        reply = analysis.get("reply", "您好！我是網球場監控助手，有什麼我可以幫您的嗎？")
        await update.message.reply_text(reply)

def format_slot_reply(slots: list, requested_dates: list) -> str:
    """把時段資料整理成 Telegram 可讀的回覆。"""
    grouped = defaultdict(list)
    for slot in slots:
        grouped[slot.get("date", "未知日期")].append(slot)

    if requested_dates:
        date_order = requested_dates
    else:
        date_order = sorted(grouped.keys())

    lines = ["🎾 網球場時段查詢結果"]

    for date_key in date_order:
        day_slots = grouped.get(date_key, [])
        if not day_slots:
            continue

        day_slots = sorted(day_slots, key=lambda item: item.get("time", ""))
        available_slots = [slot for slot in day_slots if slot.get("status") == "available"]
        booked_slots = [slot for slot in day_slots if slot.get("status") == "booked"]

        lines.append(f"\n*{date_key}*")
        lines.append(f"可用：{len(available_slots)}　已預訂：{len(booked_slots)}")

        for slot in day_slots:
            time_text = slot.get("time", "N/A")
            status = slot.get("status")
            if status == "available":
                lines.append(f"- {time_text}：空位✅")
            elif status == "booked":
                booker = slot.get("booker", "")
                if booker:
                    lines.append(f"- {time_text}：已預訂（{booker}）❌")
                else:
                    lines.append(f"- {time_text}：已預訂❌")
            else:
                lines.append(f"- {time_text}：{status or '未知'}")

    return "\n".join(lines)

if __name__ == "__main__":
    # 驗證所有必要配置
    try:
        validate_config()
        print("✅ 配置驗證通過")
    except ValueError as e:
        print(f"❌ 配置錯誤: {e}")
        exit(1)
    
    if not BOT_TOKEN:
        print("❌ 找不到 TELEGRAM_BOT_TOKEN，請檢查 .env 檔案")
        exit(1)
        
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_command))
    app.add_handler(CommandHandler("monitor", monitor_command))
    app.add_handler(CommandHandler("stop", stop_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("help", start))
    
    # 加入自然語言處理
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 設定背景任務，每 2 分鐘執行一次
    job_queue = app.job_queue
    job_queue.run_repeating(monitor_job, interval=MONITOR_INTERVAL, first=10)
    
    async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
        logger.exception("Unhandled bot error", exc_info=context.error)
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text("⚠️ 查詢時發生錯誤，請稍後再試一次。")

    app.add_error_handler(handle_error)
    print("✅ Bot 已啟動，正在等待指令...")
    app.run_polling()