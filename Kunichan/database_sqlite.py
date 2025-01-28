#flask_blog/init_db.py
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'db', 'databaseusers.db')
# open a connection between python script and database.db to create it 
connection = sqlite3.connect(db_path)

# open the schema.sql to read what inside it
with open('scheme.sql') as f:
    connection.executescript(f.read())

connection.commit()
connection.close()