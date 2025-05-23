import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
products_db_path = os.path.join(BASE_DIR, "products.db")

def get_connection():
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    # ساخت جدول اگر وجود نداشت با ستون‌های کامل و لینک یکتا
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        priceWas REAL,
        priceIs REAL,
        difference REAL,
        discount INTEGER,
        link TEXT UNIQUE,
        image TEXT
    )
    ''')
    conn.commit()
    return conn
