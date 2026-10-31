# main.py
import database
from dashboard import FocusLensApp


def main():
    database.create_tables()
    app = FocusLensApp()
    app.mainloop()


if __name__ == "__main__":
    main()