
# The following code is adapted from https://stackoverflow.com/questions/3362600/how-to-send-email-attachments

import os
import logging
import asyncio
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from email.encoders import encode_base64
from mimetypes import guess_type as _guess_mime_type

from aiosmtplib import send as send_email, SMTPException
import smtplib

from .mx_resolver import resolve_MX
from .utils import simple_sha1
from .config import EMAIL_DOMAIN

DOCUMENT_FORMATS = (".doc", ".docx", ".rtf", ".htm",
                    ".html", ".txt", ".zip", ".mobi",
                    ".pdf", ".jpg", ".gif", ".bmp",
                    ".png")

logger = logging.getLogger(__name__)


def guess_mime_type(url, default=("application", "octet-stream")):
    guess = _guess_mime_type(url)
    if guess == (None, None):
        if url.endswith(".mobi"):
            guess = ("application", "x-mobipocket-ebook")
        else:
            guess = default
    return guess


class EmailDeliveryFailure(Exception):
    pass


async def push_file(sender_email, recipient_email, file_path, file_name=None):
    if file_name is None:
        file_name = os.path.basename(file_path)

    message = MIMEMultipart()
    message['From'] = f"P2KBot <{sender_email}>"
    message['To'] = f"<{recipient_email}>"
    message['Date'] = formatdate()
    # NOTE: Message-ID and Date must be present in headers so that Kindle can receive; ref:
    # https://github.com/janeczku/calibre-web/issues/94
    message['Message-ID'] = f"<p2kbot-{simple_sha1(sender_email + file_path)}@{EMAIL_DOMAIN}>"
    # TODO: make text meaningful
    message['Subject'] = "Push to Kindle"
    message.attach(
        MIMEText("The email is sent by P2KBot to push books to Kindle.", _charset="utf-8"))

    # set attachment
    part = MIMEBase(*guess_mime_type(file_name))
    # aiosmtplib does not support sending attachment in stream yet
    # but there seems to be plans: https://github.com/cole/aiosmtplib/milestone/4
    with open(file_path, 'rb') as f:
        part.set_payload(f.read())
    # left the encoder be the default base64
    # although base64 is inefficient, but there seems no other options due to design limitations of SMTP protocol; ref:
    # https://stackoverflow.com/questions/25710599/content-transfer-encoding-7bit-or-8-bit
    # Update: it seems that the default is no encoding instead of encode_base64 and no encoding works well?
    encode_base64(part)
    # aiosmtplib is expected to properly encode filename if there is non-ASCII characters
    part.add_header('Content-Disposition', "attachment", filename=file_name)
    message.attach(part)

    hostnames = await resolve_MX(recipient_email.split("@")[1])
    logger.debug(f"Got MX {hostnames} for {recipient_email}")
    try:
        r = await send_email(message, sender_email, recipient_email, hostname=hostnames[0])
        logger.debug(
            f"email sent, attachment \"{file_path}\" as \"{file_name}\", result: {r}")
    except SMTPException as e:
        logger.debug(
            f"failed to sent email from {sender_email} to {recipient_email} (SMTP Server: {hostnames[0]}) with error {e}")
        raise EmailDeliveryFailure(
            f"Failed to send email to kindle due to error {e.__class__.__name__}: {e}") from e
