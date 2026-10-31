# FocusLens

> A lightweight, privacy-focused desktop application built in Python to help you track your digital focus, understand daily computer habits, and reduce distractions.

---

## Overview

FocusLens monitors the active Windows application and classifies its time as **Productive**, **Unproductive**, or **Other**. Every visible app is logged; apps without a rule remain **Other** until you categorize them. All telemetry data is stored locally in an SQLite database on your machine—no cloud services, no remote servers, and no tracking telemetry sent over the internet.

## Key Features

- **Automated Activity Tracking:** Records every active Windows process in the background with automatic idle detection, including unknown and Store apps.
- **Productivity Dashboard:** Real-time KPI cards displaying Focus Score, Focus Efficiency, Productive Time, Unproductive Time, and App Switches.
- **Interactive Visualizations:** Clean Matplotlib charts showing category time distribution and top used applications.
- **7-Day Activity History:** Weekly stacked bar chart and 24-hour focus intensity matrix.
- **Integrated Pomodoro Timer:** Customizable work and break intervals with audio alerts and session logging.
- **Unproductive Alerts:** Desktop reminders are enabled by default whenever an unproductive application is used; turn them off from the sidebar if desired.
- **Customizable Rules:** Add custom application categories in settings to tailor what counts as productive, necessary, or unproductive.
- **Windows Startup Option:** Enable or disable automatic launch on Windows sign-in via registry integration.
- **Privacy First & Export:** Export your usage history to CSV or clear saved data at any time.

---

## Technology Stack

- **GUI Framework:** [CustomTkinter](https://customtkinter.tomschimansky.com/) (modern wrapper around Tkinter)
- **Data Analysis:** [Pandas](https://pandas.pydata.org/) & [NumPy](https://numpy.org/)
- **Visualizations:** [Matplotlib](https://matplotlib.org/)
- **System Telemetry:** [Psutil](https://psutil.readthedocs.io/) & Windows `ctypes` APIs (`user32.dll`, `kernel32.dll`)
- **Storage:** Local SQLite database with WAL (Write-Ahead Logging) mode

---

## Installation & Setup

### Prerequisites
- Windows 10 / 11
- Python 3.9+ (tested on Python 3.12 and 3.13)

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/focuslens.git
cd focuslens
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Run FocusLens
```powershell
python main.py
```

---

## Project Structure

```text
focuslens/
│
├── main.py            # Application entrypoint
├── dashboard.py       # CustomTkinter GUI layout, tabs, and charts
├── tracker.py         # Background window monitor & idle detection thread
├── analytics.py       # Metrics calculation, KPI aggregations, and insights
├── categories.py      # App classification rules & website domain parser
├── database.py        # SQLite database connection, tables, and CRUD helpers
├── startup.py         # Windows Run key startup registry management
├── requirements.txt   # Python package dependencies
└── README.md          # Project documentation
```

---

## License

This project is open source and available under the [MIT License](LICENSE).
