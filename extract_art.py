# extract_art.py
# One-time script to extract album art for all existing songs

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.connection import get_connection
from src.catalog.repository import get_all_songs
from src.scanner.scanner import extract_album_art

conn  = get_connection()
songs = get_all_songs(conn)

found    = 0
missing  = 0

print(f"Extracting artwork for {len(songs)} songs...\n")

for song in songs:
    art_path = extract_album_art(Path(song.file_path), song.id)
    if art_path:
        found += 1
    else:
        missing += 1

print(f"\nDone.")
print(f"  Artwork found:   {found}")
print(f"  No artwork:      {missing}")

conn.close()