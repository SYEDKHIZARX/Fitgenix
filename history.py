# ============================================================
# history.py — Handles saving and loading user history
# ============================================================

import json
import os
from datetime import datetime

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_history.json")

def load_history():
    """Load all saved history from file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_entry(entry: dict):
    """
    Save one day's result to history.
    entry = {date, steps, active_minutes, bmi, calorie_score,
             calorie_intensity, rl_rec, goal, fatigue}
    """
    history = load_history()

    # Add timestamp
    entry["date"] = datetime.now().strftime("%Y-%m-%d")
    entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Avoid duplicate entries for same day
    history = [h for h in history if h.get("date") != entry["date"]]
    history.append(entry)

    # Keep last 90 days only
    history = sorted(history, key=lambda x: x["date"])[-90:]

    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

def get_streak(history):
    """Calculate current consecutive-day streak."""
    if not history:
        return 0
    from datetime import date, timedelta
    today = date.today()
    streak = 0
    for i in range(len(history) - 1, -1, -1):
        entry_date = date.fromisoformat(history[i]["date"])
        expected   = today - timedelta(days=streak)
        if entry_date == expected:
            streak += 1
        else:
            break
    return streak

def get_best_streak(history):
    """Calculate the all-time best streak."""
    if not history:
        return 0
    from datetime import date, timedelta
    best = current = 1
    for i in range(1, len(history)):
        d1 = date.fromisoformat(history[i-1]["date"])
        d2 = date.fromisoformat(history[i]["date"])
        if (d2 - d1).days == 1:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best