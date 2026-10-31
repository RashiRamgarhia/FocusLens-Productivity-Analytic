CATEGORY_NAMES = ["Productive", "Necessary", "Unproductive"]

PRODUCTIVE_APPS = [
    "code",
    "cursor",
    "antigravity",
    "antigravity ide",
    "pycharm64",
    "idea64",
    "spyder",
    "sublime_text",
    "notepad++",
    "windowsterminal",
    "cmd",
    "powershell",
    "winword",
    "excel",
    "powerpnt",
    "postman",
    "mysqlworkbench",
    "obsidian",
    "anaconda-navigator",
    "git-bash",
    "python",
    "python3",
    "chatgpt",
    "copilotapp",
    "copilotapphost"
]

UNPRODUCTIVE_APPS = [
    "steam",
    "discord",
    "telegram",
    "whatsapp",
    "snapchat",
    "epicgameslauncher",
    "spotify",
    "spotifylauncher",
    "prime video",
    "primevideo",
    "amazon video",
    "netflix",
    "disney+",
    "disneyplus",
    "hulu",
    "twitch",
    "tiktok"
]
# Legacy alias for backward compatibility
DISTRACTING_APPS = UNPRODUCTIVE_APPS

PRODUCTIVE_SITES = [
    "github",
    "stack overflow",
    "leetcode",
    "kaggle",
    "geeksforgeeks",
    "colab",
    "jupyter",
    "arxiv",
    "coursera",
    "nptel"
]

UNPRODUCTIVE_SITES = [
    "youtube",
    "spotify",
    "prime video",
    "primevideo",
    "prime",
    "amazon prime",
    "netflix",
    "hotstar",
    "disney",
    "disney+",
    "instagram",
    "facebook",
    "reddit",
    "twitter",
    "x.com",
    "twitch",
    "tiktok",
    "jiocinema",
    "zee5",
    "crunchyroll"
]
# Legacy alias for backward compatibility
DISTRACTING_SITES = UNPRODUCTIVE_SITES

BROWSERS = [
    "chrome",
    "msedge",
    "firefox",
    "brave",
    "opera",
    "vivaldi",
    "arc",
    "chromium"
]
_custom_categories = None


def refresh_custom_categories():
    global _custom_categories
    try:
        import database
        _custom_categories = dict(database.get_custom_categories())
    except Exception:
        _custom_categories = {}


def get_category(app_name):
    global _custom_categories
    if _custom_categories is None:
        refresh_custom_categories()

    app_lower = str(app_name or "").strip().lower().replace(".exe", "")
    if app_lower in _custom_categories:
        cat = _custom_categories[app_lower]
        if cat in ("Neutral", "Other"):
            cat = "Necessary"
        elif cat == "Distracting":
            cat = "Unproductive"
        if cat in CATEGORY_NAMES:
            return cat

    if _matches_known_app(app_lower, PRODUCTIVE_APPS) or any(s in app_lower for s in PRODUCTIVE_SITES):
        return "Productive"
    if _matches_known_app(app_lower, UNPRODUCTIVE_APPS) or any(s in app_lower for s in UNPRODUCTIVE_SITES):
        return "Unproductive"
    return "Necessary"


def _matches_known_app(app_name, known_apps):
    return any(
        app_name == known or app_name.startswith(f"{known}.")
        for known in known_apps
    )


def get_app_label(process_name, window_title=""):
    proc = str(process_name or "").lower().replace(".exe", "").strip()
    if not proc:
        return "desktop"

    title = str(window_title or "").lower().strip()

    # Special handling for Windows Store (UWP) apps
    if proc == "applicationframehost":
        if title:
            for item in PRODUCTIVE_APPS + UNPRODUCTIVE_APPS + PRODUCTIVE_SITES + UNPRODUCTIVE_SITES:
                if item in title:
                    return item
            clean_title = title.split(" - ")[0].split(" — ")[0].strip()
            return clean_title if clean_title else "store-app"
        return "store-app"

    # If it is a browser, extract site from window title
    if proc in BROWSERS:
        for site in PRODUCTIVE_SITES + UNPRODUCTIVE_SITES:
            if site in title:
                return site
        return proc

    # Also check if process matches a known productive or unproductive app
    for app in UNPRODUCTIVE_APPS + PRODUCTIVE_APPS:
        if app in proc:
            return app

    return proc
