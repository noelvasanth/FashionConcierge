"""Root orchestrator agent wiring for Fashion Concierge."""

from datetime import date as dt_date, datetime
import logging
from typing import Any, Dict

from adk_app.genai_fallback import ensure_genai_imports

ensure_genai_imports()

from google.generativeai import agent as genai_agent

from adk_app.config import ADKConfig
from adk_app.logging_config import get_logger, log_event, operation_context
from agents.calendar_agent import CalendarAgent
from agents.outfit_stylist_agent import OutfitStylistAgent
from agents.weather_agent import WeatherAgent
from logic.context_synthesizer import synthesize_context
from memory.session_store import SessionManager


LOGGER = get_logger(__name__)


class OrchestratorAgent:
    """Plans calls to sub-agents and tools.

    The implementation is intentionally lightweight for the initial scaffold. The
    orchestrator can respond to a simple health-check style message locally while
    still creating an ADK `LlmAgent` that will eventually coordinate the full
    workflow.
    """

    def __init__(
        self,
        config: ADKConfig,
        tools: list | None = None,
        stylist_agent: OutfitStylistAgent | None = None,
        calendar_agent: CalendarAgent | None = None,
        weather_agent: WeatherAgent | None = None,
        session_manager: SessionManager | None = None,
    ) -> None:
        self.config = config
        self.tools = tools or []
        self.stylist_agent = stylist_agent
        self.calendar_agent = calendar_agent
        self.weather_agent = weather_agent
        self.session_manager = session_manager
        self.system_instruction = (
            "You are the Fashion Concierge orchestrator. Receive user inputs, "
            "plan the next steps across calendar, weather, wardrobe and stylist "
            "agents, and compose a concise response."
        )
        self._llm_agent = self._build_llm_agent()

    def _build_llm_agent(self) -> genai_agent.LlmAgent:
        """Create the ADK LlmAgent instance."""

        return genai_agent.LlmAgent(
            model=self.config.model,
            system_instruction=self.system_instruction,
            name="orchestrator",
            tools=self.tools,
        )

    @property
    def adk_agent(self) -> genai_agent.LlmAgent:
        """Expose the underlying ADK agent for registration on the app."""

        return self._llm_agent

    def handle_message(self, message: str, session_id: str | None = None) -> Dict[str, Any]:
        """Provide a deterministic response for local smoke tests."""

        with operation_context("agent:orchestrator.handle_message", session_id=session_id) as correlation_id:
            log_event(
                LOGGER,
                level=logging.INFO,
                event="agent_call_started",
                agent="orchestrator",
                method="handle_message",
                session_id=session_id,
                correlation_id=correlation_id,
            )

            if self.session_manager and session_id:
                self.session_manager.record_turn(session_id, role="user", content=message)

            if message.lower().strip() == "hello from fashion concierge":
                response = {
                    "status": "ok",
                    "agent": "orchestrator",
                    "message": "Hello from Fashion Concierge! The orchestrator is online.",
                }
            else:
                response = {
                    "status": "unknown",
                    "agent": "orchestrator",
                    "message": "This is a scaffolded orchestrator. Expand sub-agent calls next.",
                }

            if self.session_manager and session_id:
                self.session_manager.record_turn(session_id, role="assistant", content=response["message"])

            log_event(
                LOGGER,
                level=logging.INFO,
                event="agent_call_completed",
                agent="orchestrator",
                method="handle_message",
                session_id=session_id,
                correlation_id=correlation_id,
                status=response.get("status"),
            )
            return response

    def create_outfit(self, user_id: str, mood: str | None = None) -> Dict[str, Any]:
        """Delegate outfit creation to the stylist agent when available."""

        with operation_context("agent:orchestrator.create_outfit") as correlation_id:
            if not self.stylist_agent:
                return {"status": "error", "message": "Stylist agent not configured."}
            response = self.stylist_agent.recommend_outfit(user_id=user_id, mood=mood)
            log_event(
                LOGGER,
                level=logging.INFO,
                event="agent_call_completed",
                agent="orchestrator",
                method="create_outfit",
                correlation_id=correlation_id,
                mood=mood,
            )
            return {"status": "ok", "agent": "orchestrator", "outfit": response}

    def plan_outfit_context(
        self, user_id: str, target_date: str | dt_date, location: str, mood: str, session_id: str | None = None
    ) -> Dict[str, Any]:
        """Gather calendar and weather context for the requested day."""

        with operation_context("agent:orchestrator.plan_outfit_context", session_id=session_id) as correlation_id:
            if not self.calendar_agent or not self.weather_agent:
                return {"status": "error", "message": "Calendar or weather agent not configured."}

            parsed_date = target_date if isinstance(target_date, dt_date) else self._parse_date(target_date)
            schedule_profile = self.calendar_agent.get_schedule_profile(
                user_id=user_id, target_date=parsed_date, session_id=session_id
            )
            weather_profile = self.weather_agent.get_weather_profile(
                user_id=user_id, location=location, target_date=parsed_date, session_id=session_id
            )
            daily_context = synthesize_context(schedule_profile, weather_profile)

            if self.session_manager and session_id:
                self.session_manager.record_event(
                    session_id,
                    event_type="daily_context",
                    payload={"schedule": schedule_profile, "weather": weather_profile, "context": daily_context},
                )

            response = {
                "status": "ok",
                "agent": "orchestrator",
                "request": {"user_id": user_id, "date": parsed_date.isoformat(), "location": location, "mood": mood},
                "schedule_profile": schedule_profile,
                "weather_profile": weather_profile,
                "daily_context": daily_context,
            }
            log_event(
                LOGGER,
                level=logging.INFO,
                event="agent_call_completed",
                agent="orchestrator",
                method="plan_outfit_context",
                correlation_id=correlation_id,
                request=response["request"],
            )
            return response

    def _parse_date(self, raw_date: str) -> dt_date:
        """Parse dates flexibly for user facing requests."""

        cleaned = raw_date.replace("/", "-").replace(" ", "-")
        return datetime.fromisoformat(cleaned).date()

    def plan_outfit(
        self,
        user_id: str,
        date: str | dt_date,
        location: str,
        mood: str,
        session_id: str | None = None,
    ) -> Dict[str, Any]:
        """Full pipeline: calendar, weather, context, stylist ranking."""

        with operation_context("agent:orchestrator.plan_outfit", session_id=session_id) as correlation_id:
            if not all([self.calendar_agent, self.weather_agent, self.stylist_agent]):
                return {"status": "error", "message": "Required agents not configured."}

            parsed_date = date if isinstance(date, dt_date) else self._parse_date(str(date))  # type: ignore[arg-type]
            schedule_profile = self.calendar_agent.get_schedule_profile(
                user_id=user_id, target_date=parsed_date, session_id=session_id
            )
            weather_profile = self.weather_agent.get_weather_profile(
                user_id=user_id, location=location, target_date=parsed_date, session_id=session_id
            )
            daily_context = synthesize_context(schedule_profile, weather_profile)
            stylist_response = self.stylist_agent.recommend_outfit(
                user_id=user_id,
                mood=mood,
                schedule_profile=schedule_profile,
                weather_profile=weather_profile,
                daily_context=daily_context,
            )

            if self.session_manager and session_id:
                self.session_manager.record_event(
                    session_id,
                    event_type="outfit_plan",
                    payload={
                        "request": {"user_id": user_id, "date": parsed_date.isoformat(), "location": location, "mood": mood},
                        "schedule": schedule_profile,
                        "weather": weather_profile,
                        "context": daily_context,
                        "stylist": stylist_response,
                    },
                )

            debug_summary = {
                "schedule_profile": schedule_profile,
                "weather_profile": weather_profile,
                "context": daily_context,
                "stylist_debug": stylist_response.get("debug_summary"),
            }

            response = {
                "status": "ok",
                "user_facing_summary": stylist_response.get("user_facing_rationale"),
                "request": {
                    "user_id": user_id,
                    "date": parsed_date.isoformat(),
                    "location": location,
                    "mood": mood,
                },
                "top_outfits": stylist_response.get("ranked_outfits", []),
                "context": daily_context,
                "debug_summary": debug_summary,
            }

            log_event(
                LOGGER,
                level=logging.INFO,
                event="agent_call_completed",
                agent="orchestrator",
                method="plan_outfit",
                correlation_id=correlation_id,
                request=response["request"],
                outfit_count=len(response["top_outfits"]),
            )
            return response
