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
    df["category"] = df["app_name"].apply(categories.get_category)
    return df


def calculate_metrics(df, days=1):
    goal_minutes = get_daily_goal_minutes()
    if df.empty:
        return {
            "score": 0,
            "productive_time": "0h 00m",
            "unproductive_time": "0h 00m",
            "distracting_time": "0h 00m",
            "necessary_time": "0h 00m",
            "other_time": "0h 00m",
            "neutral_time": "0h 00m",
            "context_switches": 0,
            "focus_efficiency": 0.0,
            "goal_minutes": goal_minutes,
            "productive_minutes": 0,
        }

    prod_sec = float(df[df["category"] == "Productive"]["seconds"].sum())
    unprod_sec = float(df[df["category"].isin(["Unproductive", "Distracting"])]["seconds"].sum())
    nec_sec = float(df[df["category"].isin(["Necessary", "Neutral", "Other"])]["seconds"].sum())

    rated_time = prod_sec + unprod_sec
    raw_score = (prod_sec / rated_time * 100) if rated_time > 0 else 0

    today = datetime.now().date()
    start = today - timedelta(days=max(0, days - 1))
    switches = database.get_switch_count(str(start), str(today))

    # Small penalty if there is excessive window switching
    total_hours = max((prod_sec + unprod_sec + nec_sec) / 3600.0, 0.5)
    switches_per_hour = switches / total_hours
    penalty = min(switches_per_hour * 0.4, 25.0)
    focus_efficiency = max(0.0, round(raw_score - penalty, 1))

    return {
        "score": round(raw_score),
        "productive_time": format_time(prod_sec),
        "unproductive_time": format_time(unprod_sec),
        "distracting_time": format_time(unprod_sec),
        "necessary_time": format_time(nec_sec),
        "other_time": format_time(nec_sec),
        "neutral_time": format_time(nec_sec),
        "context_switches": switches,
        "focus_efficiency": focus_efficiency,
        "goal_minutes": goal_minutes,
        "productive_minutes": int(prod_sec // 60),
    }


def hourly_intensity_matrix(df):
    hours = np.arange(24)
    matrix = pd.DataFrame(0.0, index=hours, columns=categories.CATEGORY_NAMES)

    if not df.empty:
        grouped = df.groupby(["hour", "category"])["seconds"].sum().unstack(fill_value=0)
        for cat in categories.CATEGORY_NAMES:
            if cat in grouped.columns:
                matrix[cat] = grouped[cat].reindex(hours, fill_value=0.0)

    matrix = matrix.fillna(0.0)
    return matrix / 60.0


def top_apps_breakdown(df, limit=5):
    if df.empty:
        return pd.Series(dtype=float)
    totals = df.groupby("app_name")["seconds"].sum().sort_values(ascending=False).head(limit)
    return totals / 60.0


def weekly_trend(df):
    if df.empty:
        return pd.DataFrame(columns=categories.CATEGORY_NAMES)
    pivot = df.pivot_table(
        index="date",
        columns="category",
        values="seconds",
        aggfunc="sum",
        fill_value=0
    )
    pivot = pivot.reindex(columns=categories.CATEGORY_NAMES, fill_value=0)
    return pivot / 3600.0


def generate_insights(df):
    if df.empty:
        return ["No activity logged today yet. Tracking is running in the background."]

    insights = []
    by_app = df.groupby("app_name")["seconds"].sum()
    if not by_app.empty:
        top_app = by_app.idxmax()
        insights.append(f"Most used app: {top_app} ({format_time(by_app.max())})")

    unproductive = df[df["category"].isin(["Unproductive", "Distracting"])]
    if not unproductive.empty:
        worst_app = unproductive.groupby("app_name")["seconds"].sum().idxmax()
        worst_hour = unproductive.groupby("hour")["seconds"].sum().idxmax()
        unprod_seconds = unproductive.groupby("app_name")["seconds"].sum().max()
        insights.append(f"Top unproductive: {worst_app} ({format_time(unprod_seconds)}) around {worst_hour:02d}:00")
    else:
        insights.append("Great job! Zero unproductive apps today.")

    productive = df[df["category"] == "Productive"]
    if not productive.empty:
        peak_hour = productive.groupby("hour")["seconds"].sum().idxmax()
        insights.append(f"Best focus window: {peak_hour:02d}:00 - {(peak_hour + 1) % 24:02d}:00")

    return insights


def weekly_report(df):
    metrics = calculate_metrics(df, days=7)
    if df.empty:
        return ["No activity recorded this week yet. Keep tracking to generate your summary."]

    report = [
        f"Focus score: {metrics['score']}%",
        f"Productive time: {metrics['productive_time']}",
        f"Unproductive time: {metrics['unproductive_time']}",
        f"Focus efficiency: {metrics['focus_efficiency']}%",
        f"Total app switches: {metrics['context_switches']}",
    ]

    unproductive = df[df["category"].isin(["Unproductive", "Distracting"])]
    if not unproductive.empty:
        worst_app = unproductive.groupby("app_name")["seconds"].sum().idxmax()
        report.append(f"Biggest unproductive app: {worst_app}")
    else:
        report.append("No unproductive apps detected this week.")

    productive = df[df["category"] == "Productive"]
    if not productive.empty:
        best_hour = productive.groupby("hour")["seconds"].sum().idxmax()
        report.append(f"Best focus hour: {best_hour:02d}:00 to {(best_hour + 1) % 24:02d}:00")

    if metrics["focus_efficiency"] < 60:
        report.append("Tip: Try a short 25-minute Pomodoro session before browsing.")
    elif metrics["context_switches"] > 40:
        report.append("Tip: Group similar tasks together to minimize window switching.")
    else:
        report.append("Tip: You're doing great! Keep protecting your peak focus hours.")

    return report


def export_csv(df, path):
    df.to_csv(path, index=False)
