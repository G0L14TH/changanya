# src/db/connection.py

import sqlite3
from pathlib import Path
from src.db.schema import create_all_tables, migrate_database 


def _find_project_root() -> Path:
    """
    Find the project root regardless of where the script is run from.
    Works in development (running from project root) and when
    launched as a subprocess from Tauri.

    This file lives at src/db/connection.py
    So project root is three levels up.
    """
    return Path(__file__).parent.parent.parent.resolve()


PROJECT_ROOT  = _find_project_root()
DEFAULT_DB_PATH = PROJECT_ROOT / "changanya.db"
print(f"[db] Using database at {DEFAULT_DB_PATH}", flush=True)


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:

    conn = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    # Ensure all tables exist before returning
    create_all_tables(conn)
    migrate_database(conn)
    return conn