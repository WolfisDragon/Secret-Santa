from aiogram import Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from ..crud import (
    add_participant,
    get_game,
    get_or_create_user,
    get_participant,
)
from ..db import session_factory

participants_router = Router()


class JoinGameState(StatesGroup):
    game_code = State()
    name = State()
    wish = State()
    exclude = State()


@participants_router.message(Command("join"))
async def join_game(message: Message, command: CommandObject, state: FSMContext) -> None:
    if command.args == None:
        await message.answer("Укажите код игры: /join &lt;код&gt")
        return

    game_code = command.args.strip()
    async with session_factory() as session:
        game = await get_game(session, game_code)
        if not game:
            await message.answer("Игра не найдена.")
            return

        await get_or_create_user(session, message.from_user.id, message.from_user.username)
        participant = await get_participant(session, game_code, message.from_user.id)
        if participant:
            await message.answer("Вы уже участвуете в этой игре.")
            return

    await state.update_data(game_code=game_code)
    await state.set_state(JoinGameState.name)
    await message.answer("Как вас представить другим участникам?")


@participants_router.message(StateFilter(JoinGameState.name))
async def set_participant_name(message: Message, state: FSMContext) -> None:
    if not message.text:
        await message.answer("Имя не может быть пустым.")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(JoinGameState.wish)
    await message.answer("Напишите пожелания к подарку (или '-' если нет).")


@participants_router.message(StateFilter(JoinGameState.wish))
async def ask_exclude(message: Message, state: FSMContext) -> None:
    wish = None if message.text.strip() == "-" else message.text.strip()
    await state.update_data(wish=wish)
    await state.set_state(JoinGameState.exclude)
    await message.answer(
        "Если нужно исключить конкретных участников, перечислите их Telegram user_id через запятую.\n"
        "Если ограничений нет — отправьте '-'."
    )


@participants_router.message(StateFilter(JoinGameState.exclude))
async def finish_join(message: Message, state: FSMContext) -> None:
    data = await state.get_data()

    exclude_text = message.text.strip()
    exclude_list = []
    if exclude_text != "-":
        try:
            exclude_list = [int(item.strip()) for item in exclude_text.split(",") if item.strip()]
        except ValueError:
            await message.answer("Не удалось распознать список исключений. Повторите команду /join.")
            return

    async with session_factory() as session:
        await add_participant(
            session=session,
            user_id=message.from_user.id,
            game_id=data["game_code"],
            name=data["name"],
            wish=data["wish"],
            exclude_list=exclude_list,
        )

    await state.clear()
    await message.answer("Вы в игре! Когда организатор проведёт жеребьёвку, бот пришлёт ваш результат.")

