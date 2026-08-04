# The Song dataclass — the central data type of the entire system.

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


@dataclass
class Song:
    
    file_path:    str
    title:        Optional[str]       = None
    artist:       Optional[str]       = None
    album:        Optional[str]       = None
    genre:        Optional[str]       = None
    year:         Optional[int]       = None
    duration_ms:  Optional[int]       = None
    bpm:          Optional[float]     = None
    energy:       Optional[float]     = None
    play_count:   int                 = 0
    skip_count:   int                 = 0
    last_played:  Optional[datetime]  = None
    is_recording:  bool                = False
    display_title: Optional[str]       = None
    id:           str                 = field(default_factory=lambda: str(uuid.uuid4()))
    date_added:   datetime            = field(default_factory=datetime.now)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Convenience accessor — duration in seconds instead of ms."""
        if self.duration_ms is None:
            return None
        return self.duration_ms / 1000.0

    @property
    def display_name(self) -> str:
        """
        Human-readable name for logging and UI.
        Falls back if tags are missing.
        """
        if self.display_title:
            return self.display_title
        if self.title and self.artist:
            return f"{self.artist} - {self.title}"
        if self.title:
            return self.title
        from pathlib import Path
        return Path(self.file_path).stem

    def to_db_row(self) -> dict:
        return {
            "id":           self.id,
            "file_path":    self.file_path,
            "title":        self.title,
            "artist":       self.artist,
            "album":        self.album,
            "genre":        self.genre,
            "year":         self.year,
            "duration_ms":  self.duration_ms,
            "bpm":          self.bpm,
            "energy":       self.energy,
            "date_added":   self.date_added.isoformat(),
            "play_count":   self.play_count,
            "skip_count":   self.skip_count,
            "last_played":  self.last_played.isoformat() if self.last_played else None,
            "is_recording": 1 if self.is_recording else 0,
            "display_title": self.display_title,
        }

    @classmethod
    def from_db_row(cls, row) -> "Song":
        return cls(
            id=           row["id"],
            file_path=    row["file_path"],
            title=        row["title"],
            artist=       row["artist"],
            album=        row["album"],
            genre=        row["genre"],
            year=         row["year"] if "year" in row.keys() else None,
            duration_ms=  row["duration_ms"],
            bpm=          row["bpm"],
            energy=       row["energy"],
            date_added=   datetime.fromisoformat(row["date_added"]),
            play_count=   row["play_count"],
            skip_count=   row["skip_count"],
            last_played=  datetime.fromisoformat(row["last_played"])
                        if row["last_played"] else None,
            is_recording=  bool(row["is_recording"]) if "is_recording" in row.keys() else False,
            display_title= row["display_title"] if "display_title" in row.keys() else None,
        )