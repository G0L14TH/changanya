import random
from src.scorer.models import ScoredSong

DEFAULT_POOL_SIZE = 50
MIN_SCORE_THRESHOLD = 0.05

def weighted_random_choice(candidates: list[ScoredSong]) -> ScoredSong:

    if not candidates:
        raise ValueError("Cannot select from an empty candidate list.")

    if len(candidates) == 1:
        return candidates[0]

    songs   = candidates
    weights = [max(s.final_score, 0.001) for s in songs]
    chosen = random.choices(songs, weights=weights, k=1)[0]
    return chosen


def select_next_song(
    scored_songs: list[ScoredSong],
    pool_size: int = DEFAULT_POOL_SIZE,
    exploration_songs: list[ScoredSong] | None = None,
    exploration_rate: float = 0.20,
) -> ScoredSong | None:
    """
    Pick the next song with an exploration budget.

    exploration_rate = 0.20 means roughly 1 in 5 songs
    will be an undiscovered song regardless of its score.
    This prevents the exploitation trap where only
    familiar songs ever get selected.
    """
    
    if not scored_songs:
        return None
    
    # Exploration: occasionally force an undiscovered song
    if (exploration_songs
            and random.random() < exploration_rate):
        return random.choice(exploration_songs)

    # Normal weighted selection from scored candidates
    eligible = [
        s for s in scored_songs
        if s.final_score >= MIN_SCORE_THRESHOLD
    ] or scored_songs
    
    pool = eligible[:pool_size]
    return weighted_random_choice(pool)


def select_next_n_songs(
    scored_songs: list[ScoredSong],
    n: int,
    pool_size: int = DEFAULT_POOL_SIZE,
) -> list[ScoredSong]:
    if not scored_songs:
        return []

    results  = []
    eligible = [
        s for s in scored_songs
        if s.final_score >= MIN_SCORE_THRESHOLD
    ] or scored_songs

    pool = eligible[:pool_size]
    remaining = pool.copy()

    for _ in range(min(n, len(remaining))):
        if not remaining:
            break

        chosen = weighted_random_choice(remaining)
        results.append(chosen)
        remaining = [s for s in remaining if s.song.id != chosen.song.id]

    return results