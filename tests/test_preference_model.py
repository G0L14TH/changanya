#test_preference_model

import pytest
import sqlite3
from datetime import datetime, timedelta
from src.db.schema import create_all_tables
from src.catalog.models import Song
from src.catalog.repository import insert_song
from src.event_store.models import PlayEvent, EventType
from src.event_store.repository import record_event
from src.event_store.session import Session
from src.preference_model.decay import exponential_decay, recency_penalty
from src.preference_model.calculator import calculate_song_weight, DEFAULT_WEIGHT
from src.preference_model.updater import update_song_weight, get_song_weight


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    create_all_tables(conn)
    return conn


@pytest.fixture
def song(db):
    s = Song(
        file_path="/music/test.mp3",
        title="Test",
        artist="Artist",
        duration_ms=200_000
    )
    insert_song(db, s)
    return s


@pytest.fixture
def session():
    return Session()


# ── Decay tests ────────────────────────────────────────────────

def test_decay_is_1_for_fresh_event():
    """An event that just happened should have full weight."""
    now = datetime.now()
    assert exponential_decay(now, now) == pytest.approx(1.0)


def test_decay_is_half_at_half_life():
    """After 30 days, weight should be 0.5."""
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    result = exponential_decay(thirty_days_ago, now, half_life_days=30)
    assert result == pytest.approx(0.5, abs=0.001)


def test_decay_approaches_zero_for_old_events():
    """A very old event should have almost no influence."""
    now = datetime.now()
    old = now - timedelta(days=365)
    result = exponential_decay(old, now, half_life_days=30)
    assert result < 0.01


def test_recency_penalty_no_play():
    """A song never played should have no penalty."""
    assert recency_penalty(None, datetime.now()) == 1.0


def test_recency_penalty_just_played():
    """A song played 1 minute ago should be heavily penalised."""
    now = datetime.now()
    just_now = now - timedelta(minutes=1)
    result = recency_penalty(just_now, now, cooldown_minutes=60)
    assert result < 0.05


def test_recency_penalty_fully_cooled():
    """A song played 2 hours ago (cooldown=60) should have no penalty."""
    now = datetime.now()
    two_hours_ago = now - timedelta(hours=2)
    result = recency_penalty(two_hours_ago, now, cooldown_minutes=60)
    assert result == 1.0


# ── Weight calculation tests ───────────────────────────────────

def test_unknown_song_gets_default_weight(db, song):
    """A song with no events should return the default weight."""
    weight = calculate_song_weight(db, song.id)
    assert weight == DEFAULT_WEIGHT


def test_completed_song_gains_weight(db, song, session):
    """Completing a song should increase its weight above default."""
    record_event(db, PlayEvent(
        song_id=song.id,
        event_type=EventType.COMPLETE,
        session_id=session.get_id(),
        play_duration_ms=200_000,
        song_duration_ms=200_000,
    ))
    weight = calculate_song_weight(db, song.id)
    assert weight > DEFAULT_WEIGHT


def test_early_skip_lowers_weight(db, song, session):
    """Skipping after 3 seconds should lower weight below default."""
    record_event(db, PlayEvent(
        song_id=song.id,
        event_type=EventType.SKIP,
        session_id=session.get_id(),
        play_duration_ms=3_000,
        song_duration_ms=200_000,
    ))
    weight = calculate_song_weight(db, song.id)
    assert weight < DEFAULT_WEIGHT


def test_replay_gives_highest_boost(db, song, session):
    """A replay should give a bigger boost than a complete."""
    record_event(db, PlayEvent(
        song_id=song.id,
        event_type=EventType.REPLAY,
        session_id=session.get_id(),
        play_duration_ms=200_000,
        song_duration_ms=200_000,
    ))
    replay_weight = calculate_song_weight(db, song.id)

    # New song, only completed
    song2 = Song(file_path="/music/test2.mp3", duration_ms=200_000)
    insert_song(db, song2)
    record_event(db, PlayEvent(
        song_id=song2.id,
        event_type=EventType.COMPLETE,
        session_id=session.get_id(),
        play_duration_ms=200_000,
        song_duration_ms=200_000,
    ))
    complete_weight = calculate_song_weight(db, song2.id)

    assert replay_weight > complete_weight


def test_update_and_read_weight(db, song, session):
    """update_song_weight should persist and get_song_weight should read it."""
    record_event(db, PlayEvent(
        song_id=song.id,
        event_type=EventType.COMPLETE,
        session_id=session.get_id(),
        play_duration_ms=200_000,
        song_duration_ms=200_000,
    ))
    saved_weight = update_song_weight(db, song.id)
    read_weight = get_song_weight(db, song.id)
    assert saved_weight == pytest.approx(read_weight)