from dataclasses import dataclass
from src.catalog.models import Song


@dataclass
class ScoringContext:
    """
    Everything the scorer needs to know to score one session.
    Built once per scoring run and passed to every signal calculator.

    This is the key design decision of the scorer:
    it never queries the database itself.
    The caller builds this context, the scorer just does math.

    This makes the scorer:
        - fast (no DB calls during scoring)
        - testable (inject any context you want in tests)
        - transparent (easy to see what data drove a decision)
    """
    recently_played_ids:    list[str]
    recent_artist_plays:    dict[str, list[str]]
    recent_genre_counts:    dict[str, int]
    # Total songs considered in context window
    context_window_size:    int = 10


@dataclass
class ScoredSong:
    """
    A song with its final score and a breakdown of
    how that score was reached.

    The breakdown is essential — it's what the UI will
    display to show the user why a song was chosen.
    It also makes debugging the algorithm much easier.
    """
    song:               Song
    final_score:        float

    # Individual signal contributions
    preference_score:   float = 0.0
    recency_score:      float = 0.0
    artist_score:       float = 0.0
    genre_score:        float = 0.0

    def reasoning(self) -> str:
        """
        Human-readable explanation of why this song scored
        the way it did. Used for terminal display and later UI.
        """
        parts = []
        if self.preference_score >= 1.2:
            parts.append("you enjoy this song")
        elif self.preference_score <= 0.5:
            parts.append("you tend to skip this")

        if self.recency_score >= 0.9:
            parts.append("not played recently")
        elif self.recency_score <= 0.3:
            parts.append("played recently")

        if self.artist_score <= 0.4:
            parts.append("artist played recently")

        if not parts:
            parts.append("balanced choice")

        return ", ".join(parts)
    

            # NOTES
        
    # the ai will be able to read and understand method
    # reasoning() but the users will not see it in the UI, so we can make it private
    # but there, for the ai intelligence to read and understand, how to 
    # keep the shuffle interesting
    # consider mood, BPM, style, genre and other details
    # we also add a transition of songs to give that real mixed playlist / music listening experience
    # this will be a suprise in the shuffling, i.e not having the same genre or style in a row, but also not having a complete mismatch of songs,
    # so that the user can enjoy the listening experience
    # use bpm, style, genre, etc... to bring that blend
    # ... 