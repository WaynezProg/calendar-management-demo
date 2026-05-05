from __future__ import annotations

import json
import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any


SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = SKILL_DIR / "db" / "calendar.db"


class CalendarError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            },
        }


def connect(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path or os.environ.get("CALENDAR_DB_PATH", DEFAULT_DB_PATH))
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [row_to_dict(row) for row in rows]


def json_print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def get_user(conn: sqlite3.Connection, user_id: str) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT * FROM users WHERE user_id = ? AND is_active = 1",
        (user_id,),
    ).fetchone()
    return row_to_dict(row) if row else None


def require_user(conn: sqlite3.Connection, user_id: str) -> dict[str, Any]:
    user = get_user(conn, user_id)
    if not user:
        raise CalendarError(
            "user_not_found",
            f"找不到使用者 mapping：{user_id}",
            {"user_id": user_id},
        )
    return user


def require_room(conn: sqlite3.Connection, room_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM rooms WHERE room_id = ? AND is_active = 1",
        (room_id,),
    ).fetchone()
    if not row:
        rooms = rows_to_dicts(
            conn.execute(
                "SELECT room_id, name, capacity FROM rooms WHERE is_active = 1"
            ).fetchall()
        )
        raise CalendarError(
            "room_not_found",
            f"找不到會議室：{room_id}",
            {"available_rooms": rooms},
        )
    return row_to_dict(row)


def get_user_calendar_id(conn: sqlite3.Connection, user_id: str) -> str:
    row = conn.execute(
        "SELECT calendar_id FROM calendars WHERE owner_type = 'user' AND owner_id = ?",
        (user_id,),
    ).fetchone()
    if not row:
        raise CalendarError(
            "calendar_not_found",
            f"找不到使用者行事曆：{user_id}",
            {"user_id": user_id},
        )
    return str(row["calendar_id"])


def overlaps_sql() -> str:
    return "e.starts_at < ? AND e.ends_at > ?"


def find_user_conflicts(
    conn: sqlite3.Connection,
    user_ids: list[str],
    starts_at: str,
    ends_at: str,
    exclude_event_id: str | None = None,
) -> list[dict[str, Any]]:
    if not user_ids:
        return []
    placeholders = ",".join("?" for _ in user_ids)
    params: list[Any] = [ends_at, starts_at, *user_ids]
    exclude_clause = ""
    if exclude_event_id:
        exclude_clause = "AND e.event_id <> ?"
        params.append(exclude_event_id)
    rows = conn.execute(
        f"""
        SELECT ep.user_id, u.display_name, u.english_name, e.event_id, e.title, e.starts_at, e.ends_at
        FROM events e
        JOIN event_participants ep ON ep.event_id = e.event_id
        JOIN users u ON u.user_id = ep.user_id
        WHERE e.status = 'active'
          AND {overlaps_sql()}
          AND ep.user_id IN ({placeholders})
          {exclude_clause}
        ORDER BY e.starts_at
        """,
        params,
    ).fetchall()
    return rows_to_dicts(rows)


def find_room_conflicts(
    conn: sqlite3.Connection,
    room_id: str,
    starts_at: str,
    ends_at: str,
    exclude_event_id: str | None = None,
) -> list[dict[str, Any]]:
    params: list[Any] = [room_id, ends_at, starts_at]
    exclude_clause = ""
    if exclude_event_id:
        exclude_clause = "AND e.event_id <> ?"
        params.append(exclude_event_id)
    rows = conn.execute(
        f"""
        SELECT e.event_id, e.title, e.starts_at, e.ends_at, e.room_id
        FROM events e
        WHERE e.status = 'active'
          AND e.room_id = ?
          AND {overlaps_sql()}
          {exclude_clause}
        ORDER BY e.starts_at
        """,
        params,
    ).fetchall()
    return rows_to_dicts(rows)
