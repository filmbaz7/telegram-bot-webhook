import sqlite3

DB_NAME = 'products.db'

def create_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            priceWas REAL,
            priceIs REAL,
            difference REAL,
            discount REAL,
            link TEXT UNIQUE,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB_NAME)
