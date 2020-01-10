import logging

import aiosqlite

from .config import DB_PATH
from .utils import logit

logger = logging.getLogger("database")


@logit(logger)
async def set_user_email(user_id, email):
    # There is a underlying connection pool.
    async with aiosqlite.connect(DB_PATH) as db:
        # https://www.sqlite.org/lang_UPSERT.html
        await db.execute("INSERT INTO Users VALUES (?, ?) ON CONFLICT(id) DO UPDATE SET email=(?)", (user_id, email, email))
        await db.commit()


@logit(logger)
async def get_user_email(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT * FROM Users WHERE id=?", (user_id, )) as cursor:
            entry = await cursor.fetchone()
    return entry[1] if entry else None
