import asyncio
import logging
import os

from aiohttp import web
from .calibre_ import calibre
from calibre.ebooks.conversion.plumber import Plumber  # pylint: disable=import-error
Plumber.flush = lambda _: None  # noqa
from calibre.utils.logging import Log as CalibreLog  # pylint: disable=import-error

from .utils import logit
from .config import CONVSRV_LISTEN_ADDRESS


logger = logging.getLogger(__name__)


@logit(logger)
async def handle_cwd(_request):
    return web.json_response({"success": True, "cwd": os.getcwd()})


@logit(logger)
async def handle_convert(request):
    input_file_path = request.query.get('fpath')
    toext = request.query.get('toext') or ".mobi"
    if not input_file_path:
        return web.json_response({"success": False, "reason": "Invalid file path."}, status=400)
    input_file_path = os.path.realpath(input_file_path)
    stem, ext = os.path.splitext(input_file_path)
    if not ext:
        return web.json_response({"success": False, "reason": "Invalid file extension."}, status=400)
    output_file_path = stem + toext
    # TODO: this should haved be async if not due to the lack of support by aiofiles
    if not os.path.exists(output_file_path):
        plumber_logger = CalibreLog()
        plumber = Plumber(input_file_path, output_file_path,
                          plumber_logger, plumber_logger)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, plumber.run)
    logger.debug(f"converted: {input_file_path} → {output_file_path}")
    return web.json_response({"success": True, "fpath": output_file_path})

app = web.Application()
app.add_routes((web.get('/cwd', handle_cwd),
                web.get('/convert', handle_convert)))


def run():
    host, port = CONVSRV_LISTEN_ADDRESS
    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    run()
