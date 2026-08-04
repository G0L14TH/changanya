import sys
import time
import threading
from src.db.connection import get_connection
from src.shuffle_engine.engine import ShuffleEngine


HELP_TEXT = """
  Ctrls:
    ENTER  → skip to next song
    p      → pause / resume
    q      → quit
"""


def run_cli():
    """Start the shuffle engine with a terminal interface."""
    conn   = get_connection()
    engine = ShuffleEngine(conn)

    print("\n \t CHANGANYA ENGINE")
    print("  " + "─" * 40)
    print(HELP_TEXT)

    engine.start()

    try:
        while True:
            command = input("  > ").strip().lower()

            if command == "q":
                print("\n  Stopping...")
                engine.stop()
                break

            elif command == "p":
                engine.pause_resume()

            elif command == "" :
                # ENTER = skip
                engine.skip()

            else:
                print("  ENTER=skip  p=pause  q=quit")

    except KeyboardInterrupt:
        print("\n  Stopped.")
        engine.stop()

    finally:
        conn.close()
        sys.exit(0)


if __name__ == "__main__":
    run_cli()