# tests/test_catalog.py
#
# Tests for the catalog and scanner.
# We test against a temporary in-memory database —
# tests never touch your real music_shuffle.db file.

import pytest
import sqlite3
from datetime import datetime

from src.db.schema import create_all_tables
from src.catalog.models import Song
from src.catalog.repository import (
    insert_song, get_song_by_id, get_all_songs,
    song_exists, count_songs
)


@pytest.fixture
def db():
    """
    A fresh in-memory SQLite database for each test.
    ':memory:' creates a database that lives only in RAM
    and disappears when the connection closes.
    Perfect for tests — fast, isolated, no cleanup needed.
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    create_all_tables(conn)
    return conn


@pytest.fixture
def sample_song():
    """A reusable Song object for testing."""
    return Song(
        file_path="/music/radiohead/creep.mp3",
        title="Creep",
        artist="Radiohead",
        album="Pablo Honey",
        genre="Alternative",
        duration_ms=238000,
    )


def test_insert_and_retrieve_song(db, sample_song):
    """A song we insert should come back out identically."""
    insert_song(db, sample_song)

    retrieved = get_song_by_id(db, sample_song.id)

    assert retrieved is not None
    assert retrieved.id == sample_song.id
    assert retrieved.title == "Creep"
    assert retrieved.artist == "Radiohead"
    assert retrieved.duration_ms == 238000


def test_song_exists_check(db, sample_song):
    """song_exists should return True after insert, False before."""
    assert song_exists(db, sample_song.file_path) is False
    insert_song(db, sample_song)
    assert song_exists(db, sample_song.file_path) is True


def test_insert_duplicate_is_ignored(db, sample_song):
    """Inserting the same file path twice should not create two rows."""
    insert_song(db, sample_song)
    insert_song(db, sample_song)  # second insert

    all_songs = get_all_songs(db)
    assert len(all_songs) == 1


def test_count_songs(db, sample_song):
    """count_songs should reflect inserted songs accurately."""
    assert count_songs(db) == 0
    insert_song(db, sample_song)
    assert count_songs(db) == 1


def test_song_display_name_with_tags(sample_song):
    """display_name should combine artist and title."""
    assert sample_song.display_name == "Radiohead — Creep"


def test_song_display_name_fallback():
    """display_name should use filename when tags are missing."""
    song = Song(file_path="/music/unknown_track.mp3")
    assert song.display_name == "unknown_track"


def test_song_duration_seconds(sample_song):
    """duration_seconds should convert from ms correctly."""
    assert sample_song.duration_seconds == 238.0