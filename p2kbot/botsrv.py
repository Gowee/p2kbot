#!/usr/bin/python3

import asyncio
import logging
import os

# from async_lru import alru_cache
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    InlineQuery,
    InputTextMessageContent,
    InlineQueryResultArticle,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
)
from aiogram.utils.exceptions import InvalidQueryID
from aiogram.types.message import ParseMode, ContentType
from aiogram.dispatcher.filters.builtin import CommandStart, ContentTypeFilter
from aiogram.dispatcher.handler import SkipHandler

from . import db, kindle
from .config import BOT_TOKEN, ALLOWED_KINDLE_DOMAINS
from .utils import (
    get_sender_email,
    download_file,
    simple_sha1,
    logit,
    is_valid_email_address,
    LF,
)
from .broker import convert_ebook

logger = logging.getLogger("p2kbot")

bot = Bot(token=BOT_TOKEN)
dispatcher = Dispatcher(bot)


@dispatcher.message_handler(commands=("start",))
@logit(logger)
async def handle_start(message: types.Message):
    # logger.debug(f"handle_start:{message.text}")
    args = message.get_args()
    if args:
        raise SkipHandler
    await message.reply(
        "Push to Kindle Bot helps converting and pushing books to Kindle.\nTry /help .",
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


@dispatcher.message_handler(commands=("help",))
@logit(logger)
async def handle_help(message: types.Message):
    # logger.debug(f"handle_start:{message.text}")
    await message.reply(
        f"""1. Before pushing documents, set (or update) the Send-to-Kindle email address by simply sending it here.
It is usually like <code>user@kindle.com</code>.

2. Then add the following email address to the approved email address list in <i><a href="https://www.amazon.com/hz/mycd/myx">Amazon account settings</a></i> → <i>Preferences</i> → <i>Personal Document Settings</i>:
<b>{get_sender_email(message.from_user.id)}</b>

3. Send documents.

Currently, the following Send-to-Kindle emails are supported:
<pre>{LF.join(ALLOWED_KINDLE_DOMAINS)}</pre>
""",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


@dispatcher.message_handler(content_types=(ContentType.DOCUMENT,))
@logit(logger)
async def handle_file(message: types.Message):
    if (recipient_email := await db.get_user_email(message.from_user.id)) is None:
        await message.reply(
            "Kindle email address is not set.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    else:
        sender_email = get_sender_email(message.from_user.id)
        try:
            if message.document.file_size > 20 * 1024 * 1024:
                raise Exception("File too large.")
            file = await bot.get_file(message.document.file_id)
            file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
            file_name = message.document.file_name
            file_stem, file_ext = os.path.splitext(file_name)
            file_path, reply = await asyncio.gather(
                download_file(file_url, simple_sha1(file.file_unique_id) + file_ext),
                message.reply(
                    "📥 Downloading the document...",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                ),
            )
            if file_ext.lower() not in kindle.DOCUMENT_FORMATS:
                file_path, reply = await asyncio.gather(
                    convert_ebook(file_path),
                    reply.edit_text(
                        "🔄 Converting the document...",
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                    ),
                )
            reply, _ = await asyncio.gather(
                reply.edit_text(
                    "✉️ Pushing the document to Kindle...",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                ),
                kindle.push_file(
                    sender_email,
                    recipient_email,
                    file_path,
                    file_stem + os.path.splitext(file_path)[1],
                ),
            )
            await reply.edit_text(
                "✅ Push done.\nIt may take a few minutes to reach Kindle.",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        except Exception as e:
            try:
                await reply.delete()
            except Exception:
                pass
            # FIX: e may leak secrets such as BOT_TOKEN?
            await message.reply(
                f"❌ Error:\n```\n{e.__class__.__name__}: {str(e)}\n```",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
            raise e


@dispatcher.message_handler()
@logit(logger)
async def handle_message(message: types.Message):
    if "@" in message.text:
        email = message.text.strip()
        if is_valid_email_address(email):
            if not any(email.endswith(domain) for domain in ALLOWED_KINDLE_DOMAINS):
                await message.reply(
                    "Unsupported email domain. Try /help .",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
            else:
                await db.set_user_email(message.from_user.id, email)
                await message.reply(
                    "Send-to-Kindle email address updated.",
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
        else:
            await message.reply(
                "Invalid email address.",
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
    else:
        await message.reply(
            "Unexpected message, try /help .",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )


def run():
    executor.start_polling(dispatcher)
