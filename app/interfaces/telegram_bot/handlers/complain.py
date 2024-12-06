from aiogram.types import Message
from aiogram.filters import Command
import httpx
import os
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL")
if not NOTIFICATION_URL:
    raise ValueError("NOTIFICATION_URL not found in environment variables")


async def complain_handler(message: Message, db):
    complaint_data = {
        "user_id": message.from_user.id,
        "description": "Жалоба от пользователя",
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(NOTIFICATION_URL, json=complaint_data)
            if response.status_code == 200:
                await db.complaint.create(
                    data={
                        "userId": message.from_user.id,
                        "description": complaint_data["description"],
                        "status": "sent",
                    }
                )
                await message.answer("Жалоба успешно отправлена!")
            else:
                raise httpx.HTTPStatusError(
                    f"Failed with status {response.status_code}")
    except Exception:
        await db.complaint.create(
            data={
                "userId": message.from_user.id,
                "description": complaint_data["description"],
                "status": "pending",
            }
        )
        await message.answer(
            "Не удалось отправить жалобу. Она будет отправлена позже.")


def register_complain_handler(dp, db):
    dp.message.register(
        lambda message: complain_handler(message, db), Command("complain"))
