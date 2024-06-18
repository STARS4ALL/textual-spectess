# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

# ---------------------
# Third party libraries
# ---------------------

import decouple

from sqlalchemy import MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine

url = decouple.config('DATABASE_ASYNC_URL')
 
engine = create_async_engine(url, echo=True)

metadata = MetaData(
    naming_convention = {
        'ix': "ix_%(column_0_label)s",
        'uq': "uq_%(table_name)s_%(column_0_name)s",
        'ck': "ck_%(table_name)s_%(constraint_name)s",
        'fk': "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        'pk': "pk_%(table_name)s",
    }
)

Session = sessionmaker(engine)