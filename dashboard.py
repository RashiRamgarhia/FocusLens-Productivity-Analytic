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
        ctk.CTkSwitch(startup_box, text="Run FocusLens automatically on Windows startup",
                      variable=self.startup_var, command=self._toggle_startup).pack(anchor="w", padx=16, pady=16)

        return tab

    def _refresh_quick_suggestions(self):
        if not hasattr(self, "suggestions_frame"):
            return
        for child in self.suggestions_frame.winfo_children():
            child.destroy()
        try:
            apps = database.get_today_apps()
            if not apps:
                return
            ctk.CTkLabel(self.suggestions_frame, text="Recently detected today (click to select):",
                         font=ctk.CTkFont(size=11), text_color=COLORS["subtext"]).pack(anchor="w", pady=(0, 3))
            pills_row = ctk.CTkFrame(self.suggestions_frame, fg_color="transparent")
            pills_row.pack(anchor="w", fill="x")
            for app in apps[:8]:
                ctk.CTkButton(
                    pills_row, text=app, height=22, font=ctk.CTkFont(size=11),
                    fg_color="#262A34", hover_color="#343A48",
                    command=lambda a=app: self.new_app_name_var.set(a)
                ).pack(side="left", padx=2, pady=2)
        except Exception:
            pass

    # ------------------ EXPORT & DATA TAB ------------------
    def _create_export_tab(self):
        tab = ctk.CTkFrame(self.tab_container, fg_color="transparent")

        card = ctk.CTkFrame(tab, fg_color=COLORS["card"], corner_radius=12, width=440)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text="Data Management", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(24, 8))
        ctk.CTkLabel(card, text="Export your usage data or clear saved history.", text_color=COLORS["subtext"]).pack(pady=(0, 16))

        ctk.CTkButton(card, text="Export CSV to File", width=220, command=self._export_to_csv).pack(pady=8)
        ctk.CTkButton(card, text="Clear All History", width=220, fg_color=COLORS["Unproductive"],
                      hover_color="#CC0000", command=self._clear_all_data).pack(pady=(8, 24))

        return tab

    # ------------------ REFRESH & CHARTS ------------------
    def refresh_all_visuals(self):
        df_today = analytics.load_data(days=1)
        metrics = analytics.calculate_metrics(df_today, days=1)

        # Update KPIs
        self.kpi_labels["Score"].configure(text=f"{metrics['score']}%")
        self.kpi_labels["Focus Efficiency"].configure(text=f"{metrics['focus_efficiency']}")
        self.kpi_labels["Productive Time"].configure(text=metrics["productive_time"])
        if "Unproductive" in self.kpi_labels:
            self.kpi_labels["Unproductive"].configure(text=metrics["unproductive_time"])
        elif "Distractions" in self.kpi_labels:
            self.kpi_labels["Distractions"].configure(text=metrics["unproductive_time"])
        self.kpi_labels["App Switches"].configure(text=str(metrics["context_switches"]))

        goal = metrics["goal_minutes"]
        completed = metrics["productive_minutes"]
        self.goal_text.configure(text=f"Daily goal: {completed}m / {goal}m")
        self.goal_progress.set(min(completed / max(1, goal), 1.0))

        # Insights
        insights = analytics.generate_insights(df_today)
        self.insight_banner.configure(text="  •  ".join(insights))

        # Dashboard charts
        self.fig_dash.clear()
        if not df_today.empty and df_today["seconds"].sum() > 0:
            ax1 = self.fig_dash.add_subplot(121)
            totals = df_today.groupby("category")["seconds"].sum()
            colors = [COLORS.get(cat, COLORS.get("Necessary", "#F1C40F")) for cat in totals.index]
            ax1.pie(
                totals, labels=totals.index, autopct="%1.0f%%", startangle=90,
                colors=colors, wedgeprops=dict(width=0.45, edgecolor=COLORS["card"])
            )
            ax1.set_title("Time by Category", fontsize=11, pad=10)

            ax2 = self.fig_dash.add_subplot(122)
            top = analytics.top_apps_breakdown(df_today, 5)
            if not top.empty:
                bars = ax2.barh(top.index[::-1], top.values[::-1], color=COLORS["accent"], height=0.55)
                labels = [analytics.format_time(int(round(v * 60))) for v in top.values[::-1]]
                ax2.bar_label(bars, labels=labels, padding=4, color=COLORS["text"], fontsize=9)
                ax2.set_title("Top Apps Today", fontsize=11, pad=10)
                max_val = max(top.values) if len(top.values) > 0 else 1
                ax2.set_xlim(0, max_val * 1.35 + 0.1)
                ax2.spines["top"].set_visible(False)
                ax2.spines["right"].set_visible(False)
                ax2.grid(axis="x", linestyle="--", alpha=0.3)
        else:
            ax = self.fig_dash.add_subplot(111)
            ax.text(0.5, 0.5, "No activity logged today yet.\nTracking is running in the background.",
                    ha="center", va="center", color=COLORS["subtext"], fontsize=12)
            ax.set_axis_off()

        self.fig_dash.tight_layout()
        self.canvas_dash.draw_idle()

        # History charts
        df_week = analytics.load_data(days=7)
        self.fig_history.clear()
        if not df_week.empty and df_week["seconds"].sum() > 0:
            ax_week = self.fig_history.add_subplot(211)
            week_table = analytics.weekly_trend(df_week)
            colors = [COLORS.get(c, COLORS.get("Necessary", "#F1C40F")) for c in week_table.columns]
            week_table.plot(kind="bar", stacked=True, ax=ax_week, color=colors, width=0.45, rot=0)
            ax_week.set_title("Past 7 Days (Hours)", fontsize=11)
            ax_week.set_ylabel("Hours")
            ax_week.spines["top"].set_visible(False)
            ax_week.spines["right"].set_visible(False)

            ax_hourly = self.fig_history.add_subplot(212)
            matrix = analytics.hourly_intensity_matrix(df_week)
            ax_hourly.plot(matrix.index, matrix["Productive"], label="Productive", color=COLORS["Productive"], lw=2)
            unprod_col = "Unproductive" if "Unproductive" in matrix.columns else "Distracting"
            ax_hourly.plot(matrix.index, matrix[unprod_col], label="Unproductive", color=COLORS["Unproductive"], lw=2)
            ax_hourly.fill_between(matrix.index, matrix["Productive"], color=COLORS["Productive"], alpha=0.15)
            ax_hourly.set_title("Daily Focus by Hour (Average Minutes)", fontsize=11)
            ax_hourly.set_xlabel("Hour of Day (0–23)")
            ax_hourly.set_xticks(range(0, 24, 2))
            ax_hourly.legend(frameon=False, loc="upper right")
            ax_hourly.spines["top"].set_visible(False)
            ax_hourly.spines["right"].set_visible(False)
        else:
            ax = self.fig_history.add_subplot(111)
            ax.text(0.5, 0.5, "No activity logged over the past 7 days.", ha="center", va="center",
                    color=COLORS["subtext"], fontsize=12)
            ax.set_axis_off()

        self.fig_history.tight_layout()
        self.canvas_history.draw_idle()

        self._refresh_weekly_summary()

    def _auto_refresh_loop(self):
        self.refresh_all_visuals()
        self.after(20000, self._auto_refresh_loop)

    def _check_warnings_loop(self):
        while not self.tracker.warnings.empty():
            bad_app = self.tracker.warnings.get()
            self._show_distraction_notice(bad_app)
        self.after(1000, self._check_warnings_loop)

    def _toggle_tracking(self):
        if self.tracker.running:
            self.tracker.stop()
            self.track_btn.configure(text="Start Tracking", fg_color=COLORS["accent"])
            self.status_lbl.configure(text="○ Tracker Paused", text_color=COLORS["subtext"])
        else:
            self.tracker.start()
            self.track_btn.configure(text="Stop Tracking", fg_color=COLORS["Unproductive"], hover_color="#CC0000")
            self.status_lbl.configure(text="● Tracking Active", text_color=COLORS["Productive"])

    def _toggle_focus_mode(self):
        self.tracker.focus_mode = bool(self.alert_switch.get())

    def _show_distraction_notice(self, app_name):
        # Prevent spamming multiple alert popups
        if self.active_alert and self.active_alert.winfo_exists():
            return

        try:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass

        self.active_alert = ctk.CTkToplevel(self)
        self.active_alert.title("Focus Reminder")
        self.active_alert.geometry("340x120")
        self.active_alert.resizable(False, False)
        self.active_alert.attributes("-topmost", True)

        ctk.CTkLabel(self.active_alert, text="Unproductive App Reminder", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["Unproductive"]).pack(pady=(16, 4))
        ctk.CTkLabel(self.active_alert, text=f"{app_name} is marked as Unproductive.\nReady to get back to work?").pack()
        self.active_alert.after(4000, lambda: self.active_alert.destroy() if self.active_alert and self.active_alert.winfo_exists() else None)

    # ------------------ POMODORO LOGIC ------------------
    def _apply_pomodoro_settings(self):
        try:
            work = int(self.work_minutes_var.get())
            pause = int(self.break_minutes_var.get())
            if not (1 <= work <= 180 and 1 <= pause <= 60):
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter 1–180 minutes for work and 1–60 for break.")
            return

        self.work_seconds = work * 60
        self.break_seconds = pause * 60
        self._reset_pomodoro()

    def _toggle_pomodoro(self):
        if self.pomodoro_running:
            self.pomodoro_running = False
            if self.pomo_job:
                self.after_cancel(self.pomo_job)
                self.pomo_job = None
            self.pomo_action_btn.configure(text="Resume")
        else:
            self.pomodoro_running = True
            self.pomo_action_btn.configure(text="Pause")
            if self.pomo_job:
                self.after_cancel(self.pomo_job)
            self.pomo_job = self.after(1000, self._pomo_tick)

    def _pomo_tick(self):
        if not self.pomodoro_running:
            return

        if self.time_left > 0:
            self.time_left -= 1
            mins = self.time_left // 60
            secs = self.time_left % 60
            self.pomo_clock_lbl.configure(text=f"{mins:02d}:{secs:02d}")
            self.pomo_job = self.after(1000, self._pomo_tick)
        else:
            # Interval complete
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass

            if self.is_work_time:
                database.add_focus_session(self.work_seconds // 60, self.break_seconds // 60)
                self._update_session_history_label()

            self.is_work_time = not self.is_work_time
            self.time_left = self.work_seconds if self.is_work_time else self.break_seconds
            status_text = "Focus Session" if self.is_work_time else "Break Time"
            self.pomo_title_lbl.configure(text=status_text)

            mins = self.time_left // 60
            secs = self.time_left % 60
            self.pomo_clock_lbl.configure(text=f"{mins:02d}:{secs:02d}")

            messagebox.showinfo("Pomodoro Timer", f"Time is up! Starting: {status_text}")
            self.pomo_job = self.after(1000, self._pomo_tick)

    def _reset_pomodoro(self):
        if self.pomo_job:
            self.after_cancel(self.pomo_job)
            self.pomo_job = None
        self.pomodoro_running = False
        self.is_work_time = True
        self.time_left = self.work_seconds
        self.pomo_title_lbl.configure(text="Focus Session")

        mins = self.time_left // 60
        secs = self.time_left % 60
        self.pomo_clock_lbl.configure(text=f"{mins:02d}:{secs:02d}")
        self.pomo_action_btn.configure(text="Start Session")

    def _update_session_history_label(self):
        sessions = database.get_focus_sessions(5)
        if not sessions:
            self.pomo_history_lbl.configure(text="Recent completed sessions: none yet")
            return
        lines = [f"{d}: {w}m work / {b}m break" for d, w, b in sessions]
        self.pomo_history_lbl.configure(text="Recent completed sessions:\n" + "\n".join(lines))

    # ------------------ SETTINGS ACTIONS ------------------
    def _save_goal(self):
        try:
            minutes = int(self.goal_input_var.get())
            if not 1 <= minutes <= 1440:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a daily goal between 1 and 1440 minutes.")
            return

        database.set_setting("daily_goal_minutes", minutes)
        self.refresh_all_visuals()
        messagebox.showinfo("Saved", f"Daily goal set to {minutes} minutes.")

    def _add_custom_category(self):
        name = self.new_app_name_var.get().strip().lower().replace(".exe", "")
        if not name:
            messagebox.showerror("Missing Name", "Please enter an application name.")
            return

        database.save_custom_category(name, self.new_category_var.get())
        categories.refresh_custom_categories()
        self.new_app_name_var.set("")
        self._refresh_categories_ui()
        self._refresh_quick_suggestions()
        self.refresh_all_visuals()

    def _refresh_categories_ui(self):
        for child in self.categories_list_frame.winfo_children():
            child.destroy()

        entries = database.get_custom_categories()
        if not entries:
            ctk.CTkLabel(self.categories_list_frame, text="No custom categories added.",
                         text_color=COLORS["subtext"]).pack(anchor="w")
            return

        for app_name, category in entries:
            row = ctk.CTkFrame(self.categories_list_frame, fg_color="#262A34")
            row.pack(fill="x", pady=2)
            cat_color = COLORS.get(category, COLORS["Necessary"])
            ctk.CTkLabel(row, text=f"{app_name}  →  ", font=ctk.CTkFont(size=12)).pack(side="left", padx=(10, 0), pady=4)
            ctk.CTkLabel(row, text=category, text_color=cat_color, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left", pady=4)
            ctk.CTkButton(
                row, text="Remove", width=65, height=24, fg_color=COLORS["Unproductive"],
                hover_color="#CC0000",
                command=lambda a=app_name: self._remove_custom_category(a)
            ).pack(side="right", padx=6, pady=2)

    def _remove_custom_category(self, app_name):
        database.remove_custom_category(app_name)
        categories.refresh_custom_categories()
        self._refresh_categories_ui()
        self._refresh_quick_suggestions()
        self.refresh_all_visuals()

    def _toggle_startup(self):
        try:
            startup.set_enabled(bool(self.startup_var.get()))
        except Exception as err:
            self.startup_var.set(1 if startup.is_enabled() else 0)
            messagebox.showerror("Error", f"Could not update Windows startup setting:\n{err}")

    # ------------------ EXPORT & REPORT ------------------
    def _refresh_weekly_summary(self):
        if not hasattr(self, "weekly_textbox"):
            return
        lines = analytics.weekly_report(analytics.load_data(days=7))
        self.weekly_textbox.configure(state="normal")
        self.weekly_textbox.delete("1.0", "end")
        self.weekly_textbox.insert("end", "\n\n".join(lines))
        self.weekly_textbox.configure(state="disabled")

    def _export_to_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="focuslens_data.csv"
        )
        if file_path:
            df = analytics.load_data(days=30)
            analytics.export_csv(df, file_path)
            messagebox.showinfo("Export Successful", f"Saved 30-day usage data to:\n{file_path}")

    def _clear_all_data(self):
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to erase all logged tracking data?"):
            database.clear_all()
            self.refresh_all_visuals()
            self._refresh_quick_suggestions()
            messagebox.showinfo("Cleared", "All tracking data has been cleared.")

    def _on_closing(self):
        if self.pomo_job:
            self.after_cancel(self.pomo_job)
        if self.tracker.running:
            self.tracker.stop()
        self.destroy()
