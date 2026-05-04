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


def test_core_returns_user_and_detects_missing_mapping():
    core = importlib.import_module("calendar_core")
    conn = load_demo_db()

    assert core.get_user(conn, "user_001")["display_name"] == "王大明"
    assert core.get_user(conn, "user_missing") is None


def test_core_detects_user_conflict():
    core = importlib.import_module("calendar_core")
    conn = load_demo_db()

    conflicts = core.find_user_conflicts(
        conn,
        ["user_001"],
        "2026-05-11T10:30:00+08:00",
        "2026-05-11T11:00:00+08:00",
    )

    assert conflicts[0]["user_id"] == "user_001"
    assert conflicts[0]["title"] == "技術架構審查"


def test_core_detects_room_conflict():
    core = importlib.import_module("calendar_core")
    conn = load_demo_db()

    conflicts = core.find_room_conflicts(
        conn,
        "room_B",
        "2026-05-25T14:00:00+08:00",
        "2026-05-25T15:00:00+08:00",
    )

    assert conflicts[0]["event_id"] == "evt_20260525_team_sync"


def test_query_events_returns_owned_and_invited_events():
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
    assert "市場需求對齊" in titles
