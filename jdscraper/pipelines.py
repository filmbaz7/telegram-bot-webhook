import sqlite3
from db import create_database, save_product

class JdscraperPipeline:
    def open_spider(self, spider):
        # دیتابیس ساخته و جدول ایجاد می‌شود
        create_database()
        # اتصال دیتابیس باز می‌شود
        self.conn = sqlite3.connect('products.db')
        self.cursor = self.conn.cursor()
        # حذف تمام داده‌های قبلی برای تازه‌سازی
        self.cursor.execute('DELETE FROM products')
        self.conn.commit()

    def close_spider(self, spider):
        # بستن اتصال دیتابیس
        self.conn.close()

    def process_item(self, item, spider):
        save_product(item)
        return item
