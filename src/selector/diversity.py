from src.scorer.models import ScoredSong


def apply_hard_filters(
    candidates: list[ScoredSong],
    last_song_id: str | None = None,
    last_artist: str | None  = None,
) -> list[ScoredSong]:
    
    filtered = candidates

    # Rule 1: No same song twice in a row
    if last_song_id:
        without_last = [
            s for s in filtered
            if s.song.id != last_song_id
        ]
        if without_last:
            filtered = without_last

    # Rule 2: No same artist twice in a row
    if last_artist:
        without_artist = [
            s for s in filtered
            if s.song.artist != last_artist
        ]
        if without_artist:
            filtered = without_artist

    return filtered


def get_selection_explanation(chosen: ScoredSong) -> str:
    score = chosen.final_score
    reasoning = chosen.reasoning()

    if score >= 2.5:
        strength = "Strong pick"
    elif score >= 1.5:
        strength = "Good pick"
    elif score >= 0.8:
        strength = "Moderate pick"
    else:
        strength = "Exploratory pick"

    return f"{strength} ({score:.2f}) — {reasoning}"