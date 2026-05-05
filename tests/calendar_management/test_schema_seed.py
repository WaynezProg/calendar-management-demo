import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "skills" / "calendar-management"
INIT_SQL = SKILL_DIR / "db" / "init.sql"
SEED_SQL = SKILL_DIR / "db" / "seed.sql"


def load_demo_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(INIT_SQL.read_text(encoding="utf-8"))
    conn.executescript(SEED_SQL.read_text(encoding="utf-8"))
    return conn


def test_schema_creates_required_tables():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(INIT_SQL.read_text(encoding="utf-8"))

    tables = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }

    assert tables >= {
        "users",
        "rooms",
        "calendars",
        "events",
        "event_participants",
        "notification_logs",
    }


def test_seed_has_demo_users_rooms_and_may_events():
    conn = load_demo_db()

    assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 7
    assert conn.execute("SELECT COUNT(*) FROM rooms").fetchone()[0] == 2
    assert conn.execute(
        "SELECT COUNT(*) FROM events WHERE starts_at >= '2026-05-01T00:00:00+08:00' "
        "AND starts_at < '2026-06-01T00:00:00+08:00'"
    ).fetchone()[0] >= 12


def test_seed_users_have_english_names():
    conn = load_demo_db()

    rows = conn.execute(
        "SELECT user_id, display_name, english_name FROM users ORDER BY user_id"
    ).fetchall()

    assert len(rows) == 7
    assert rows[0]["display_name"] == "王大明"
    assert rows[0]["english_name"] == "David Wang"
    assert all(row["english_name"] for row in rows)


def test_seed_can_query_user_owned_and_invited_events():
    conn = load_demo_db()

    rows = conn.execute(
        """
        SELECT e.title
        FROM events e
        JOIN event_participants ep ON ep.event_id = e.event_id
        WHERE ep.user_id = 'user_001'
          AND e.starts_at >= '2026-05-11T00:00:00+08:00'
          AND e.starts_at < '2026-05-16T00:00:00+08:00'
          AND e.status = 'active'
        ORDER BY e.starts_at
        """
    ).fetchall()

    titles = [row["title"] for row in rows]
    assert "Daily Standup" in titles
    assert "技術架構審查" in titles
    assert "市場需求對齊" in titles
