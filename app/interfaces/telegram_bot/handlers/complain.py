from aiogram import F
from aiogram.types import Message, Location
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import httpx
import os
from functools import partial
import logging

logger = logging.getLogger("telegram_bot.handlers.complain")

NOTIFICATION_URL = os.getenv("NOTIFICATION_URL")
if not NOTIFICATION_URL:
    logger.critical("NOTIFICATION_URL не найден в переменных окружения")
    raise ValueError("NOTIFICATION_URL не найден в переменных окружения")


class ComplainStates(StatesGroup):
    waiting_for_description = State()
    waiting_for_location_or_skip = State()


async def start_command(message: Message):
    welcome_message = (
        "👋 Добро пожаловать в бот для подачи жалоб!\n\n"
        "Этот бот поможет вам быстро и удобно подать жалобу на различные аспекты городской жизни.\n\n"
        "📌 Команды:\n"
        "/complain - Подать новую жалобу\n"
        "Вы можете начать с команды /complain, чтобы оставить свою жалобу."
    )
    await message.answer(welcome_message)
    logger.debug(f"Пользователь {message.from_user.id} использовал команду /start.")


async def complain_start(message: Message, db, state: FSMContext):
    await message.answer("Пожалуйста, опишите вашу жалобу.")
    await state.set_state(ComplainStates.waiting_for_description)
    logger.debug(f"Пользователь {message.from_user.id} начал жалобу.")


async def process_description(message: Message, db, state: FSMContext):
    description = message.text
    await state.update_data(description=description)
    await message.answer(
        "Хотите отправить ваше местоположение для более быстрой обработки?\n"
        "Нажмите 'Отправить местоположение' или 'Пропустить'.",
        reply_markup=await get_location_or_skip_keyboard()
    )
    await state.set_state(ComplainStates.waiting_for_location_or_skip)
    logger.debug(f"Пользователь {message.from_user.id} предоставил описание: {description}")


async def process_location(message: Message, db, state: FSMContext):
    if message.location:
        location: Location = message.location
        data = await state.get_data()
        description = data.get("description")

        complaint_data = {
            "user_id": message.from_user.id,
            "description": description,
            "latitude": location.latitude,
            "longitude": location.longitude,
        }
        logger.debug(f"Получены данные жалобы от user_id: {message.from_user.id}: {complaint_data}")

        try:
            complaint = await db.complaint.create(
                data={
                    "userId": message.from_user.id,
                    "description": description,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "status": "pending",
                }
            )
            logger.debug(f"Жалоба сохранена в базе данных с id: {complaint.id}")
        except Exception as e:
            logger.exception(f"Ошибка при сохранении жалобы в базе данных: {e}")
            await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
            await state.clear()
            return

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                logger.info(f"Отправка жалобы на {NOTIFICATION_URL}")
                response = await client.post(NOTIFICATION_URL, json=complaint_data)
                response.raise_for_status()
                logger.info("Жалоба успешно отправлена на внешний сервис.")

                # Обновление статуса жалобы на "sent"
                await db.complaint.update(
                    where={"id": complaint.id},
                    data={"status": "sent"}
                )
                logger.debug(f"Статус жалобы id {complaint.id} обновлен на 'sent'.")

                await message.answer("Жалоба успешно отправлена!")
        except httpx.HTTPStatusError as http_err:
            if http_err.response.status_code == 405:
                status = "server_load"
                logger.error(f"HTTP 405: Метод не разрешен для {NOTIFICATION_URL}")
                await db.complaint.update(
                    where={"id": complaint.id},
                    data={"status": status}
                )
                await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
            else:
                status = "server_load"
                logger.error(f"HTTP ошибка {http_err.response.status_code}: {http_err}")
                await db.complaint.update(
                    where={"id": complaint.id},
                    data={"status": status}
                )
                await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
        except httpx.RequestError as req_err:
            status = "server_load"
            logger.error(f"HTTP запрос не удался: {req_err}")
            await db.complaint.update(
                where={"id": complaint.id},
                data={"status": status}
            )
            await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
        except Exception as e:
            logger.exception(f"Произошла неожиданная ошибка: {e}")
            await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
        finally:
            await state.clear()
    else:
        await message.answer("Пожалуйста, отправьте корректное местоположение или нажмите 'Пропустить'.")
        logger.debug(f"Пользователь {message.from_user.id} не отправил местоположение.")


async def skip_location(message: Message, db, state: FSMContext):
    data = await state.get_data()
    description = data.get("description")

    complaint_data = {
        "user_id": message.from_user.id,
        "description": description,
        "latitude": None,
        "longitude": None,
    }
    logger.debug(f"Пользователь {message.from_user.id} пропустил отправку местоположения: {complaint_data}")

    try:
        complaint = await db.complaint.create(
            data={
                "userId": message.from_user.id,
                "description": description,
                "latitude": None,
                "longitude": None,
                "status": "pending",
            }
        )
        logger.debug(f"Жалоба сохранена в базе данных с id: {complaint.id}")
    except Exception as e:
        logger.exception(f"Ошибка при сохранении жалобы в базе данных: {e}")
        await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
        await state.clear()
        return

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            logger.info(f"Отправка жалобы на {NOTIFICATION_URL} без местоположения")
            response = await client.post(NOTIFICATION_URL, json=complaint_data)
            response.raise_for_status()
            logger.info("Жалоба успешно отправлена на внешний сервис.")

            # Обновление статуса жалобы на "sent"
            await db.complaint.update(
                where={"id": complaint.id},
                data={"status": "sent"}
            )
            logger.debug(f"Статус жалобы id {complaint.id} обновлен на 'sent'.")

            await message.answer("Жалоба успешно отправлена!")
    except httpx.HTTPStatusError as http_err:
        if http_err.response.status_code == 405:
            status = "server_load"
            logger.error(f"HTTP 405: Метод не разрешен для {NOTIFICATION_URL}")
            await db.complaint.update(
                where={"id": complaint.id},
                data={"status": status}
            )
            await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
        else:
            status = "server_load"
            logger.error(f"HTTP ошибка {http_err.response.status_code}: {http_err}")
            await db.complaint.update(
                where={"id": complaint.id},
                data={"status": status}
            )
            await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
    except httpx.RequestError as req_err:
        status = "server_load"
        logger.error(f"HTTP запрос не удался: {req_err}")
        await db.complaint.update(
            where={"id": complaint.id},
            data={"status": status}
        )
        await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
    except Exception as e:
        logger.exception(f"Произошла неожиданная ошибка: {e}")
        await message.answer("Серверы сейчас перегружены. Ваша жалоба сохранена и будет обработана позже.")
    finally:
        await state.clear()


async def get_location_or_skip_keyboard():
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
    buttons = [
        [
            KeyboardButton(text="Отправить местоположение", request_location=True),
            KeyboardButton(text="Пропустить")
        ]
    ]
    keyboard = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def register_complain_handler(dp, db):
    dp.message.register(start_command, Command("start"))

    dp.message.register(
        partial(complain_start, db=db),
        Command("complain")
    )
    dp.message.register(
        partial(process_description, db=db),
        ComplainStates.waiting_for_description
    )
    dp.message.register(
        partial(process_location, db=db),
        ComplainStates.waiting_for_location_or_skip,
        F.location
    )
    dp.message.register(
        partial(skip_location, db=db),
        ComplainStates.waiting_for_location_or_skip,
        F.text == "Пропустить"
    )
