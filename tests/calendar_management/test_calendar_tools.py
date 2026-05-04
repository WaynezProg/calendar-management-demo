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


def test_find_available_rooms_excludes_conflicting_room():
    find_available_rooms = importlib.import_module("find_available_rooms")
    conn = load_demo_db()

    payload = find_available_rooms.find_available_rooms(
        conn,
        starts_at="2026-05-25T14:00:00+08:00",
        ends_at="2026-05-25T15:00:00+08:00",
        min_capacity=4,
    )

    room_ids = [room["room_id"] for room in payload["rooms"]]
    assert payload["ok"] is True
    assert "room_A" in room_ids
    assert "room_B" not in room_ids


def test_find_free_slots_returns_open_slot_for_participants():
    find_free_slots = importlib.import_module("find_free_slots")
    conn = load_demo_db()

    payload = find_free_slots.find_free_slots(
        conn,
        user_ids=["user_002", "user_003", "user_004"],
        day="2026-05-26",
        duration_minutes=60,
    )

    slots = [(slot["starts_at"], slot["ends_at"]) for slot in payload["slots"]]
    assert payload["ok"] is True
    assert ("2026-05-26T14:00:00+08:00", "2026-05-26T15:00:00+08:00") in slots


def test_create_event_writes_event_participants_and_notifications():
    create_event = importlib.import_module("create_event")
    conn = load_demo_db()

    payload = create_event.create_event(
        conn,
        creator_user_id="user_002",
        participant_user_ids=["user_003", "user_004"],
        room_id="room_B",
        title="使用者需求討論",
        description="Demo 建立會議",
        starts_at="2026-05-26T14:00:00+08:00",
        ends_at="2026-05-26T15:00:00+08:00",
        dry_run_line=True,
    )

    assert payload["ok"] is True
    event_id = payload["event"]["event_id"]
    participant_count = conn.execute(
        "SELECT COUNT(*) FROM event_participants WHERE event_id = ?",
        (event_id,),
    ).fetchone()[0]
    notification_count = conn.execute(
        "SELECT COUNT(*) FROM notification_logs WHERE event_id = ?",
        (event_id,),
    ).fetchone()[0]
    assert participant_count == 3
    assert notification_count == 2


def test_create_event_rejects_participant_conflict():
    create_event = importlib.import_module("create_event")
    conn = load_demo_db()

    payload = create_event.create_event(
        conn,
        creator_user_id="user_002",
        participant_user_ids=["user_001"],
        room_id="room_A",
        title="衝突會議",
        description="Demo 衝突",
        starts_at="2026-05-11T10:30:00+08:00",
        ends_at="2026-05-11T11:00:00+08:00",
        dry_run_line=True,
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "participant_conflict"
