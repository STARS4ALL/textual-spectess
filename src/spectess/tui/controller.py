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

from sqlalchemy import select, inspect
from sqlalchemy.exc import IntegrityError

#--------------
# local imports
# -------------

from ..photometer import REF, TEST, label
from ..photometer.tessw import Photometer
from ..ring import RingBuffer 
from ..dbase.model import Config, Samples, Photometer as DbPhotometer
from ..utils.misc import measurements_session_id

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the logger

log = logging.getLogger(__name__)

# -------------------
# Auxiliary functions
# -------------------

# -------
# Classes
# -------

class Controller:

    def __init__(self, engine, session_factory):
        self.photometer = [None, None]
        self.producer = [None, None]
        self.consumer = [None, None]
        self.ring = [None, None]
        self.quit_event =  None
        self.photometer[TEST] = Photometer(role=TEST, old_payload=False)
        self.engine = engine
        self.session_factory = session_factory
        self._nsamples = 0
        self._wavelength = 0
        self._save = False
        self._meas_session = measurements_session_id()
       

    # ----------------------------------------
    # Public API to be used by the Textual TUI
    # ----------------------------------------

    def set_view(self, view):
        self.view = view

    def quit(self):
        self.view.exit(return_code=2)

    @property
    def nsamples(self):
        return str(self._nsamples)

    @nsamples.setter
    def nsamples(self, value):
        self._nsamples = int(value)

    @property
    def wavelength(self):
        return str(self._wavelength)

    @wavelength.setter
    def wavelength(self, value):
        self._wavelength = int(value)

    @property
    def save(self):
        return bool(self._save)

    @save.setter
    def save(self, value):
        log.info("setting save to %s", value)
        self._save = bool(value)

    async def load(self):
        '''Load configuration data from the database'''
        log.info("loading configuration data")
        async with self.session_factory() as session:
            q = select(Config.value).where(Config.section == 'calibration', Config.prop == 'samples')
            self._nsamples = int((await session.scalars(q)).one())
            q = select(Config.value).where(Config.section == 'calibration', Config.prop == 'wavelength')
            self._wavelength = int((await session.scalars(q)).one())
    
        
    async def get_info(self, role):
        '''Get Photometer Info'''
        log = logging.getLogger(label(role))
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
            async with self.session_factory() as session:
                session.begin()
                try:
                    q = select(DbPhotometer).where(DbPhotometer.mac == info.get('mac'))
                    dbphot = (await session.scalars(q)).one_or_none()
                    if not dbphot:
                        session.add(
                            DbPhotometer(
                                name= info.get('name'), 
                                mac = info.get('mac'),
                                sensor = info.get('sensor'),
                                model = info.get('model'),
                                firmware = info.get('firmware'),
                                zero_point = info.get('zp'),
                                freq_offset = info.get('freq_offset'),
                            )
                        )
                    await session.commit()
                except Exception as e:
                    log.warn("Ignoring already saved photometer entry")
                    await session.rollback()
            self._cur_mac = info.get('mac')
                    

    def start_readings(self, role):
        self.photometer[role].clear()
        self.ring[role] = RingBuffer(capacity=self._nsamples)
        self.consumer[role] = asyncio.create_task(self.receive(role))
        self.producer[role] = asyncio.create_task(self.photometer[role].readings())


    async def save_samples(self, role):
        log = logging.getLogger(label(role))
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        async with self.session_factory() as session:
            session.begin()
            try:
                q = select(DbPhotometer).where(DbPhotometer.mac == self._cur_mac)
                dbphot = (await session.scalars(q)).one()
                await dbphot.awaitable_attrs.samples # Asunchronous relationship preload
                while len(self.ring[role]) > 0:
                    s = self.ring[role].pop()
                    dbphot.samples.append(
                        Samples(
                            tstamp = s['tstamp'],
                            session = 0,
                            seq = s['seq'],
                            mag = s['mag'],
                            freq = s['freq'],
                            temp_box = s['tamb'],
                            wave = self._wavelength,
                        )
                    )
                session.add(dbphot)
                await session.commit()
            except Exception as e:
                log.warn("An error ocurred")
                log.error(e)
                await session.rollback()
        logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)


    async def receive(self, role):
        '''Receiver consumer coroutine'''
        log = logging.getLogger(label(role))
        while len(self.ring[role]) < self._nsamples:
            msg = await self.photometer[role].queue.get()
            self.ring[role].append(msg)
            line = f"{msg['tstamp'].strftime('%Y-%m-%d %H:%M:%S')} [{msg.get('seq')}] f={msg['freq']} Hz, tbox={msg['tamb']}, tsky={msg['tsky']}"
            self.view.append_log(role, line)
        self.producer[role].cancel()
        median, mean, stdev = self.ring[role].statistics()
        line = f"median = {median:0.3f} Hz, \u03BC = {mean:0.3f} Hz, \u03C3 = {stdev:0.3f} Hz @ \u03BB = {self._wavelength} nm"
        self.view.append_log(role, line)
        await self.save_samples(role)
       

    # ----------------------
    # Private helper methods
    # ----------------------
        
       