import sys
import os

# Добавляем путь к директории с app.py в sys.path, чтобы Python мог найти модуль app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ChanForum'))

from app import app
application = app

if __name__ == "__main__":
    app.run()
