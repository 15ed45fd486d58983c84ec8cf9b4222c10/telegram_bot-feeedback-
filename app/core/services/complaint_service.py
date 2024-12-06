import httpx
import os


class ComplaintService:
    def __init__(self):
        """
        Инициализация сервиса. URL для отправки
        уведомлений берется из переменных окружения.
        """
        self.notification_url = os.getenv("NOTIFICATION_URL")
        if not self.notification_url:
            raise ValueError(
                "NOTIFICATION_URL not found in environment variables")

    async def send_complaint(self, user_id: int, description: str):
        """
        Отправляет жалобу на указанный API.

        :param user_id: ID пользователя, отправившего жалобу
        :param description: Описание жалобы
        :return: Ответ от API или исключение при ошибке
        """
        complaint_data = {
            "user_id": user_id,
            "description": description,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.notification_url,
                                         json=complaint_data)
            response.raise_for_status()
            return response.json()
