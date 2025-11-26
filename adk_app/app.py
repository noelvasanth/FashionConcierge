"""ADK app bootstrap."""

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google import generativeai as genai
from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from agents.orchestrator import OrchestratorAgent
from agents.wardrobe_ingestion import WardrobeIngestionAgent
from agents.wardrobe_query import WardrobeQueryAgent
from agents.calendar_agent import CalendarAgent
from agents.weather_agent import WeatherAgent
from agents.outfit_stylist import OutfitStylistAgent
from agents.quality_critic import QualityCriticAgent
from tools.calendar import GoogleCalendarProvider
from tools.weather import OpenWeatherProvider
from memory.user_profile import UserMemoryService
from tools.memory_tools import user_profile_tool
from tools.wardrobe_store import SQLiteWardrobeStore
from tools.wardrobe_tools import WardrobeTools
from tools.product_page_fetcher import fetch_product_page_tool
from tools.product_parser import parse_product_html_tool


class FashionConciergeApp:
    """Wires together the ADK app, agents and tools."""

    def __init__(self, config: ADKConfig | None = None) -> None:
        self.config = config or ADKConfig.from_env()
        genai.configure(api_key=self.config.api_key)

        self.memory_service = UserMemoryService()
        self.calendar_provider = GoogleCalendarProvider(project_id=self.config.project_id)
        self.weather_provider = OpenWeatherProvider()
        self.wardrobe_store = SQLiteWardrobeStore(
            self.config.wardrobe_db_path or "data/wardrobe.db"
        )
        self.wardrobe_tools = WardrobeTools(self.wardrobe_store)
        self.wardrobe_tool_defs = self.wardrobe_tools.tool_defs()
        self.ingestion_tool_defs = [fetch_product_page_tool(), parse_product_html_tool()]

        all_ingestion_tools = self.wardrobe_tool_defs + self.ingestion_tool_defs

        self.orchestrator = OrchestratorAgent(config=self.config, tools=all_ingestion_tools)
        self.wardrobe_ingestion = WardrobeIngestionAgent(
            config=self.config, wardrobe_tools=self.wardrobe_tools, tools=all_ingestion_tools
        )
        self.wardrobe_query = WardrobeQueryAgent(config=self.config, tools=self.wardrobe_tool_defs)
        self.calendar_agent = CalendarAgent(config=self.config, provider=self.calendar_provider)
        self.weather_agent = WeatherAgent(config=self.config, provider=self.weather_provider)
        self.outfit_stylist = OutfitStylistAgent(config=self.config)
        self.quality_critic = QualityCriticAgent(config=self.config)

        self.adk_app = self._build_adk_app()

    def _build_adk_app(self) -> genai_agent.App:
        """Register the orchestrator and its tools on an ADK App."""

        app = genai_agent.App()
        app.register(self.orchestrator.adk_agent)
        app.register(self.wardrobe_ingestion.adk_agent)
        app.register(self.wardrobe_query.adk_agent)
        app.register(self.calendar_agent.adk_agent)
        app.register(self.weather_agent.adk_agent)
        app.register(self.outfit_stylist.adk_agent)
        app.register(self.quality_critic.adk_agent)
        for tool in self.wardrobe_tool_defs + self.ingestion_tool_defs:
            app.register(tool)

        # Attach memory tool to orchestrator for early personalization hooks.
        app.register(user_profile_tool(self.memory_service))
        return app

    def send_test_message(self, message: str) -> str:
        """Send a test message through the orchestrator for local verification."""

        response = self.orchestrator.handle_message(message)
        return response["message"]


__all__ = ["FashionConciergeApp"]
