from __future__ import annotations

import argparse
from datetime import datetime, timedelta

from calendar_core import (
    CalendarError,
    connect,
    find_user_conflicts,
    json_print,
    require_user,
)


TZ_SUFFIX = "+08:00"


def iso(day: str, hour: int, minute: int) -> str:
    return f"{day}T{hour:02d}:{minute:02d}:00{TZ_SUFFIX}"


def parse_local(value: str) -> datetime:
    return datetime.fromisoformat(value)


def find_free_slots(
    conn,
    user_ids: list[str],
    day: str,
    duration_minutes: int,
    work_start_hour: int = 9,
    work_end_hour: int = 17,
    step_minutes: int = 30,
) -> dict:
    for user_id in user_ids:
        require_user(conn, user_id)

    slots = []
    cursor = parse_local(iso(day, work_start_hour, 0))
    end_of_day = parse_local(iso(day, work_end_hour, 0))
    duration = timedelta(minutes=duration_minutes)
    step = timedelta(minutes=step_minutes)

    while cursor + duration <= end_of_day:
        starts_at = cursor.isoformat()
        ends_at = (cursor + duration).isoformat()
        if not find_user_conflicts(conn, user_ids, starts_at, ends_at):
            slots.append({"starts_at": starts_at, "ends_at": ends_at})
        cursor += step

    return {"ok": True, "slots": slots}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path")
    parser.add_argument("--user-ids", required=True, help="Comma-separated user ids")
    parser.add_argument("--day", required=True)
    parser.add_argument("--duration-minutes", type=int, required=True)
    args = parser.parse_args()
    try:
        with connect(args.db_path) as conn:
            json_print(
                find_free_slots(
                    conn,
                    args.user_ids.split(","),
                    args.day,
                    args.duration_minutes,
                )
            )
    except CalendarError as exc:
        json_print(exc.to_payload())


if __name__ == "__main__":
    main()
