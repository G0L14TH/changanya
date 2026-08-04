import pytest
from src.catalog.models import Song
from src.scorer.models import ScoredSong, ScoringContext
from src.selector.selector import (
    weighted_random_choice,
    select_next_song,
    select_next_n_songs,
    MIN_SCORE_THRESHOLD,
)
from src.selector.diversity import apply_hard_filters


def make_scored(
    path: str,
    score: float,
    artist: str = "Artist",
    genre: str  = "Rock"
) -> ScoredSong:
    """Helper — quickly create a ScoredSong for testing."""
    song = Song(file_path=path, artist=artist, genre=genre)
    return ScoredSong(
        song=           song,
        final_score=    score,
        preference_score=score,
        recency_score=  1.0,
        artist_score=   1.0,
        genre_score=    1.0,
    )

# ────── Basic selection test ────────────

def test_select_returns_one_song():
    """select_next_song must always return exactly one song."""
    candidates = [make_scored(f"/{i}.mp3", float(i)) for i in range(1, 6)]
    result = select_next_song(candidates)
    assert result is not None
    assert isinstance(result, ScoredSong)


def test_select_from_empty_returns_none():
    """Selecting from an empty list should return None gracefully."""
    result = select_next_song([])
    assert result is None


def test_single_candidate_always_chosen():
    """When only one song exists it must always be returned."""
    only_song = make_scored("/only.mp3", 2.0)
    result = select_next_song([only_song])
    assert result.song.id == only_song.song.id


def test_below_threshold_songs_filtered():
    """
    Songs below MIN_SCORE_THRESHOLD should not be selected
    when better options exist.
    """
    good = make_scored("/good.mp3", 2.0)
    bad  = make_scored("/bad.mp3",  0.01)
    results = {select_next_song([good, bad]).song.id for _ in range(20)}
    assert bad.song.id not in results


def test_select_n_returns_correct_count():
    """select_next_n_songs should return exactly n songs."""
    candidates = [make_scored(f"/{i}.mp3", float(i)) for i in range(1, 11)]
    results = select_next_n_songs(candidates, n=5)
    assert len(results) == 5


def test_select_n_no_duplicates():
    """select_next_n_songs should never return the same song twice."""
    candidates = [make_scored(f"/{i}.mp3", float(i)) for i in range(1, 11)]
    results = select_next_n_songs(candidates, n=5)
    ids = [r.song.id for r in results]
    assert len(ids) == len(set(ids))


def test_select_n_respects_pool_size():
    """
    If pool_size is 3, we can't get more than 3 unique songs
    even if n is larger.
    """
    candidates = [make_scored(f"/{i}.mp3", float(i)) for i in range(1, 11)]
    results = select_next_n_songs(candidates, n=8, pool_size=3)
    assert len(results) <= 3


# ── Weighted distribution tests ────────────

def test_high_scorer_chosen_more_often():
    high = make_scored("/high.mp3", 10.0)
    low  = make_scored("/low.mp3",   1.0)

    high_count = 0
    trials = 1000

    for _ in range(trials):
        result = weighted_random_choice([high, low])
        if result.song.id == high.song.id:
            high_count += 1

    high_ratio = high_count / trials

    assert high_ratio > 0.75, (
        f"High scorer only won {high_ratio:.1%} of trials — "
        f"weighting may not be working"
    )


# ── Diversity guardrail tests ───────────────

def test_hard_filter_removes_last_song():
    """The song just played should be filtered out."""
    song_a = make_scored("/a.mp3", 3.0, artist="Artist A")
    song_b = make_scored("/b.mp3", 2.0, artist="Artist B")

    filtered = apply_hard_filters(
        [song_a, song_b],
        last_song_id=song_a.song.id,
    )

    ids = [s.song.id for s in filtered]
    assert song_a.song.id not in ids
    assert song_b.song.id in ids


def test_hard_filter_removes_same_artist():
    """Songs by the same artist as the last song should be filtered."""
    song_a1 = make_scored("/a1.mp3", 3.0, artist="Radiohead")
    song_a2 = make_scored("/a2.mp3", 2.5, artist="Radiohead")
    song_b  = make_scored("/b.mp3",  2.0, artist="Coldplay")

    filtered = apply_hard_filters(
        [song_a1, song_a2, song_b],
        last_song_id=song_a1.song.id,
        last_artist="Radiohead",
    )

    artists = [s.song.artist for s in filtered]
    assert "Radiohead" not in artists
    assert "Coldplay" in artists


def test_hard_filter_never_leaves_empty():
    
    only_artist = [
        make_scored("/a.mp3", 2.0, artist="Radiohead"),
        make_scored("/b.mp3", 1.5, artist="Radiohead"),
    ]

    filtered = apply_hard_filters(
        only_artist,
        last_artist="Radiohead",
    )

    assert len(filtered) > 0