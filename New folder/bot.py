import sqlite3
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

TOKEN = "توکن-ربات-تو"

bot = Bot(token=TOKEN)
app = FastAPI()

# دیتابیس کاربران (همانند کد قبلی)
conn_users = sqlite3.connect("users.db", check_same_thread=False)
cursor_users = conn_users.cursor()
cursor_users.execute("""
CREATE TABLE IF NOT EXISTS users (
    chat_id INTEGER PRIMARY KEY
)
""")
conn_users.commit()

def add_user(chat_id):
    cursor_users.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (chat_id,))
    conn_users.commit()

def get_all_users():
    cursor_users.execute("SELECT chat_id FROM users")
    return [row[0] for row in cursor_users.fetchall()]

# دیتابیس محصولات
def get_discounted_products(min_discount=30, limit=10):
    conn = sqlite3.connect("products.db")
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

# تعریف هندلرهای async

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)
    await update.message.reply_text(
        "سلام! من ربات تخفیف‌های JD Sports هستم.\nبرای دیدن محصولات با تخفیف بالای ۳۰٪ دستور /deals رو بفرست."
    )

async def deals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    products = get_discounted_products()
    if not products:
        await update.message.reply_text("هیچ محصولی با تخفیف بالای ۳۰٪ پیدا نشد.")
        return

    for name, priceWas, priceIs, discount, link in products:
        text = (
            f"نام محصول: {name}\n"
            f"قیمت قبل: {priceWas} یورو\n"
            f"قیمت فعلی: {priceIs} یورو\n"
            f"تخفیف: {discount}%\n"
            f"لینک: {link}\n"
        )
        await update.message.reply_text(text)

# ایجاد اپلیکیشن تلگرام

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("deals", deals))

# مسیر وبهوک

@app.post(f"/webhook/{TOKEN}")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot)
    await application.process_update(update)
    return {"ok": True}

# ارسال خودکار دوره‌ای (3 دقیقه)

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
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        print(f"خطا در ارسال پیام به {chat_id}: {e}")
        await asyncio.sleep(180)

# اجرای periodic task در پس‌زمینه با FastAPI

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(send_periodic_deals())

# اجرای uvicorn

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
