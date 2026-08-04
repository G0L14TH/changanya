# If the schema changes, you fix it here
# and nowhere else in the codebase notices.

import sqlite3
from typing import Optional
from src.catalog.models import Song


def insert_song(conn: sqlite3.Connection, song: Song) -> None:
    """
    Insert a new song into the database.
    If a song with the same file_path already exists, do nothing.
    This makes the scanner safe to run multiple times.
    """
    conn.execute(
        """
        INSERT OR IGNORE INTO songs
            (id, file_path, title, artist, album, genre,
             duration_ms, bpm, energy, date_added,
             play_count, skip_count, last_played)
        VALUES
            (:id, :file_path, :title, :artist, :album, :genre,
             :duration_ms, :bpm, :energy, :date_added,
             :play_count, :skip_count, :last_played)
        """,
        song.to_db_row()
    )
    conn.commit()


def get_song_by_id(conn: sqlite3.Connection, song_id: str) -> Optional[Song]:
    """
    Fetch a single song by its UUID.
    Returns None if not found — never raises an exception for missing data.
    """
    row = conn.execute(
        "SELECT * FROM songs WHERE id = ?", (song_id,)
    ).fetchone()

    return Song.from_db_row(row) if row else None


def get_all_songs(conn: sqlite3.Connection) -> list[Song]:
    """
    Fetch every song in the library.
    The scorer uses this to build the candidate pool.
    """
    rows = conn.execute("SELECT * FROM songs").fetchall()
    return [Song.from_db_row(row) for row in rows]


def get_songs_by_artist(conn: sqlite3.Connection, artist: str) -> list[Song]:
    """Fetch all songs by a given artist name."""
    rows = conn.execute(
        "SELECT * FROM songs WHERE artist = ?", (artist,)
    ).fetchall()
    return [Song.from_db_row(row) for row in rows]


def get_songs_by_album(
    conn: sqlite3.Connection,
    album: str,
    artist: str,
) -> list[Song]:
    """Fetch all songs in a given album/artist pair."""
    rows = conn.execute(
        """
        SELECT * FROM songs
        WHERE COALESCE(album, 'Unknown Album') = ?
          AND COALESCE(artist, 'Unknown Artist') = ?
        ORDER BY file_path
        """,
        (album, artist),
    ).fetchall()
    return [Song.from_db_row(row) for row in rows]


def update_album_tags(
    conn: sqlite3.Connection,
    album: str,
    artist: str,
    new_album: str | None = None,
    new_artist: str | None = None,
    genre: str | None = None,
    year: int | None = None,
) -> int:
    """Update metadata for every song in an album/artist pair."""
    updates: list[str] = []
    params: list[object] = []

    if new_album is not None:
        updates.append("album = ?")
        params.append(new_album)
    if new_artist is not None:
        updates.append("artist = ?")
        params.append(new_artist)
    if genre is not None:
        updates.append("genre = ?")
        params.append(genre)
    if year is not None:
        updates.append("year = ?")
        params.append(year)

    if not updates:
        return 0

    params.extend([album, artist])
    sql = (
        "UPDATE songs SET "
        + ", ".join(updates)
        + " WHERE COALESCE(album, 'Unknown Album') = ?"
        + " AND COALESCE(artist, 'Unknown Artist') = ?"
    )
    cursor = conn.execute(sql, params)
    conn.commit()
    return cursor.rowcount


def song_exists(conn: sqlite3.Connection, file_path: str) -> bool:
    """
    Check whether a file path is already in the catalog.
    Used by the scanner to skip files it has already indexed.
    """
    row = conn.execute(
        "SELECT 1 FROM songs WHERE file_path = ?", (file_path,)
    ).fetchone()
    return row is not None


def count_songs(conn: sqlite3.Connection) -> int:
    """Return the total number of songs in the library."""
    row = conn.execute("SELECT COUNT(*) FROM songs").fetchone()
    return row[0]