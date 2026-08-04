# src/shuffle_engine/ipc.py
#
# IPC bridge — lets the Tauri backend control the
# Python engine by sending JSON commands over stdin
# and receiving JSON events over stdout.
#
# This is the ONLY new file needed to make the existing
# engine work with the Tauri UI. Everything else stays
# exactly as built.

import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

# Add project root to path so imports work when
# launched as a subprocess from Tauri
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.catalog.repository import update_album_tags
from src.db.connection import get_connection
from src.shuffle_engine.engine import ShuffleEngine


def sanitise(value: str | None, fallback: str = "Unknown") -> str:
    """
    Remove or replace characters that aren't valid UTF-8.
    Rust's stdout reader requires clean UTF-8 on every line.
    """
    if value is None:
        return fallback
    return value.encode("utf-8", errors="replace").decode("utf-8")


def emit(event_type: str, data: dict) -> None:
    """
    Write a JSON event to stdout.
    Tauri reads these lines and forwards them to React.
    Each line is one complete JSON object — never split.
    ensure_ascii=True forces all non-ASCII characters to be
    escaped as uXXXX sequences — guaranteed safe for Rust's
    UTF-8 reader regardless of song metadata.
    """
    payload = json.dumps(
        {"event": event_type, "data": data},
        ensure_ascii=True,
    )
    print(payload, flush=True)


def _toggle_like(conn, song_id: str) -> None:
    """Toggle favourite status for a song."""
    existing = conn.execute(
        "SELECT 1 FROM favourites WHERE song_id = ?",
        (song_id,),
    ).fetchone()

    if existing:
        conn.execute(
            "DELETE FROM favourites WHERE song_id = ?",
            (song_id,),
        )
    else:
        conn.execute(
            "INSERT INTO favourites (song_id, liked_at) VALUES (?, ?)",
            (song_id, datetime.now().isoformat()),
        )
        # Boost preference weight for liked songs
        conn.execute(
            """
            INSERT INTO song_weights (song_id, weight, skip_ratio,
                play_count, skip_count, last_updated)
            VALUES (?, 3.0, 0.0, 0, 0, ?)
            ON CONFLICT(song_id) DO UPDATE SET
                weight = MIN(weight + 1.0, 5.0),
                last_updated = excluded.last_updated
            """,
            (song_id, datetime.now().isoformat()),
        )
    conn.commit()


def _is_liked(conn, song_id: str) -> bool:
    """Check if a song is favourited."""
    row = conn.execute(
        "SELECT 1 FROM favourites WHERE song_id = ?",
        (song_id,),
    ).fetchone()
    return row is not None


def _emit_home_data(conn) -> None:
    """
    Emit all data needed for the Home screen in one call.
    Recently played, recommended picks, favorites summary.
    """
    threading.Thread(target=_emit_home_data_bg, args=(conn,), daemon=True).start()


