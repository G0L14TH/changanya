# Time decay functions — make recent events matter more than old ones.
# This is the mathematical heart of the learning system

from datetime import datetime
import math


def exponential_decay(
    event_time: datetime,
    now: datetime,
    half_life_days: float = 30.0
) -> float:
    """
    Calculate how much an event still matters based on its age.

    Returns a value between 0.0 and 1.0:
        1.0  → event happened right now, full weight
        0.5  → event happened exactly half_life_days ago
        0.25 → event happened 2 * half_life_days ago
        ~0.0 → event happened a very long time ago

    half_life_days = 30 means an event loses half its
    influence every 30 days. You can tune this number:
        Lower (e.g. 7)  → adapts to taste changes quickly
        Higher (e.g. 90) → more stable, slower to forget

    The formula is the standard exponential decay function
    used in physics, finance, and recommendation systems:
        weight = 0.5 ^ (age_in_days / half_life_days)

    Which is equivalent to:
        weight = e ^ (-lambda * age_in_days)
    where lambda = ln(2) / half_life_days
    """
    age_days = (now - event_time).total_seconds() / 86_400.0

    # Never let age go negative (clock drift, timezone issues)
    age_days = max(0.0, age_days)

    return math.pow(0.5, age_days / half_life_days)


def recency_penalty(
    last_played: datetime | None,
    now: datetime,
    cooldown_minutes: float = 60.0
) -> float:
    """
    How much to penalise a song for having been played recently.

    Returns a multiplier between 0.0 and 1.0:
        0.0  → played just now, don't play again
        0.5  → played half a cooldown period ago
        1.0  → cooldown period has fully passed, no penalty

    cooldown_minutes = 60 means a song needs an hour before
    it's fully eligible again. Adjust to taste:
        30 min  → short sessions, small libraries
        120 min → long sessions, avoid repetition more strongly
    """
    if last_played is None:
        return 1.0  # Never played, no penalty at all

    minutes_since = (now - last_played).total_seconds() / 60.0
    minutes_since = max(0.0, minutes_since)

    if minutes_since >= cooldown_minutes:
        return 1.0  # Fully cooled down

    # Linear ramp from 0.0 to 1.0 over the cooldown period
    return minutes_since / cooldown_minutes