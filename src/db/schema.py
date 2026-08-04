#defines the database schema for music recommendation system.

CREATE_SONGS_TABLE = """
CREATE TABLE IF NOT EXISTS songs (
    id           TEXT PRIMARY KEY,
    file_path    TEXT NOT NULL UNIQUE,
    title        TEXT,
    artist       TEXT,
    album        TEXT,
    genre        TEXT,
    year         INTEGER,
    duration_ms  INTEGER,
    bpm          REAL,
    energy       REAL,
    date_added   TEXT NOT NULL,
    play_count   INTEGER NOT NULL DEFAULT 0,
    skip_count   INTEGER NOT NULL DEFAULT 0,
    last_played  TEXT,
    is_recording   INTEGER NOT NULL DEFAULT 0,
    display_title    TEXT
);
"""
CREATE_FAVOURITES_TABLE = """
CREATE TABLE IF NOT EXISTS favourites (
    song_id     TEXT PRIMARY KEY,
    liked_at    TEXT NOT NULL,
    FOREIGN KEY (song_id) REFERENCES songs (id)
);
"""

CREATE_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS events (
    id               TEXT PRIMARY KEY,
    song_id          TEXT NOT NULL,
    event_type       TEXT NOT NULL,
    timestamp        TEXT NOT NULL,
    session_id       TEXT NOT NULL,
    play_duration_ms INTEGER,
    song_duration_ms INTEGER,
    FOREIGN KEY (song_id) REFERENCES songs (id)
);
"""
CREATE_SONG_WEIGHTS_TABLE = """
CREATE TABLE IF NOT EXISTS song_weights (
    song_id      TEXT PRIMARY KEY,
    weight       REAL NOT NULL DEFAULT 1.0,
    skip_ratio   REAL NOT NULL DEFAULT 0.0,
    play_count   INTEGER NOT NULL DEFAULT 0,
    skip_count   INTEGER NOT NULL DEFAULT 0,
    last_played  TEXT,
    last_updated TEXT NOT NULL,
    FOREIGN KEY (song_id) REFERENCES songs (id)
);
"""
CREATE_TAG_WEIGHTS_TABLE = """
CREATE TABLE IF NOT EXISTS tag_weights (
    id           TEXT PRIMARY KEY,
    tag_type     TEXT NOT NULL,
    tag_value    TEXT NOT NULL,
    weight       REAL NOT NULL DEFAULT 1.0,
    last_updated TEXT NOT NULL,
    UNIQUE (tag_type, tag_value)
);
"""
CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_events_song_id ON events (song_id);",
    "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_events_session ON events (session_id);",
    "CREATE INDEX IF NOT EXISTS idx_tag_weights_type ON tag_weights (tag_type);",
]

def create_all_tables(conn) -> None:
    """
    Run all CREATE TABLE and CREATE INDEX statements against a connection.
    Safe to call multiple times — IF NOT EXISTS means it won't
    fail or duplicate anything if the tables already exist.
    """
    cursor = conn.cursor()
    
    cursor.execute(CREATE_SONGS_TABLE)
    cursor.execute(CREATE_EVENTS_TABLE)
    cursor.execute(CREATE_SONG_WEIGHTS_TABLE)
    cursor.execute(CREATE_TAG_WEIGHTS_TABLE)
    cursor.execute(CREATE_FAVOURITES_TABLE)

    for index_sql in CREATE_INDEXES:
        cursor.execute(index_sql)

    conn.commit()
def migrate_database(conn) -> None:
    """
    Add many tables that don't exist yet to an existing database.
    Safe to run on any DB version"""

    cursor = conn.cursor()

    # add favorites table if it doesn't exist
    cursor.execute(CREATE_FAVOURITES_TABLE)

    # adds new columns if missing, ALTER TABLE is safe to run
    # even if the column already exists, it will just fail silently.
    new_colums = [
        ("songs", "year", "INTEGER"),
        ("songs", "is_recording", "INTEGER NOT NULL DEFAULT 0"),
        ("songs", "display_title", "TEXT"),
    ]

    for table, column, col_type in new_colums:
        try: 
            cursor.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {col_type};"
            )
        except Exception:
            pass # colum already exists, ignore the error

    conn.commit()