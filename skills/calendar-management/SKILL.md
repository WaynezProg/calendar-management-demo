---
name: calendar-management
description: Demo-only calendar management for OpenClaw Line conversations. Use for querying schedules, creating meetings, updating meetings, cancelling meetings, finding free slots, and finding available rooms in the SQLite-backed May 2026 demo calendar.
---

# Calendar Management Demo

Use this skill only for the demo calendar flow. It is backed by SQLite and does not integrate with enterprise calendar systems.

## Scope

- Query a demo user's owned and invited events.
- Create a meeting after checking participant conflicts and room availability.
- Update a meeting title, time, or room after conflict checks.
- Cancel a meeting.
- Find common free slots.
- Find available rooms.

## Hard Limits

- Do not claim this is connected to a production enterprise calendar.
- Do not promise invite accept/reject handling.
- Do not create users automatically.
- Do not run cron reminders.
- Do not treat the SQLite database as production data.

## Tool Commands

Run commands from the `skills/calendar-management` directory or pass `--db-path`.

```bash
python tools/query_events.py --db-path db/calendar.db --user-id user_001 --starts-at 2026-05-11T00:00:00+08:00 --ends-at 2026-05-16T00:00:00+08:00
```

```bash
python tools/create_event.py --db-path db/calendar.db --creator-user-id user_002 --participant-user-ids user_003,user_004 --room-id room_B --title 使用者需求討論 --description Demo --starts-at 2026-05-26T14:00:00+08:00 --ends-at 2026-05-26T15:00:00+08:00 --dry-run-line
```

```bash
python tools/cancel_event.py --db-path db/calendar.db --event-id <event_id> --actor-user-id user_002 --dry-run-line
```

## Line Push

Real Line push requires:

- `LINE_CHANNEL_ACCESS_TOKEN` in the runtime environment.
- Real Line user ids in `users.line_user_id`; the seed `Udemo*` values are placeholders.

If either is missing, use `--dry-run-line` for demo rehearsal.
