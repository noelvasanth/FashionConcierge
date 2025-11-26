"""Configuration helpers for the Fashion Concierge ADK app."""

from dataclasses import dataclass
import os
from typing import Optional

DEFAULT_GEMINI_MODEL = "models/gemini-1.5-flash-002"


@dataclass
class ADKConfig:
    """Configuration values for the ADK app.

    This class keeps the local bootstrap simple while aligning with the ADK
    expectation that a project id, location and model are provided when creating
    agents and tools.
    """

    project_id: str
    location: str = "us-central1"
    model: str = DEFAULT_GEMINI_MODEL
    api_key: Optional[str] = None
    wardrobe_db_path: Optional[str] = None
    session_store_backend: str = "json"
    session_store_path: Optional[str] = None

    @classmethod
    def from_env(cls) -> "ADKConfig":
        """Build a config from environment variables.

        GOOGLE_API_KEY is used by the Google ADK when running locally without
        Cloud credentials. PROJECT_ID and LOCATION keep parity with Vertex AI
        deployments.
        """

        project_id = os.getenv("PROJECT_ID", "fashion-concierge-local")
        location = os.getenv("LOCATION", "us-central1")
        model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
        api_key = os.getenv("GOOGLE_API_KEY")
        session_store_backend = os.getenv("SESSION_STORE_BACKEND", "json")
        session_store_path = os.getenv("SESSION_STORE_PATH")
        return cls(
            project_id=project_id,
            location=location,
            model=model,
            api_key=api_key,
            session_store_backend=session_store_backend,
            session_store_path=session_store_path,
        )
