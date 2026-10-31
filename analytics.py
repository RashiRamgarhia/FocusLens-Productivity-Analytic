from datetime import datetime, timedelta
import numpy as np
import pandas as pd

import categories
import database


def get_daily_goal_minutes():
    try:
        val = int(database.get_setting("daily_goal_minutes", 180))
        return val if 1 <= val <= 1440 else 180
    except Exception:
        return 180


def format_time(seconds):
    seconds = int(seconds or 0)
    if seconds <= 0:
        return "0h 00m"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}h {minutes:02d}m"
    if minutes > 0:
        return f"{minutes}m {secs:02d}s" if secs > 0 else f"{minutes}m"
    return f"{secs}s"


def load_data(days=1):
    today = datetime.now().date()
    start = today - timedelta(days=max(0, days - 1))

    rows = database.get_usage(str(start), str(today))
    if not rows:
        return pd.DataFrame(columns=["date", "hour", "app_name", "seconds", "category"])

    df = pd.DataFrame(rows, columns=["date", "hour", "app_name", "seconds"])
