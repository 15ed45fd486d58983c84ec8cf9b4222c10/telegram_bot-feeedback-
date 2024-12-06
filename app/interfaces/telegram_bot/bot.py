import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from handlers import register_handlers
from prisma import Prisma
import os
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db = Prisma()


async def main():
    await db.connect()
    register_handlers(dp, db)
    try:
        await dp.start_polling(bot)
    finally:
        await db.disconnect()
        print("Bot stopped and database connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
