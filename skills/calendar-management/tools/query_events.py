from __future__ import annotations

import argparse

from calendar_core import CalendarError, connect, json_print, require_user, rows_to_dicts


def query_events(conn, user_id: str, starts_at: str, ends_at: str) -> dict:
    require_user(conn, user_id)
    rows = conn.execute(
        """
        SELECT
            e.event_id,
            e.title,
            e.description,
            e.starts_at,
            e.ends_at,
            e.room_id,
            r.name AS room_name,
            e.creator_user_id,
            ep.response_status
        FROM events e
        JOIN event_participants ep ON ep.event_id = e.event_id
        LEFT JOIN rooms r ON r.room_id = e.room_id
        WHERE ep.user_id = ?
          AND e.status = 'active'
          AND e.starts_at >= ?
          AND e.starts_at < ?
        ORDER BY e.starts_at, e.ends_at
        """,
        (user_id, starts_at, ends_at),
    ).fetchall()
    return {"ok": True, "events": rows_to_dicts(rows)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--starts-at", required=True)
    parser.add_argument("--ends-at", required=True)
    args = parser.parse_args()
    try:
        with connect(args.db_path) as conn:
            json_print(query_events(conn, args.user_id, args.starts_at, args.ends_at))
    except CalendarError as exc:
        json_print(exc.to_payload())


if __name__ == "__main__":
    main()
