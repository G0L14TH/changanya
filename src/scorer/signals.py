from src.catalog.models import Song
from src.scorer.models import ScoringContext
from src.preference_model.updater import get_song_weight
import sqlite3


def preference_signal(
    conn: sqlite3.Connection,
    song: Song,
) -> float:
    """
    How much does this user enjoy this song historically?
    Reads from song_weights table which already calculated by
    the preference model after each event.

    Returns the raw weight (not clamped to 0-1 because
    the scorer uses it as a multiplier, not just a factor).
    """
    return get_song_weight(conn, song.id, default=1.0)


def recency_signal(
    song: Song,
    context: ScoringContext,
    strong_penalty_count: int = 3,
    soft_penalty_count: int = 10,
) -> float:
    """
    How long ago was this song last played?

    Uses position in the recently_played_ids list:
        - In last 3 songs → score near 0.0 (strong penalty)
        - In last 10 songs → score 0.0 to 0.7 (graduated penalty)
        - Not in recent history → score 1.0 (no penalty)

    Position-based rather than time-based because it works
    correctly regardless of how fast the user is listening.
    """
    try:
        position = context.recently_played_ids.index(song.id)
    except ValueError:
        return 1.0  # Not in recent history — no penalty

    if position < strong_penalty_count:
        # Played very recently — almost zero chance of replaying
        return position / strong_penalty_count * 0.2

    if position < soft_penalty_count:
        # Played somewhat recently — graduated penalty
        progress = (position - strong_penalty_count) / (
            soft_penalty_count - strong_penalty_count
        )
        return 0.2 + progress * 0.8

    return 1.0


def artist_spacing_signal(
    song: Song,
    context: ScoringContext,
    max_recent: int = 3,
) -> float:
    """
    How recently was this artist played?

    If you've heard 3 songs from this artist in the
    last 10 tracks, this signal will push them down
    regardless of how much you like their songs.

    This prevents the "plays one artist all night"
    problem that plagues naive shuffle algorithms.
    """
    if song.artist is None:
        return 1.0  # No artist info — no penalty

    recent_by_artist = context.recent_artist_plays.get(song.artist, [])
    count = len(recent_by_artist)

    if count == 0:
        return 1.0
    if count >= max_recent:
        return 0.1  # Too many recent plays from this artist

    # Graduated penalty based on how many recent plays
    return 1.0 - (count / max_recent) * 0.9


def genre_diversity_signal(
    song: Song,
    context: ScoringContext,
) -> float:
    """
    Has this genre been dominating recently?

    A gentle diversity nudge. If 8 of the last 10 songs
    were Rock, this pushes non-Rock songs slightly higher.
    Not strong enough to force genre changes — just enough
    to encourage variety over long sessions.
    """
    if song.genre is None:
        return 1.0  # No genre info — neutral

    genre_count = context.recent_genre_counts.get(song.genre, 0)
    total = context.context_window_size

    if total == 0:
        return 1.0

    dominance = genre_count / total  # 0.0 to 1.0

    # If this genre is 80%+ of recent plays, apply a penalty
    if dominance > 0.8:
        return 0.3
    if dominance > 0.5:
        return 0.7

    return 1.0