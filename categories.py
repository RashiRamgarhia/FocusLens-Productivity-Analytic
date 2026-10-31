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
