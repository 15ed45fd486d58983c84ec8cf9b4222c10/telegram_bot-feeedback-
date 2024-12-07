import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from handlers import register_handlers
from prisma import Prisma
import os
import colorlog

logger = logging.getLogger("telegram_bot")
logger.setLevel(logging.DEBUG)

handler = colorlog.StreamHandler()
handler.setLevel(logging.DEBUG)

formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
)
handler.setFormatter(formatter)
logger.addHandler(handler)

os.environ['DEBUG'] = 'prisma:*'
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    logger.critical("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
    raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения")

NOTIFICATION_URL = os.getenv("NOTIFICATION_URL")
if not NOTIFICATION_URL:
    logger.critical("NOTIFICATION_URL не найден в переменных окружения")
    raise ValueError("NOTIFICATION_URL не найден в переменных окружения")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.critical("DATABASE_URL не найден в переменных окружения")
    raise ValueError("DATABASE_URL не найден в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
db = Prisma()


async def main():
    logger.info("Подключение к базе данных...")
    await db.connect()
    logger.info("База данных подключена.")

    register_handlers(dp, db)
    logger.info("Обработчики зарегистрированы. Запуск polling...")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    finally:
        await db.disconnect()
        logger.info("Бот остановлен и соединение с базой данных закрыто.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Запрос на завершение работы бота от пользователя.")
