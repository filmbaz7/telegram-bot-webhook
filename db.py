import sqlite3
import os

DB_NAME = 'products.db'

# تابع ایجاد دیتابیس و جدول در صورت نیاز
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

# تابع ذخیره یک محصول
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
        # اگر لینک تکراری باشد (یعنی قبلاً ذخیره شده)
        pass
    conn.close()

# تابع خواندن تمام محصولات
def get_all_products():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name, priceWas, priceIs, difference, discount, link, image FROM products ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return [
        {
            'name': row[0],
            'priceWas': row[1],
            'priceIs': row[2],
            'difference': row[3],
            'discount': row[4],
            'link': row[5],
            'image': row[6]
        }
        for row in rows
    ]


# در اجرای مستقیم فایل، دیتابیس ساخته شود
if __name__ == '__main__':
    create_database()
    print("Database created or already exists.")
