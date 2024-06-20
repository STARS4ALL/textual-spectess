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
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

#--------------
# local imports
# -------------

from . import url, engine, metadata as metadata_obj, Session

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

class Model(AsyncAttrs, DeclarativeBase):
    metadata = metadata_obj

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
    mac:            Mapped[str] = mapped_column(String(17), unique=True)
    sensor:         Mapped[str] = mapped_column(String(12))
    model:          Mapped[str] = mapped_column(String(8))
    firmware:       Mapped[str] = mapped_column(String(17))
    zero_point:     Mapped[float]
    freq_offset:    Mapped[float]

    # This is not a real column, it s meant for the ORM
    samples: Mapped[List['Samples']] = relationship(back_populates="photometer")

    def __repr__(self) -> str:
        return f"TESS(id={self.id!r}, name={self.name!r}, mac={self.mac!r})"
   

class Samples(Model):
    __tablename__ = "samples_t"

    id:         Mapped[int] = mapped_column(primary_key=True)
    tess_id:    Mapped[int] = mapped_column(ForeignKey("photometer_t.id"), index=True)
    tstamp:     Mapped[datetime]
    session:    Mapped[int]
    seq:        Mapped[int]
    mag:        Mapped[float]
    freq:       Mapped[float]
    temp_box:   Mapped[float]
    wave:       Mapped[int]

    # This is not a real column, it s meant for the ORM
    photometer: Mapped['Photometer'] = relationship(back_populates="samples")

    def __repr__(self) -> str:
        return f"Sample(id={self.id!r}, freq={self.freq!r}, mag={self.mag!r}, seq={self.seq!r}, wave={self.wave})"

