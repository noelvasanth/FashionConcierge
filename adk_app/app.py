"""ADK app bootstrap."""

from datetime import date as dt_date
import logging

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google import generativeai as genai
from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from adk_app.logging_config import configure_logging, get_logger, log_event, operation_context
from pydantic import ValidationError
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
from tools.memory_tools import update_user_preferences_tool, user_profile_tool
from memory.session_store import JSONSessionStore, SessionManager, SessionStore, SQLiteSessionStore
from tools.session_tools import session_toolkit
from tools.wardrobe_store import SQLiteWardrobeStore
from tools.wardrobe_tools import WardrobeTools
from tools.product_page_fetcher import fetch_product_page_tool
from tools.product_parser import parse_product_html_tool
from logic.validation import OutfitRequest, OutfitResponse, validation_failure


LOGGER = get_logger(__name__)


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
        self.memory_tool_defs = [
            user_profile_tool(self.memory_service),
            update_user_preferences_tool(self.memory_service),
        ]

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

    def orchestrate_outfit(
        self,
        *,
        user_id: str,
        location: str,
        date: str | dt_date,
        mood: str,
        session_id: str | None = None,
    ) -> dict:
        """Session-aware outfit orchestration entry point.

        This method delegates to the orchestrator for calendar/weather context and
        then calls the deterministic stylist agent to build outfits.
        """

        with operation_context("app:orchestrate_outfit", session_id=session_id) as correlation_id:
            log_event(
                LOGGER,
                level=logging.INFO,
                event="app_call_started",
                agent="app",
                method="orchestrate_outfit",
                session_id=session_id,
                user_id=user_id,
                mood=mood,
                location=location,
            )

            context_result = self.orchestrator.plan_outfit_context(
                user_id=user_id,
                target_date=date,
                location=location,
                mood=mood,
                session_id=session_id,
            )
            if context_result.get("status") != "ok":
                return context_result

            try:
                request = OutfitRequest.model_validate(context_result.get("request", {}))
            except ValidationError as exc:
                log_event(
                    LOGGER,
                    level=logging.WARNING,
                    event="app_request_invalid",
                    agent="app",
                    method="orchestrate_outfit",
                    details=str(exc),
                    correlation_id=correlation_id,
                )
                return validation_failure("Invalid outfit request payload", exc)

            stylist_response = self.outfit_stylist.recommend_outfit(
                user_id=user_id,
                mood=mood,
                schedule_profile=context_result.get("schedule_profile"),
                weather_profile=context_result.get("weather_profile"),
                daily_context=context_result.get("daily_context"),
            )

            response = {
                "status": "ok",
                "request": request,
                "top_outfits": stylist_response.get("ranked_outfits", []),
                "user_facing_summary": stylist_response.get("user_facing_rationale"),
                "context": {
                    "schedule": context_result.get("schedule_profile"),
                    "weather": context_result.get("weather_profile"),
                    "daily": context_result.get("daily_context"),
                },
                "debug_summary": {
                    "context": context_result.get("daily_context"),
                    "stylist_debug": stylist_response.get("debug_summary"),
                },
            }

            try:
                OutfitResponse.model_validate(response)
            except ValidationError as exc:
                log_event(
                    LOGGER,
                    level=logging.WARNING,
                    event="app_response_invalid",
                    agent="app",
                    method="orchestrate_outfit",
                    details=str(exc),
                    correlation_id=correlation_id,
                )
                return validation_failure("Outfit response failed schema checks", exc)

            if self.session_manager and session_id:
                self.session_manager.record_event(
                    session_id,
                    event_type="outfit_plan",
                    payload=response,
                )

            log_event(
                LOGGER,
                level=logging.INFO,
                event="app_call_completed",
                agent="app",
                method="orchestrate_outfit",
                session_id=session_id,
                correlation_id=correlation_id,
                outfit_count=len(response["top_outfits"]),
            )

            return response

    def plan_outfit(
        self,
        *,
        user_id: str,
        location: str,
        date: str | dt_date,
        mood: str,
        session_id: str | None = None,
    ) -> dict:
        """Alias for orchestrate_outfit to match expected notebook calls."""

        return self.orchestrate_outfit(
            user_id=user_id,
            location=location,
            date=date,
            mood=mood,
            session_id=session_id,
        )

    def converse_with_memory(
        self,
        *,
        user_id: str,
        session_id: str,
        message: str,
        preference_updates: dict | None = None,
    ) -> dict:
        """Lightweight conversational entry point that persists preferences.

        The method echoes stored preferences to demonstrate end-to-end memory.
        It records both turns in the session store so downstream tools can use
        the same history surfaced through ``session_tool_defs``.
        """

        with operation_context("app:converse_with_memory", session_id=session_id) as correlation_id:
            log_event(
                LOGGER,
                level=logging.INFO,
                event="app_call_started",
                agent="app",
                method="converse_with_memory",
                session_id=session_id,
                correlation_id=correlation_id,
            )

            if self.session_manager:
                self.session_manager.record_turn(session_id, role="user", content=message)

            if preference_updates:
                stored_preferences = self.memory_service.update_user_preferences(
                    user_id=user_id, updates=preference_updates
                )
                if self.session_manager:
                    self.session_manager.record_event(
                        session_id,
                        event_type="preference_update",
                        payload=preference_updates,
                    )
            else:
                stored_preferences = self.memory_service.get_user_profile(user_id=user_id)

            response_message = self._render_memory_response(message, stored_preferences)

            if self.session_manager:
                self.session_manager.record_turn(session_id, role="assistant", content=response_message)

            log_event(
                LOGGER,
                level=logging.INFO,
                event="app_call_completed",
                agent="app",
                method="converse_with_memory",
                session_id=session_id,
                correlation_id=correlation_id,
            )

            return {
                "status": "ok",
                "session_id": session_id,
                "message": response_message,
                "preferences": stored_preferences,
            }

    def send_test_message(self, message: str, session_id: str | None = None) -> str:
        """Send a test message through the orchestrator for local verification."""

        response = self.orchestrator.handle_message(message, session_id=session_id)
        return response["message"]

    @staticmethod
    def _render_memory_response(message: str, preferences: dict | None) -> str:
        """Summarize saved preferences in the assistant reply."""

        base = message.strip() if message else "Noted your update."
        if not preferences:
            return f"{base} I do not have any saved preferences yet, but I will remember future updates."

        pref_summary = "; ".join(f"{key}: {value}" for key, value in preferences.items())
        return (
            f"{base} I've stored these preferences for future suggestions: {pref_summary}. "
            "Tell me if you want to adjust them."
        )


__all__ = ["FashionConciergeApp"]
