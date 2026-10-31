import ctypes
import queue
import threading
import time
import psutil

import categories
import database

CHECK_INTERVAL = 3
IDLE_LIMIT_SECONDS = 240
MEDIA_IDLE_LIMIT_SECONDS = 1800  # 30 mins for passive video/audio watching
WARNING_COOLDOWN_SECONDS = 45

MEDIA_KEYWORDS = (
    "youtube", "spotify", "prime", "video", "netflix", "hotstar",
    "disney", "twitch", "vlc", "hulu", "crunchyroll"
)


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint),
    ]


def get_active_window():
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return "desktop", "Desktop"

        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
