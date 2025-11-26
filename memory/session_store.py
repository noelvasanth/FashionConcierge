"""Session store abstractions and a manager for conversational state."""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class ChatTurn:
    """Represents one conversational turn."""

    role: str
    content: str
    created_at: float = field(default_factory=lambda: time.time())
    metadata: Dict[str, Any] | None = None


@dataclass
class SessionEvent:
    """Tracks notable events beyond chat turns."""

    event_type: str
    payload: Dict[str, Any] | None = None
    created_at: float = field(default_factory=lambda: time.time())


class SessionStore:
    """Interface for chat session persistence."""

    def create_session(self, user_id: str, metadata: Dict[str, Any] | None = None) -> str:
        raise NotImplementedError

    def session_exists(self, session_id: str) -> bool:
        raise NotImplementedError

    def append_turn(
        self, session_id: str, role: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> None:
        raise NotImplementedError

    def append_event(
        self, session_id: str, event_type: str, payload: Dict[str, Any] | None = None
    ) -> None:
        raise NotImplementedError

    def get_recent_turns(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_all_turns(self, session_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_events(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def get_summary(self, session_id: str) -> str | None:
        raise NotImplementedError

    def upsert_summary(self, session_id: str, summary: str) -> str:
        raise NotImplementedError

    def turn_count(self, session_id: str) -> int:
        raise NotImplementedError

    def trim_turns(self, session_id: str, keep: int = 20) -> None:
        raise NotImplementedError


class JSONSessionStore(SessionStore):
    """JSON-file-backed SessionStore suitable for local runs."""

    def __init__(self, base_dir: str = "data/sessions") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def _load(self, session_id: str) -> Dict[str, Any]:
        path = self._path(session_id)
        if not path.exists():
            raise ValueError(f"Unknown session_id {session_id}")
        return json.loads(path.read_text())

    def _save(self, session_id: str, payload: Dict[str, Any]) -> None:
        self._path(session_id).write_text(json.dumps(payload, indent=2))

    def create_session(self, user_id: str, metadata: Dict[str, Any] | None = None) -> str:
        session_id = str(uuid4())
        payload = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": time.time(),
            "metadata": metadata or {},
            "turns": [],
            "events": [],
            "summary": None,
        }
        self._save(session_id, payload)
        return session_id

    def session_exists(self, session_id: str) -> bool:
        return self._path(session_id).exists()

    def append_turn(
        self, session_id: str, role: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> None:
        record = self._load(session_id)
        turn = ChatTurn(role=role, content=content, metadata=metadata)
        record["turns"].append(turn.__dict__)
        self._save(session_id, record)

    def append_event(
        self, session_id: str, event_type: str, payload: Dict[str, Any] | None = None
    ) -> None:
        record = self._load(session_id)
        event = SessionEvent(event_type=event_type, payload=payload)
        record["events"].append(event.__dict__)
        self._save(session_id, record)

    def get_recent_turns(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        record = self._load(session_id)
        return list(record.get("turns", [])[-limit:])

    def get_all_turns(self, session_id: str) -> List[Dict[str, Any]]:
        record = self._load(session_id)
        return list(record.get("turns", []))

    def get_events(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        record = self._load(session_id)
        return list(record.get("events", [])[-limit:])

    def get_summary(self, session_id: str) -> str | None:
        record = self._load(session_id)
        return record.get("summary")

    def upsert_summary(self, session_id: str, summary: str) -> str:
        record = self._load(session_id)
        record["summary"] = summary
        self._save(session_id, record)
        return summary

    def turn_count(self, session_id: str) -> int:
        record = self._load(session_id)
        return len(record.get("turns", []))

    def trim_turns(self, session_id: str, keep: int = 20) -> None:
        record = self._load(session_id)
        record["turns"] = list(record.get("turns", [])[-keep:])
        self._save(session_id, record)


class SQLiteSessionStore(SessionStore):
    """SQLite-backed session store for lightweight durability."""

    def __init__(self, db_path: str = "data/session_store.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at REAL,
                    metadata TEXT
                );
                CREATE TABLE IF NOT EXISTS turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    role TEXT,
                    content TEXT,
                    created_at REAL,
                    metadata TEXT,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    event_type TEXT,
                    payload TEXT,
                    created_at REAL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );
                CREATE TABLE IF NOT EXISTS summaries (
                    session_id TEXT PRIMARY KEY,
                    summary TEXT,
                    updated_at REAL,
                    FOREIGN KEY(session_id) REFERENCES sessions(session_id)
                );
                """
            )

    def create_session(self, user_id: str, metadata: Dict[str, Any] | None = None) -> str:
        session_id = str(uuid4())
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sessions(session_id, user_id, created_at, metadata) VALUES (?, ?, ?, ?)",
                (session_id, user_id, time.time(), json.dumps(metadata or {})),
            )
        return session_id

    def session_exists(self, session_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM sessions WHERE session_id = ? LIMIT 1", (session_id,)
            ).fetchone()
        return row is not None

    def append_turn(
        self, session_id: str, role: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO turns(session_id, role, content, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
                (session_id, role, content, time.time(), json.dumps(metadata or {})),
            )

    def append_event(
        self, session_id: str, event_type: str, payload: Dict[str, Any] | None = None
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events(session_id, event_type, payload, created_at) VALUES (?, ?, ?, ?)",
                (session_id, event_type, json.dumps(payload or {}), time.time()),
            )

    def get_recent_turns(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content, metadata, created_at FROM turns WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        turns = [self._row_to_turn(row) for row in reversed(rows)]
        return turns

    def get_all_turns(self, session_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT role, content, metadata, created_at FROM turns WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
        return [self._row_to_turn(row) for row in rows]

    def get_events(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT event_type, payload, created_at FROM events WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        events = []
        for row in reversed(rows):
            payload = json.loads(row["payload"]) if row["payload"] else {}
            events.append({"event_type": row["event_type"], "payload": payload, "created_at": row["created_at"]})
        return events

    def get_summary(self, session_id: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT summary FROM summaries WHERE session_id = ?", (session_id,)
            ).fetchone()
        return row["summary"] if row else None

    def upsert_summary(self, session_id: str, summary: str) -> str:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO summaries(session_id, summary, updated_at) VALUES (?, ?, ?)\n"
                "ON CONFLICT(session_id) DO UPDATE SET summary=excluded.summary, updated_at=excluded.updated_at",
                (session_id, summary, time.time()),
            )
        return summary

    def turn_count(self, session_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as ct FROM turns WHERE session_id = ?", (session_id,)
            ).fetchone()
        return int(row["ct"]) if row else 0

    def trim_turns(self, session_id: str, keep: int = 20) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM turns WHERE session_id = ? AND id NOT IN (\n"
                "  SELECT id FROM turns WHERE session_id = ? ORDER BY created_at DESC LIMIT ?\n)",
                (session_id, session_id, keep),
            )

    def _row_to_turn(self, row: sqlite3.Row) -> Dict[str, Any]:
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        return {
            "role": row["role"],
            "content": row["content"],
            "metadata": metadata,
            "created_at": row["created_at"],
        }


def summarize_turns(turns: List[Dict[str, Any]], prior_summary: str | None = None, max_items: int = 8) -> str:
    """Produce a compact summary of turns."""

    snippets = [f"{t['role']}: {t['content'][:160]}" for t in turns[-max_items:]]
    joined = "\n".join(f"- {snippet}" for snippet in snippets)
    if prior_summary:
        return f"Existing summary: {prior_summary}\nRecent turns:\n{joined}"
    return f"Conversation so far:\n{joined}"


class SessionManager:
    """Coordinates session creation, history retrieval and summarization."""

    def __init__(
        self,
        store: SessionStore,
        summary_trigger: int = 30,
        history_keep: int = 15,
    ) -> None:
        self.store = store
        self.summary_trigger = summary_trigger
        self.history_keep = history_keep

    def start_session(self, user_id: str, metadata: Dict[str, Any] | None = None) -> str:
        return self.store.create_session(user_id=user_id, metadata=metadata)

    def record_turn(
        self, session_id: str, role: str, content: str, metadata: Dict[str, Any] | None = None
    ) -> None:
        if not self.store.session_exists(session_id):
            raise ValueError(f"Unknown session {session_id}")
        self.store.append_turn(session_id=session_id, role=role, content=content, metadata=metadata)
        self._maybe_summarize(session_id)

    def record_event(
        self, session_id: str, event_type: str, payload: Dict[str, Any] | None = None
    ) -> None:
        if not self.store.session_exists(session_id):
            raise ValueError(f"Unknown session {session_id}")
        self.store.append_event(session_id=session_id, event_type=event_type, payload=payload)

    def get_recent_turns(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return self.store.get_recent_turns(session_id=session_id, limit=limit)

    def get_context(self, session_id: str, limit: int = 10) -> Dict[str, Any]:
        return {
            "summary": self.store.get_summary(session_id),
            "recent_turns": self.get_recent_turns(session_id, limit=limit),
            "events": self.store.get_events(session_id, limit=limit),
        }

    def summarize_session(self, session_id: str, max_items: int = 12) -> str:
        turns = self.store.get_all_turns(session_id)
        summary = summarize_turns(turns, prior_summary=self.store.get_summary(session_id), max_items=max_items)
        return self.store.upsert_summary(session_id, summary)

    def _maybe_summarize(self, session_id: str) -> None:
        if self.store.turn_count(session_id) >= self.summary_trigger:
            self.summarize_session(session_id=session_id, max_items=self.history_keep)
            self.store.trim_turns(session_id=session_id, keep=self.history_keep)


__all__ = [
    "ChatTurn",
    "SessionEvent",
    "SessionManager",
    "SessionStore",
    "JSONSessionStore",
    "SQLiteSessionStore",
    "summarize_turns",
]
