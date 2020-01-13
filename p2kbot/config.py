import os

__all__ = (
    "BOT_TOKEN",
    "TEMP_DIR",
    "DB_PATH",
    "EMAIL_DOMAIN",
    "CONVSRV_LISTEN_ADDRESS",
    "BROKER_CONNECT_ADDRESS",
    "ALLOWED_KINDLE_DOMAINS",
)

BOT_TOKEN = None
TEMP_DIR = "./tmp/"
DB_PATH = "./p2kbot.db"
EMAIL_DOMAIN = "p2kbot.example.com"
CONVSRV_LISTEN_ADDRESS = "127.0.0.1:12000"
BROKER_CONNECT_ADDRESS = Ellipsis
ALLOWED_KINDLE_DOMAINS = ["@kindle.com", "@kindle.cn", "@free.kindle.com"]


class ConfigMissing(Exception):
    pass


for envvar in __all__:
    val = os.environ.get(envvar)
    if val is not None:
        globals()[envvar] = val
    elif globals().get(envvar) is None:
        raise ConfigMissing(envvar)

TEMP_DIR = os.path.realpath(TEMP_DIR)
if BROKER_CONNECT_ADDRESS is Ellipsis:
    BROKER_CONNECT_ADDRESS = CONVSRV_LISTEN_ADDRESS
CONVSRV_LISTEN_ADDRESS = tuple(CONVSRV_LISTEN_ADDRESS.rsplit(":", maxsplit=1))
# BROKER_CONNECT_ADDRESS = tuple(BROKER_CONNECT_ADDRESS.rsplit(":", maxsplit=1))
