import os
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "FocusLens"


def _command():
    program = sys.executable
    pythonw = os.path.join(os.path.dirname(program), "pythonw.exe")
    if os.path.exists(pythonw):
        program = pythonw
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.py")
    return f'"{program}" "{script}"'


def is_enabled():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
        return value == _command()
    except Exception:
        return False


def set_enabled(enabled):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _command())
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
    except Exception:
        pass
