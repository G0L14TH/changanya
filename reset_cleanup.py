# reset_cleanup.py
# Resets display_title and artist fallbacks so cleanup can re-run cleanly

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from src.db.connection import get_connection

conn = get_connection()

# Only reset songs that got Unknown Artist from our cleanup
# Don't touch songs that had real artist data
conn.execute("""
    UPDATE songs
    SET display_title = NULL,
        artist = NULL
    WHERE artist = 'Unknown Artist'
    AND is_recording = 0
""")

# Reset all display titles so they get regenerated with fixes
conn.execute("""
    UPDATE songs
    SET display_title = NULL
    WHERE is_recording = 0
""")

conn.commit()
print("Reset complete. Run cleanup_metadata.py again.")
conn.close()
