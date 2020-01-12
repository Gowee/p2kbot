"""A simplistic DNS resolver for MX record only using DoH."""

import aiohttp
import logging

from .utils import logit

logger = logging.getLogger(__name__)


class DNSResolutionError(Exception):
    pass


class QTYPE:
    MX = 15


resolver_session = aiohttp.ClientSession(raise_for_status=True)
simple_cache = {}


@logit(logger, level=logging.DEBUG)
async def resolve_MX(hostname):
    # TODO: where is not there a usable pure Python async DNS resolver?
    # TODO: no cache so far
    try:
        async with resolver_session.get("https://cloudflare-dns.com/dns-query",
                                        params={"name": hostname,
                                                "type": "MX"},
                                        headers={"Accept": "application/dns-json"}) as response:
            response = await response.json(content_type="application/dns-json")
    except aiohttp.ClientError as e:
        raise DNSResolutionError("DoH request failed.") from e
    if response['Status'] != 0:  # NoError
        msg = f"DNS resolution failed for {hostname} (MX) with status {response['status']}."
        logger.warn(msg)
        raise DNSResolutionError(msg)
    results = [(int((data := answer['data'].split(" ", maxsplit=1))[0]), data[1])
               for answer in response['Answer'] if answer['type'] == QTYPE.MX]
    results.sort(key=lambda e: e[0])
    return list(map(lambda e: e[1], results))
