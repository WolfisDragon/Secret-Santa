from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from ..crud import get_or_create_user
from ..db import session_factory

start_router = Router()


@start_router.message(CommandStart())
async def handle_start(message: Message) -> None:
    async with session_factory() as session:
        await get_or_create_user(session, message.from_user.id, message.from_user.username)

    await message.answer(
        "Привет! Я бот «Тайный Санта» 🎅\n\n"
        "Команды:\n"
        "/create_game — создать новую игру\n"
        "/join &lt;код&gt; — присоединиться к игре\n"
        "/draw &lt;код&gt; — провести жеребьёвку\n"
        "Пора дарить чудеса!"
    )

