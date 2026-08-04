# tests/test_event_store.py

import pytest
import sqlite3
from src.db.schema import create_all_tables
from src.catalog.models import Song
from src.catalog.repository import insert_song
from src.event_store.models import PlayEvent, EventType
from src.event_store.repository import (
    record_event, get_recent_events, get_events_for_song,
    get_recently_played_song_ids, count_events_by_type
)
from src.event_store.session import Session


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    create_all_tables(conn)
    return conn


@pytest.fixture
def sample_song(db):
    """Insert a real song so foreign key constraints pass."""
    song = Song(
        file_path="/music/test.mp3",
        title="Test Song",
        artist="Test Artist",
        duration_ms=240_000,
    )
    insert_song(db, song)
    return song


@pytest.fixture
def session():
    return Session()


def test_record_and_retrieve_event(db, sample_song, session):
    """An event we record should come back out correctly."""
    event = PlayEvent(
        song_id=          sample_song.id,
        event_type=       EventType.COMPLETE,
        session_id=       session.get_id(),
        play_duration_ms= 240_000,
        song_duration_ms= 240_000,
    )
    record_event(db, event)

    events = get_events_for_song(db, sample_song.id)
    assert len(events) == 1
    assert events[0].event_type == EventType.COMPLETE
    assert events[0].play_duration_ms == 240_000


def test_completion_ratio_full_listen(db, sample_song, session):
    """A completed song should have a ratio of 1.0."""
    event = PlayEvent(
        song_id=          sample_song.id,
        event_type=       EventType.COMPLETE,
        session_id=       session.get_id(),
        play_duration_ms= 240_000,
        song_duration_ms= 240_000,
    )
    assert event.completion_ratio == 1.0


def test_completion_ratio_early_skip(db, sample_song, session):
    """A 4-second skip on a 4-minute song should be a very low ratio."""
    event = PlayEvent(
        song_id=          sample_song.id,
        event_type=       EventType.SKIP,
        session_id=       session.get_id(),
        play_duration_ms= 4_000,
        song_duration_ms= 240_000,
    )
    assert event.completion_ratio < 0.02


def test_is_meaningful_listen(sample_song, session):
    """Under 20s should not be meaningful. Over 20s should be."""
    short = PlayEvent(
        song_id=          sample_song.id,
        event_type=       EventType.SKIP,
        session_id=       session.get_id(),
        play_duration_ms= 5_000,
        song_duration_ms= 240_000,
    )
    long = PlayEvent(
        song_id=          sample_song.id,
        event_type=       EventType.SKIP,
        session_id=       session.get_id(),
        play_duration_ms= 30_000,
        song_duration_ms= 240_000,
    )
    assert short.is_meaningful_listen is False
    assert long.is_meaningful_listen is True


def test_count_events_by_type(db, sample_song, session):
    """count_events_by_type should reflect what was recorded."""
    for _ in range(3):
        record_event(db, PlayEvent(
            song_id=    sample_song.id,
            event_type= EventType.PLAY,
            session_id= session.get_id(),
        ))
    record_event(db, PlayEvent(
        song_id=    sample_song.id,
        event_type= EventType.SKIP,
        session_id= session.get_id(),
    ))

    counts = count_events_by_type(db, sample_song.id)
    assert counts[EventType.PLAY] == 3
    assert counts[EventType.SKIP] == 1
    assert counts[EventType.COMPLETE] == 0


def test_invalid_event_type_raises(db, sample_song, session):
    """Recording an unknown event type should raise immediately."""
    with pytest.raises(ValueError):
        record_event(db, PlayEvent(
            song_id=    sample_song.id,
            event_type= "listened",   # invalid
            session_id= session.get_id(),
        ))


def test_recently_played_song_ids(db, sample_song, session):
    """get_recently_played_song_ids should return the song we played."""
    record_event(db, PlayEvent(
        song_id=    sample_song.id,
        event_type= EventType.PLAY,
        session_id= session.get_id(),
    ))
    recent = get_recently_played_song_ids(db, limit=10)
    assert sample_song.id in recent


def test_session_has_unique_id():
    """Two sessions should never share the same ID."""
    s1 = Session()
    s2 = Session()
    assert s1.get_id() != s2.get_id()