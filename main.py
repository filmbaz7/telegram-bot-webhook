import os
import sqlite3
import asyncio
import subprocess
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from jdscraper.spiders.jdsports_spider import JDSportsSpider

# ---------- تنظیمات ----------
TOKEN = "7633382786:AAFEy54nrYrhW-5KKAxk_J-_JMt52DFu1Y8"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
users_db_path = os.path.join(BASE_DIR, "users.db")
products_db_path = os.path.join(BASE_DIR, "products.db")

app = FastAPI()
bot = Bot(token=TOKEN)

# ---------- ساخت دیتابیس ----------
def init_users_db():
    conn = sqlite3.connect(users_db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        chat_id INTEGER PRIMARY KEY
    )
    """)
    conn.commit()
    conn.close()

def init_products_db():
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        priceWas REAL,
        priceIs REAL,
        discount INTEGER,
        link TEXT,
        image TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sent_discounts (
        discount_key TEXT PRIMARY KEY
    )
    """)
    conn.commit()
    conn.close()

def add_image_column_if_not_exists():
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'image' not in columns:
        try:
            cursor.execute("ALTER TABLE products ADD COLUMN image TEXT DEFAULT ''")
            print("ستون image اضافه شد.")
        except Exception as e:
            print("خطا در اضافه کردن ستون image:", e)
    else:
        print("ستون image قبلا وجود دارد.")
    conn.commit()
    conn.close()

init_users_db()
init_products_db()

# ---------- عملیات دیتابیس ----------
def add_user(chat_id: int):
    conn = sqlite3.connect(users_db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(users_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_discounted_products(min_discount=30, limit=10):
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT name, priceWas, priceIs, discount, link, image
    FROM products
    WHERE discount >= ?
    ORDER BY discount DESC
    LIMIT ?
    """, (min_discount, limit))
    results = cursor.fetchall()
    conn.close()
    return results

def is_discount_sent(discount_key):
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sent_discounts WHERE discount_key = ?", (discount_key,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_discount_as_sent(discount_key):
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO sent_discounts (discount_key) VALUES (?)", (discount_key,))
    conn.commit()
    conn.close()

# ---------- دستورات تلگرام ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    add_user(update.effective_chat.id)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="سلام! من ربات تخفیف‌های JD Sports هستم.\nبرای دیدن محصولات با تخفیف بالای ۳۰٪ دستور /deals رو بفرست."
    )

async def deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = get_discounted_products()
    if not products:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="هیچ محصولی با تخفیف بالای ۳۰٪ پیدا نشد.")
        return

    for name, priceWas, priceIs, discount, link, image in products:
        text = (
            f"نام محصول: {name}\n"
            f"قیمت قبل: {priceWas} یورو\n"
            f"قیمت فعلی: {priceIs} یورو\n"
            f"تخفیف: {discount}%\n"
            f"لینک: {link}\n"
            f"تصویر: {image}"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

# ---------- اپلیکیشن تلگرام ----------
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("deals", deals))

@app.post(f"/webhook/{TOKEN}")
async def telegram_webhook(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, bot)
    await application.process_update(update)
    return {"status": "ok"}

# ---------- ارسال پیام به کاربران ----------
async def send_periodic_deals():
    while True:
        users = get_all_users()
        products = get_discounted_products()

        for name, priceWas, priceIs, discount, link, image in products:
            discount_key = f"{name}|{priceIs}"
            if is_discount_sent(discount_key):
                continue
            text = (
                f"نام محصول: {name}\n"
                f"قیمت قبل: {priceWas} یورو\n"
                f"قیمت فعلی: {priceIs} یورو\n"
                f"تخفیف: {discount}%\n"
                f"لینک: {link}\n"
                f"تصویر: {image}"
            )
            for chat_id in users:
                try:
                    await bot.send_message(chat_id=chat_id, text=text)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"خطا در ارسال پیام به {chat_id}: {e}")
            mark_discount_as_sent(discount_key)

        await asyncio.sleep(180)

# ---------- اجرای Scrapy با subprocess ----------
async def run_spider_async():
    try:
        subprocess.run(["scrapy", "crawl", "jdsports"], check=True)
    except Exception as e:
        print(f"خطا در اجرای اسپایدر: {e}")

# ---------- اجرای Scrapy هر ۱۵ دقیقه ----------
async def periodic_scrape():
    while True:
        print("شروع اسکرپ...")
        await run_spider_async()
        print("اسکرپ کامل شد.")
        await asyncio.sleep(900)

# ---------- استارت و شات‌دان ----------
@app.on_event("startup")
async def startup_event():
    await application.initialize()
    await application.start()
    add_image_column_if_not_exists()  # اضافه کردن ستون image اگر نبود
    asyncio.create_task(send_periodic_deals())
    asyncio.create_task(periodic_scrape())

@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
    await application.shutdown()
