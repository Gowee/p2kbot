# aiosmtplib does not support sending attachment in stream yet
# but there seems to be plans: https://github.com/cole/aiosmtplib/milestone/4

# The following code is adapted from https://stackoverflow.com/questions/3362600/how-to-send-email-attachments

import os
from urllib.parse import quote as percent_encode
from io import BytesIO
from email.generator import BytesGenerator
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from mimetypes import guess_type
import logging

import aiosmtplib

from .mx_resolver import resolve_MX


logger = logging.getLogger("kindle-pusher")


def multipart_to_bytes(multipart: MIMEMultipart) -> bytes:
    fp = BytesIO()
    g = BytesGenerator(fp)
    g.flatten(multipart)
    return fp.getvalue()


async def push_file(sender_email, recipient_email, file_path, file_name=None):
    if file_name is None:
        file_name = os.path.basename(file_path)
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Date'] = formatdate()
    # TODO: make text meaningful
    message['Subject'] = "P2KBot Push"
    message.attach(
        MIMEText("The email is sent by P2KBot to push books to the kindle inbox."))
    # set attachment
    part = MIMEBase(*guess_type(file_path))
    with open(file_path, 'rb') as f:
        part.set_payload(f.read())
    # left the encoder be the default base64
    # although base64 is inefficient, but there seems no other options due to design limitations of SMTP protocol; ref:
    # https://stackoverflow.com/questions/25710599/content-transfer-encoding-7bit-or-8-bit
    # encoders.encode_base64(part)

    # use `ext-val` to send non-ASCII file name; ref:
    # https://github.com/actix/actix-web/blob/6c9f9fff735023005a99bb3d17d3359bb46339c0/actix-http/src/header/mod.rs
    # TODO: put transliterated file name into `filename` field?
    part.add_header('Content-Disposition',
                    f"attachment; filename=\"{file_name}\"; filename*=UTF-8''{percent_encode(file_name)}")
    message.attach(part)

    # TODO: better way to convert `MIMEMultipart` into `Message`?
    hostnames = await resolve_MX(recipient_email.split("@")[1])
    logging.debug(f"Got MX {hostnames} for {recipient_email}")
    await aiosmtplib.send(multipart_to_bytes(message), sender_email, recipient_email, hostname=hostnames[0])
