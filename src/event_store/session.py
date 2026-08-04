import uuid
from datetime import datetime

class Session:
    """
    Tracks the current listening session.

    Every event recorded during this session shares
    the same session_id — so we can later ask:
    "what did this user listen to in one sitting?"
    """

    def __init__(self):
        self.session_id:  str      = str(uuid.uuid4())
        self.started_at:  datetime = datetime.now()

    def get_id(self) -> str:
        return self.session_id

    def duration_minutes(self) -> float:
        """How long has this session been running?"""
        delta = datetime.now() - self.started_at
        return delta.total_seconds() / 60