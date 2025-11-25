from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(length=255))
    reg_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    participants: Mapped[list["Participant"]] = relationship(
        back_populates="user", foreign_keys="Participant.user_id"
    )
    created_games: Mapped[list["Game"]] = relationship(back_populates="creator")


class GameStatus:
    CREATED = "created"
    ASSIGNED = "assigned"
    FINISHED = "finished"


class Game(Base):
    __tablename__ = "games"

    game_id: Mapped[str] = mapped_column(String(length=32), primary_key=True)
    creator_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    title: Mapped[str] = mapped_column(String(length=255))
    deadline: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    budget: Mapped[Optional[int]] = mapped_column(Integer)
    allow_chat: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(length=32), default=GameStatus.CREATED)

    creator: Mapped["User"] = relationship(back_populates="created_games")
    participants: Mapped[list["Participant"]] = relationship(back_populates="game")


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_participant"),
        CheckConstraint("user_id <> assigned_to", name="no_self_assignment"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))
    game_id: Mapped[str] = mapped_column(ForeignKey("games.game_id"))
    name: Mapped[str] = mapped_column(String(length=255))
    wish: Mapped[Optional[str]] = mapped_column(Text)
    exclude_list: Mapped[list[int]] = mapped_column(JSONB, default=list)
    assigned_to: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("users.user_id"))

    user: Mapped["User"] = relationship(back_populates="participants", foreign_keys=[user_id])
    game: Mapped["Game"] = relationship(back_populates="participants")

