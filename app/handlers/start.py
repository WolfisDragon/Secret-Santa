from aiogram import Router
from aiogram.filters import CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from ..crud import get_or_create_user
from ..db import session_factory
from .participants import join_game

start_router = Router()

@start_router.message(CommandStart(deep_link=True))
async def handle_start_with_deep_link(message: Message, command: CommandObject, state: FSMContext) -> None:
    async with session_factory() as session:
        await get_or_create_user(session, message.from_user.id, message.from_user.username)
        await join_game(message, command, state)

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

