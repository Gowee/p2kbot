from hashlib import sha1
import struct
import os
import logging
from functools import wraps
from itertools import chain
import re

from .config import BOT_TOKEN, EMAIL_DOMAIN, TEMP_DIR, DB_PATH

CHUNK_SIZE = 1024 * 1024


def get_sender_email(user_id):
    h = sha1()
    h.update(struct.pack("!q", user_id))
    h.update(b"p2kbot")
    h.update(BOT_TOKEN.encode("latin-1"))
    local_part = h.hexdigest()[11:21]
    return f"{local_part}@{EMAIL_DOMAIN}"


REGEX_EMAIL_ADDRESS = re.compile(
    r"^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$")


def is_valid_email_address(s):
    return REGEX_EMAIL_ADDRESS.match(s) is not None


def simple_sha1(s):
    h = sha1()
    h.update(s.encode("utf-8"))
    return h.hexdigest()


def logit(logger: logging.Logger, level=logging.DEBUG, when_done=False):
    def decorator(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            # TODO: improve flow?
            if when_done:
                r = func(*args, **kwargs)
            logger.log(level,
                       func.__name__ + ": " + ", ".join(
                           chain(map(str, args),
                                 map(lambda e: str(e[0]) + "=" + str(e[1]), kwargs.items()))
                       ))
            if not when_done:
                r = func(*args, **kwargs)
            return r
        return wrapped
    return decorator


async def download_file(url, name):
    import aiofiles
    import aiohttp
    path = os.path.join(TEMP_DIR, name)
    async with aiohttp.request("GET", url) as response:
        async with aiofiles.open(path, mode="w+b") as f:
            while True:
                chunk = await response.content.read(CHUNK_SIZE)
                if not chunk:
                    break
                await f.write(chunk)
    return path


async def remove_file(path):
    # TODO
    pass
    # return await aiofiles.os.remove(path)


def init_db(drop=False):
    import sqlite3 as sqlite
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.mkdir(os.path.dirname(DB_PATH))
    with sqlite.connect(DB_PATH) as connection:
        # with connection.cursor() as cursor:
        if drop:
            connection.execute("DROP TABLE IF EXISTS Users")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS Users(id INTEGER PRIMARY KEY, email TEXT)")


LF = "\n"
CR = "\r"
CRLF = "\r\n"
