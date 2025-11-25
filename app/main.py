import asyncio
import logging
import os

from dotenv import load_dotenv  # type: ignore

from .bot import bot, dp
from .db import Base, engine
from .handlers import games_router, participants_router, start_router


def setup_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )


async def init_models() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    load_dotenv()
    setup_logging()

    dp.include_router(start_router)
    dp.include_router(games_router)
    dp.include_router(participants_router)

    await init_models()

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())

