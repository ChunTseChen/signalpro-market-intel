"""
Discord Bot — Karen (Marketing) — 透過 CrewAI 雲端觸發市場情報分析。

觸發後任務在 CrewAI 雲端執行，可在 dashboard 上查看進度。
完成後自動寄 email 報告。

使用方式（在 Discord 頻道中 @mention）：
  @Karen(Marketing)                → 觸發 AI 全領域分析
  @Karen(Marketing) AI Agents      → 觸發指定主題分析
  @Karen(Marketing) 狀態            → 查看最近一次執行狀態

設定步驟：
  1. Discord Developer Portal → Bot → USERNAME 改為 Karen(Marketing)
  2. 開啟 MESSAGE CONTENT INTENT
  3. .env 中設定：
     DISCORD_BOT_TOKEN=你的discord bot token
     CREWAI_CREW_URL=你的crew公開URL
     CREWAI_CREW_TOKEN=你的crew token
  4. 執行: run_discord_bot
"""
import os
from datetime import datetime

import discord
import httpx

DEFAULT_TOPIC = "AI 全領域（LLM、AI Agents、多模態、AI 安全、基礎設施）"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

_last = {"kickoff_id": None, "topic": None, "time": None}


def _get_crewai_config():
    url = os.environ.get("CREWAI_CREW_URL")
    token = os.environ.get("CREWAI_CREW_TOKEN")
    if not url or not token:
        raise RuntimeError("CREWAI_CREW_URL and CREWAI_CREW_TOKEN must be set in .env")
    return url, token


def _trigger_crew(topic: str) -> str:
    """Call CrewAI platform API to kick off the crew. Returns kickoff_id."""
    url, token = _get_crewai_config()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "inputs": {
            "topic": topic,
            "current_date": datetime.now().strftime("%Y-%m-%d"),
        }
    }
    r = httpx.post(f"{url}/kickoff", headers=headers, json=payload, timeout=30)
    r.raise_for_status()
    return r.json().get("kickoff_id", "unknown")


def _get_crew_status(kickoff_id: str) -> dict:
    """Check the status of a kickoff on CrewAI platform."""
    url, token = _get_crewai_config()
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = httpx.get(f"{url}/status/{kickoff_id}", headers=headers, timeout=15)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {"status": "unknown"}


@client.event
async def on_ready():
    print(f"Karen (Marketing) online: {client.user}")
    print(f"Connected to {len(client.guilds)} server(s)")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if client.user not in message.mentions:
        return

    # Strip mentions to get command text
    text = message.content
    for mention in message.mentions:
        text = text.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
    text = text.strip()

    # Status command
    if text in ("狀態", "status"):
        if _last["kickoff_id"]:
            status_info = _get_crew_status(_last["kickoff_id"])
            await message.channel.send(
                f"**Karen (Marketing) 最近一次執行**\n"
                f"主題：{_last['topic']}\n"
                f"觸發時間：{_last['time']}\n"
                f"Kickoff ID：`{_last['kickoff_id']}`\n"
                f"狀態：{status_info.get('status', 'unknown')}\n\n"
                f"詳細進度請到 CrewAI Dashboard 查看。"
            )
        else:
            await message.channel.send("目前尚未執行過任何任務。")
        return

    # Trigger crew
    topic = text if text else DEFAULT_TOPIC

    try:
        kickoff_id = _trigger_crew(topic)
        _last["kickoff_id"] = kickoff_id
        _last["topic"] = topic
        _last["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")

        await message.channel.send(
            f"收到！Karen 已在雲端啟動市場情報分析\n"
            f"**主題：**{topic}\n"
            f"**Kickoff ID：**`{kickoff_id}`\n\n"
            f"你可以在 CrewAI Dashboard 上即時查看進度。\n"
            f"完成後報告將自動寄送至 email。\n"
            f"輸入 `@Karen(Marketing) 狀態` 查看執行狀態。"
        )
    except Exception as e:
        await message.channel.send(f"觸發失敗：{e}")


def main():
    from dotenv import load_dotenv
    load_dotenv()

    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN not set. Add to .env")

    # Validate CrewAI config on startup
    _get_crewai_config()

    print("Karen (Marketing) starting. Press Ctrl+C to stop.")
    client.run(token)
