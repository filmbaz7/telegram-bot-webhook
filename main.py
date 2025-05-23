import os
import sqlite3
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

from scrapy.crawler import CrawlerRunner
from twisted.internet import reactor
from scrapy.utils.log import configure_logging
from jdscraper.spiders.jdsports_spider import JDSportsSpider
from scrapy.utils.project import get_project_settings

TOKEN = "7633382786:AAFEy54nrYrhW-5KKAxk_J-_JMt52DFu1Y8"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

users_db_path = os.path.join(BASE_DIR, "users.db")
products_db_path = os.path.join(BASE_DIR, "products.db")

app = FastAPI()
bot = Bot(token=TOKEN)

# --- محصولات ---
def init_products_db():
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sent_discounts (
        discount_key TEXT PRIMARY KEY
    )
    """)
    conn.commit()
    conn.close()

def get_discounted_products(min_discount=30, limit=10):
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT name, priceWas, priceIs, discount, link 
    FROM products
    WHERE discount >= ?
    ORDER BY discount DESC
    LIMIT ?
    """, (min_discount, limit))
    results = cursor.fetchall()
    conn.close()
    return results

def is_discount_sent(discount_key: str) -> bool:
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM sent_discounts WHERE discount_key = ?", (discount_key,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_sent_discount(discount_key: str):
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO sent_discounts (discount_key) VALUES (?)", (discount_key,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

# --- کاربران ---
conn_users = sqlite3.connect(users_db_path, check_same_thread=False)
cursor_users = conn_users.cursor()
cursor_users.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY
)
""")
conn_users.commit()

def add_user(chat_id: int):
    cursor_users.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn_users.commit()

def get_all_users():
    cursor_users.execute("SELECT chat_id FROM users")
    return [row[0] for row in cursor_users.fetchall()]

# --- ربات تلگرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    await context.bot.send_message(chat_id=chat_id, text="سلام! برای دیدن تخفیف‌های جدید، دستور /deals رو بفرست.")

async def deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = get_discounted_products()
    if not products:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="تخفیفی موجود نیست.")
        return

    for name, priceWas, priceIs, discount, link in products:
        text = (
            f"نام محصول: {name}\n"
            f"قیمت قبل: {priceWas} یورو\n"
            f"قیمت فعلی: {priceIs} یورو\n"
            f"تخفیف: {discount}%\n"
            f"لینک: {link}"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("deals", deals))

# --- وبهوک ---
@app.post(f"/webhook/{TOKEN}")
async def telegram_webhook(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, bot)
    await application.process_update(update)
    return {"status": "ok"}

# --- ارسال خودکار ---
async def send_periodic_deals():
    while True:
        users = get_all_users()
        products = get_discounted_products()
        if products:
            for name, priceWas, priceIs, discount, link in products:
                discount_key = link  # شناسه یکتا برای جلوگیری از تکرار
                if not is_discount_sent(discount_key):
                    text = (
                        f"نام محصول: {name}\n"
                        f"قیمت قبل: {priceWas} یورو\n"
                        f"قیمت فعلی: {priceIs} یورو\n"
                        f"تخفیف: {discount}%\n"
                        f"لینک: {link}"
                    )
                    for chat_id in users:
                        try:
                            await bot.send_message(chat_id=chat_id, text=text)
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            print(f"خطا در ارسال به {chat_id}: {e}")
                    save_sent_discount(discount_key)
        await asyncio.sleep(180)  # هر ۳ دقیقه

# --- اسکرپینگ ---
def run_spider():
    configure_logging()
    runner = CrawlerRunner(get_project_settings())
    d = runner.crawl(JDSportsSpider)
    d.addBoth(lambda _: reactor.stop())
    reactor.run()

async def run_spider_async():
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, run_spider)

async def periodic_scrape():
    while True:
        print("شروع اسکرپ...")
        await run_spider_async()
        print("پایان اسکرپ.")
        await asyncio.sleep(900)  # هر ۱۵ دقیقه

# --- شروع برنامه ---
@app.on_event("startup")
async def startup_event():
    init_products_db()
    await application.initialize()
    await application.start()
    asyncio.create_task(send_periodic_deals())
    asyncio.create_task(periodic_scrape())

@app.on_event("shutdown")
async def shutdown_event():
    await application.stop()
    await application.shutdown()
