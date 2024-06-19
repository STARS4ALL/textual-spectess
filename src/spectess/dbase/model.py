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

from sqlalchemy import String, ForeignKey, PrimaryKeyConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.ext.declarative import declarative_base

#--------------
# local imports
# -------------

from spectess.dbase import url, engine, metadata, Session

# ----------------
# Module constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

# get the root logger
log = logging.getLogger(__name__)

# ---------------------
# Data Model as classes
# ---------------------


Model = declarative_base(metadata=metadata)

class Config(Model):

    __tablename__ = "config_t"

    section:   Mapped[str] = mapped_column(String(32))
    prop:      Mapped[str] = mapped_column('property', String(255))
    value:     Mapped[str] = mapped_column(String(255))

    __table_args__ = (
        PrimaryKeyConstraint(
            section,
            prop),
        {})

    def __repr__(self) -> str:
        return f"TESS(id={self.id!r}, nname={self.name!r}, mac={self.mac!r})"


class Photometer(Model):

    __tablename__ = "photometer_t"

    id:             Mapped[int] = mapped_column(primary_key=True)
    name:           Mapped[str] = mapped_column(String(10))
    mac:            Mapped[str] = mapped_column(String(17))
    sensor:         Mapped[str] = mapped_column(String(12))
    model:          Mapped[str] = mapped_column(String(8))
    firmware:       Mapped[str] = mapped_column(String(17))
    zero_point:     Mapped[float]
    freq_offset:    Mapped[float]

    # This is not a real column, it s meant for the ORM
    samples: Mapped[List['Samples']] = relationship(back_populates="photometer")

    def __repr__(self) -> str:
        return f"TESS(id={self.id!r}, nname={self.name!r}, mac={self.mac!r})"
   

class Samples(Model):
    __tablename__ = "samples_t"

    id:        Mapped[int] = mapped_column(primary_key=True)
    tess_id:   Mapped[int] = mapped_column(ForeignKey("photometer_t.id"))
    tstamp:    Mapped[datetime]
    session:   Mapped[int]
    seq:       Mapped[int]
    mag:       Mapped[float]
    freq:      Mapped[float]
    temp_box:  Mapped[float]

    # This is not a real column, it s meant for the ORM
    photometer: Mapped['Photometer'] = relationship(back_populates="samples")

    def __repr__(self) -> str:
        return f"Sample(id={self.id!r}, freq={self.freq!r}, mag={self.mag!r}, seq={self.seq!r})"

