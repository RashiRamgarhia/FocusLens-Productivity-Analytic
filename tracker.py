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
        title = buf.value

        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return "desktop", title

        try:
            name = psutil.Process(pid.value).name()
        except Exception:
            name = "system"

        name = str(name).lower().replace(".exe", "")
        return name, title
    except Exception:
        return "system", "Active Window"


def get_idle_seconds():
    try:
        info = LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(LASTINPUTINFO)
        if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            now = ctypes.windll.kernel32.GetTickCount()
            elapsed_ms = ctypes.c_uint(now - info.dwTime).value
            return elapsed_ms / 1000.0
    except Exception:
        pass
    return 0.0


def _is_media_active(app_name):
    lower = str(app_name or "").lower()
    return any(k in lower for k in MEDIA_KEYWORDS)


