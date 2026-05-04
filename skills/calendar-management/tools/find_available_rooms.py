from __future__ import annotations

import argparse

from calendar_core import (
    CalendarError,
    connect,
    find_room_conflicts,
    json_print,
    rows_to_dicts,
)


def find_available_rooms(
    conn, starts_at: str, ends_at: str, min_capacity: int = 1
) -> dict:
    rooms = rows_to_dicts(
        conn.execute(
            """
            SELECT room_id, name, capacity, equipment
            FROM rooms
            WHERE is_active = 1 AND capacity >= ?
            ORDER BY capacity, room_id
            """,
            (min_capacity,),
        ).fetchall()
    )
    available = [
        room
        for room in rooms
        if not find_room_conflicts(conn, room["room_id"], starts_at, ends_at)
    ]
    return {"ok": True, "rooms": available}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path")
    parser.add_argument("--starts-at", required=True)
    parser.add_argument("--ends-at", required=True)
    parser.add_argument("--min-capacity", type=int, default=1)
    args = parser.parse_args()
    try:
        with connect(args.db_path) as conn:
            json_print(
                find_available_rooms(
                    conn, args.starts_at, args.ends_at, args.min_capacity
                )
            )
    except CalendarError as exc:
        json_print(exc.to_payload())


if __name__ == "__main__":
    main()
