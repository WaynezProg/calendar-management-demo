# Calendar Management Demo Skill

Use this skill only for demo calendar actions inside OpenClaw.

## Scope

- Query personal schedule.
- Create meeting after checking participant free time and room availability.
- Update meeting title, time, or room.
- Cancel meeting.
- Find free slots.
- Find available rooms.

## Hard Limits

- Do not claim integration with enterprise calendar systems.
- Do not promise invite acceptance or rejection handling.
- Do not create new users automatically.
- Do not run cron reminders.
- Do not expose this SQLite data as production data.

## Required Behavior

If a user mapping is missing, explain that the demo user registry does not contain that user. If a room is missing, show available rooms. If a time conflict exists, return the conflicting event and ask for a different time. For meeting create and cancel actions, send Line push notification through the tool result path.
