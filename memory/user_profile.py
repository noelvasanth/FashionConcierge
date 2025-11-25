"""User profile and memory helpers."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict


@dataclass
class UserProfile:
    user_id: str
    preferences: Dict[str, str]


class UserMemoryService:
    """Simple JSON-backed memory store."""

    def __init__(self, base_dir: str = "data/memory") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _profile_path(self, user_id: str) -> Path:
        return self.base_dir / f"{user_id}.json"

    def get_user_profile(self, user_id: str) -> Dict[str, str]:
        path = self._profile_path(user_id)
        if not path.exists():
            profile = UserProfile(user_id=user_id, preferences={})
            path.write_text(json.dumps(asdict(profile), indent=2))
            return profile.preferences

        data = json.loads(path.read_text())
        return data.get("preferences", {})

    def update_user_preferences(self, user_id: str, updates: Dict[str, str]) -> Dict[str, str]:
        path = self._profile_path(user_id)
        profile = UserProfile(user_id=user_id, preferences=self.get_user_profile(user_id))
        profile.preferences.update(updates)
        path.write_text(json.dumps(asdict(profile), indent=2))
        return profile.preferences
