import sqlite3

conn = sqlite3.connect('products.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    priceWas REAL,
    priceIs REAL,
    difference REAL,
    discount REAL,
    link TEXT,
    image TEXT
)
''')
conn.commit()

def save_product(item):
    cursor.execute('''
        INSERT INTO products (name, priceWas, priceIs, difference, discount, link, image) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        item.get('name'),
        item.get('priceWas'),
        item.get('priceIs'),
        item.get('difference'),
        item.get('discount'),
        item.get('link'),
        item.get('image')
    ))
    conn.commit()

class JdscraperPipeline:
    def open_spider(self, spider):
        # حذف تمام محصولات قبلی برای تازه‌سازی دیتابیس
        cursor.execute('DELETE FROM products')
        conn.commit()

    def process_item(self, item, spider):
        save_product(item)
        return item
