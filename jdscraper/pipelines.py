import sqlite3

# اتصال به دیتابیس (یا ایجاد اگر نبود)
conn = sqlite3.connect('products.db')
cursor = conn.cursor()

# ایجاد جدول اگر وجود نداشت
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
    # ذخیره داده‌ها داخل دیتابیس
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
    def process_item(self, item, spider):
        save_product(item)
        return item
