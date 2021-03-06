import sys
import os
import logging


def main(args=sys.argv):
    if len(args) > 1 and args[1] == "botsrv":
        from .botsrv import run
    elif len(args) > 1 and args[1] == "convsrv":
        from .convsrv import run
    elif len(args) > 1 and args[1] == "initdb":
        from .utils import init_db

        drop = len(args) > 2 and args[2].lower() == "drop"

        def run():
            return init_db(drop)

    else:
        print(
            f"""Usage:
    {args[0]} botsrv
        Run bot service.
    {args[0]} convsrv
        Run converter service.
    {args[0]} initdb
        Create and initialize SQLite DB file."""
        )
        exit(-1)

    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())

    run()


if __name__ == "__main__":
    main()
