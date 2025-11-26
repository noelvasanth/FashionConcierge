"""Unit tests for session store and manager helpers."""

from pathlib import Path

from memory.session_store import JSONSessionStore, SessionManager


def test_json_session_store_roundtrip(tmp_path: Path) -> None:
    store = JSONSessionStore(base_dir=tmp_path)
    session_id = store.create_session("user-123")

    store.append_turn(session_id, role="user", content="hello")
    store.append_event(session_id, event_type="calendar", payload={"count": 1})

    assert store.session_exists(session_id)
    assert store.turn_count(session_id) == 1
    turns = store.get_recent_turns(session_id)
    assert turns[0]["content"] == "hello"
    events = store.get_events(session_id)
    assert events[0]["payload"] == {"count": 1}


def test_session_manager_summarizes_and_trims(tmp_path: Path) -> None:
    store = JSONSessionStore(base_dir=tmp_path)
    manager = SessionManager(store=store, summary_trigger=3, history_keep=2)
    session_id = manager.start_session("user-456")

    for i in range(5):
        manager.record_turn(session_id, role="user", content=f"message {i}")

    summary = store.get_summary(session_id)
    assert summary is not None and "message" in summary
    assert store.turn_count(session_id) <= 2
    context = manager.get_context(session_id)
    assert context["summary"] == summary
    assert len(context["recent_turns"]) <= 2
