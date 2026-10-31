import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "focuslens.db")
_initialized = False


def get_connection():
    global _initialized
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA busy_timeout = 10000")
    if not _initialized:
        _init_db(conn)
        _initialized = True
    return conn


def _init_db(conn):
    conn.execute("PRAGMA journal_mode = WAL")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usage (
            date TEXT,
            hour INTEGER,
            app_name TEXT,
            seconds INTEGER,
            PRIMARY KEY (date, hour, app_name)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS window_switches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            date TEXT,
            hour INTEGER,
            app_name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS custom_categories (
            app_name TEXT PRIMARY KEY COLLATE NOCASE,
            category TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS focus_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            date TEXT NOT NULL,
            work_minutes INTEGER NOT NULL,
            break_minutes INTEGER NOT NULL
        )
    """)

    # Migrate legacy category names
    cursor.execute("UPDATE custom_categories SET category = 'Other' WHERE category IN ('Neutral', 'Necessary')")
    cursor.execute("UPDATE custom_categories SET category = 'Unproductive' WHERE category = 'Distracting'")

    conn.commit()


def create_tables():
    conn = get_connection()
    conn.close()


def add_usage(app_name, seconds):
    if not app_name or seconds <= 0:
        return
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    hour = now.hour

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO usage (date, hour, app_name, seconds)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(date, hour, app_name)
        DO UPDATE SET seconds = seconds + excluded.seconds
    """, (date_str, hour, app_name, int(seconds)))
    conn.commit()
    conn.close()


def record_window_switch(app_name):
    if not app_name:
        return
    now = datetime.now()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO window_switches (timestamp, date, hour, app_name)
        VALUES (?, ?, ?, ?)
    """, (now.isoformat(), now.strftime("%Y-%m-%d"), now.hour, app_name))
    conn.commit()
    conn.close()


def get_usage(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT date, hour, app_name, seconds 
        FROM usage 
        WHERE date BETWEEN ? AND ?
    """, (start_date, end_date)).fetchall()
    conn.close()
    return rows


def get_switch_count(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("""
        SELECT COUNT(*) 
        FROM window_switches 
        WHERE date BETWEEN ? AND ?
    """, (start_date, end_date)).fetchone()
    conn.close()
    return row[0] if row else 0


def clear_all():
    conn = get_connection()
