# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import logging
import asyncio

# ---------------------
# Third party libraries
# ---------------------

from lica.misc import chop

# ------------
# Own packages
# ------------

from . import TEST, REF, label, endpoint, TESSW, TAS, TESSP

from .protocol.transport import UDPTransport, TCPTransport, SerialTransport
from .protocol.payload   import JSONPayload, OldPayload
from .protocol.photinfo  import HTMLInfo, DBaseInfo


class Photometer:

    def __init__(self, role):
        self.role = role
        self.label = label(role)
        self.log = logging.getLogger(self.label)
        self._queue = asyncio.Queue()
        self.decoder = None
        self.transport = None
        self.info = None

    def attach(self, transport, info, decoder):
        self.decoder = decoder
        self.transport = transport
        self.info = info
        
    @property
    def queue(self):
        return self._queue

    # -----------
    # Private API
    # -----------

    def handle_readings(self, payload, timestamp):
        flag, message = self.decoder.decode(payload, timestamp)
        # message is now a dict containing the timestamp among other fields
        if flag:
            try:
                self._queue.put_nowait(message)
            except Exception as e:
                self.log.error("%s", e)
                self.log.error("receiver lost, discarded message")

    # ----------
    # Public API
    # ----------

    def clear(self):
        self.decoder.clear()

    async def readings(self):
        return await self.transport.readings()

    async def get_info(self, timeout=5):
        return await self.info.get_info(timeout)

    async def save_zero_point(self, zero_point):
        return await self.info.save_zero_point(zero_point)


class PhotometerBuilder:


    def build(self, model, role):
        url = endpoint(role)
        transport, name, number = chop(url,sep=':')
        number = int(number) if number else 80

        photometer = Photometer(role)

        if role == REF:
            assert model == TESSW, "Reference photometer model should be TESS-W"
            assert transport == "serial", "Reference photometer should use a serial transport" 
            info_obj = DBaseInfo(photometer, engine)
            transport_obj = SerialTransport(photometer, port=name, baudrate=number)
            decoder_obj = OldPayload(photometer)
        else:
            if transport == 'serial':
                assert model == TESSP or model == TAS, "Test photometer model on serial port should be TESS-P or TAS"
                info_obj = CLInfo(photometer)
                transport_obj = SerialTransport(photometer, port=name, baudrate=number)
                decoder_obj = JSONPayload(photometer)
            elif transport == 'tcp':
                assert model == TESSW, "Test photometer model using TCP should be TESS-W"
                info_obj = HTMLInfo(photometer, addr=name)
                transport_obj = TCPTransport(photometer, host=name, port=number)
                decoder_obj = JSONPayload(photometer)
            elif transport == 'udp':
                assert model == TESSW, "Test photometer model using UDP should be TESS-W"
                info_obj = HTMLInfo(photometer, addr=name)
                transport_obj = UDPTransport(photometer, port=number)
                decoder_obj = JSONPayload(photometer)
            else:
                raise ValueError(f"Transport {transport} not known")
        photometer.attach(transport_obj, info_obj, decoder_obj)
        return photometer




