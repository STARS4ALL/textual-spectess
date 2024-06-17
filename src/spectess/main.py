# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import sys
import logging

# -------------------
# Third party imports
# -------------------

import asyncio

#--------------
# local imports
# -------------

from spectess import __version__
from spectess.utils.argsparse import args_parser
from spectess.utils.logging import configure
from spectess.tui.application import SpecTessApp
from spectess.tui.controller import Controller

# ----------------
# Module constants
# ----------------

DESCRIPTION = "TESS Spectral Response Tool"
# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger()

# -------------------
# Auxiliary functions
# -------------------

async def bootstrap():
    controller = Controller()
    tui = SpecTessApp(controller, DESCRIPTION)
    controller.set_view(tui)
    t1 = asyncio.create_task(tui.run_async())
    t2 = asyncio.create_task(controller.wait())
    await asyncio.gather(t1, t2)

def main():
    '''The main entry point specified by pyproject.toml'''
    parser = args_parser(
        name = __name__,
        version = __version__,
        description = DESCRIPTION
    )
   
    args = parser.parse_args(sys.argv[1:])
    configure(args)
    try:
        asyncio.run(bootstrap())
    except KeyboardInterrupt:
        log.warn("Application quits by user request")
