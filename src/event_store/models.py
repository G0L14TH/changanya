#
# The PlayEvent dataclass — records one thing a user did.
# This is the raw learning data for the entire intelligence system.

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


# These are the only valid event types.
# Using constants prevents typos scattered across the codebase.
# If you type EventType.SKIPP Python raises an AttributeError immediately.
# If you type the string "skipp" the bug silently enters the database.
class EventType:
    PLAY     = "play"
    SKIP     = "skip"
    COMPLETE = "complete"
    REPLAY   = "replay"

    ALL = {PLAY, SKIP, COMPLETE, REPLAY}


@dataclass
class PlayEvent:
    """
    A single recorded user action on a song.

    Every interaction the user has with the player
    becomes one of these. Over time, hundreds of these
    build a precise picture of taste and behaviour.

    """
    song_id:          str
    event_type:       str
    session_id:       str

    # How long they actually listened in milliseconds.
    # None means we don't know (e.g. app crashed mid-song).
    # This is the most valuable learning signal we collect.
    play_duration_ms: Optional[int] = None

    # The full song duration at time of event.
    # Stored here so we can calculate completion ratio
    # even if the song's metadata changes later.
    song_duration_ms: Optional[int] = None

    # Auto-generated fields
    id:        str      = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def completion_ratio(self) -> Optional[float]:
        """
        What fraction of the song did they hear? (0.0 to 1.0)

        Examples:
            0.02 → skipped after 2 seconds (strong dislike)
            0.50 → skipped halfway (mild dislike or mood mismatch)
            0.95 → nearly finished (positive signal, soft skip)
            1.00 → completed fully (strong positive signal)

        Returns None if we don't have duration information.
        
        """
        if self.play_duration_ms is None or self.song_duration_ms is None:
            return None
        if self.song_duration_ms == 0:
            return None
        return min(self.play_duration_ms / self.song_duration_ms, 1.0)

    @property
    def is_meaningful_listen(self) -> bool:
        """
        Did they listen long enough for this to be a real signal?

        Listening to less than 20 seconds could just mean
        the song started at a bad moment — not that they dislike it.
        We use 20 seconds as the threshold for a meaningful interaction.
        """
        if self.play_duration_ms is None:
            return False
        return self.play_duration_ms >= 20_000

    def to_db_row(self) -> dict:
        return {
            "id":               self.id,
            "song_id":          self.song_id,
            "event_type":       self.event_type,
            "timestamp":        self.timestamp.isoformat(),
            "session_id":       self.session_id,
            "play_duration_ms": self.play_duration_ms,
            "song_duration_ms": self.song_duration_ms,
        }

    @classmethod
    def from_db_row(cls, row) -> "PlayEvent":
        return cls(
            id=               row["id"],
            song_id=          row["song_id"],
            event_type=       row["event_type"],
            timestamp=        datetime.fromisoformat(row["timestamp"]),
            session_id=       row["session_id"],
            play_duration_ms= row["play_duration_ms"],
            song_duration_ms= row["song_duration_ms"],
        )