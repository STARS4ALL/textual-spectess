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

from sqlalchemy import select

#--------------
# local imports
# -------------

from spectess.photometer import REF, TEST, label
from spectess.photometer.tessw import Photometer
from spectess.ring import RingBuffer 

from spectess.dbase import engine, Session
from spectess.dbase.model import Config, Samples, Photometer as DbPhotometer

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

    def __init__(self):
        self.photometer = [None, None]
        self.producer = [None, None]
        self.consumer = [None, None]
        self.ring = [None, None]
        self.quit_event =  None
        self.photometer[TEST] = Photometer(role=TEST, old_payload=False)
        self.engine = engine
        self.Session = Session
       

    # ----------------------------------------
    # Public API to be used by the Textual TUI
    # ----------------------------------------

    def set_view(self, view):
        self.view = view

    @property
    def samples(self):
        return str(self._samples)

    async def load(self):
        '''Load configuration data from the database'''
        async with self.Session() as session:
            q = select(Config.value).where(Config.section == 'calibration', Config.prop == 'samples')
            self._samples = int((await session.scalars(q)).one())
            
    async def wait(self):
        self.quit_event = asyncio.Event() if self.quit_event is None else self.quit_event
        await self.quit_event.wait()
        await self.engine.dispose()
        raise  KeyboardInterrupt("User quits")

    async def get_info(self, role):
        '''Get Photometer Info'''
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

    def start_readings(self, role):
        self.consumer[role] = asyncio.create_task(self.receptor(role))
        self.producer[role] = asyncio.create_task(self.photometer[role].readings())

    def cancel_readings(self, role):
        self.producer[role].cancel()
        self.consumer[role].cancel()
        self.view.append_log(role, "READINGS PAUSED")

    async def receptor(self, role):
        '''Receiver consumer coroutine'''
        self.ring[TEST] = RingBuffer(self._samples)
        while True:
            msg = await self.photometer[role].queue.get()
            self.ring[role].append(msg)
            line = f"{msg['tstamp'].strftime('%Y-%m-%d %H:%M:%S')} [{msg.get('seq')}] f={msg['freq']} Hz, tbox={msg['tamb']}, tsky={msg['tsky']}"
            self.view.append_log(role, line)
            self.view.update_progress(role, 1)
            data = self.ring[role].frequencies()
            self.view.update_graph(role, data)

   
       