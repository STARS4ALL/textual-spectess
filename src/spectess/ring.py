# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import math
import logging
import statistics
import collections

# -------------------
# Third party imports
# -------------------


#--------------
# local imports
# -------------

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

def magnitude(zp, fo, f):
    return zp - 2.5*math.log10(f - fo)

# ------- 
# Classes
# -------

class RingBuffer:

    def __init__(self, capacity=75, zp=20.50, fo=0.0):
        self._buffer = collections.deque([], capacity)
        self._zp = zp
        self._fo = fo

    def append(self, item):
        self._buffer.append(item)

    def magnitude(self, f):
        return self._zp - 2.5*math.log10(f - self._fo)

    def frequencies(self):
        return [item['freq'] for item in self._buffer]
        
    def statistics(self):
        frequencies = [item['freq'] for item in self._buffer]
        aver = statistics.median_low(frequencies)
        stdev = statistics.stdev(frequencies, aver)
        return aver, stdev
    