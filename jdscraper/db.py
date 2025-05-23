import sqlite3

DB_NAME = 'products.db'

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # جدول sent_discounts
    c.execute('''
        CREATE TABLE IF NOT EXISTS sent_discounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discount_key TEXT UNIQUE
        )
    ''')
    # جدول products
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            priceWas TEXT,
            priceIs TEXT,
            difference TEXT,
            discount TEXT,
            link TEXT UNIQUE,
            image TEXT
        )
    ''')
    conn.commit()
    conn.close()

def is_discount_sent(discount_key):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT 1 FROM sent_discounts WHERE discount_key = ?', (discount_key,))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_discount(discount_key):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO sent_discounts (discount_key) VALUES (?)', (discount_key,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
