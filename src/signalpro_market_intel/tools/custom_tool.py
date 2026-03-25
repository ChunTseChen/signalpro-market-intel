from crewai_tools import SerperDevTool, ScrapeWebsiteTool

# Web search tool — uses SERPER_API_KEY from environment
search_tool = SerperDevTool()

# Web scraping tool — fetches full page content from URLs
scrape_tool = ScrapeWebsiteTool()
