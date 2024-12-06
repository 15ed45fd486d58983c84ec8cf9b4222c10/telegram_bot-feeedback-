import os
from aiogram.types import Message
from aiogram.filters import Command
import httpx
from httpx_socks import AsyncProxyTransport

PROXY_URL = "socks5://127.0.0.1:2080"
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL")
if not NOTIFICATION_URL:
    raise ValueError("NOTIFICATION_URL not found in environment variables")

transport = AsyncProxyTransport.from_url(PROXY_URL)


async def complain_handler(message: Message):
    complaint_data = {
        "user_id": message.from_user.id,
        "description": "Жалоба от пользователя",
    }

    async with httpx.AsyncClient(transport=transport) as client:
        response = await client.post(NOTIFICATION_URL, json=complaint_data)
        if response.status_code == 200:
            await message.answer("Жалоба успешно отправлена!")
        else:
            await message.answer(
                f"Ошибка при отправке жалобы: {response.status_code}")


def register_complain_handler(dp):
    dp.message.register(complain_handler, Command("complain"))
