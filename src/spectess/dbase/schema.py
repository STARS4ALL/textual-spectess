# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# --------------------
# System wide imports
# -------------------

import sys
import uuid
import asyncio
import logging


# ---------------------
# Third party libraries
# ---------------------


from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession as AsyncSessionClass
from lica.textual.argparse import args_parser
from lica.textual.logging import configure_logging

from lica.sqlalchemy.asyncio.dbase import url, engine, Model, AsyncSession

# --------------
# local imports
# -------------

from .. import __version__
from .model import Config

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__.split(".")[-1])

# -------------------
# Auxiliary functions
# -------------------


async def populate(async_session: async_sessionmaker[AsyncSessionClass]) -> None:
    async with async_session() as session:
        async with session.begin():
            session.add(Config(section="database", prop="uuid", value=str(uuid.uuid4())))
            session.add(Config(section="calibration", prop="author", value="Rafael González"))
            session.add(Config(section="calibration", prop="nsamples", value=17))
            session.add(Config(section="calibration", prop="wavelength", value=350))
            session.add(Config(section="calibration", prop="wave_incr", value=5))


async def schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
        await conn.run_sync(Model.metadata.create_all)
        await populate(AsyncSession)
    await engine.dispose()


def main():
    """The main entry point specified by pyproject.toml"""
    parser = args_parser(name=__name__, version=__version__, description="Example SQLAlchemy App")
    args = parser.parse_args(sys.argv[1:])
    configure_logging(args)
    if args.verbose:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        logging.getLogger("aiosqlite").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    log.info("Creating new schema for %s", url)
    asyncio.run(schema())
