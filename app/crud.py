import secrets
from datetime import datetime
from typing import Iterable, Optional, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Game, GameStatus, Participant, User


async def get_or_create_user(
    session: AsyncSession, user_id: int, username: Optional[str]
) -> User:
    user = await session.get(User, user_id)
    if user:
        if username and user.username != username:
            user.username = username
        return user

    user = User(user_id=user_id, username=username)
    session.add(user)
    await session.flush()
    return user


def generate_game_code() -> str:
    return secrets.token_hex(4)


async def create_game(
    session: AsyncSession,
    creator_id: int,
    title: str,
    deadline: datetime,
    budget: Optional[int],
    allow_chat: bool = False,
) -> Game:
    game_code = generate_game_code()
    while await session.get(Game, game_code):
        game_code = generate_game_code()

    game = Game(
        game_id=game_code,
        creator_id=creator_id,
        title=title,
        deadline=deadline,
        budget=budget,
        allow_chat=allow_chat,
    )
    session.add(game)
    await session.flush()
    return game


async def get_game(session: AsyncSession, game_code: str) -> Optional[Game]:
    result = await session.execute(select(Game).where(Game.game_id == game_code))
    return result.scalar_one_or_none()


async def add_participant(
    session: AsyncSession,
    user_id: int,
    game_id: str,
    name: str,
    wish: Optional[str],
    exclude_list: Optional[list[int]] = None,
) -> Participant:
    participant = Participant(
        user_id=user_id,
        game_id=game_id,
        name=name,
        wish=wish,
        exclude_list=exclude_list or [],
    )
    session.add(participant)
    await session.flush()
    return participant


async def get_participants(session: AsyncSession, game_id: str) -> Sequence[Participant]:
    result = await session.execute(
        select(Participant).where(Participant.game_id == game_id)
    )
    return result.scalars().all()


async def get_participant(
    session: AsyncSession, game_id: str, user_id: int
) -> Optional[Participant]:
    result = await session.execute(
        select(Participant).where(
            Participant.game_id == game_id, Participant.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def set_assignments(
    session: AsyncSession, assignments: Iterable[tuple[int, int]], game_id: str
) -> None:
    for giver_id, receiver_id in assignments:
        await session.execute(
            update(Participant)
                .where(Participant.game_id == game_id, Participant.user_id == giver_id)
                .values(assigned_to=receiver_id)
        )
    await session.execute(
        update(Game)
        .where(Game.game_id == game_id)
        .values(status=GameStatus.ASSIGNED)
    )

