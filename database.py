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
