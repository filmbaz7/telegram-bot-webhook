import os
import sqlite3
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = "7633382786:AAFEy54nrYrhW-5KKAxk_J-_JMt52DFu1Y8"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

users_db_path = os.path.join(BASE_DIR, "users.db")
products_db_path = os.path.join(BASE_DIR, "products.db")

app = FastAPI()

bot = Bot(token=TOKEN)

# --- دیتابیس محصولات ---
def get_discounted_products(min_discount=30, limit=10):
    conn = sqlite3.connect(products_db_path)
    cursor = conn.cursor()

    query = """
    SELECT name, priceWas, priceIs, discount, link 
    FROM products
    WHERE discount >= ?
    ORDER BY discount DESC
    LIMIT ?
    """
    cursor.execute(query, (min_discount, limit))
    results = cursor.fetchall()
    conn.close()
    return results

# --- دیتابیس کاربران ---
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

# --- دستورات تلگرام ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    await context.bot.send_message(
        chat_id=chat_id,
        text="سلام! من ربات تخفیف‌های JD Sports هستم.\nبرای دیدن محصولات با تخفیف بالای ۳۰٪ دستور /deals رو بفرست."
    )

async def deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = get_discounted_products()

    if not products:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="هیچ محصولی با تخفیف بالای ۳۰٪ پیدا نشد.")
        return

    for name, priceWas, priceIs, discount, link in products:
        text = (
            f"نام محصول: {name}\n"
            f"قیمت قبل: {priceWas} یورو\n"
            f"قیمت فعلی: {priceIs} یورو\n"
            f"تخفیف: {discount}%\n"
            f"لینک: {link}\n"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

# --- ایجاد برنامه تلگرام ---
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

# --- ارسال خودکار هر 3 دقیقه به همه کاربران ---
async def send_periodic_deals():
    while True:
        users = get_all_users()
        products = get_discounted_products()

        if products:
            for chat_id in users:
                for name, priceWas, priceIs, discount, link in products:
                    text = (
                        f"نام محصول: {name}\n"
                        f"قیمت قبل: {priceWas} یورو\n"
                        f"قیمت فعلی: {priceIs} یورو\n"
                        f"تخفیف: {discount}%\n"
                        f"لینک: {link}\n"
                    )
                    try:
                        await bot.send_message(chat_id=chat_id, text=text)
                        await asyncio.sleep(0.5)  # وقفه برای جلوگیری از محدودیت API
                    except Exception as e:
                        print(f"خطا در ارسال پیام به {chat_id}: {e}")

        await asyncio.sleep(180)  # صبر 3 دقیقه

# شروع تسک ارسال دوره‌ای (با BackgroundTasks یا asyncio.create_task)
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(send_periodic_deals())
