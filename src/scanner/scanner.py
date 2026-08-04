
import sqlite3
from pathlib import Path
from typing import Iterator, Optional
import mutagen
from mutagen import MutagenError

from src.catalog.models import Song
from src.catalog.repository import insert_song, song_exists

SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".ogg", ".m4a", ".aac", ".wav", ".opus"}


def _get_artwork_dir() -> Path:
    """Find artwork directory relative to project root."""
    project_root = Path(__file__).parent.parent.parent.resolve()
    artwork_dir  = project_root / "artwork"
    artwork_dir.mkdir(exist_ok=True)
    return artwork_dir


def extract_album_art(file_path: Path, song_id: str) -> str | None:
    """
    Extract embedded album art from an audio file
    and save it as a PNG in the artwork folder.

    Returns the path to the saved artwork file,
    or None if no artwork was found.
    """
    artwork_dir = _get_artwork_dir()
    output_path = artwork_dir / f"{song_id}.png"

    # Already extracted — skip
    if output_path.exists():
        return str(output_path)

    try:
        audio = mutagen.File(str(file_path))
        if audio is None:
            return None

        art_data = None

        # MP3 — ID3 tags store art as APIC frames
        if hasattr(audio, 'tags') and audio.tags:
            for key in audio.tags.keys():
                if key.startswith('APIC'):
                    art_data = audio.tags[key].data
                    break

        # FLAC / OGG — picture block
        if art_data is None and hasattr(audio, 'pictures'):
            if audio.pictures:
                art_data = audio.pictures[0].data

        # M4A / AAC — covr atom
        if art_data is None and 'covr' in (audio or {}):
            covers = audio['covr']
            if covers:
                art_data = bytes(covers[0])

        if art_data:
            output_path.write_bytes(art_data)
            return str(output_path)

    except Exception:
        pass

    return None


def _read_tag(tags, *keys: str) -> str | None:
    """
    Try multiple tag key names and return the first value found.
    """
    if tags is None:
        return None
    for key in keys:
        value = tags.get(key)
        if value:
            return str(value[0]).strip() if isinstance(value, list) else str(value).strip()
    return None

def _read_year(audio) -> Optional[int]:
    """Extract year from audio tags"""
    raw = _read_tag(audio, "date", "year", "originaldate")
    if raw is None:
        return None
    try:
        # year can be "2024" or "2024-01-15", take first 4 chars
        return int(str(raw)[:4])
    except (ValueError, TypeError):
        return None

def read_song_metadata(file_path: Path) -> Song | None:
    """
    Read one audio file and return a Song with its metadata.
    Returns None if the file can't be read.
    """
    try:
        audio = mutagen.File(str(file_path), easy=True)

        if audio is None:
            return None

        duration_ms = None
        if audio.info and hasattr(audio.info, 'length'):
            duration_ms = int(audio.info.length * 1000)

        return Song(
            file_path=   str(file_path.resolve()),
            title=       _read_tag(audio, "title"),
            artist=      _read_tag(audio, "artist", "albumartist"),
            album=       _read_tag(audio, "album"),
            genre=       _read_tag(audio, "genre"),
            year=       _read_year(audio),
            duration_ms= duration_ms,
        )

    except MutagenError:
        return None
    except Exception:
        return None


def iter_audio_files(root_path: Path) -> Iterator[Path]:
    for file_path in root_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            yield file_path


def scan_library(
    conn: sqlite3.Connection,
    music_folder: str | Path,
    verbose: bool = True
) -> dict:
    """
    Scan a folder and add all found songs to the catalog.

    Returns a summary dict:
        found:    total audio files discovered
        added:    new songs inserted into the catalog
        skipped:  files already in the catalog
        failed:   files that couldn't be read
    """
    root = Path(music_folder)

    if not root.exists():
        raise FileNotFoundError(f"Music folder not found: {root}")
    if not root.is_dir():
        raise ValueError(f"Path is not a folder: {root}")

    stats = {"found": 0, "added": 0, "skipped": 0, "failed": 0}

    for file_path in iter_audio_files(root):
        stats["found"] += 1

        if song_exists(conn, str(file_path.resolve())):
            stats["skipped"] += 1
            continue

        song = read_song_metadata(file_path)

        if song is None:
            stats["failed"] += 1
            continue

        insert_song(conn, song)

        # Extract album art alongside scanning
        extract_album_art(file_path, song.id)

        stats["added"] += 1

        if verbose:
            print(f"  + {song.display_name}")

    return stats