from __future__ import annotations

import argparse

from calendar_core import CalendarError, connect, json_print, rows_to_dicts
from line_push import push_to_user


def get_active_event(conn, event_id: str) -> dict | None:
    rows = rows_to_dicts(
        conn.execute(
            "SELECT * FROM events WHERE event_id = ? AND status = 'active'",
            (event_id,),
        ).fetchall()
    )
    return rows[0] if rows else None


def cancel_event(conn, event_id: str, actor_user_id: str, dry_run_line: bool = False) -> dict:
    try:
        event = get_active_event(conn, event_id)
        if not event:
            raise CalendarError(
                "event_not_found",
                f"找不到可取消事件：{event_id}",
                {"event_id": event_id},
            )
        if event["creator_user_id"] != actor_user_id:
            raise CalendarError(
                "not_event_creator",
                "只有發起人可取消 demo 會議",
                {"actor_user_id": actor_user_id},
            )

        conn.execute(
            "UPDATE events SET status = 'cancelled', updated_at = datetime('now') WHERE event_id = ?",
            (event_id,),
        )
        attendee_ids = [
            row["user_id"]
            for row in conn.execute(
                "SELECT user_id FROM event_participants WHERE event_id = ? AND user_id <> ?",
                (event_id, actor_user_id),
            ).fetchall()
        ]
        message = f"會議取消：{event['title']}\n原時間：{event['starts_at']} - {event['ends_at']}"
        notifications = [
            push_to_user(
                conn,
                user_id,
                event_id,
                "cancellation",
                message,
                dry_run=dry_run_line,
            )
            for user_id in attendee_ids
        ]
        conn.commit()
        return {"ok": True, "event_id": event_id, "notifications": notifications}
    except CalendarError as exc:
        conn.rollback()
        return exc.to_payload()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path")
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--actor-user-id", required=True)
    parser.add_argument("--dry-run-line", action="store_true")
    args = parser.parse_args()
    with connect(args.db_path) as conn:
        json_print(cancel_event(conn, args.event_id, args.actor_user_id, args.dry_run_line))


if __name__ == "__main__":
    main()
