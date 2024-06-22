# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

# ---------------------
# Third party libraries
# ---------------------

import decouple

# ---------
# Constants
# ---------

# Photometer roles
REF  = 1
TEST = 0

TEST_LABEL = 'TEST'
REF_LABEL  = 'REF.'

# Photometer models
TESSW = "TESS-W"
TESSP = "TESS-P"
TAS   = "TAS"


def label(role: int) -> str:
    return REF_LABEL.upper() if role == REF else TEST_LABEL.upper()

# By exclusive OR
def other(role: int) -> int:
    return 1 ^ role

def endpoint(role: int) -> str:
    env_var = 'REF_ENDPOINT' if role == REF else 'TEST_ENDPOINT'
    return decouple.config(env_var)

