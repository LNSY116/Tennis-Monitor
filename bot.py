from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import scraper, ai_helper
from dotenv import load_dotenv
import os
import re

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


def parse_query_dates(user_query: str) -> list:
    """從指令提取日期，支援單日/區間/中英混寫，統一轉為 MM/DD"""
    if not user_query:
        return []

    raw_dates = re.findall(r'(\d{1,2})[月/-](\d{1,2})', user_query)
    if not raw_dates:
        return []

    dates = []
    for month, day in raw_dates:
        dates.append(f"{int(month):02d}/{int(day):02d}")
    return sorted(set(dates))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎾 歡迎使用網球場監控小助手！\n"
        "可用指令：\n"
        "/check 5/15-5/20 → 查詢時段\n"
        "/help → 查看說明"
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_query = ' '.join(context.args) if context.args else ""
    parsed_dates = parse_query_dates(raw_query)
    
    # 顯示「正在輸入...」讓使用者知道 Bot 有反應
    await update.message.chat.send_action(action="typing")
    
    # 1. 抓取資料
    result = scraper.fetch_venue_slots(target_dates=parsed_dates or None)
    alerts = result.get("alerts", [])
    
    # 2. AI 整理
    reply = ai_helper.generate_telegram_reply(alerts)
    
    # 3. 回傳
    await update.message.reply_text(reply, parse_mode='Markdown')

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ 找不到 TELEGRAM_BOT_TOKEN，請檢查 .env 檔案")
        exit()
        
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("check", check_command))
    print("✅ Bot 已啟動，正在等待指令...")
    app.run_polling()