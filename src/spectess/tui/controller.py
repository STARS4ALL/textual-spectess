# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import sys
import argparse
import logging
import asyncio

# -------------------
# Third party imports
# -------------------


#--------------
# local imports
# -------------

from spectess.photometer import REF, TEST, label
from spectess.photometer.tessw import Photometer
from spectess.ring import RingBuffer 

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger()

# -------------------
# Auxiliary functions
# -------------------

# -------
# Classes
# -------

class Controller:

    def __init__(self, ring_buffer_size=75):
        self.photometer = [None, None]
        self.producer = [None, None]
        self.consumer = [None, None]
        self.ring = [None, None]
        self.quit_event =  None
        self.photometer[TEST] = Photometer(role=TEST, old_payload=False)
        self.ring[TEST] = RingBuffer(ring_buffer_size)
       

    # ----------------------------------------
    # Public API to be used by the Textual TUI
    # ----------------------------------------

    def set_view(self, view):
        self.view = view

    async def wait(self):
        self.quit_event = asyncio.Event() if self.quit_event is None else self.quit_event
        await self.quit_event.wait()
        raise  KeyboardInterrupt("User quits")

    async def get_info(self, role):
        try:
            info = await self.photometer[role].get_info()
        except asyncio.exceptions.TimeoutError:
            line = f"Failed contacting {label(role)} photometer"
            log.error(line)
            self.view.append_log(role, line)
            self.view.reset_switch(role)
        except Exception as e:
            log.error(e)
        else:
            self.view.clear_metadata_table(role)
            self.view.update_metadata_table(role, info)


    async def receptor(self, role):
        while True:
            msg = await self.photometer[role].queue.get()
            self.ring[role].append(msg)
            line = f"{msg['tstamp'].strftime('%Y-%m-%d %H:%M:%S')} [{msg.get('seq')}] f={msg['freq']} Hz, tbox={msg['tamb']}, tsky={msg['tsky']}"
            self.view.append_log(role, line)
            self.view.update_progress(role, 1)
            data = self.ring[role].frequencies()
            self.view.update_graph(role, data)

    def cancel_readings(self, role):
        self.producer[role].cancel()
        self.consumer[role].cancel()
        self.view.append_log(role, "READINGS PAUSED")

    def start_readings(self, role):
        self.consumer[role] = asyncio.create_task(self.receptor(role))
        self.producer[role] = asyncio.create_task(self.photometer[role].readings())
       