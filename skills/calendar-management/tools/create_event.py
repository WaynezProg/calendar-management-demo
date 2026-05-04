from __future__ import annotations

import argparse

from calendar_core import (
    CalendarError,
    connect,
    find_room_conflicts,
    find_user_conflicts,
    get_user_calendar_id,
    json_print,
    new_id,
    require_room,
    require_user,
)
from line_push import push_to_user


def create_event(
    conn,
    creator_user_id: str,
    participant_user_ids: list[str],
    room_id: str | None,
    title: str,
    description: str,
    starts_at: str,
    ends_at: str,
    dry_run_line: bool = False,
) -> dict:
    try:
        require_user(conn, creator_user_id)
        for user_id in participant_user_ids:
            require_user(conn, user_id)
        if room_id:
            require_room(conn, room_id)

        all_user_ids = [creator_user_id, *participant_user_ids]
        user_conflicts = find_user_conflicts(conn, all_user_ids, starts_at, ends_at)
        if user_conflicts:
            raise CalendarError(
                "participant_conflict",
                "參與者時段衝突",
                {"conflicts": user_conflicts},
            )

        if room_id:
            room_conflicts = find_room_conflicts(conn, room_id, starts_at, ends_at)
            if room_conflicts:
                raise CalendarError(
                    "room_conflict",
                    "會議室時段衝突",
                    {"conflicts": room_conflicts},
                )

        event_id = new_id("evt")
        calendar_id = get_user_calendar_id(conn, creator_user_id)
        conn.execute(
            """
            INSERT INTO events (
                event_id, calendar_id, creator_user_id, room_id,
                title, description, starts_at, ends_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                calendar_id,
                creator_user_id,
                room_id,
                title,
                description,
                starts_at,
                ends_at,
            ),
        )
        conn.execute(
            "INSERT INTO event_participants (event_id, user_id, role, response_status) VALUES (?, ?, 'organizer', 'accepted')",
            (event_id, creator_user_id),
        )
        for user_id in participant_user_ids:
            conn.execute(
                "INSERT INTO event_participants (event_id, user_id, role, response_status) VALUES (?, ?, 'attendee', 'pending')",
                (event_id, user_id),
            )

        notifications = []
        message = f"會議邀請：{title}\n時間：{starts_at} - {ends_at}"
        for user_id in participant_user_ids:
            notifications.append(
                push_to_user(
                    conn,
                    user_id,
                    event_id,
                    "invitation",
                    message,
                    dry_run=dry_run_line,
                )
            )

        conn.commit()
        return {
            "ok": True,
            "event": {
                "event_id": event_id,
                "title": title,
                "starts_at": starts_at,
                "ends_at": ends_at,
                "room_id": room_id,
                "participants": all_user_ids,
            },
            "notifications": notifications,
        }
    except CalendarError as exc:
        conn.rollback()
        return exc.to_payload()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path")
    parser.add_argument("--creator-user-id", required=True)
    parser.add_argument("--participant-user-ids", default="")
    parser.add_argument("--room-id")
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--starts-at", required=True)
    parser.add_argument("--ends-at", required=True)
    parser.add_argument("--dry-run-line", action="store_true")
    args = parser.parse_args()
    with connect(args.db_path) as conn:
        json_print(
            create_event(
                conn,
                args.creator_user_id,
                [value for value in args.participant_user_ids.split(",") if value],
                args.room_id,
                args.title,
                args.description,
                args.starts_at,
                args.ends_at,
                args.dry_run_line,
            )
        )


if __name__ == "__main__":
    main()
