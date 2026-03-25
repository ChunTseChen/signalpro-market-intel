"""
Discord Bot — 觸發 SignalPro Market Intel 分析。

設定步驟：
  1. 前往 https://discord.com/developers/applications → New Application
  2. 左側選 Bot → Reset Token → 複製 token
  3. 開啟 MESSAGE CONTENT INTENT
  4. 左側選 OAuth2 → URL Generator → 勾選 bot + Send Messages
  5. 用產生的 URL 邀請 bot 到你的 server
  6. 在 .env 加入 DISCORD_BOT_TOKEN=你的token
  7. 執行: run_discord_bot

Bot 指令（在 Discord 頻道中輸入）：
  !run          — 觸發 AI 全領域分析
  !run <主題>   — 觸發指定主題分析（如 !run AI Agents）
"""
import os
import threading

import discord
from discord.ext import commands


DEFAULT_TOPIC = "AI 全領域（LLM、AI Agents、多模態、AI 安全、基礎設施）"

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Discord bot online: {bot.user}")


@bot.command(name="run", help="觸發 AI 市場情報分析。用法: !run [主題]")
async def run_analysis(ctx: commands.Context, *, topic: str = DEFAULT_TOPIC):
    await ctx.send(
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
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN not set. "
            "Create one at https://discord.com/developers/applications, then add to .env"
        )

    print("Discord bot starting. Press Ctrl+C to stop.")
    bot.run(token)
