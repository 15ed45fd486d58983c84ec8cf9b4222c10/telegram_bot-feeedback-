from functools import partial
from .complain import ComplainStates, start_command, complain_start, skip_location
from aiogram.filters import Command
from .complain import process_description, process_location
from aiogram import F


def register_handlers(dp, db):
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
