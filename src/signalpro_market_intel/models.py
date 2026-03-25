from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    """Single news item collected from sources."""
    title: str = Field(description="News headline")
    source: str = Field(description="Source publication or website")
    url: str = Field(description="URL to the original article")
    summary: str = Field(description="Brief summary of the news item")
    relevance_score: float = Field(
        description="Relevance score from 0.0 to 1.0", ge=0.0, le=1.0
    )


class TrendAnalysis(BaseModel):
    """Analysis of a single market trend."""
    trend_name: str = Field(description="Name of the identified trend")
    description: str = Field(description="Detailed description of the trend")
    impact_level: str = Field(description="Impact level: high, medium, or low")
    key_players: list[str] = Field(description="Key companies or organizations involved")
    evidence: list[str] = Field(description="Evidence supporting this trend")


class CompetitorInsight(BaseModel):
    """Insight about a specific competitor."""
    company: str = Field(description="Company name")
    recent_moves: list[str] = Field(description="Recent strategic moves or announcements")
    strategic_direction: str = Field(description="Assessed strategic direction")


class MarketAnalysisReport(BaseModel):
    """Complete market analysis report structure."""
    executive_summary: str = Field(description="Executive summary of the report")
    news_items: list[NewsItem] = Field(description="Collected news items")
    trends: list[TrendAnalysis] = Field(description="Identified market trends")
    competitor_insights: list[CompetitorInsight] = Field(
        description="Competitor analysis insights"
    )
    opportunities: list[str] = Field(description="Identified opportunities")
    risks: list[str] = Field(description="Identified risks")
    recommendations: list[str] = Field(description="Strategic recommendations")