def _emit_home_data_bg(conn) -> None:
    """Runs in the background; scoring takes a moment."""
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT s.id, s.title, s.artist, s.album,
                            s.duration_ms, e.timestamp
            FROM events e
            JOIN songs s ON s.id = e.song_id
            WHERE e.event_type IN ('play', 'complete')
            ORDER BY e.timestamp DESC
            LIMIT 8
            """
        ).fetchall()

        recently_played = []
        seen = set()
        for row in rows:
            if row["id"] not in seen:
                seen.add(row["id"])
                project_root = Path(__file__).parent.parent.parent.resolve()
                art = project_root / "artwork" / f"{row['id']}.png"
                recently_played.append(
                    {
                        "id": sanitise(row["id"]),
                        "title": sanitise(row["title"]),
                        "artist": sanitise(row["artist"]),
                        "album": sanitise(row["album"]),
                        "duration_ms": row["duration_ms"] or 0,
                        "artwork_path": str(art) if art.exists() else None,
                    }
                )

        from src.scorer.scorer import score_all_songs

        scored = score_all_songs(conn)

        recent_ids = {s["id"] for s in recently_played}
        recommended_raw = [
            s
            for s in scored
            if s.song.id not in recent_ids
        ][:5]

        recommended = []
        for s in recommended_raw:
            project_root = Path(__file__).parent.parent.parent.resolve()
            art = project_root / "artwork" / f"{s.song.id}.png"
            recommended.append(
                {
                    "id": sanitise(s.song.id),
                    "title": sanitise(s.song.title),
                    "artist": sanitise(s.song.artist),
                    "album": sanitise(s.song.album),
                    "duration_ms": s.song.duration_ms or 0,
                    "artwork_path": str(art) if art.exists() else None,
                    "score": round(s.final_score, 2),
                }
            )

        fav_rows = conn.execute(
            """
            SELECT s.id, s.title, s.artist, s.duration_ms
            FROM favourites f
            JOIN songs s ON s.id = f.song_id
            ORDER BY f.liked_at DESC
            LIMIT 20
            """
        ).fetchall()

        favorites = [
            {
                "id": sanitise(r["id"]),
                "title": sanitise(r["title"]),
                "artist": sanitise(r["artist"]),
                "duration_ms": r["duration_ms"] or 0,
            }
            for r in fav_rows
        ]

        mood_playlists = _generate_mood_playlists(conn)

        emit(
            "home_data",
            {
                "recently_played": recently_played,
                "recommended": recommended,
                "favorites": favorites,
                "mood_playlists": mood_playlists,
            },
        )
    except Exception as e:
        import traceback

        traceback.print_exc()
        emit("error", {"message": f"home data failed: {e}"})


def _generate_mood_playlists(conn) -> list:
    """
    Generate mood-based playlist suggestions from the library.
    This is based on genre clusters and listening patterns.
    """
    playlists = []

    fav_count = conn.execute("SELECT COUNT(*) FROM favourites").fetchone()[0]
    if fav_count > 0:
        playlists.append(
            {
                "id": "favorites",
                "name": "Favorites",
                "count": fav_count,
                "icon": "heart",
            }
        )

    genre_rows = conn.execute(
        """
        SELECT genre, COUNT(*) as cnt
        FROM songs
        WHERE genre IS NOT NULL
        GROUP BY genre
        ORDER BY cnt DESC
        LIMIT 6
        """
    ).fetchall()

    mood_map = {
        "hip hop": ("Dark Hours", "moon"),
        "rap": ("Street Vibes", "microphone"),
        "r&b": ("Late Night", "stars"),
        "jazz": ("Deep Focus", "coffee"),
        "classical": ("Focus Mode", "piano"),
        "rock": ("High Energy", "bolt"),
        "pop": ("Feel Good", "sun"),
        "electronic": ("Night Drive", "headphones"),
        "ambient": ("Chill Zone", "wave"),
    }

    for row in genre_rows:
        genre_lower = (row["genre"] or "").lower()
        for key, (name, icon) in mood_map.items():
            if key in genre_lower:
                playlists.append(
                    {
                        "id": f"mood_{key}",
                        "name": name,
                        "count": row["cnt"],
                        "icon": icon,
                    }
                )
                break

    unplayed_count = conn.execute(
        """
        SELECT COUNT(*) FROM songs s
        LEFT JOIN song_weights w ON s.id = w.song_id
        WHERE w.last_played IS NULL
            OR w.last_played < datetime('now', '-30 days')
        """
    ).fetchone()[0]

    if unplayed_count > 0:
        playlists.append(
            {
                "id": "throwback",
                "name": "Throwback",
                "count": min(unplayed_count, 50),
                "icon": "clock",
            }
        )

    return playlists[:5]


class IPCEngine(ShuffleEngine):
    """
    ShuffleEngine with IPC event emission added.
    Overrides _handle_player_event to also emit
    state to the UI after every player interaction.
    """
    def _play_next(self) -> None:
        was_album = self._album_mode
        super()._play_next()
        #notify UI when album mode ends
        if was_album and not self._album_mode:
            emit("album_mode_changed", {"enabled": False})
            emit("queue-update", {"upcoming": []})
            
    def _handle_player_event(self, event) -> None:
        # Run the normal engine logic first
        super()._handle_player_event(event)

        # Then emit current state to the UI after every interaction
        if event.event_type in ("started", "completed", "skipped"):
            try:
                self._emit_now_playing()
            except Exception as e:
                import traceback

                emit("error", {"message": f"emit failed: {e}"})
                traceback.print_exc(file=sys.stderr)

    def _get_artwork_path(self, song_id: str) -> str | None:
        """Return artwork file path if it exists, else None."""
        project_root = Path(__file__).parent.parent.parent.resolve()
        art_path = project_root / "artwork" / f"{song_id}.png"
        return str(art_path) if art_path.exists() else None

    def _emit_now_playing(self) -> None:
        """Emit current song and queue state to the UI."""
        song = self.get_current_song()

        if not song:
            emit("status", {"message": "loading"})
            return

        emit(
            "now_playing",
            {
                "id": sanitise(song.id),
                "title": sanitise(song.title),
                "artist": sanitise(song.artist),
                "album": sanitise(song.album),
                "year": song.year,
                "duration_ms": song.duration_ms or 0,
                "artwork_path": self._get_artwork_path(song.id),
                "liked": _is_liked(self.conn, song.id),
                "album_mode": getattr(self, "_album_mode", False),
                "shuffle_enabled": getattr(self, "_global_shuffle_enabled", False),
                "album_shuffle_enabled": getattr(self, "_album_shuffle_enabled", False),
            },
        )

        # Emit queue separately in a background thread
        # so that UI updates instantly without waiting for scoring
        threading.Thread(target=self._emit_queue, daemon=True).start()

    def _emit_queue(self) -> None:
        """Score and emit the upcoming queue; runs in the background."""
        try:
            song = self.get_current_song()
            if not song:
                return

            # Album mode - emit remaining album songs, not shuffle picks
            if self._album_mode and self._album_queue:
                upcoming = []
                for s in self._album_queue[:5]:
                    art_path = self._get_artwork_path(s.id)
                    upcoming.append({
                        "id": sanitise(s.id),
                        "title": sanitise(s.display_title or s.title),
                        "artist": sanitise(s.artist) if s.artist else "Uknown Artist",
                        "score": 1.0,
                        "reason": "Album queue",
                        "artwork_path": art_path,
                    })
                    return
                
                # Normal shuffle mode - score and pick
                from src.scorer.scorer import score_all_songs
                from src.selector.selector import select_next_n_songs
                from src.selector.diversity import apply_hard_filters

                scored = score_all_songs(self.conn)
                filtered = apply_hard_filters(
                    scored,
                    last_song_id=song.id,
                    last_artist=song.artist,
                )
                upcoming_scored = select_next_n_songs(filtered, n=5)

                emit("queue_update", {
                    "upcoming": [
                        {
                            "id": sanitise(s.song.id),
                            "title": sanitise(s.song.display_title or s.song.title),
                            "artist":sanitise(s.song.artist) if s.song.artist else "Unknown Artist",
                            "score": round(s.final_score, 2),
                            "reason": sanitise(s.reasoning()),
                            "artwork_path": self._get_artwork_path(s.song.id),
                        }
                        for s in upcoming_scored
                    ]
                })
        except Exception as e:
            emit("error", {"message": f"queue emit failed: {e}"})

def _emit_library_songs(conn, sort_by: str = "title") -> None:
    """Emit all non-recording songs sorted by the given field."""
    # For title sorting, put items whose first character is not a letter
    # (symbols, numbers) before letter-starting titles (a..z), then sort
    # case-insensitively. Other sort modes remain unchanged.
    if sort_by == "title":
        display_field = "COALESCE(display_title, title, file_path)"
        order = (
            "CASE WHEN lower(substr(" + display_field + ", 1, 1)) BETWEEN 'a' AND 'z' "
            "THEN 1 ELSE 0 END, lower(" + display_field + ")"
        )
    else:
        valid_sorts = {
            "artist":     "COALESCE(artist, 'Unknown Artist')",
            "album":      "COALESCE(album, '')",
            "date_added": "date_added DESC",
            "play_count": "play_count DESC",
        }
        order = valid_sorts.get(sort_by, "COALESCE(display_title, title, file_path)")

    rows = conn.execute(f"""
        SELECT id, title, artist, album, genre, year,
            duration_ms, play_count, display_title
        FROM songs
        WHERE is_recording = 0
        ORDER BY {order}
    """).fetchall()

    project_root = Path(__file__).parent.parent.parent.resolve()

    songs = []
    for r in rows:
        art = project_root / "artwork" / f"{r['id']}.png"
        songs.append({
            "id":           sanitise(r["id"]),
            "title":        sanitise(r.get("display_title") or r.get("title")),
            "artist":       sanitise(r["artist"]) if r["artist"] else "Unknown Artist",
            "album":        sanitise(r["album"]) if r["album"] else "Unknown Album",
            "genre":        sanitise(r["genre"]) if r["genre"] else "",
            "year":         r.get("year"),
            "duration_ms":  r.get("duration_ms") or 0,
            "play_count":   r.get("play_count") or 0,
            "artwork_path": str(art) if art.exists() else None,
        })

    emit("library_songs", {"songs": songs})


def _emit_library_artists(conn) -> None:
    """Emit all artists with song counts."""
    rows = conn.execute("""
        SELECT
            COALESCE(artist, 'Unknown Artist') as artist,
            COUNT(*) as song_count,
            MIN(id) as sample_id
        FROM songs
        WHERE is_recording = 0
        GROUP BY COALESCE(artist, 'Unknown Artist')
        ORDER BY artist
    """).fetchall()

    from pathlib import Path as _P
    project_root = _P(__file__).parent.parent.parent.resolve()

    artists = []
    for r in rows:
        art = project_root / "artwork" / f"{r['sample_id']}.png"
        artists.append({
            "name":         sanitise(r["artist"]),
            "song_count":   r["song_count"],
            "artwork_path": str(art) if art.exists() else None,
        })

    emit("library_artists", {"artists": artists})


def _emit_library_albums(conn) -> None:
    """Emit all albums with track counts."""
    rows = conn.execute("""
        SELECT
            COALESCE(album, 'Unknown Album') as album,
            COALESCE(artist, 'Unknown Artist') as artist,
            COUNT(*) as track_count,
            MIN(year) as year,
            MIN(id) as sample_id
        FROM songs
        WHERE is_recording = 0
        GROUP BY COALESCE(album, 'Unknown Album'),
                 COALESCE(artist, 'Unknown Artist')
        ORDER BY album
    """).fetchall()

    from pathlib import Path as _P
    project_root = _P(__file__).parent.parent.parent.resolve()

    albums = []
    for r in rows:
        art = project_root / "artwork" / f"{r['sample_id']}.png"
        albums.append({
            "name":         sanitise(r["album"]),
            "artist":       sanitise(r["artist"]),
            "track_count":  r["track_count"],
            "year":         r["year"],
            "artwork_path": str(art) if art.exists() else None,
        })

    emit("library_albums", {"albums": albums})


def _emit_artist_songs(conn, artist: str) -> None:
    """Emit all songs by a specific artist."""
    rows = conn.execute("""
        SELECT id, title, album, year, duration_ms, display_title
        FROM songs
        WHERE is_recording = 0
          AND COALESCE(artist, 'Unknown Artist') = ?
        ORDER BY album, title
    """, (artist,)).fetchall()

    from pathlib import Path as _P
    project_root = _P(__file__).parent.parent.parent.resolve()

    songs = []
    for r in rows:
        art = project_root / "artwork" / f"{r['id']}.png"
        songs.append({
            "id":           sanitise(r["id"]),
            "title":        sanitise(r["display_title"] or r["title"]),
            "album":        sanitise(r["album"]) if r["album"] else "Unknown Album",
            "year":         r["year"],
            "duration_ms":  r["duration_ms"] or 0,
            "artwork_path": str(art) if art.exists() else None,
        })

    emit("artist_songs", {"artist": sanitise(artist), "songs": songs})


def _emit_album_songs(conn, album: str, artist: str) -> None:
    """Emit all songs in a specific album."""
    rows = conn.execute("""
        SELECT id, title, year, duration_ms, display_title
        FROM songs
        WHERE is_recording = 0
          AND COALESCE(album, 'Unknown Album') = ?
          AND COALESCE(artist, 'Unknown Artist') = ?
        ORDER BY file_path
    """, (album, artist)).fetchall()

    from pathlib import Path as _P
    project_root = _P(__file__).parent.parent.parent.resolve()

    songs = []
    for r in rows:
        art = project_root / "artwork" / f"{r['id']}.png"
        songs.append({
            "id":           sanitise(r["id"]),
            "title":        sanitise(r["display_title"] or r["title"]),
            "year":         r["year"],
            "duration_ms":  r["duration_ms"] or 0,
            "artwork_path": str(art) if art.exists() else None,
        })

    emit("album_songs", {
        "album":  sanitise(album),
        "artist": sanitise(artist),
        "songs":  songs,
    })


def run_ipc() -> None:
    """
    Main IPC loop.
    Starts the engine, then reads JSON commands
    from stdin forever until the process is killed.
    """
    conn = get_connection()
    engine = IPCEngine(conn)

    emit("ready", {"status": "engine started"})
    engine.start()

    # Give engine time to load first song
    time.sleep(2)
    engine._emit_now_playing()

    def progress_ticker() -> None:
        # Wait for first song to start
        while not engine.player.is_playing():
            time.sleep(0.5)

        while True:
            time.sleep(1)
            try:
                if engine.player.is_playing():
                    ms = engine.player._get_play_duration_ms()
                    if ms > 0:
                        emit("progress", {"ms": ms})
            except Exception as e:
                sys.stderr.write(f"[progress ticker] {e}\n")
                sys.stderr.flush()

    ticker = threading.Thread(target=progress_ticker, daemon=True)
    ticker.start()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            command = json.loads(line)
            action = command.get("action")

            if action == "skip":
                engine.skip()
            elif action == "pause_resume":
                engine.pause_resume()
            elif action == "seek":
                position_ms = command.get("position_ms", 0)
                engine.player.seek(int(position_ms))
            elif action == "stop":
                engine.stop()
                break
            elif action == "get_state":
                engine._emit_now_playing()
            elif action == "like_song":
                song_id = command.get("song_id")
                if song_id:
                    _toggle_like(engine.conn, song_id)
                    engine._emit_now_playing()

            elif action == "seek_relative":
                delta_ms = command.get("delta_ms", 0)
                current = engine.player._get_play_duration_ms()
                new_pos = max(0, current + int(delta_ms))
                engine.player.seek(new_pos)

            elif action == "play_album_track":
                album = command.get("album", "")
                artist = command.get("artist", "")
                song_id = command.get("song_id", "")
                if album and artist and song_id:
                    engine.play_album_track(album, artist, song_id)

            elif action == "get_liked":
                song_id = command.get("song_id")
                if song_id:
                    liked = _is_liked(engine.conn, song_id)
                    emit("like_status", {"song_id": song_id, "liked": liked})
                    
            elif action == "set_global_shuffle":
                enabled = command.get("enabled", True)
                engine._shuffle_enabled = enabled
                emit("shuffle_changed", {"enabled": enabled})

            elif action == "set_album_shuffle":
                enabled = command.get("enabled", True)
                engine.set_album_shuffle(enabled)
                emit("album_shuffle_changed", {"enabled": enabled})
                
            elif action == "set_volume":
                vol = command.get("volume", 75)
                engine.player.set_volume(int(vol))

            elif action == "get_library_songs":
                sort_by = command.get("sort_by", "title")
                _emit_library_songs(conn, sort_by)

            elif action == "get_library_artists":
                _emit_library_artists(conn)

            elif action == "get_library_albums":
                _emit_library_albums(conn)

            elif action == "get_artist_songs":
                artist = command.get("artist", "")
                _emit_artist_songs(conn, artist)

            elif action == "get_album_songs":
                album  = command.get("album", "")
                artist = command.get("artist", "")
                _emit_album_songs(conn, album, artist)
                
            elif action == "get_home_data":
                _emit_home_data(engine.conn)
            
            elif action == "play_specific":
                song_id = command.get("song_id")
                if song_id:
                    engine.play_specific(song_id)

            elif action == "play_album":
                album = command.get("album", "")
                artist = command.get("artist", "")
                shuffle = command.get("shuffle", False)
                engine.play_album(album, artist, shuffle)
                emit("album_mode_changed", {"enabled": True})
                emit("album_shuffle_changed", {"enabled": shuffle})
                emit("shuffle_changed", {"enabled": False})


            elif action == "set_shuffle":
                enabled = bool(command.get("enabled", False))
                engine.set_global_shuffle(enabled)

            elif action == "set_album_shuffle":
                enabled = bool(command.get("enabled", False))
                engine.set_album_shuffle(enabled)

            elif action == "edit_album_tags":
                album = command.get("album", "")
                artist = command.get("artist", "")
                new_album = command.get("new_album")
                new_artist = command.get("new_artist")
                genre = command.get("genre")
                year_text = command.get("year")
                year = None
                if year_text not in (None, ""):
                    try:
                        year = int(year_text)
                    except ValueError:
                        year = None

                update_album_tags(
                    conn,
                    album,
                    artist,
                    new_album=new_album,
                    new_artist=new_artist,
                    genre=genre,
                    year=year,
                )
                _emit_library_songs(conn, "title")
                _emit_library_artists(conn)
                _emit_library_albums(conn)
                emit("status", {"message": "album tags updated"})

            elif action == "back":
                engine.back()
        except json.JSONDecodeError:
            emit("error", {"message": f"Invalid command: {line}"})
        except Exception as e:
            emit("error", {"message": str(e)})

    conn.close()
