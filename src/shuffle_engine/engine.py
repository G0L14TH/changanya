# src/shuffle_engine/engine.py

import random
import threading
import sqlite3
from typing import Optional

from src.catalog.models import Song
from src.event_store.models import PlayEvent, EventType
from src.event_store.repository import record_event
from src.event_store.session import Session
from src.preference_model.updater import update_song_weight
from src.scorer.scorer import score_all_songs, build_scoring_context
from src.selector.selector import select_next_song
from src.selector.diversity import apply_hard_filters, get_selection_explanation
from src.playback.player import MusicPlayer, TrackEvent
from src.scorer.models import ScoredSong


class ShuffleEngine:
    """
    The central orchestrator.
    Manages the listening session, reacts to player events,
    records interactions, and keeps music flowing.
    """

    def __init__(self, conn: sqlite3.Connection):
        self.conn           = conn
        self.session        = Session()
        self.player         = MusicPlayer(on_event=self._handle_player_event)

        self._current_song:  Optional[Song]       = None
        self._prefetched:    Optional[ScoredSong] = None
        self._last_artist:   Optional[str]        = None
        self._is_running:    bool                 = False
        self._history:       list                 = []
        self._lock           = threading.Lock()

        # Album playback mode — when enabled, only songs from the
        # album queue will be played until the queue finishes or the
        # mode is explicitly exited (by play_specific or user action).
        self._album_mode:    bool                 = False
        self._album_queue:   list[Song]           = []
        self._album_shuffle_enabled: bool         = False
        self._original_album_queue: list[Song]    = []
        self._global_shuffle_enabled: bool        = False

        print(f"  Session started: {self.session.get_id()[:8]}...")

    # ── Public interface ───────────────────────────────────────

    def start(self) -> None:
        """Begin the shuffle session."""
        self._is_running = True
        self._play_next()

    def skip(self) -> None:
        """User requested skip."""
        self.player.skip()

    def pause_resume(self) -> None:
        """Toggle pause/resume."""
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.resume()

    def stop(self) -> None:
        """Stop everything cleanly."""
        self._is_running = False
        self.player.stop()

    def get_current_song(self) -> Optional[Song]:
        return self._current_song

    def play_specific(self, song_id: str) -> None:
        """
        Play a specific song immediately.
        Called when user clicks a queue item.
        This exits album playback mode to allow normal shuffle/selection.
        """
        from src.catalog.repository import get_song_by_id
        song = get_song_by_id(self.conn, song_id)
        if song is None:
            return

        # Exiting album mode when user explicitly plays another song
        self._album_mode = False
        self._album_queue = []
        self._album_shuffle_enabled = False

        # Save current song to history
        if self._current_song:
            self._history.append(self._current_song)

        # Stop current and play requested
        self.player.stop()
        self._current_song = song
        self._last_artist  = song.artist
        self.player.play(song)

        # Prefetch next in background
        threading.Thread(
            target=self._prefetch_next,
            daemon=True
        ).start()

    def _build_album_queue(self, songs: list[Song]) -> list[Song]:
        """Return the album queue with album-only shuffle applied when enabled."""
        q = songs[:]
        if self._album_shuffle_enabled:
            random.shuffle(q)
        return q

    def set_global_shuffle(self, enabled: bool) -> None:
        """Enable or disable the global shuffle mode."""
        with self._lock:
            self._global_shuffle_enabled = enabled

        try:
            if hasattr(self, "_emit_now_playing"):
                self._emit_now_playing()
        except Exception:
            pass

    def set_album_shuffle(self, enabled: bool) -> None:
        """Enable or disable shuffle for the current album queue."""
        import random
        with self._lock:
            self._album_shuffle_enabled = enabled

            if self._album_mode and self._album_queue:
                if enabled:
                    # Shuffle remaining songs
                    random.shuffle(self._album_queue)
                else:
                    # Restore original order for remaining songs only
                    remaining_ids = {s.id for s in self._album_queue}
                    self._album_queue = [
                        s for s in self._original_album_queue
                        if s.id in remaining_ids
                    ]
                    
    def play_album(self, album: str, artist: str, shuffle: bool = False) -> None:
        """Queue and play an album from start to finish. When album mode
        is active, only album tracks will be played until the album ends
        or album mode is exited.
        """
        from src.catalog.repository import get_songs_by_album

        songs = get_songs_by_album(self.conn, album, artist)
        if not songs:
            return

        if self._current_song:
            self._history.append(self._current_song)
            if len(self._history) > 50:
                self._history.pop(0)

        # Set album mode and populate queue (preserve order unless shuffle requested)
        q = songs[:]
        if shuffle:
            random.shuffle(q)

        with self._lock:
            self._album_mode = True
            self._album_queue = q
            self._original_album_queue = list(q)
            self._album_shuffle_enabled = bool(shuffle)
            self._is_running = True

        self.player.stop()
        self._play_next()

    def play_album_track(
        self,
        song_id:  str,
        album:    str = "",
        artist:   str = "",
    ) -> None:
        """
        Play a specific track from the current album queue.
        Removes songs before the selected track so playback
        continues from that point forward.
        Never resets the queue to the full album.
        """
        with self._lock:
            if self._album_mode and self._album_queue:
                # Find the track in the remaining queue
                track_index = next(
                    (idx for idx, s in enumerate(self._album_queue)
                    if s.id == song_id),
                    None
                )

                if track_index is not None:
                    selected_track = self._album_queue[track_index]
                    # Keep this track and everything after it
                    remaining = self._album_queue[track_index + 1:]

                    if self._current_song:
                        self._history.append(self._current_song)
                        if len(self._history) > 50:
                            self._history.pop(0)

                    self._current_song = selected_track
                    self._last_artist  = selected_track.artist
                    self._album_queue  = remaining
                    self._is_running   = True

                else:
                    # Song not found in remaining queue — ignore click
                    return

            else:
                # Not in album mode — treat as normal play_specific
                from src.catalog.repository import get_song_by_id
                song = get_song_by_id(self.conn, song_id)
                if song is None:
                    return
                if self._current_song:
                    self._history.append(self._current_song)
                self._current_song = song
                self._last_artist  = song.artist

            success = self.player.play(self._current_song)
            if not success:
                self._play_next()

    def back(self) -> None:
        """
        Go back to previous song.
        First press restarts current if played more than 3 seconds.
        Second press plays previous song from history.
        """
        if self._current_song:
            duration_played = self.player._get_play_duration_ms()
            if duration_played > 3000:
                self.player.stop()
                self.player.play(self._current_song)
                return

        if self._history:
            prev_song = self._history.pop()
            self.player.stop()
            self._current_song = prev_song
            self._last_artist  = prev_song.artist
            self.player.play(prev_song)

    # ── Private methods ────────────────────────────────────────

    def _play_next(self) -> None:
        """
        Play the next song. If album mode is active and there are
        songs in the album queue, play them in-order (or shuffled
        if album queue was shuffled). Otherwise, use the normal
        prefetched / scoring flow.
        """
        with self._lock:
            # If album-mode is active, obey the album queue strictly
            if self._album_mode:
                if self._album_queue:
                    next_song = self._album_queue.pop(0)
                    chosen = None
                else:
                    # Album finished — return to normal shuffle
                    self._album_mode = False
                    self._album_queue = []
                    self._album_shuffle_enabled = False
                    chosen = self._select_next_song()
                    next_song = None
                    return
            else:
                if self._prefetched is not None:
                    chosen = self._prefetched
                    self._prefetched = None
                else:
                    chosen = self._select_next_song()
                next_song = None

            if next_song is None and chosen is None:
                print("\n  No songs available to play.")
                return

        # Save current song to history before switching
        if self._current_song:
            self._history.append(self._current_song)
            # Keep history bounded to last 50 songs
            if len(self._history) > 50:
                self._history.pop(0)

        if next_song is not None:
            song_to_play = next_song
            print(f"\n  Now playing (album): {song_to_play.display_name}")
            self._current_song = song_to_play
            self._last_artist  = song_to_play.artist
            success = self.player.play(song_to_play)

            # Emit queue update if available (IPCEngine provides helper)
            try:
                if hasattr(self, "_emit_queue"):
                    self._emit_queue()
            except Exception:
                pass

            if not success:
                # File unplayable — try next album track
                self._play_next()
            return

        # Normal selection path
        self._current_song = chosen.song
        self._last_artist  = chosen.song.artist

        print(f"\n  Now playing: {chosen.song.display_name}")
        print(f"  {get_selection_explanation(chosen)}")

        success = self.player.play(chosen.song)

        if success:
            threading.Thread(
                target=self._prefetch_next,
                daemon=True
            ).start()
        else:
            # File unplayable — skip to next immediately
            self._play_next()

    def _prefetch_next(self) -> None:
        """
        Run in background thread during playback.
        By the time current song ends, next one is ready.
        """
        chosen = self._select_next_song()
        with self._lock:
            self._prefetched = chosen

    def _select_next_song(self) -> Optional[ScoredSong]:
        """Score all songs and select the next one."""
        from src.scorer.scorer import get_unplayed_songs
        from src.scorer.models import ScoringContext

        scored   = score_all_songs(self.conn)
        context  = build_scoring_context(self.conn)

        if not scored:
            return None

        # Build exploration pool from unplayed songs
        unplayed = get_unplayed_songs(self.conn, limit=50)
        exploration_pool = [
            ScoredSong(
                song=s,
                final_score=1.0,
                preference_score=1.0,
                recency_score=1.0,
                artist_score=1.0,
                genre_score=1.0,
            )
            for s in unplayed
        ]

        # Apply hard diversity rules
        filtered = apply_hard_filters(
            scored,
            last_song_id=self._current_song.id if self._current_song else None,
            last_artist=self._last_artist,
        )

        if self._global_shuffle_enabled:
            return random.choice(filtered) if filtered else None

        return select_next_song(
            filtered,
            exploration_songs=exploration_pool,
            exploration_rate=0.20,
        )

    def _handle_player_event(self, event: TrackEvent) -> None:
        """
        Called by the player whenever something happens.
        This is the core reactive loop of the engine.
        """
        if event.event_type == "started":
            self._record_event(
                event.song, EventType.PLAY, event.play_duration_ms
            )

        elif event.event_type == "completed":
            self._record_event(
                event.song, EventType.COMPLETE, event.play_duration_ms
            )
            self._update_weight(event.song.id)
            if self._is_running:
                if self._album_mode and self._album_queue:
                    self._play_next()
                elif self._album_mode:
                    self._album_mode = False
                    self._album_queue = []
                    self._album_shuffle_enabled = False
                    self._is_running = False
                else:
                    self._play_next()

        elif event.event_type == "skipped":
            self._record_event(
                event.song, EventType.SKIP, event.play_duration_ms
            )
            self._update_weight(event.song.id)
            if self._is_running:
                self._play_next()

    def _record_event(
        self,
        song: Song,
        event_type: str,
        play_duration_ms: int
    ) -> None:
        """Write one event to the event store."""
        try:
            record_event(self.conn, PlayEvent(
                song_id=          song.id,
                event_type=       event_type,
                session_id=       self.session.get_id(),
                play_duration_ms= play_duration_ms,
                song_duration_ms= song.duration_ms,
            ))
        except Exception as e:
            print(f"  [engine] Failed to record event: {e}")

    def _update_weight(self, song_id: str) -> None:
        """Update the preference model after an interaction."""
        try:
            update_song_weight(self.conn, song_id)
        except Exception as e:
            print(f"  [engine] Failed to update weight: {e}")