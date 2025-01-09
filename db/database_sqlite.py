import sqlite3


with sqlite3.connect('datab/database.db') as db:
    cursor = db.cursor()
    query = """ CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, email TEXT, password TEXT) """
    cursor.execute(query)