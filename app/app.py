from persistence.database import init_db
from ui import RouletteApp


if __name__ == "__main__":
    init_db()
    RouletteApp().run()
