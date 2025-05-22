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

def save_product(product):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO products (name, priceWas, priceIs, difference, discount, link, image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            product['name'],
            product['priceWas'],
            product['priceIs'],
            product['difference'],
            product['discount'],
            product['link'],
            product['image']
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
