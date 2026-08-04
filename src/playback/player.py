# src/playback/player.py
# VLC-based audio player

# src/playback/player.py

import os
import sys
import platform
import time
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Callable, Optional
from enum import Enum, auto

def _setup_vlc_path() -> None:
    """
    Set up VLC library path based on the current platform.
    Must run before importing vlc.
    """
    system = platform.system()

    if system == "Windows":
        vlc_from_env = os.environ.get("CHANGANYA_VLC_PATH", "")
        if vlc_from_env and os.path.exists(vlc_from_env):
            os.add_dll_directory(vlc_from_env)
            os.environ["PATH"] = vlc_from_env + ";" + os.environ.get("PATH", "")
            return

        candidates = [
            r"C:\Program Files\VideoLAN\VLC",
            r"C:\Program Files (x86)\VideoLAN\VLC",
        ]
        for path in candidates:
            if os.path.exists(path):
                os.add_dll_directory(path)
                os.environ["PATH"] = path + ";" + os.environ.get("PATH", "")
                return

    elif system == "Darwin":
        candidates = [
            "/Applications/VLC.app/Contents/MacOS/lib",
            "/Applications/VLC.app/Contents/MacOS",
        ]
        for path in candidates:
            if os.path.exists(path):
                os.environ["DYLD_LIBRARY_PATH"] = (
                    path + ":" + os.environ.get("DYLD_LIBRARY_PATH", "")
                )
                return

_setup_vlc_path()
import vlc

from src.catalog.models import Song

class PlayerState(Enum):
    STOPPED = auto()
    PLAYING = auto()
    PAUSED  = auto()


@dataclass
class TrackEvent:
    """Something happened during playback."""
    event_type:       str
    song:             Song
    play_duration_ms: int
    timestamp:        datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class MusicPlayer:
    """
    VLC-based music player.
    Emits TrackEvents so the shuffle engine can react
    without polling or tight coupling.
    """

    def __init__(self, on_event: Callable[[TrackEvent], None]):
        self._on_event         = on_event
        self._instance         = vlc.Instance("--no-xlib --quiet")
        self._media_player     = self._instance.media_player_new()
        self._current_song:    Optional[Song]  = None
        self._state:           PlayerState     = PlayerState.STOPPED
        self._play_started:    Optional[float] = None
        self._paused_elapsed:  float           = 0.0
        self._paused_at:       Optional[float] = None
        self._ending:           bool            = False

        # Wire VLC's end-of-media event
        events = self._media_player.event_manager()
        events.event_attach(
            vlc.EventType.MediaPlayerEndReached,
            self._on_track_end
        )

    # ── Public interface ────────────────

    def play(self, song: Song) -> bool:
        """Load and play an audio file."""
        path = Path(song.file_path)
        if not path.exists():
            print(f"  [player] File not found: {path.name}")
            return False

        try:
            media = self._instance.media_new(str(path))
            self._media_player.set_media(media)
            self._media_player.play()

            time.sleep(0.1)

            self._current_song   = song
            self._state          = PlayerState.PLAYING
            self._play_started   = time.time()
            self._paused_elapsed = 0.0
            self._paused_at      = None

            self._on_event(TrackEvent(
                event_type="started",
                song=song,
                play_duration_ms=0,
            ))
            return True

        except Exception as e:
            print(f"  [player] Could not play {path.name}: {e}")
            return False

    def skip(self) -> None:
        """User pressed skip."""
        if self._current_song and self._state == PlayerState.PLAYING:
            self._ending = True   # prevent _on_track_end from also firing
        duration = self._get_play_duration_ms()
        song     = self._current_song

        self._media_player.stop()
        self._state        = PlayerState.STOPPED
        self._current_song = None
        self._ending       = False

        self._on_event(TrackEvent(
            event_type="skipped",
            song=song,
            play_duration_ms=duration,
        ))
    def set_volume(self, volume: int) -> None:
        """
        set playback volume.
        volume: 0 - 100
        """
        clamped = max(0, min(100, volume))
        self._media_player.audio_set_volume(clamped)

    def pause(self) -> None:
        """Pause playback."""
        if self._state == PlayerState.PLAYING:
            self._media_player.pause()
            self._state     = PlayerState.PAUSED
            self._paused_at = time.time()

            self._on_event(TrackEvent(
                event_type="paused",
                song=self._current_song,
                play_duration_ms=self._get_play_duration_ms(),
            ))

    def resume(self) -> None:
        """Resume from pause."""
        if self._state == PlayerState.PAUSED:
            self._media_player.pause()

            if self._paused_at:
                self._paused_elapsed += time.time() - self._paused_at
                self._paused_at = None

            self._state = PlayerState.PLAYING
            
    def seek(self, position_ms: int) -> None:
        """Seek to a specifi pisition in the current track.
        position_ms: milliseconds from the start of the track"""
        if self._state in (PlayerState.PLAYING, PlayerState.PAUSED):
            self._media_player.set_time(max(0,position_ms))

            # reset our internal play timer to match new position
            # so _get_play_duration_ms stays accurate
        if self._play_started is not None:
            import time
            self._play_started = time.time() - (position_ms / 1000.0)

    def stop(self) -> None:
        """Stop completely."""
        self._media_player.stop()
        self._state        = PlayerState.STOPPED
        self._current_song = None

    def is_playing(self) -> bool:
        return self._state == PlayerState.PLAYING

    def get_current_song(self) -> Optional[Song]:
        return self._current_song

    # ── Private ────────────────────

    def _get_play_duration_ms(self) -> int:
        """Actual listening time excluding pauses."""
        if self._play_started is None:
            return 0
        elapsed = time.time() - self._play_started - self._paused_elapsed
        return max(0, int(elapsed * 1000))

    def _on_track_end(self, event) -> None:
        """Called by VLC when a track finishes naturally."""
        # If skip() is handling this transition, do nothing
        if self._ending:
            return

        song     = self._current_song
        duration = self._get_play_duration_ms()

        self._state        = PlayerState.STOPPED
        self._current_song = None

        if song:
            def fire_after_delay():
                time.sleep(0.5)
                self._on_event(TrackEvent(
                    event_type="completed",
                    song=song,
                    play_duration_ms=duration,
                ))

            threading.Thread(
                target=fire_after_delay,
                daemon=True
            ).start()