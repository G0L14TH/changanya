# check_db.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.db.connection import get_connection

conn = get_connection()

recordings    = conn.execute("SELECT COUNT(*) FROM songs WHERE is_recording = 1").fetchone()[0]
cleaned       = conn.execute("SELECT COUNT(*) FROM songs WHERE display_title IS NOT NULL AND is_recording = 0").fetchone()[0]
still_unknown = conn.execute("SELECT COUNT(*) FROM songs WHERE title IS NULL AND is_recording = 0").fetchone()[0]
total         = conn.execute("SELECT COUNT(*) FROM songs").fetchone()[0]

print(f"Total songs:        {total}")
print(f"Recordings flagged: {recordings}")
print(f"Titles cleaned:     {cleaned}")
print(f"Still unknown:      {still_unknown}")

print("\nSample flagged as recordings:")
rows = conn.execute("""
    SELECT file_path FROM songs
    WHERE is_recording = 1
    LIMIT 20
""").fetchall()
for r in rows:
    print(f"  {Path(r['file_path']).name}")

print("\nSample cleaned titles:")
rows = conn.execute("""
    SELECT title, artist, display_title
    FROM songs
    WHERE display_title IS NOT NULL
    AND is_recording = 0
    LIMIT 8
""").fetchall()
for r in rows:
    print(f"  [{r['display_title']}] — {r['artist']}")

conn.close()