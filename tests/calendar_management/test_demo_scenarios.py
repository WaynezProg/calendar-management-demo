import importlib
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skills" / "calendar-management"
TOOLS_DIR = SKILL_DIR / "tools"
sys.path.insert(0, str(TOOLS_DIR))


def load_demo_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript((SKILL_DIR / "db" / "init.sql").read_text(encoding="utf-8"))
    conn.executescript((SKILL_DIR / "db" / "seed.sql").read_text(encoding="utf-8"))
    return conn


def test_demo_scenario_query_personal_schedule():
    query_events = importlib.import_module("query_events")
    conn = load_demo_db()

    payload = query_events.query_events(
        conn,
        user_id="user_001",
        starts_at="2026-05-11T00:00:00+08:00",
        ends_at="2026-05-16T00:00:00+08:00",
    )

    titles = [event["title"] for event in payload["events"]]
    assert payload["ok"] is True
    assert "Daily Standup" in titles
    assert "技術架構審查" in titles
    assert "出差拜訪客戶" in titles


def test_demo_scenario_create_meeting_with_room_and_notifications():
    create_event = importlib.import_module("create_event")
    conn = load_demo_db()

    payload = create_event.create_event(
        conn,
        creator_user_id="user_002",
        participant_user_ids=["user_003", "user_004"],
        room_id="room_B",
        title="使用者需求討論",
        description="Demo 場景二",
        starts_at="2026-05-26T14:00:00+08:00",
        ends_at="2026-05-26T15:00:00+08:00",
        dry_run_line=True,
    )

    assert payload["ok"] is True
    assert payload["event"]["room_id"] == "room_B"
    assert len(payload["notifications"]) == 2


def test_demo_scenario_cancel_meeting_with_notification():
    create_event = importlib.import_module("create_event")
    cancel_event = importlib.import_module("cancel_event")
    conn = load_demo_db()

    created = create_event.create_event(
        conn,
        creator_user_id="user_002",
        participant_user_ids=["user_003"],
        room_id="room_A",
        title="取消測試會議",
        description="Demo 場景三",
        starts_at="2026-05-26T15:00:00+08:00",
        ends_at="2026-05-26T16:00:00+08:00",
        dry_run_line=True,
    )
    event_id = created["event"]["event_id"]

    cancelled = cancel_event.cancel_event(
        conn,
        event_id=event_id,
        actor_user_id="user_002",
        dry_run_line=True,
    )

    status = conn.execute(
        "SELECT status FROM events WHERE event_id = ?",
        (event_id,),
    ).fetchone()["status"]
    assert cancelled["ok"] is True
    assert status == "cancelled"
