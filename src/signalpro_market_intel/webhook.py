"""
FastAPI webhook server for triggering SignalPro Market Intel.

Provides a universal HTTP endpoint that can be called from:
- curl / Postman (direct API call)
- Slack slash commands
- LINE / Telegram / Discord bots (via webhook forwarding)
- Zapier / Make / IFTTT (no-code automation)
- Email triggers (via Zapier email parser → webhook)

Start: run_webhook  (or: uvicorn signalpro_market_intel.webhook:app --host 0.0.0.0 --port 8000)
"""
import os
import threading
from datetime import datetime

from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(
    title="SignalPro Market Intel",
    description="AI 市場情報系統 — Webhook 觸發入口",
)

# Simple in-memory state
_state = {"running": False, "last_run": None, "last_topic": None}


class TriggerRequest(BaseModel):
    topic: str = "AI 全領域（LLM、AI Agents、多模態、AI 安全、基礎設施）"


def _execute_crew(topic: str):
    """Run the crew in background. Updates _state on start/finish."""
    from signalpro_market_intel.main import run_with_topic

    _state["running"] = True
    _state["last_topic"] = topic
    try:
        run_with_topic(topic)
    finally:
        _state["running"] = False
        _state["last_run"] = datetime.now().isoformat()


# ── Endpoints ────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", **_state}


@app.post("/trigger")
async def trigger(req: TriggerRequest, background_tasks: BackgroundTasks):
    """
    Generic trigger — accepts JSON body.

    Examples:
      curl -X POST http://localhost:8000/trigger -H 'Content-Type: application/json' -d '{"topic": "AI Agents"}'
      curl -X POST http://localhost:8000/trigger   # uses default topic
    """
    if _state["running"]:
        return JSONResponse(
            status_code=409,
            content={"error": "A crew run is already in progress. Please wait."},
        )
    background_tasks.add_task(_execute_crew, req.topic)
    return {
        "status": "triggered",
        "topic": req.topic,
        "message": "AI 市場情報分析已啟動，完成後將寄送 email。",
    }


@app.post("/trigger/slack")
async def trigger_slack(request: Request, background_tasks: BackgroundTasks):
    """
    Slack slash command endpoint.

    Setup in Slack:
      1. Create a Slack App → Slash Commands
      2. Command: /intel
      3. Request URL: https://your-server/trigger/slack
      4. User types: /intel AI Agents
    """
    form = await request.form()
    text = str(form.get("text", "")).strip()
    topic = text if text else "AI 全領域（LLM、AI Agents、多模態、AI 安全、基礎設施）"

    if _state["running"]:
        return {"response_type": "ephemeral", "text": "分析正在執行中，請稍候。"}

    background_tasks.add_task(_execute_crew, topic)
    return {
        "response_type": "in_channel",
        "text": f"AI 市場情報分析已觸發\n主題：{topic}\n完成後報告將寄送至 email。",
    }


@app.post("/trigger/line")
async def trigger_line(request: Request, background_tasks: BackgroundTasks):
    """
    LINE Messaging API webhook endpoint.

    Setup:
      1. LINE Developers Console → Create Messaging API channel
      2. Webhook URL: https://your-server/trigger/line
      3. User sends any message to the bot → triggers default analysis
      4. User sends a topic (e.g., "AI Agents") → triggers with that topic
    """
    body = await request.json()
    events = body.get("events", [])

    for event in events:
        if event.get("type") == "message" and event["message"].get("type") == "text":
            user_text = event["message"]["text"].strip()
            topic = user_text if user_text else "AI 全領域"

            if not _state["running"]:
                background_tasks.add_task(_execute_crew, topic)
                # Reply via LINE requires channel access token + reply API
                # For simplicity, just acknowledge here
                return {"status": "triggered", "topic": topic}

    return {"status": "ok"}


@app.post("/trigger/discord")
async def trigger_discord(request: Request, background_tasks: BackgroundTasks):
    """
    Discord Interactions endpoint.

    Can be used with Discord slash commands or a simple bot webhook.
    For simple use: forward messages to this endpoint via a Discord bot.
    """
    body = await request.json()

    # Discord verification ping
    if body.get("type") == 1:
        return {"type": 1}

    # Slash command interaction
    content = ""
    if body.get("type") == 2:  # APPLICATION_COMMAND
        options = body.get("data", {}).get("options", [])
        for opt in options:
            if opt.get("name") == "topic":
                content = opt.get("value", "")

    topic = content.strip() if content.strip() else "AI 全領域"

    if _state["running"]:
        return {"type": 4, "data": {"content": "分析正在執行中，請稍候。"}}

    background_tasks.add_task(_execute_crew, topic)
    return {
        "type": 4,
        "data": {"content": f"AI 市場情報分析已觸發，主題：{topic}\n完成後報告將寄送至 email。"},
    }
