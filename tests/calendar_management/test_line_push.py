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


def test_line_push_dry_run_logs_notification():
    line_push = importlib.import_module("line_push")
    conn = load_demo_db()

    payload = line_push.push_to_user(
        conn,
        user_id="user_002",
        event_id="evt_20260511_arch",
        notification_type="invitation",
        message="測試通知",
        dry_run=True,
    )

    assert payload["ok"] is True
    assert payload["status"] == "dry_run"
    count = conn.execute("SELECT COUNT(*) FROM notification_logs").fetchone()[0]
    assert count == 1


def test_line_push_missing_mapping_returns_error_payload():
    line_push = importlib.import_module("line_push")
    conn = load_demo_db()

    payload = line_push.push_to_user(
        conn,
        user_id="user_missing",
        event_id="evt_20260511_arch",
        notification_type="invitation",
        message="測試通知",
        dry_run=True,
    )

    assert payload["ok"] is False
    assert payload["error"]["code"] == "user_not_found"
