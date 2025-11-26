"""ADK app bootstrap."""

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google import generativeai as genai
from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from adk_app.logging_config import configure_logging
from agents.orchestrator import OrchestratorAgent
from agents.wardrobe_ingestion import WardrobeIngestionAgent
from agents.wardrobe_query import WardrobeQueryAgent
from agents.calendar_agent import CalendarAgent
from agents.weather_agent import WeatherAgent
from agents.outfit_stylist_agent import OutfitStylistAgent
from agents.quality_critic import QualityCriticAgent
from tools.calendar_provider import GoogleCalendarProvider
from tools.weather_provider import OpenWeatherProvider
from memory.user_profile import UserMemoryService
from tools.memory_tools import user_profile_tool
from memory.session_store import JSONSessionStore, SessionManager, SessionStore, SQLiteSessionStore
from tools.session_tools import session_toolkit
from tools.wardrobe_store import SQLiteWardrobeStore
from tools.wardrobe_tools import WardrobeTools
from tools.product_page_fetcher import fetch_product_page_tool
from tools.product_parser import parse_product_html_tool


class FashionConciergeApp:
    """Wires together the ADK app, agents and tools."""

    def __init__(self, config: ADKConfig | None = None) -> None:
        self.config = config or ADKConfig.from_env()
        configure_logging()
        genai.configure(api_key=self.config.api_key)

        self.memory_service = UserMemoryService()
        self.session_store = self._build_session_store()
        self.session_manager = SessionManager(store=self.session_store)
        self.calendar_provider = GoogleCalendarProvider(
            project_id=self.config.project_id,
            calendar_id=self.config.calendar_id,
            credentials_path=self.config.google_credentials_path,
        )
        self.weather_provider = OpenWeatherProvider(api_key=self.config.weather_api_key)
        self.wardrobe_store = SQLiteWardrobeStore(
            self.config.wardrobe_db_path or "data/wardrobe.db"
        )
        self.wardrobe_tools = WardrobeTools(self.wardrobe_store)
        self.wardrobe_tool_defs = self.wardrobe_tools.tool_defs()
        self.ingestion_tool_defs = [fetch_product_page_tool(), parse_product_html_tool()]
        self.session_tool_defs = session_toolkit(self.session_manager)
        self.memory_tool_defs = [user_profile_tool(self.memory_service)]

        all_ingestion_tools = self.wardrobe_tool_defs + self.ingestion_tool_defs + self.session_tool_defs

        self.outfit_stylist = OutfitStylistAgent(
            config=self.config, wardrobe_tools=self.wardrobe_tools
        )
        self._validate_stylist_agent()
        self.calendar_agent = CalendarAgent(
            config=self.config,
            provider=self.calendar_provider,
            session_manager=self.session_manager,
            context_tools=self.session_tool_defs + self.memory_tool_defs,
        )
        self.weather_agent = WeatherAgent(
            config=self.config,
            provider=self.weather_provider,
            session_manager=self.session_manager,
            context_tools=self.session_tool_defs + self.memory_tool_defs,
        )
        self.orchestrator = OrchestratorAgent(
            config=self.config,
            tools=all_ingestion_tools + self.memory_tool_defs,
            stylist_agent=self.outfit_stylist,
            calendar_agent=self.calendar_agent,
            weather_agent=self.weather_agent,
            session_manager=self.session_manager,
        )
        self.wardrobe_ingestion = WardrobeIngestionAgent(
            config=self.config, wardrobe_tools=self.wardrobe_tools, tools=all_ingestion_tools
        )
        self.wardrobe_query = WardrobeQueryAgent(config=self.config, tools=self.wardrobe_tool_defs)
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
        for tool in (
            self.wardrobe_tool_defs
            + self.ingestion_tool_defs
            + self.session_tool_defs
            + self.memory_tool_defs
        ):
            app.register(tool)

        return app

    def _validate_stylist_agent(self) -> None:
        """Ensure the canonical stylist agent is wired in instead of the legacy stub."""

        if self.outfit_stylist.__class__.__module__ == "agents.outfit_stylist":
            msg = (
                "The deprecated agents.outfit_stylist stub should not be registered. "
                "Import OutfitStylistAgent from agents.outfit_stylist_agent instead."
            )
            raise RuntimeError(msg)

    def _build_session_store(self) -> SessionStore:
        if self.config.session_store_backend.lower() == "sqlite":
            return SQLiteSessionStore(self.config.session_store_path or "data/session_store.db")
        return JSONSessionStore(self.config.session_store_path or "data/sessions")

    def start_session(self, user_id: str, metadata: dict | None = None) -> str:
        """Create a session and return its identifier for downstream calls."""

        return self.session_manager.start_session(user_id=user_id, metadata=metadata)

    def send_test_message(self, message: str) -> str:
        """Send a test message through the orchestrator for local verification."""

        response = self.orchestrator.handle_message(message)
        return response["message"]


__all__ = ["FashionConciergeApp"]
