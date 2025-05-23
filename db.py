import sqlite3

DB_NAME = 'products.db'  # یا اسم دیتابیسی که تخفیف‌ها توش ذخیره میشن

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sent_discounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discount_key TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

def is_discount_sent(discount_key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT 1 FROM sent_discounts WHERE discount_key = ?', (discount_key,))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_discount(discount_key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO sent_discounts (discount_key) VALUES (?)', (discount_key,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
