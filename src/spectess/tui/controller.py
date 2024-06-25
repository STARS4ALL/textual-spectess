# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import csv
import logging
import asyncio

from pathlib import PurePath

# -------------------
# Third party imports
# -------------------

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

#--------------
# local imports
# -------------

from ..photometer import TESSW, REF, TEST, label
from ..photometer.builder import PhotometerBuilder

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

    def __init__(self, engine, session_class):
        self.photometer = [None, None]
        self.producer = [None, None]
        self.consumer = [None, None]
        self.ring = [None, None]
        self.quit_event =  None
        builder = PhotometerBuilder()
        self.photometer[TEST] = builder.build(TESSW, TEST)
        self.engine = engine
        self.session_class = session_class
        self._role = TEST
        self._nsamples = 0
        self._wavelength = 0
        self._wave_incr = 0
        self._save = False
        self._meas_session = measurements_session_id()
        self._filename = PurePath(f"spectrum_calib_{self._meas_session}.csv")
        self._directory = PurePath(os.getcwd())
        self._selected_session = None
       

    # ========================================
    # Public API to be used by the Textual TUI
    # ========================================

    def set_view(self, view):
        self.view = view

    def quit(self):
        self.view.exit(return_code=2)

    @property
    def session_id(self):
        return self._meas_session

    @property
    def wavelength(self):
        return str(self._wavelength)

    @property
    def role(self):
        return int(self._role)

    @role.setter
    def role(self, value):
        self._role = int(value)

    @property
    def save(self):
        return bool(self._save)

    @save.setter
    def save(self, value):
        self._save = bool(value)

    @property
    def filename(self):
        return str(self._filename)

    @filename.setter
    def filename(self, value):
        self._filename = PurePath(value)

    @property
    def directory(self):
        return str(self._directory)

    @directory.setter
    def directory(self, value):
        self._directory = PurePath(value)
    

    def set_selected_session(self, value):
        log.info("Setting selected session at %s", value)
        self._selected_session = int(value)
        self._filename = PurePath(f"spectrum_calib_{value}.csv")
        self.view.set_filename(str(self._filename))

    # ---------------------------
    # Database Config section API
    # ---------------------------

    async def set_nsamples(self, value):
        log.info("Setting nsamples to %s", value)
        self._nsamples = int(value)
        await self._set_property('calibration', 'nsamples', value)

    async def get_nsamples(self):
        value = await self._get_property('calibration', 'nsamples')
        self._nsamples = int(value)
        return value

    async def set_start_wavelength(self, value):
        log.info("Setting starting wavelength to %s", value)
        self._wavelength = int(value)
        await self._set_property('calibration', 'wavelength', value)
        self.view.set_wavelength(value)

    async def get_start_wavelength(self):
        value = await self._get_property('calibration', 'wavelength')
        self._wavelength = int(value)
        return value

    async def set_wave_incr(self, value):
        log.info("Setting wavelength increment to %s", value)
        self._wave_incr = int(value)
        await self._set_property('calibration', 'wave_incr', value)

    async def get_wave_incr(self):
        value = await self._get_property('calibration', 'wave_incr')
        self._wave_incr = int(value)
        return value
        
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
            async with self.session_class() as session:
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
            self.view.enable_capture()

    async def receive(self, role):
        '''Receiver consumer coroutine'''
        log = logging.getLogger(label(role))
        self.view.reset_progress(role)
        while len(self.ring[role]) < self._nsamples:
            msg = await self.photometer[role].queue.get()
            self.ring[role].append(msg)
            line = f"{msg['tstamp'].strftime('%Y-%m-%d %H:%M:%S')} [{msg.get('seq')}] [{self._wavelength} nm] f={msg['freq']} Hz, tbox={msg['tamb']}, tsky={msg['tsky']}"
            self.view.append_log(role, line)
            self.view.update_progress(role, 1)
        self.producer[role].cancel()
        median, mean, stdev = self.ring[role].statistics()
        line = f"median = {median:0.3f} Hz, \u03BC = {mean:0.3f} Hz, \u03C3 = {stdev:0.3f} Hz @ \u03BB = {self._wavelength} nm"
        self.view.append_log(role, line)
        if not self._save:
            self.view.append_log(role, "WARNING: not saving samples") 
        else:
            await self.save_samples(role)
            self._wavelength += self._wave_incr
            self.view.set_wavelength(self._wavelength)
                    

    def start_readings(self, role):
        self.photometer[role].clear()
        self.ring[role] = RingBuffer(capacity=self._nsamples)
        self.consumer[role] = asyncio.create_task(self.receive(role))
        self.producer[role] = asyncio.create_task(self.photometer[role].readings())


    async def save_samples(self, role):
        #logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
        async with self.session_class() as session:
            async with session.begin():
                q = select(DbPhotometer).where(DbPhotometer.mac == self._cur_mac)
                dbphot = (await session.scalars(q)).one()
                samples = await dbphot.awaitable_attrs.samples # Asunchronous relationship reload
                while len(self.ring[role]) > 0:
                    s = self.ring[role].pop()
                    samples.append(
                        Samples(
                            tstamp = s['tstamp'],
                            role = label(role),
                            session = self._meas_session,
                            seq = s['seq'],
                            mag = s['mag'],
                            freq = s['freq'],
                            temp_box = s['tamb'],
                            wave = self._wavelength,
                        )
                    )
                session.add(dbphot)
        #logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    async def get_sessions(self, role):
        async with self.session_class() as session:
            async with session.begin():
                q = (select(Samples.session).distinct().join(Samples.photometer)
                    .where(Samples.role == label(role))).order_by(Samples.session.desc())
                session_ids = (await session.scalars(q)).all()
                result = tuple(str(item) for item in session_ids)
        return result

    async def export_samples(self):
        HEADERS = ("name", "mac", "model", "sensor", "freq_offset", "session","role","wavelength","seq_number","timestamp","frequency","box_temperature")
        async with self.session_class() as session:
            async with session.begin():
                q = (select(Samples).join(Samples.photometer.and_(DbPhotometer.mac == self._cur_mac))
                    .where(Samples.session == self._selected_session)
                    .order_by(Samples.wave, Samples.seq))
                samples = (await session.scalars(q)).all()
                filename = str(self._directory / self._filename)
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(HEADERS)
                for sample in samples:
                    phot = await sample.awaitable_attrs.photometer # Asunchronous relationship reload
                    row = [phot.name, phot.mac, phot.model, phot.sensor, phot.freq_offset, 
                        sample.session, sample.role, sample.wave, sample.seq, sample.tstamp,  sample.freq, sample.temp_box]
                    writer.writerow(row)
       

    # ======================
    # Private helper methods
    # ======================
        
    async def _get_property(self, section, property):
        async with self.engine.begin() as conn:
            result = await conn.execute(text("SELECT value FROM config_t WHERE section = :section AND property = :property"), 
                {"section": section, "property": property}
            )
            result = result.scalar_one()
        return result


    async def _set_property(self, section, property, value):
        async with self.engine.begin() as conn:
            await conn.execute(text("UPDATE config_t SET value = :value WHERE section = :section AND property = :property"), 
                {"section": section, "property": property , "value": value}
            )
            await conn.commit()