# src/event_store/repository.py
#
# All database operations for play events.
# Write events in, read them back out in useful shapes.

import sqlite3
from datetime import datetime
from typing import Optional
from src.event_store.models import PlayEvent, EventType


def record_event(conn: sqlite3.Connection, event: PlayEvent) -> None:
    """
    Write one event to the database.
    This is called every time the user does anything — play, skip, etc.
    It should be fast and never fail silently.
    """
    if event.event_type not in EventType.ALL:
        raise ValueError(
            f"Invalid event type: '{event.event_type}'. "
            f"Must be one of: {EventType.ALL}"
        )

    conn.execute(
        """
        INSERT INTO events
            (id, song_id, event_type, timestamp,
             session_id, play_duration_ms, song_duration_ms)
        VALUES
            (:id, :song_id, :event_type, :timestamp,
             :session_id, :play_duration_ms, :song_duration_ms)
        """,
        event.to_db_row()
    )
    conn.commit()


def get_recent_events(
    conn: sqlite3.Connection,
    limit: int = 50
) -> list[PlayEvent]:
    """
    Fetch the most recent N events across all songs.
    Used by the scorer to calculate recency penalties —
    songs played recently should score lower.
    """
    rows = conn.execute(
        """
        SELECT * FROM events
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    return [PlayEvent.from_db_row(row) for row in rows]


def get_events_for_song(
    conn: sqlite3.Connection,
    song_id: str
) -> list[PlayEvent]:
    """
    Fetch all events for one specific song.
    Used by the preference model to calculate
    that song's weight from its full history.
    """
    rows = conn.execute(
        """
        SELECT * FROM events
        WHERE song_id = ?
        ORDER BY timestamp DESC
        """,
        (song_id,)
    ).fetchall()
    return [PlayEvent.from_db_row(row) for row in rows]


def get_recently_played_song_ids(
    conn: sqlite3.Connection,
    limit: int = 10
) -> list[str]:
    """
    Return the IDs of the last N songs that were played.
    The scorer uses this list to apply a strong recency
    penalty — we never want the same song twice in a row,
    and songs played recently should surface less often.
    """
    rows = conn.execute(
        """
        SELECT DISTINCT song_id FROM events
        WHERE event_type IN ('play', 'complete')
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    return [row["song_id"] for row in rows]


def get_session_events(
    conn: sqlite3.Connection,
    session_id: str
) -> list[PlayEvent]:
    """
    Fetch all events from one listening session.
    Sessions group behaviour by context — what you
    listened to at 2am is different from 8am.
    """
    rows = conn.execute(
        """
        SELECT * FROM events
        WHERE session_id = ?
        ORDER BY timestamp ASC
        """,
        (session_id,)
    ).fetchall()
    return [PlayEvent.from_db_row(row) for row in rows]


def count_events_by_type(
    conn: sqlite3.Connection,
    song_id: str
) -> dict[str, int]:
    """
    Return a summary of how many times each event type
    occurred for a given song.

    Example return value:
        {'play': 12, 'skip': 3, 'complete': 8, 'replay': 1}

    The preference model uses these counts to calculate
    the skip ratio and overall preference weight.
    """
    rows = conn.execute(
        """
        SELECT event_type, COUNT(*) as count
        FROM events
        WHERE song_id = ?
        GROUP BY event_type
        """,
        (song_id,)
    ).fetchall()

    # Start with zeros for all types so the caller
    # never has to check if a key exists
    counts = {t: 0 for t in EventType.ALL}
    for row in rows:
        counts[row["event_type"]] = row["count"]
    return counts