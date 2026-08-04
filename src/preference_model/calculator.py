import sqlite3
from datetime import datetime
from src.event_store.models import EventType
from src.event_store.repository import get_events_for_song
from src.preference_model.decay import exponential_decay

EVENT_SCORES = {
    EventType.COMPLETE: +0.3,   # finished the song — positive
    EventType.REPLAY:   +0.6,   # went back to hear it again — very positive
    EventType.PLAY:     +0.0,   # neutral — just started it
    EventType.SKIP:     -0.4,   # skipped — negative, but we'll refine by duration
}

MIN_WEIGHT = 0.05
MAX_WEIGHT = 5.0
DEFAULT_WEIGHT = 1.0


def calculate_song_weight(
    conn: sqlite3.Connection,
    song_id: str,
    now: datetime | None = None,
    half_life_days: float = 30.0
) -> float:
    """
    Read a song's full event history and return its current weight.

    The weight is a single float that summarises this user's
    relationship with this song right now:
        < 1.0 → they tend to skip it
        = 1.0 → unknown or neutral
        > 1.0 → they tend to enjoy or replay it

    The calculation works in three steps:
        1. Load all events for this song
        2. Score each event, scaled by how recent it was
        3. Apply the skip ratio as an additional penalty
    """
    if now is None:
        now = datetime.now()

    events = get_events_for_song(conn, song_id)

    if not events:
        return DEFAULT_WEIGHT

    weight = DEFAULT_WEIGHT
    play_count = 0
    skip_count = 0

    for event in events:
        # How much does this event still matter given its age?
        decay = exponential_decay(event.timestamp, now, half_life_days)

        # Base score for this event type
        base_score = EVENT_SCORES.get(event.event_type, 0.0)
        
        if event.event_type == EventType.SKIP:
            ratio = event.completion_ratio
            if ratio is not None:
                if ratio < 0.05:
                    base_score = -0.8   # skipped in first 5% → strong dislike
                elif ratio < 0.25:
                    base_score = -0.5   # skipped in first quarter → dislike
                elif ratio < 0.75:
                    base_score = -0.3   # skipped in second half → mild dislike
                else:
                    base_score = -0.1   # almost finished → barely counts

        # Apply decay — old events contribute less
        weight += base_score * decay

        # Track counts for skip ratio calculation
        if event.event_type in (EventType.PLAY, EventType.COMPLETE, EventType.REPLAY):
            play_count += 1
        if event.event_type == EventType.SKIP:
            skip_count += 1

    # Apply skip ratio penalty on top of the event-based weight.
    # A song with a high skip rate gets an additional downward pull
    # regardless of how old or new those skips are.
    total = play_count + skip_count
    if total > 0:
        skip_ratio = skip_count / total
        if skip_ratio > 0.6:
            # More than 60% skips — apply a meaningful penalty
            weight *= (1.0 - (skip_ratio - 0.6))

    # Clamp to valid range
    return max(MIN_WEIGHT, min(MAX_WEIGHT, weight))