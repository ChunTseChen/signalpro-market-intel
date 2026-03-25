import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

from signalpro_market_intel.tools.custom_tool import search_tool

DEFAULT_RECIPIENTS = "jameschen1127@gmail.com,aks60808@gmail.com"


@CrewBase
class SignalproMarketIntel():
    """SignalproMarketIntel crew"""

    agents: list[BaseAgent]
    tasks: list[Task]

    @before_kickoff
    def prepare_inputs(self, inputs):
        if not inputs.get("current_date"):
            inputs["current_date"] = datetime.now().strftime("%Y-%m-%d")
        if not inputs.get("topic"):
            inputs["topic"] = "AI 全領域（LLM、AI Agents、多模態、AI 安全、基礎設施）"
        return inputs

    @after_kickoff
    def send_report_email(self, result):
        """Send the completed report via Gmail after crew finishes."""
        sender = os.environ.get("GMAIL_SENDER")
        password = os.environ.get("GMAIL_APP_PASSWORD")
        recipients = os.environ.get("EMAIL_RECIPIENTS", DEFAULT_RECIPIENTS)
        recipient_list = [r.strip() for r in recipients.split(",") if r.strip()]

        if not sender or not password:
            print("Email not configured. Set GMAIL_SENDER and GMAIL_APP_PASSWORD.")
            return result

        report_content = str(result)
        date_str = datetime.now().strftime("%Y-%m-%d")

        msg = MIMEMultipart()
        msg["From"] = sender
        msg["To"] = ", ".join(recipient_list)
        msg["Subject"] = f"AI 市場情報報告 — {date_str}"
        msg.attach(MIMEText(report_content, "plain", "utf-8"))

        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(report_content.encode("utf-8"))
        encoders.encode_base64(attachment)
        attachment.add_header(
            "Content-Disposition", f"attachment; filename=report_{date_str}.md"
        )
        msg.attach(attachment)

        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(sender, password)
                server.send_message(msg)
            print(f"Report emailed to {', '.join(recipient_list)}")
        except Exception as e:
            print(f"Failed to send email: {e}")

        return result

    @agent
    def news_collector(self) -> Agent:
        return Agent(
            config=self.agents_config['news_collector'],
            llm="gpt-4o-mini",
            tools=[search_tool],
            max_iter=15,
            verbose=True,
        )

    @agent
    def market_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['market_analyst'],
            llm="anthropic/claude-sonnet-4-6",
            verbose=True,
        )

    @agent
    def report_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['report_writer'],
            llm="anthropic/claude-haiku-4-5-20251001",
            verbose=True,
        )

    @task
    def collect_intelligence(self) -> Task:
        return Task(
            config=self.tasks_config['collect_intelligence'],
        )

    @task
    def analyze_market(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_market'],
            context=[self.collect_intelligence()],
        )

    @task
    def write_report(self) -> Task:
        return Task(
            config=self.tasks_config['write_report'],
            context=[self.collect_intelligence(), self.analyze_market()],
            output_file='output/report.md',
        )

    @crew
    def crew(self) -> Crew:
        """Creates the SignalproMarketIntel crew"""
        user_pref = TextFileKnowledgeSource(
            file_paths=["user_preference.txt"],
        )

        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            knowledge_sources=[user_pref],
            verbose=True,
        )
