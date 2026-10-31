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
            self.sidebar, text="Productivity Tracker", font=ctk.CTkFont(size=12),
            text_color=COLORS["subtext"]
        ).pack(pady=(0, 20))

        self.track_btn = ctk.CTkButton(
            self.sidebar, text="Start Tracking", command=self._toggle_tracking,
            fg_color=COLORS["accent"], hover_color="#2980B9", height=38,
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.track_btn.pack(padx=16, pady=6, fill="x")

        self.status_lbl = ctk.CTkLabel(
            self.sidebar, text="○ Tracker Paused", text_color=COLORS["subtext"],
            font=ctk.CTkFont(size=12)
        )
        self.status_lbl.pack(pady=(2, 14))

        self.alert_switch = ctk.CTkSwitch(
            self.sidebar, text="Unproductive Alert", command=self._toggle_focus_mode,
            progress_color=COLORS["accent"]
        )
        self.alert_switch.pack(padx=16, pady=8, anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=16)

        self.nav_btns = {}
        tab_names = ["Dashboard", "Activity History", "Pomodoro Timer", "Weekly Summary", "Settings", "Export & Data"]
        for name in tab_names:
            btn = ctk.CTkButton(
                self.sidebar, text=name, height=36,
                fg_color="transparent", hover_color="#2A2F3B", anchor="w",
                font=ctk.CTkFont(size=13),
                command=lambda n=name: self._show_tab(n)
            )
            btn.pack(fill="x", padx=12, pady=3)
            self.nav_btns[name] = btn

    def _build_tabs(self):
        self.tab_container = ctk.CTkFrame(self, fg_color="transparent")
        self.tab_container.pack(side="right", fill="both", expand=True, padx=16, pady=16)

        self.tabs = {
            "Dashboard": self._create_dashboard_tab(),
            "Activity History": self._create_history_tab(),
            "Pomodoro Timer": self._create_pomodoro_tab(),
            "Weekly Summary": self._create_weekly_tab(),
            "Settings": self._create_settings_tab(),
            "Export & Data": self._create_export_tab(),
        }
        self._show_tab("Dashboard")

    def _show_tab(self, name):
        for tab_name, frame in self.tabs.items():
            if tab_name == name:
                frame.pack(fill="both", expand=True)
                self.nav_btns[tab_name].configure(fg_color="#2A2F3B")
                if tab_name == "Settings":
                    self._refresh_quick_suggestions()
            else:
                frame.pack_forget()
                self.nav_btns[tab_name].configure(fg_color="transparent")

    # ------------------ DASHBOARD TAB ------------------
    def _create_dashboard_tab(self):
        tab = ctk.CTkFrame(self.tab_container, fg_color="transparent")

        # KPI Summary cards
        kpi_row = ctk.CTkFrame(tab, fg_color="transparent")
        kpi_row.pack(fill="x", pady=(0, 10))

        self.kpi_labels = {}
        cards = [
            ("Score", "0%", COLORS["Productive"]),
            ("Focus Efficiency", "0.0", COLORS["accent"]),
            ("Productive Time", "0h 00m", COLORS["Productive"]),
            ("Unproductive", "0h 00m", COLORS["Unproductive"]),
            ("App Switches", "0", COLORS["subtext"])
        ]
        for title, val, color in cards:
            card = ctk.CTkFrame(kpi_row, fg_color=COLORS["card"], corner_radius=8)
            card.pack(side="left", fill="both", expand=True, padx=4)
            ctk.CTkLabel(card, text=title.upper(), font=ctk.CTkFont(size=10, weight="bold"),
                         text_color=COLORS["subtext"]).pack(pady=(10, 0))
            lbl = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=18, weight="bold"), text_color=color)
            lbl.pack(pady=(0, 10))
            self.kpi_labels[title] = lbl

        # Chart Zone
        chart_frame = ctk.CTkFrame(tab, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True)

        self.fig_dash = Figure(figsize=(7, 4), dpi=100)
        self.canvas_dash = FigureCanvasTkAgg(self.fig_dash, master=chart_frame)
        self.canvas_dash.get_tk_widget().pack(fill="both", expand=True)

        # Insights Banner
        self.insight_banner = ctk.CTkLabel(
            tab, text="", font=ctk.CTkFont(size=12), text_color="#D5DBDB",
            fg_color=COLORS["card"], corner_radius=8, height=34
        )
        self.insight_banner.pack(fill="x", pady=(8, 0))

        # Goal Progress Bar
        self.goal_text = ctk.CTkLabel(tab, text="Daily goal: 0m / 180m", text_color=COLORS["subtext"])
        self.goal_text.pack(anchor="w", pady=(8, 2))
        self.goal_progress = ctk.CTkProgressBar(tab, progress_color=COLORS["Productive"])
        self.goal_progress.pack(fill="x")
        self.goal_progress.set(0)

        return tab

    # ------------------ ACTIVITY HISTORY TAB ------------------
    def _create_history_tab(self):
        tab = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        self.fig_history = Figure(figsize=(8, 5), dpi=100)
        self.canvas_history = FigureCanvasTkAgg(self.fig_history, master=tab)
        self.canvas_history.get_tk_widget().pack(fill="both", expand=True)
        return tab

    # ------------------ POMODORO TAB ------------------
    def _create_pomodoro_tab(self):
        card_holder = ctk.CTkFrame(self.tab_container, fg_color="transparent")

        card = ctk.CTkFrame(card_holder, fg_color=COLORS["card"], corner_radius=12, width=440, height=400)
        card.place(relx=0.5, rely=0.5, anchor="center")

        self.pomo_title_lbl = ctk.CTkLabel(
            card, text="Focus Session", font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["accent"]
        )
        self.pomo_title_lbl.pack(pady=(24, 6))

        inputs_row = ctk.CTkFrame(card, fg_color="transparent")
        inputs_row.pack(pady=4)
        ctk.CTkLabel(inputs_row, text="Work (min):").pack(side="left", padx=4)
        ctk.CTkEntry(inputs_row, width=45, textvariable=self.work_minutes_var).pack(side="left", padx=4)
        ctk.CTkLabel(inputs_row, text="Break (min):").pack(side="left", padx=(12, 4))
        ctk.CTkEntry(inputs_row, width=45, textvariable=self.break_minutes_var).pack(side="left", padx=4)
        ctk.CTkButton(inputs_row, text="Apply", width=60, command=self._apply_pomodoro_settings).pack(side="left", padx=8)

        self.pomo_clock_lbl = ctk.CTkLabel(
            card, text="25:00", font=ctk.CTkFont(size=56, weight="bold"), text_color="#FFFFFF"
        )
        self.pomo_clock_lbl.pack(pady=12)

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(pady=10)

        self.pomo_action_btn = ctk.CTkButton(
            btn_row, text="Start Session", width=110, command=self._toggle_pomodoro,
            fg_color=COLORS["accent"]
        )
        self.pomo_action_btn.pack(side="left", padx=8)

        ctk.CTkButton(
            btn_row, text="Reset", width=80, fg_color="#34495E", hover_color="#415B76",
            command=self._reset_pomodoro
        ).pack(side="left", padx=8)

        self.pomo_history_lbl = ctk.CTkLabel(
            card, text="Recent sessions: none yet", text_color=COLORS["subtext"], justify="left"
        )
        self.pomo_history_lbl.pack(pady=(16, 20))
        self._update_session_history_label()

        return card_holder

    # ------------------ WEEKLY SUMMARY TAB ------------------
    def _create_weekly_tab(self):
        tab = ctk.CTkFrame(self.tab_container, fg_color="transparent")
        ctk.CTkLabel(tab, text="Weekly Summary", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", pady=(10, 4))
        ctk.CTkLabel(tab, text="A simple overview of your computer usage over the last 7 days.",
                     text_color=COLORS["subtext"]).pack(anchor="w")

        self.weekly_textbox = ctk.CTkTextbox(tab, fg_color=COLORS["card"], corner_radius=10, font=ctk.CTkFont(size=14))
        self.weekly_textbox.pack(fill="both", expand=True, pady=16)

        ctk.CTkButton(tab, text="Refresh Report", width=120, command=self._refresh_weekly_summary).pack(anchor="e")
        self._refresh_weekly_summary()
        return tab

    # ------------------ SETTINGS TAB ------------------
    def _create_settings_tab(self):
        tab = ctk.CTkScrollableFrame(self.tab_container, fg_color="transparent")
        ctk.CTkLabel(tab, text="Settings", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", pady=(8, 14))

        # Daily Goal Card
        goal_box = ctk.CTkFrame(tab, fg_color=COLORS["card"])
        goal_box.pack(fill="x", pady=6)
        ctk.CTkLabel(goal_box, text="Daily Productive Goal", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))

        goal_row = ctk.CTkFrame(goal_box, fg_color="transparent")
        goal_row.pack(anchor="w", padx=16, pady=(0, 14))
        self.goal_input_var = tk.StringVar(value=str(database.get_setting("daily_goal_minutes", 180)))
        ctk.CTkEntry(goal_row, width=80, textvariable=self.goal_input_var).pack(side="left")
        ctk.CTkLabel(goal_row, text="minutes").pack(side="left", padx=8)
        ctk.CTkButton(goal_row, text="Save Goal", width=90, command=self._save_goal).pack(side="left", padx=8)

        # Custom Categories Card
        cat_box = ctk.CTkFrame(tab, fg_color=COLORS["card"])
        cat_box.pack(fill="x", pady=6)
        ctk.CTkLabel(cat_box, text="Custom App Categories", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(cat_box, text="Add an application name (e.g. chrome, spotify, youtube) to override its category.",
                     text_color=COLORS["subtext"]).pack(anchor="w", padx=16)

        input_row = ctk.CTkFrame(cat_box, fg_color="transparent")
        input_row.pack(fill="x", padx=16, pady=10)
        self.new_app_name_var = tk.StringVar()
        self.new_category_var = tk.StringVar(value="Productive")
        ctk.CTkEntry(input_row, textvariable=self.new_app_name_var, placeholder_text="App name (e.g. spotify, chrome)").pack(side="left", fill="x", expand=True)
        ctk.CTkOptionMenu(input_row, values=["Productive", "Necessary", "Unproductive"], variable=self.new_category_var, width=130).pack(side="left", padx=8)
        ctk.CTkButton(input_row, text="Add", width=70, command=self._add_custom_category).pack(side="left")

        # Quick suggestions row
        self.suggestions_frame = ctk.CTkFrame(cat_box, fg_color="transparent")
        self.suggestions_frame.pack(fill="x", padx=16, pady=(0, 8))
        self._refresh_quick_suggestions()

        self.categories_list_frame = ctk.CTkFrame(cat_box, fg_color="transparent")
        self.categories_list_frame.pack(fill="x", padx=16, pady=(0, 14))
        self._refresh_categories_ui()

        # Startup Card
        startup_box = ctk.CTkFrame(tab, fg_color=COLORS["card"])
        startup_box.pack(fill="x", pady=6)
        self.startup_var = tk.IntVar(value=1 if startup.is_enabled() else 0)
