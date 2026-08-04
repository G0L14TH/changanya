# src/scanner/musicbrainz.py
#
# Fetch missing metadata from MusicBrainz.
# Free API, no key needed.
# Rate limit: 1 request per second (we respect this).

import time
import sqlite3
import urllib.request
import urllib.parse
import json
from pathlib import Path
from typing import Optional


MUSICBRAINZ_URL = "https://musicbrainz.org/ws/2"
USER_AGENT      = "Changanya/1.0 (music player; contact@changanya.app)"
RATE_LIMIT_SEC  = 1.1   # slightly over 1 second to be safe


def _search(query: str, entity: str = "recording") -> Optional[dict]:
    """
    Search MusicBrainz for a recording.
    Returns the first result or None.
    """
    params = urllib.parse.urlencode({
        "query": query,
        "limit": 1,
        "fmt":   "json",
    })
    url = f"{MUSICBRAINZ_URL}/{entity}?{params}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            recordings = data.get("recordings", [])
            if recordings:
                return recordings[0]
    except Exception:
        pass

    return None


def fetch_metadata_for_song(
    title: str,
    artist: Optional[str] = None,
) -> Optional[dict]:
    """
    Look up a song on MusicBrainz and return metadata.

    Returns a dict with keys: title, artist, album, year
    or None if not found.
    """
    if artist:
        query = f'recording:"{title}" AND artist:"{artist}"'
    else:
        query = f'recording:"{title}"'

    result = _search(query)
    if not result:
        return None

    # Extract what we need
    meta: dict = {}

    meta["title"] = result.get("title")

    # Artist
    credits = result.get("artist-credit", [])
    if credits:
        meta["artist"] = credits[0].get("artist", {}).get("name")

    # Album and year from first release
    releases = result.get("releases", [])
    if releases:
        release = releases[0]
        meta["album"] = release.get("title")
        date = release.get("date", "")
        if date and len(date) >= 4:
            try:
                meta["year"] = int(date[:4])
            except ValueError:
                pass

    return meta if meta.get("title") else None


def enrich_library_metadata(
    conn: sqlite3.Connection,
    limit: int = 100,
    verbose: bool = True,
) -> dict:
    """
    Find songs with partial metadata and enrich them via MusicBrainz.
    Only processes songs that have a title but might be missing
    artist, album, or year — not recordings.

    limit: max songs to process in one run (respect rate limits)
    """
    rows = conn.execute("""
        SELECT id, title, artist, album, year
        FROM songs
        WHERE is_recording = 0
          AND title IS NOT NULL
          AND (artist IS NULL OR album IS NULL OR year IS NULL)
        LIMIT ?
    """, (limit,)).fetchall()

    stats = {"processed": 0, "enriched": 0, "not_found": 0}

    for row in rows:
        stats["processed"] += 1

        if verbose:
            print(f"  Looking up: {row['title']}", end="", flush=True)

        meta = fetch_metadata_for_song(row["title"], row["artist"])

        if meta:
            conn.execute("""
                UPDATE songs SET
                    artist = COALESCE(artist, ?),
                    album  = COALESCE(album,  ?),
                    year   = COALESCE(year,   ?)
                WHERE id = ?
            """, (
                meta.get("artist"),
                meta.get("album"),
                meta.get("year"),
                row["id"],
            ))
            conn.commit()
            stats["enriched"] += 1
            if verbose:
                print(f" → {meta.get('artist', '?')} / {meta.get('album', '?')}")
        else:
            stats["not_found"] += 1
            if verbose:
                print(" → not found")

        # Respect MusicBrainz rate limit
        time.sleep(RATE_LIMIT_SEC)

    return stats