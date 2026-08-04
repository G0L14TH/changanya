# src/scanner/metadata_cleaner.py
#
# Cleans up song metadata for songs with missing tags.
# Three strategies are involved: filename parsing, recording detection,
# and optional MusicBrainz lookup.

import re
import sqlite3
from pathlib import Path
from typing import Optional


# Patterns that indicate a file is a recording, not a song
RECORDING_PATTERNS = [
    r'\d{4}-\d{2}-\d{2}',              # date: 2023-08-21
    r'\d{2}-\d{2}-\d{2}_RECORD',       # timestamp_RECORD
    r'_RECORD$',                         # ends with _RECORD
    r'^RECORD_',                         # starts with RECORD_
    r'recording',                        # contains "recording"
    r'voice[\s_]memo',                   # voice memo
    r'voice[\s_]note',                   # voice note
    r'^AUD-\d{8}-WA',                   # WhatsApp audio
    r'^\d+\.\d+\s*bpm',                 # BPM in filename (FL Studio)
    r'\d{3}\.\d+\s*bpm',               # "129.706 bpm"
]

RECORDING_RE = re.compile(
    '|'.join(RECORDING_PATTERNS),
    re.IGNORECASE
)


def is_likely_recording(filename: str) -> bool:
    """
    Check if a filename looks like a recording rather than a song.
    FL Studio recordings, voice memos, screen recordings etc.
    """
    return bool(RECORDING_RE.search(filename))


def clean_filename_to_title(filename: str) -> str:
    """
    Convert a filename into a readable display title.

    Examples:
        "jay_z_heaven.mp3"          → "Jay Z Heaven"
        "01 - Creep.flac"           → "Creep"
        "Track 03.mp3"              → "Track 03"
        "Radiohead-Creep.mp3"       → "Radiohead - Creep"
    """
    # Remove extension
    name = Path(filename).stem

    # Remove leading track numbers: "01 - ", "01. ", "01 "
    name = re.sub(r'^\d{1,3}[\s.\-_]+', '', name)

    # Replace underscores and dots with spaces
    name = name.replace('_', ' ')

    # Normalise multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    # Clean up common patterns
    name = re.sub(r'\s*\(\d+\)\s*$', '', name) # remove (1), (2) at end

    # Title case — but preserve ALL CAPS words (acronyms)
    words = []
    for word in name.split():
        if word.isupper() and len(word) > 2:
            words.append(word)
        elif word.lower() in ('ft', 'feat', 'featuring', 'x', 'vs', 'and', 'the', 'a'):
            words.append(word.lower())
        else:
            words.append(word.capitalize())
    name = ' '.join(words)

    return name or Path(filename).stem


def parse_artist_title_from_filename(
    filename: str
) -> tuple[Optional[str], str]:
    """
    Try to extract artist and title from common filename formats.

    Patterns tried:
        "Artist - Title.mp3"     → ("Artist", "Title")
        "Artist_Title.mp3"       → fallback, ("Unknown", cleaned name)
        "Title.mp3"              → (None, "Title")
    """
    stem = Path(filename).stem

    # remove content in parantheses that look like fetures
    # before splitting so it doesn't confuse the separator detection
    # "Nimerudi Tena - Remix (feat. derrick!)" -> "Nimerudi Tena - Remix"

    clean_stem = re.sub(r'\s*\(feat[^)]*\)', '', stem, flags=re.IGNORECASE)
    clean_stem = re.sub(r'\s*ft\.[^-_]+', '', clean_stem, flags=re.IGNORECASE)

    # Pattern 1: "Title _ Artist ft Someone.mp3"
    match = re.match(r'^(.+?)\s*[_]\s*(.+)$', clean_stem)
    if match:
        # check which sides looks like a title vs artist
        artist = clean_filename_to_title(match.group(1))
        title  = clean_filename_to_title(match.group(2))
        return artist, title

    # Pattern 2: "Artist - Title"
    match = re.match(r'^(.+?)\s*[-]\s*(.+)$', clean_stem)
    if match:
        artist = clean_filename_to_title(match.group(1))
        title  = clean_filename_to_title(match.group(2))
        return artist, title

    # No artist separator found — just clean the filename
    return None, clean_filename_to_title(stem)


def apply_filename_fallbacks(conn: sqlite3.Connection) -> dict:
    """
    For all songs with missing title or artist, apply
    filename-based fallbacks and detect recordings.

    Returns a summary of what was updated.
    """
    rows = conn.execute("""
        SELECT id, file_path, title, artist
        FROM songs
        WHERE title IS NULL OR artist IS NULL
    """).fetchall()

    stats = {
        "total":      len(rows),
        "recordings": 0,
        "cleaned":    0,
    }

    for row in rows:
        filename    = Path(row["file_path"]).name
        song_id     = row["id"]
        title       = row["title"]
        artist      = row["artist"]

        # Check if this is a recording
        if is_likely_recording(filename):
            conn.execute("""
                UPDATE songs
                SET is_recording  = 1,
                    display_title = ?
                WHERE id = ?
            """, (f"[Recording] {clean_filename_to_title(filename)}", song_id))
            stats["recordings"] += 1
            continue

        # Parse artist and title from filename
        parsed_artist, parsed_title = parse_artist_title_from_filename(filename)

        new_title  = title  or parsed_title
        new_artist = artist or parsed_artist

        conn.execute("""
            UPDATE songs
            SET display_title = ?,
                title  = CASE WHEN title  IS NULL THEN ? ELSE title  END,
                artist = CASE WHEN artist IS NULL THEN 'Unknown Artist' ELSE artist END
            WHERE id = ?
        """, (new_title, new_title, song_id))
        stats["cleaned"] += 1

    conn.commit()
    return stats