#!/usr/bin/env python
import os
import sys
import shutil
import smtplib
import warnings

from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from signalpro_market_intel.crew import SignalproMarketIntel

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

DEFAULT_RECIPIENT = "jameschen1127@gmail.com"


def run():
    """
    Run the crew once, save a timestamped report, and email it.
    """
    inputs = {
        'topic': 'AI 全領域（LLM、AI Agents、多模態、AI 安全、基礎設施）',
        'current_date': datetime.now().strftime("%Y-%m-%d"),
    }

    try:
        SignalproMarketIntel().crew().kickoff(inputs=inputs)
        report_path = _copy_report_with_timestamp()
        if report_path:
            _send_report_email(report_path)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def run_scheduled():
    """
    Start a blocking scheduler that runs the crew every 3 days.
    Defaults to 08:00; override with SCHEDULE_HOUR / SCHEDULE_MINUTE env vars.
    Override interval with SCHEDULE_INTERVAL_DAYS (default: 3).
    Executes once immediately on startup, then on schedule.
    """
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    hour = int(os.environ.get("SCHEDULE_HOUR", "8"))
    minute = int(os.environ.get("SCHEDULE_MINUTE", "0"))
    interval_days = int(os.environ.get("SCHEDULE_INTERVAL_DAYS", "3"))

    scheduler = BlockingScheduler()

    # First run is scheduled at the next occurrence of HH:MM,
    # then repeats every interval_days.
    from datetime import time as dt_time
    start = datetime.combine(datetime.now().date(), dt_time(hour, minute))
    if start <= datetime.now():
        from datetime import timedelta
        start += timedelta(days=interval_days)

    scheduler.add_job(
        run,
        IntervalTrigger(days=interval_days, start_date=start),
        id="periodic_intel",
        name=f"AI Market Intelligence (every {interval_days} days)",
    )

    print(f"Scheduler started. Will run every {interval_days} days at {hour:02d}:{minute:02d}.")
    print("Running immediately on startup...")
    run()

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")


def run_with_trigger():
    """
    Run the crew with a JSON payload from CLI argument.
    Usage: run_with_trigger '{"topic": "AI Agents"}'
    """
    import json

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    return run_with_topic(trigger_payload.get("topic", "AI 全領域"))


def run_with_topic(topic: str = "AI 全領域"):
    """
    Programmatic entry point — callable from webhook or other integrations.
    """
    inputs = {
        "topic": topic,
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }

    try:
        result = SignalproMarketIntel().crew().kickoff(inputs=inputs)
        report_path = _copy_report_with_timestamp()
        if report_path:
            _send_report_email(report_path)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def run_webhook():
    """
    Start the FastAPI webhook server.
    Override host/port with WEBHOOK_HOST / WEBHOOK_PORT env vars.
    """
    import uvicorn

    host = os.environ.get("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.environ.get("WEBHOOK_PORT", "8000"))
    uvicorn.run("signalpro_market_intel.webhook:app", host=host, port=port)


def _copy_report_with_timestamp() -> str | None:
    """Copy the output report to a timestamped file. Returns the new path."""
    src = "output/report.md"
    if os.path.exists(src):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = f"output/report_{timestamp}.md"
        shutil.copy2(src, dst)
        print(f"Report saved to {dst}")
        return dst
    return None


def _send_report_email(report_path: str):
    """Send the report via Gmail SMTP.

    Required env vars:
      GMAIL_SENDER      - sender Gmail address
      GMAIL_APP_PASSWORD - Gmail App Password (https://myaccount.google.com/apppasswords)
    Optional:
      EMAIL_RECIPIENT    - defaults to jameschen1127@gmail.com
    """
    sender = os.environ.get("GMAIL_SENDER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    recipient = os.environ.get("EMAIL_RECIPIENT", DEFAULT_RECIPIENT)

    if not sender or not password:
        print("Email not configured. Set GMAIL_SENDER and GMAIL_APP_PASSWORD in .env to enable.")
        return

    with open(report_path, "r", encoding="utf-8") as f:
        report_content = f.read()

    date_str = datetime.now().strftime("%Y-%m-%d")
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = f"AI 市場情報報告 — {date_str}"

    msg.attach(MIMEText(report_content, "plain", "utf-8"))

    attachment = MIMEBase("application", "octet-stream")
    attachment.set_payload(report_content.encode("utf-8"))
    encoders.encode_base64(attachment)
    filename = os.path.basename(report_path)
    attachment.add_header("Content-Disposition", f"attachment; filename={filename}")
    msg.attach(attachment)

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
        print(f"Report emailed to {recipient}")
    except Exception as e:
        print(f"Failed to send email: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI 全領域（LLM、AI Agents、多模態、AI 安全、基礎設施）",
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }
    try:
        SignalproMarketIntel().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        SignalproMarketIntel().crew().replay(task_id=sys.argv[1])
    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI 全領域（LLM、AI Agents、多模態、AI 安全、基礎設施）",
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }
    try:
        SignalproMarketIntel().crew().test(
            n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs
        )
    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")
