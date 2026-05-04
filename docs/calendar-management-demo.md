# Calendar Management Demo

## Purpose

This is a demo-only OpenClaw calendar-management skill. It uses SQLite data seeded for May 2026 and proves OpenClaw can operate a simple calendar flow through Line. It is not connected to enterprise calendar systems.

## Setup

```bash
rm -f skills/calendar-management/db/calendar.db
sqlite3 skills/calendar-management/db/calendar.db < skills/calendar-management/db/init.sql
sqlite3 skills/calendar-management/db/calendar.db < skills/calendar-management/db/seed.sql
```

For real Line push, replace the placeholder `Udemo*` values in `skills/calendar-management/db/seed.sql` or the runtime `users.line_user_id` rows with real Line user ids, then set:

```bash
export LINE_CHANNEL_ACCESS_TOKEN="<channel-access-token>"
```

## Demo Users

- `user_001`: 王大明
- `user_002`: 李小美
- `user_003`: 張小志
- `user_004`: 陳小鳳
- `user_005`: 林志強
- `user_006`: 黃雅婷
- `user_007`: 趙建宏

## Demo Scenarios

### 1. Query Schedule

Ask OpenClaw to query `user_001` schedule from `2026-05-11` to `2026-05-15`.

Expected result includes `Daily Standup`, `技術架構審查`, `出差拜訪客戶`, and `市場需求對齊`.

### 2. Create Meeting

Ask OpenClaw to create `使用者需求討論` for `user_002`, `user_003`, and `user_004` in `room_B` at `2026-05-26 14:00-15:00`.

Expected result: event is created, room is booked, and Line push notification is sent to attendees when real Line user ids and token are configured.

### 3. Cancel Meeting

Ask OpenClaw to cancel the meeting created in scenario 2.

Expected result: event status becomes `cancelled`, and Line cancellation notice is sent to attendees when real Line user ids and token are configured.

## CLI Smoke

Query:

```bash
python skills/calendar-management/tools/query_events.py \
  --db-path skills/calendar-management/db/calendar.db \
  --user-id user_001 \
  --starts-at 2026-05-11T00:00:00+08:00 \
  --ends-at 2026-05-16T00:00:00+08:00
```

Create meeting with dry-run Line notification:

```bash
python skills/calendar-management/tools/create_event.py \
  --db-path skills/calendar-management/db/calendar.db \
  --creator-user-id user_002 \
  --participant-user-ids user_003,user_004 \
  --room-id room_B \
  --title 使用者需求討論 \
  --description Demo \
  --starts-at 2026-05-26T14:00:00+08:00 \
  --ends-at 2026-05-26T15:00:00+08:00 \
  --dry-run-line
```

## Scope Guard

This demo does not support enterprise calendar sync, invite reply handling, cron reminders, recurring event management, or automatic user creation.
