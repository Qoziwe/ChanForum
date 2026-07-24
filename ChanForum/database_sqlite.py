"""
ChanForum Database Initializer

WARNING: Running this script will DELETE all existing databases and recreate them.
This is intended for initial setup only. Do NOT run in production without confirmation.

Usage: python database_sqlite.py
"""

import sqlite3
import os
import sys

# ===== ШАГ 7: Защита от случайного запуска (VULN-007) =====
def initialize_databases():
    """Инициализирует базы данных. Запрашивает подтверждение если данные уже существуют."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_dir = os.path.join(BASE_DIR, 'db')

    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Проверяем, существуют ли уже базы данных
    existing_dbs = [f for f in ['databaseusers.db', 'databasepost.db']
                    if os.path.exists(os.path.join(db_dir, f))]

    if existing_dbs:
        print(f"WARNING: The following databases already exist: {existing_dbs}")
        confirm = input("Are you sure you want to DELETE all data and reinitialize? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)

    # Clear old DBs
    for filename in ['databaseusers.db', 'databasepost.db', 'databasefriends.db']:
        db_path = os.path.join(db_dir, filename)
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Deleted: {db_path}")

    # Initialize Users Database
    conn_users = sqlite3.connect(os.path.join(db_dir, 'databaseusers.db'))
    conn_users.executescript('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        profile_image TEXT DEFAULT NULL,
        uniq_id TEXT NOT NULL UNIQUE
    );

    CREATE TABLE user_friends (
        user_id TEXT NOT NULL,
        friend_id TEXT NOT NULL,
        PRIMARY KEY (user_id, friend_id),
        FOREIGN KEY (user_id) REFERENCES users(uniq_id),
        FOREIGN KEY (friend_id) REFERENCES users(uniq_id)
    );
    ''')
    conn_users.commit()
    conn_users.close()

    # Initialize Posts Database
    conn_posts = sqlite3.connect(os.path.join(db_dir, 'databasepost.db'))
    conn_posts.executescript('''
    CREATE TABLE posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        description TEXT,
        post_image TEXT DEFAULT NULL,
        like_count INTEGER DEFAULT 0,
        author TEXT NOT NULL,
        user_uniq_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE post_likes (
        user_id INTEGER,
        post_id INTEGER,
        valuelike INTEGER,
        PRIMARY KEY (user_id, post_id)
    );

    CREATE TABLE comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        comment_content TEXT NOT NULL,
        author TEXT NOT NULL,
        user_id TEXT NOT NULL
    );
    ''')
    conn_posts.commit()
    conn_posts.close()

    print("Databases successfully initialized.")


if __name__ == '__main__':
    initialize_databases()