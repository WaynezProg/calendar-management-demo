from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from calendar_core import CalendarError, new_id, require_user


LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def log_notification(
    conn,
    event_id: str,
    user_id: str,
    notification_type: str,
    line_user_id: str,
    message: str,
    status: str,
    error_message: str = "",
) -> None:
    conn.execute(
        """
        INSERT INTO notification_logs (
            notification_id, event_id, user_id, notification_type,
            line_user_id, message, status, error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            new_id("ntf"),
            event_id,
            user_id,
            notification_type,
            line_user_id,
            message,
            status,
            error_message,
        ),
    )


def push_to_user(
    conn,
    user_id: str,
    event_id: str,
    notification_type: str,
    message: str,
    dry_run: bool = False,
) -> dict:
    try:
        user = require_user(conn, user_id)
    except CalendarError as exc:
        return exc.to_payload()

    line_user_id = user["line_user_id"]
    if dry_run:
        log_notification(
            conn,
            event_id,
            user_id,
            notification_type,
            line_user_id,
            message,
            "dry_run",
        )
        return {"ok": True, "status": "dry_run", "line_user_id": line_user_id}

    token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    if not token:
        log_notification(
            conn,
            event_id,
            user_id,
            notification_type,
            line_user_id,
            message,
            "failed",
            "LINE_CHANNEL_ACCESS_TOKEN is not set",
        )
        return {
            "ok": False,
            "error": {
                "code": "line_token_missing",
                "message": "LINE_CHANNEL_ACCESS_TOKEN is not set",
            },
        }

    body = json.dumps(
        {"to": line_user_id, "messages": [{"type": "text", "text": message}]}
    ).encode("utf-8")
    request = urllib.request.Request(
        LINE_PUSH_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            response.read()
            status = response.status
    except urllib.error.HTTPError as exc:
        error_text = exc.read().decode("utf-8", errors="replace")
        log_notification(
            conn,
            event_id,
            user_id,
            notification_type,
            line_user_id,
            message,
            "failed",
            error_text,
        )
        return {
            "ok": False,
            "error": {
                "code": "line_push_failed",
                "message": error_text,
                "status": exc.code,
            },
        }
    except urllib.error.URLError as exc:
        error_text = str(exc.reason)
        log_notification(
            conn,
            event_id,
            user_id,
            notification_type,
            line_user_id,
            message,
            "failed",
            error_text,
        )
        return {
            "ok": False,
            "error": {"code": "line_push_failed", "message": error_text},
        }

    log_notification(
        conn,
        event_id,
        user_id,
        notification_type,
        line_user_id,
        message,
        "sent",
    )
    return {
        "ok": True,
        "status": "sent",
        "http_status": status,
        "line_user_id": line_user_id,
    }
