import logging
from datetime import datetime
from typing import Sequence

from aiogram import Router
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError

from ..crud import (
    create_game,
    get_or_create_user,
    get_game,
    get_participants,
    set_assignments,
)
from ..db import session_factory
from ..models import Game, GameStatus, Participant
from ..utils.random_assign import random_assign

games_router = Router()


class CreateGameState(StatesGroup):
    title = State()
    deadline = State()
    budget = State()


@games_router.message(Command("create_game"))
async def start_create_game(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateGameState.title)
    await message.answer("Введите название игры:")


@games_router.message(StateFilter(CreateGameState.title))
async def set_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=message.text.strip())
    await state.set_state(CreateGameState.deadline)
    await message.answer("Укажите дедлайн в формате 22.12.2025 22:00:")


@games_router.message(StateFilter(CreateGameState.deadline))
async def set_deadline(message: Message, state: FSMContext) -> None:
    try:
        deadline = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("Неверный формат. Повторите в виде 22.12.2025 22:00.")
        return

    await state.update_data(deadline=deadline)
    await state.set_state(CreateGameState.budget)
    await message.answer("Укажите бюджет (число, руб.). Можно написать 0, если не важно.")


@games_router.message(StateFilter(CreateGameState.budget))
async def finish_create(message: Message, state: FSMContext) -> None:
    try:
        budget = int(message.text.strip())
    except ValueError:
        await message.answer("Нужно ввести число. Попробуйте снова.")
        return

    data = await state.get_data()
    await state.clear()

    async with session_factory() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        game = await create_game(
            session=session,
            creator_id=user.user_id,
            title=data["title"],
            deadline=data["deadline"],
            budget=budget,
        )

    await message.answer(
        f"Игра создана! Код: <code>{game.game_id}</code>\n"
        f"Поделитесь кодом с друзьями, чтобы они могли присоединиться через /join {game.game_id}."
        f"Или используйте ссылку https://t.me/AnotherSilencebot?start={game.game_id}"
    )


@games_router.message(Command("draw"))
async def handle_draw(message: Message, command: CommandObject) -> None:
    if not command.args:
        await message.answer("Укажите код игры: /draw <код>")
        return

    game_code = command.args.strip()

    async with session_factory() as session:
        game = await get_game(session, game_code)
        if not game:
            await message.answer("Игра не найдена.")
            return
        if game.creator_id != message.from_user.id:
            await message.answer("Жеребьёвку может запускать только создатель игры.")
            return
        if game.status == GameStatus.ASSIGNED:
            await message.answer("Жеребьёвка уже проведена.")
            return

        participants = await get_participants(session, game_code)
        if len(participants) < 2:
            await message.answer("Нужно минимум два участника.")
            return

        try:
            assignments = random_assign([(p.user_id, p.exclude_list or []) for p in participants])
        except RuntimeError as err:
            await message.answer(str(err))
            return
        await set_assignments(session, assignments, game_code)

    await notify_participants(message, participants, assignments, game)


async def notify_participants(
    message: Message,
    participants: Sequence[Participant],
    assignments: list[tuple[int, int]],
    game: Game,
) -> None:
    participant_map = {p.user_id: p for p in participants}
    budget_text = f"{game.budget}₽" if game.budget else "без ограничений"
    deadline_text = game.deadline.strftime("%d.%m.%Y %H:%M")

    for giver_id, receiver_id in assignments:
        giver = participant_map[giver_id]
        receiver = participant_map[receiver_id]
        text = (
            f"🎁 Игра: {game.title}\n"
            f"Дедлайн: {deadline_text} UTC\n"
            f"Бюджет: {budget_text}\n\n"
            f"Ты даришь подарок для: <b>{receiver.name}</b>\n"
            f"Пожелания: {receiver.wish or 'не указаны'}"
        )
        try:
            await message.bot.send_message(chat_id=giver.user_id, text=text)
        except TelegramForbiddenError:
            logging.warning("Не удалось отправить сообщение пользователю %s", giver.user_id)

    await message.answer("Жеребьёвка завершена! Рассылки отправлены.")

