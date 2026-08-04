# tests/test_scorer.py

import pytest
import sqlite3
from src.db.schema import create_all_tables
from src.catalog.models import Song
from src.catalog.repository import insert_song
from src.event_store.models import PlayEvent, EventType
from src.event_store.repository import record_event
from src.event_store.session import Session
from src.preference_model.updater import update_song_weight
from src.scorer.models import ScoringContext, ScoredSong
from src.scorer.signals import (
    recency_signal, artist_spacing_signal, genre_diversity_signal
)
from src.scorer.scorer import score_song, score_all_songs, build_scoring_context


@pytest.fixture
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    create_all_tables(conn)
    return conn


@pytest.fixture
def session():
    return Session()


def make_song(db, path, artist="Artist A", genre="Rock", title="Song"):
    """Helper to quickly insert a song and return it."""
    s = Song(
        file_path=path,
        title=title,
        artist=artist,
        genre=genre,
        duration_ms=200_000
    )
    insert_song(db, s)
    return s


# ── Signal unit tests ──────────────────────────────────────────

def test_recency_signal_not_played():
    """A song not in recent history should score 1.0."""
    song = Song(file_path="/x.mp3")
    ctx = ScoringContext(
        recently_played_ids=[],
        recent_artist_plays={},
        recent_genre_counts={},
    )
    assert recency_signal(song, ctx) == 1.0


def test_recency_signal_just_played():
    """The most recently played song should score near 0."""
    song = Song(file_path="/x.mp3")
    ctx = ScoringContext(
        recently_played_ids=[song.id, "other1", "other2"],
        recent_artist_plays={},
        recent_genre_counts={},
    )
    assert recency_signal(song, ctx) < 0.1


def test_artist_spacing_no_recent_plays():
    """Artist not played recently should score 1.0."""
    song = Song(file_path="/x.mp3", artist="Radiohead")
    ctx = ScoringContext(
        recently_played_ids=[],
        recent_artist_plays={},
        recent_genre_counts={},
    )
    assert artist_spacing_signal(song, ctx) == 1.0


def test_artist_spacing_too_many_recent():
    """Artist played 3+ times recently should score very low."""
    song = Song(file_path="/x.mp3", artist="Radiohead")
    ctx = ScoringContext(
        recently_played_ids=[],
        recent_artist_plays={"Radiohead": ["id1", "id2", "id3"]},
        recent_genre_counts={},
    )
    assert artist_spacing_signal(song, ctx) <= 0.1


def test_genre_diversity_dominant_genre():
    """A heavily dominant genre should be penalised."""
    song = Song(file_path="/x.mp3", genre="Rock")
    ctx = ScoringContext(
        recently_played_ids=[],
        recent_artist_plays={},
        recent_genre_counts={"Rock": 9},
        context_window_size=10,
    )
    assert genre_diversity_signal(song, ctx) <= 0.3


# ── Full scorer tests ──────────────────────────────────────────

def test_loved_song_scores_higher_than_unknown(db, session):
    """
    A song with completed plays/strong preference history should outscore a never-played one. 
    Even when neither has been played recently
    """
    loved  = make_song(db, "/loved.mp3",   artist="A", genre="Rock")
    unseen = make_song(db, "/unseen.mp3",  artist="B", genre="Jazz")

    # Record that we love the first song
    for _ in range(3):
        record_event(db, PlayEvent(
            song_id=loved.id,
            event_type=EventType.COMPLETE,
            session_id=session.get_id(),
            play_duration_ms=200_000,
            song_duration_ms=200_000,
        ))
    update_song_weight(db, loved.id)

    ctx = ScoringContext(
        recently_played_ids=[],
        recent_artist_plays={},
        recent_genre_counts={},
    )
    
    loved_score  = score_song(db, loved, ctx)
    unseen_score = score_song(db, unseen, ctx)

    assert loved_score.final_score > unseen_score.final_score


def test_recently_played_scores_lower(db, session):
    """A just-played song should score lower than an unplayed one."""
    recent   = make_song(db, "/recent.mp3",   artist="A", genre="Pop")
    unplayed = make_song(db, "/unplayed.mp3", artist="B", genre="Pop")

    record_event(db, PlayEvent(
        song_id=recent.id,
        event_type=EventType.PLAY,
        session_id=session.get_id(),
    ))

    ctx = build_scoring_context(db)
    recent_score   = score_song(db, recent,   ctx)
    unplayed_score = score_song(db, unplayed, ctx)

    assert unplayed_score.final_score > recent_score.final_score


def test_score_all_songs_returns_sorted_list(db, session):
    """score_all_songs should return songs sorted highest score first."""
    for i in range(5):
        make_song(db, f"/song{i}.mp3", artist=f"Artist{i}")

    results = score_all_songs(db)

    assert len(results) == 5
    scores = [r.final_score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_scored_song_has_reasoning(db):
    """Every scored song should produce a non-empty reasoning string."""
    song = make_song(db, "/x.mp3")
    ctx = ScoringContext(
        recently_played_ids=[],
        recent_artist_plays={},
        recent_genre_counts={},
    )
    result = score_song(db, song, ctx)
    assert len(result.reasoning()) > 0