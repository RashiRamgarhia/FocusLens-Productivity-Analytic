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
