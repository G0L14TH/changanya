# scan.py
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.db.connection import get_connection
from src.scanner.scanner import scan_library

MUSIC_FOLDER = r"C:\Users\obaed\Music\Music"

if __name__ == "__main__":
    print(f"Scanning: {MUSIC_FOLDER}\n")
    conn = get_connection()
    stats = scan_library(conn, MUSIC_FOLDER, verbose=True)

    print()
    print("-" * 40)
    print(f"  Found:   {stats['found']}")
    print(f"  Added:   {stats['added']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Failed:  {stats['failed']}")