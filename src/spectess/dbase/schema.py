# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys
import asyncio
import logging

from typing import Optional, List
from datetime import datetime

# ------------------
# SQLAlchemy imports
# -------------------

#--------------
# local imports
# -------------

from spectess import __version__
from spectess.utils.argsparse import args_parser
from spectess.utils.logging import configure
from spectess.dbase import url, engine, metadata, Session
from spectess.dbase.model import Model, Photometer, Samples, Config

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the module logger
log = logging.getLogger(__name__)

# -------------------
# Auxiliary functions
# -------------------

async def schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Model.metadata.drop_all)
        await conn.run_sync(Model.metadata.create_all)
    await engine.dispose()

def main():
    '''The main entry point specified by pyproject.toml'''
    parser = args_parser(
        name = __name__,
        version = __version__,
        description = "Example SQLAlchemy App"
    )
    args = parser.parse_args(sys.argv[1:])
    configure(args)
    log.info("Creating/Opening schema %s", url)
    asyncio.run(schema())