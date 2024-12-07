from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prisma import Prisma
from dotenv import load_dotenv
import os
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from handlers.complaints import router as complaints_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

if not DATABASE_URL:
    logger.critical("DATABASE_URL не найден в переменных окружения")
    raise ValueError("DATABASE_URL не найден в переменных окружения")

db = Prisma()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    logger.info("Подключение к базе данных...")
    await db.connect()
    app.state.db = db 
    logger.info("База данных подключена.")
    try:
        yield
    finally:
        logger.info("Отключение от базы данных...")
        await db.disconnect()
        logger.info("База данных отключена.")

app = FastAPI(title="Complaints API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(complaints_router, prefix="/complaints")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.api.main:app", host=HOST, port=PORT, reload=True)
