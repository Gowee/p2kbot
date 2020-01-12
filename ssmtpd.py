# pylint: skip-file
# Adapted from https://github.com/aio-libs/aiosmtpd/blob/97730f37f4a283b3da3fa3dbf30dd925695fea69/examples/server.py
"""Simple SMTP server that dumps messages received to files."""
import asyncio
import logging
from aiosmtpd.controller import Controller
from time import time as now


class ExampleHandler:
    # async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
    #     if not address.endswith('@example.com'):
    #         return '550 not relaying to that domain'
    #     envelope.rcpt_tos.append(address)
    #     return '250 OK'
    async def handle_DATA(self, server, session, envelope, enable_SMTPUTF8=True):
        print("Message from %s" % envelope.mail_from)
        print("Message for %s" % envelope.rcpt_tos)
        print("Message data:\n")
        with open(f"tmp/{str(int(now() * 1000))}.eml", "wb") as f:
            f.write(envelope.original_content)
        print("End of message")
        return "250 Message accepted for delivery"


async def amain():
    controller = Controller(ExampleHandler(), hostname="", port=8025)
    controller.start()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.create_task(amain())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
