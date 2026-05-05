PRAGMA foreign_keys = ON;

CREATE TABLE users (
    user_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    english_name TEXT NOT NULL,
    department TEXT NOT NULL,
    line_user_id TEXT UNIQUE NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'Asia/Taipei',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE rooms (
    room_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    equipment TEXT NOT NULL DEFAULT '',
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1))
);

CREATE TABLE calendars (
    calendar_id TEXT PRIMARY KEY,
    owner_type TEXT NOT NULL CHECK (owner_type IN ('user', 'room')),
    owner_id TEXT NOT NULL,
    name TEXT NOT NULL,
    timezone TEXT NOT NULL DEFAULT 'Asia/Taipei',
    UNIQUE(owner_type, owner_id)
);

CREATE TABLE events (
    event_id TEXT PRIMARY KEY,
    calendar_id TEXT NOT NULL REFERENCES calendars(calendar_id),
    creator_user_id TEXT NOT NULL REFERENCES users(user_id),
    room_id TEXT REFERENCES rooms(room_id),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    starts_at TEXT NOT NULL,
    ends_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (starts_at < ends_at)
);

CREATE TABLE event_participants (
    event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    role TEXT NOT NULL DEFAULT 'attendee' CHECK (role IN ('organizer', 'attendee')),
    response_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (response_status IN ('pending', 'accepted', 'declined', 'tentative')),
    PRIMARY KEY (event_id, user_id)
);

CREATE TABLE notification_logs (
    notification_id TEXT PRIMARY KEY,
    event_id TEXT REFERENCES events(event_id),
    user_id TEXT REFERENCES users(user_id),
    notification_type TEXT NOT NULL CHECK (notification_type IN ('invitation', 'update', 'cancellation')),
    line_user_id TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('sent', 'dry_run', 'failed')),
    error_message TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX idx_events_starts_at ON events(starts_at);
CREATE INDEX idx_events_room_time ON events(room_id, starts_at, ends_at);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_participants_user ON event_participants(user_id);
CREATE INDEX idx_notifications_event ON notification_logs(event_id);
