import tkinter as tk
from tkinter import filedialog, messagebox
import winsound
import customtkinter as ctk
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import analytics
import categories
import database
import startup
from tracker import Tracker

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "bg": "#14161B",
    "card": "#1E2129",
    "border": "#2C313D",
    "Productive": "#2ECC71",
    "Necessary": "#F1C40F",
    "Unproductive": "#FF0000",
    # Legacy aliases for backward compatibility
    "Other": "#F1C40F",
    "Neutral": "#F1C40F",
    "Distracting": "#FF0000",
    "accent": "#3498DB",
    "text": "#ECF0F1",
    "subtext": "#95A5A6"
}

matplotlib.rcParams.update({
    "text.color": COLORS["text"],
    "axes.labelcolor": COLORS["text"],
    "xtick.color": COLORS["subtext"],
    "ytick.color": COLORS["subtext"],
    "figure.facecolor": COLORS["card"],
    "axes.facecolor": COLORS["card"],
    "grid.color": COLORS["border"],
    "font.family": "sans-serif"
})


class FocusLensApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("FocusLens - Personal Focus & Productivity Tracker")
        self.geometry("1120x740")
        self.minsize(980, 640)
        self.configure(fg_color=COLORS["bg"])

        self.tracker = Tracker()
        self.active_alert = None

        # Pomodoro variables
        self.work_minutes_var = tk.StringVar(value="25")
        self.break_minutes_var = tk.StringVar(value="5")
        self.work_seconds = 25 * 60
        self.break_seconds = 5 * 60
        self.time_left = self.work_seconds
        self.is_work_time = True
        self.pomodoro_running = False
        self.pomo_job = None

        self._build_sidebar()
        self._build_tabs()

        categories.refresh_custom_categories()
        self.refresh_all_visuals()

        # Start tracking automatically on launch
        self._toggle_tracking()

        # Start periodic background loops
        self._check_warnings_loop()
        self.after(20000, self._auto_refresh_loop)

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=COLORS["card"])
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(
            self.sidebar, text="FocusLens", font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFFFFF"
        ).pack(pady=(24, 2))

        ctk.CTkLabel(
