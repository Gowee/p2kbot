import logging
import aiohttp

from .config import BROKER_CONNECT_ADDRESS
from .utils import remove_file, logit

logger = logging.getLogger(__name__)


class ConvertError(Exception):
    pass


@logit(logger)
async def convert_ebook(file_path, remove_old=True):
    async with aiohttp.request("GET", f"http://{BROKER_CONNECT_ADDRESS}/convert", params={"fpath": file_path}) as response:
        result = await response.json()
        if not result['success']:
            raise ConvertError(result.get('reason') or "Unkown.")
        new_file_path = result['fpath']
    # TODO: retry on failures
    if remove_old and new_file_path != file_path:
        await remove_file(file_path)
    logger.debug(f"brober converted: {file_path} → {new_file_path}")
    return new_file_path
