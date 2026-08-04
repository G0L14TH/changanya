# cleanup_metadata.py
# Run once to clean up unknown songs in your library.
# Step 1: filename fallbacks (instant)
# Step 2: MusicBrainz lookup (optional, slow, needs internet)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.db.connection import get_connection
from src.scanner.metadata_cleaner import apply_filename_fallbacks
from src.scanner.musicbrainz import enrich_library_metadata

conn = get_connection()

print("=" * 100)
print("Step 1: Applying filename fallbacks...")
print("=" * 100)
stats = apply_filename_fallbacks(conn)
print(f"\n  Total processed: {stats['total']}")
print(f"  Recordings flagged: {stats['recordings']}")
print(f"  Titles cleaned: {stats['cleaned']}")

print()
print("=" * 100)
print("Step 2: MusicBrainz lookup (first 100 songs)")
print("This is slow — 1 request per second.")
print("Press Ctrl+C to stop early.")
print("=" * 100)

try:
    mb_stats = enrich_library_metadata(conn, limit=100, verbose=True)
    print(f"\n  Processed: {mb_stats['processed']}")
    print(f"  Enriched:  {mb_stats['enriched']}")
    print(f"  Not found: {mb_stats['not_found']}")
except KeyboardInterrupt:
    print("\nStopped early.")

print()
print("Done. Run again to process more songs.")
conn.close()