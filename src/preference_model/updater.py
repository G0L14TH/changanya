# src/preference_model/updater.py
#
# Writes calculated weights back to the database.
# Called after every event so the scorer always
# reads fresh weights.

import sqlite3
from datetime import datetime
from src.preference_model.calculator import calculate_song_weight
from src.event_store.models import EventType
from src.event_store.repository import (
    record_event, count_events_by_type
)


def update_song_weight(
    conn: sqlite3.Connection,
    song_id: str
) -> float:
    """
    Recalculate and persist the weight for one song.
    Returns the new weight so the caller can log it.

    Call this immediately after recording any event
    for this song — keeps the weights always current.
    """
    now = datetime.now()
    new_weight = calculate_song_weight(conn, song_id, now)
    counts = count_events_by_type(conn, song_id)

    skip_count  = counts[EventType.SKIP]
    play_count  = counts[EventType.PLAY]
    complete    = counts[EventType.COMPLETE]
    total_plays = play_count + complete

    skip_ratio = (
        skip_count / (total_plays + skip_count)
        if (total_plays + skip_count) > 0
        else 0.0
    )

    conn.execute(
        """
        INSERT INTO song_weights
            (song_id, weight, skip_ratio, play_count,
             skip_count, last_updated)
        VALUES
            (:song_id, :weight, :skip_ratio, :play_count,
             :skip_count, :last_updated)
        ON CONFLICT(song_id) DO UPDATE SET
            weight       = excluded.weight,
            skip_ratio   = excluded.skip_ratio,
            play_count   = excluded.play_count,
            skip_count   = excluded.skip_count,
            last_updated = excluded.last_updated
        """,
        {
            "song_id":      song_id,
            "weight":       new_weight,
            "skip_ratio":   skip_ratio,
            "play_count":   total_plays,
            "skip_count":   skip_count,
            "last_updated": now.isoformat(),
        }
    )
    conn.commit()
    return new_weight


def get_song_weight(
    conn: sqlite3.Connection,
    song_id: str,
    default: float = 1.0
) -> float:
    """
    Read the stored weight for a song.
    Returns default if no weight has been calculated yet.
    The scorer calls this for every candidate song.
    """
    row = conn.execute(
        "SELECT weight FROM song_weights WHERE song_id = ?",
        (song_id,)
    ).fetchone()

    return row["weight"] if row else default