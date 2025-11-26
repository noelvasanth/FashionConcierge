"""Configuration helpers for the Fashion Concierge ADK app."""

from dataclasses import dataclass
from pathlib import Path
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
    google_credentials_path: Optional[str] = None
    calendar_id: Optional[str] = None
    weather_api_key: Optional[str] = None
    default_location: Optional[str] = None
    wardrobe_db_path: Optional[str] = None
    session_store_backend: str = "json"
    session_store_path: Optional[str] = None
    environment: str | None = None

    @classmethod
    def from_env(cls) -> "ADKConfig":
        """Build a config from environment variables or an environment YAML file.

        Environment specific YAML lives in ``config/environments/<env>.yaml`` by
        default and is merged with environment variables so that secrets can be
        injected via Secret Manager or the runtime environment.
        """

        env_name = os.getenv("APP_ENV")
        config_path = os.getenv("APP_CONFIG_PATH")
        config_dir = Path(os.getenv("ADK_CONFIG_DIR", "config/environments"))
        yaml_config: dict = {}

        if config_path:
            path = Path(config_path)
        elif env_name:
            path = config_dir / f"{env_name}.yaml"
        else:
            path = None

        if path and path.exists():
            yaml_config = cls._load_yaml_config(path)

        def get_value(key: str, default: Optional[str] = None) -> Optional[str]:
            env_key = key.upper()
            return os.getenv(env_key, yaml_config.get(key, default))

        project_id = get_value("project_id", "fashion-concierge-local")
        location = get_value("location", "us-central1")
        model = get_value("model", DEFAULT_GEMINI_MODEL)
        api_key = get_value("google_api_key")
        google_credentials_path = get_value("google_credentials_path")
        calendar_id = get_value("calendar_id")
        weather_api_key = get_value("openweather_api_key")
        default_location = get_value("default_location")
        session_store_backend = get_value("session_store_backend", "json")
        session_store_path = get_value("session_store_path")

        return cls(
            project_id=str(project_id or "fashion-concierge-local"),
            location=str(location or "us-central1"),
            model=str(model or DEFAULT_GEMINI_MODEL),
            api_key=api_key,
            google_credentials_path=google_credentials_path,
            calendar_id=calendar_id,
            weather_api_key=weather_api_key,
            default_location=default_location,
            session_store_backend=session_store_backend,
            session_store_path=session_store_path,
            environment=env_name,
        )

    @staticmethod
    def _load_yaml_config(path: Path) -> dict:
        """Parse a minimal YAML/INI-style config without external dependencies."""

        config: dict[str, str] = {}
        for line in path.read_text().splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if ":" not in stripped:
                continue
            key, raw_value = stripped.split(":", 1)
            value = raw_value.strip()
            if (value.startswith("\"") and value.endswith("\"")) or (
                value.startswith("'") and value.endswith("'")
            ):
                value = value[1:-1]
            config[key.strip()] = value
        return config
