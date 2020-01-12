# aiosmtplib does not support sending attachment in stream yet
# but there seems to be plans: https://github.com/cole/aiosmtplib/milestone/4

# The following code is adapted from https://stackoverflow.com/questions/3362600/how-to-send-email-attachments

import os
from urllib.parse import quote as percent_encode
from io import BytesIO
from email.generator import BytesGenerator
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.utils import formatdate
from email.header import Header
from email.encoders import encode_base64
import logging
import asyncio

import aiosmtplib
import smtplib

from .mx_resolver import resolve_MX
from .utils import simple_sha1
from .config import EMAIL_DOMAIN

DOCUMENT_FORMATS = (".doc", ".docx", ".rtf", ".htm",
                    ".html", ".txt", ".zip", ".mobi",
                    ".pdf", ".jpg", ".gif", ".bmp",
                    ".png")

logger = logging.getLogger(__name__)


def multipart_to_bytes(multipart: MIMEMultipart) -> bytes:
    fp = BytesIO()
    g = BytesGenerator(fp)
    g.flatten(multipart)
    return fp.getvalue()


async def push_file(sender_email, recipient_email, file_path, file_name=None):
    # ref:
    # https://stackoverflow.com/questions/3362600/how-to-send-email-attachments
    # http://code.activestate.com/recipes/578150-sending-non-ascii-emails-from-python-3/
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
    part = MIMEBase("application", "pdf")  # "x-mobipocket-ebook")
    with open(file_path, 'rb') as f:
        part.set_payload(f.read())
    # left the encoder be the default base64
    # although base64 is inefficient, but there seems no other options due to design limitations of SMTP protocol; ref:
    # https://stackoverflow.com/questions/25710599/content-transfer-encoding-7bit-or-8-bit
    encode_base64(part)
    part.add_header('Content-Disposition', "attachment", filename=file_name)
    message.attach(part)
    hostnames = await resolve_MX(recipient_email.split("@")[1])
    logger.debug(f"Got MX {hostnames} for {recipient_email}")
    # r = await send_email(message, hostnames[0])#hostnames[0])
    # r = await send_email(multipart_to_bytes(message), "127.0.0.1", 8025)#hostnames[0])
    r = await aiosmtplib.send(message, sender_email, recipient_email, hostname=hostnames[0])
    logger.debug(
        f"email sent, attachment \"{file_path}\" as \"{file_name}\", result: {r}")


def send_email(message, hostname="localhost", port=25):
    def sender():
        with smtplib.SMTP(hostname, port) as s:
            return s.sendmail("gowe.agent@gmail.com", ["gowe.agent@kindle.cn"], message)
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, sender)
