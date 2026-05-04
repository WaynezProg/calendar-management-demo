from __future__ import annotations

import argparse

from calendar_core import (
    CalendarError,
    connect,
    find_room_conflicts,
    find_user_conflicts,
    json_print,
    require_room,
    rows_to_dicts,
)


def get_event(conn, event_id: str) -> dict | None:
    rows = rows_to_dicts(
        conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchall()
    )
    return rows[0] if rows else None


def update_event(
    conn,
    event_id: str,
    actor_user_id: str,
    title: str,
    room_id: str | None,
    starts_at: str,
    ends_at: str,
) -> dict:
    try:
        event = get_event(conn, event_id)
        if not event or event["status"] != "active":
            raise CalendarError(
                "event_not_found",
                f"找不到可修改事件：{event_id}",
                {"event_id": event_id},
            )
        if event["creator_user_id"] != actor_user_id:
            raise CalendarError(
                "not_event_creator",
                "只有發起人可修改 demo 會議",
                {"actor_user_id": actor_user_id},
            )
        if room_id:
            require_room(conn, room_id)

        participants = [
            row["user_id"]
            for row in conn.execute(
                "SELECT user_id FROM event_participants WHERE event_id = ?",
                (event_id,),
            ).fetchall()
        ]
        user_conflicts = find_user_conflicts(
            conn,
            participants,
            starts_at,
            ends_at,
            exclude_event_id=event_id,
        )
        if user_conflicts:
            raise CalendarError(
                "participant_conflict",
                "參與者時段衝突",
                {"conflicts": user_conflicts},
            )
        if room_id:
            room_conflicts = find_room_conflicts(
                conn,
                room_id,
                starts_at,
                ends_at,
                exclude_event_id=event_id,
            )
            if room_conflicts:
                raise CalendarError(
                    "room_conflict",
                    "會議室時段衝突",
                    {"conflicts": room_conflicts},
                )

        conn.execute(
            """
            UPDATE events
            SET title = ?, room_id = ?, starts_at = ?, ends_at = ?, updated_at = datetime('now')
            WHERE event_id = ?
            """,
            (title, room_id, starts_at, ends_at, event_id),
        )
        conn.commit()
        return {"ok": True, "event": get_event(conn, event_id)}
    except CalendarError as exc:
        conn.rollback()
        return exc.to_payload()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path")
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--actor-user-id", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--room-id")
    parser.add_argument("--starts-at", required=True)
    parser.add_argument("--ends-at", required=True)
    args = parser.parse_args()
    with connect(args.db_path) as conn:
        json_print(
            update_event(
                conn,
                args.event_id,
                args.actor_user_id,
                args.title,
                args.room_id,
                args.starts_at,
                args.ends_at,
            )
        )


if __name__ == "__main__":
    main()
