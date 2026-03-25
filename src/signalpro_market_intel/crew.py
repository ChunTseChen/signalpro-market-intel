from datetime import datetime

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

from signalpro_market_intel.tools.custom_tool import search_tool, scrape_tool


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

    @agent
    def news_collector(self) -> Agent:
        return Agent(
            config=self.agents_config['news_collector'],
            llm="gpt-4o-mini",
            tools=[search_tool, scrape_tool],
            max_iter=25,
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
            llm="anthropic/claude-sonnet-4-6",
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
