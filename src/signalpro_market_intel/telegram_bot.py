"""
Telegram Bot — 觸發 SignalPro Market Intel 分析。

設定步驟：
  1. Telegram 搜尋 @BotFather，傳送 /newbot，依指示建立 bot
  2. 複製 BotFather 給你的 token
  3. 在 .env 加入 TELEGRAM_BOT_TOKEN=你的token
  4. 執行: run_telegram_bot

Bot 指令：
  /start       — 顯示說明
  /run          — 觸發 AI 全領域分析
  /run <主題>   — 觸發指定主題分析（如 /run AI Agents）
"""
import os
import threading

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes


DEFAULT_TOPIC = "AI 全領域（LLM、AI Agents、多模態、AI 安全、基礎設施）"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "SignalPro Market Intel Bot\n\n"
        "可用指令：\n"
        "/run — 觸發 AI 全領域市場情報分析\n"
        "/run <主題> — 指定主題分析（如 /run AI Agents）\n\n"
        "分析完成後報告會寄到你的 email。"
    )


async def run_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = " ".join(context.args) if context.args else DEFAULT_TOPIC
    await update.message.reply_text(
        f"AI 市場情報分析已觸發\n主題：{topic}\n\n"
        "分析需要幾分鐘，完成後報告將寄送至 email。"
    )

    thread = threading.Thread(target=_execute_crew, args=(topic,), daemon=True)
    thread.start()


def _execute_crew(topic: str):
    from signalpro_market_intel.main import run_with_topic
    try:
        run_with_topic(topic)
    except Exception as e:
        print(f"Crew execution failed: {e}")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN not set. "
            "Get one from @BotFather on Telegram, then add to .env"
        )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("run", run_analysis))

    print("Telegram bot started. Press Ctrl+C to stop.")
    app.run_polling()
