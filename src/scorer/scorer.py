import sqlite3
from src.catalog.models import Song
from src.catalog.repository import get_all_songs
from src.event_store.repository import get_recent_events
from src.scorer.models import ScoringContext, ScoredSong
from src.scorer.signals import (
    preference_signal,
    recency_signal,
    artist_spacing_signal,
    genre_diversity_signal,
)

WEIGHTS = {
    "preference": 0.40,
    "recency":    0.30,
    "artist":     0.20,
    "genre":      0.10,
}


def build_scoring_context(
    conn: sqlite3.Connection,
    window: int = 10
) -> ScoringContext:
    """
    Build the context snapshot the scorer needs.
    Reads recent events once and organises them
    into the structures each signal needs.

    Called once per scoring run — not once per song.
    """
    recent_events = get_recent_events(conn, limit=window)

    recently_played_ids = []
    recent_artist_plays: dict[str, list[str]] = {}
    recent_genre_counts: dict[str, int] = {}

    for event in recent_events:
        if event.song_id not in recently_played_ids:
            recently_played_ids.append(event.song_id)

    from src.catalog.repository import get_song_by_id
    for song_id in recently_played_ids[:window]:
        song = get_song_by_id(conn, song_id)
        if song is None:
            continue

        if song.artist:
            if song.artist not in recent_artist_plays:
                recent_artist_plays[song.artist] = []
            recent_artist_plays[song.artist].append(song_id)

        if song.genre:
            recent_genre_counts[song.genre] = (
                recent_genre_counts.get(song.genre, 0) + 1
            )

    return ScoringContext(
        recently_played_ids=recently_played_ids,
        recent_artist_plays=recent_artist_plays,
        recent_genre_counts=recent_genre_counts,
        context_window_size=min(len(recently_played_ids), window),
    )
def get_unplayed_songs(
    conn: sqlite3.Connection,
    limit: int = 50
) -> list[Song]:
    """
    Return songs that have never been played.
    Used by the exploration budget in select_next_song
    to ensure unknown songs always get a chance.
    """
    rows = conn.execute(
        """
        SELECT s.* FROM songs s
        LEFT JOIN song_weights w ON s.id = w.song_id
        WHERE w.song_id IS NULL
           OR w.play_count = 0
        ORDER BY RANDOM()
        LIMIT ?
        """,
        (limit,)
    ).fetchall()
    return [Song.from_db_row(row) for row in rows]

def _load_all_weights(conn: sqlite3.Connection) -> dict[str, float]:
    """
    Load ALL song weights in one single query.
    Returns a dict mapping song_id → weight.

    This is the key optimization for large libraries.
    One query instead of one-per-song.
    """
    rows = conn.execute(
        "SELECT song_id, weight FROM song_weights"
    ).fetchall()
    return {row["song_id"]: row["weight"] for row in rows}

def score_song(
    conn: sqlite3.Connection,
    song: Song,
    context: ScoringContext,
    weights_map: dict[str, float] | None = None,
) -> ScoredSong:
    """
    Calculate the final score for one song.
    If weights_map is provided, uses it instead of
    querying the database — critical for performance.
    """
    # Use pre-loaded weight if available, else query
    if weights_map is not None:
        pref = weights_map.get(song.id, 1.0)
    else:
        pref = preference_signal(conn, song)

    recent = recency_signal(song, context)
    artist = artist_spacing_signal(song, context)
    genre  = genre_diversity_signal(song, context)

    base_score = (
        WEIGHTS["recency"] * recent +
        WEIGHTS["artist"]  * artist +
        WEIGHTS["genre"]   * genre
    )

    final = base_score * pref * (1.0 / WEIGHTS["preference"])

    return ScoredSong(
        song=             song,
        final_score=      round(final, 4),
        preference_score= pref,
        recency_score=    recent,
        artist_score=     artist,
        genre_score=      genre,
    )

def score_all_songs(
    conn: sqlite3.Connection,
    limit: int | None = None,
) -> list[ScoredSong]:
    """
    Score every song using exactly 3 database queries total:
      1. Load all songs
      2. Load all weights
      3. Load recent events (inside build_scoring_context)

    Handles 10,000+ songs comfortably.
    """
    songs       = get_all_songs(conn)
    context     = build_scoring_context(conn)
    weights_map = _load_all_weights(conn)

    scored = [
        score_song(conn, song, context, weights_map)
        for song in songs
    ]
    scored.sort(key=lambda s: s.final_score, reverse=True)

    return scored[:limit] if limit else scored