# ----------------------------------------------------------------------
# Copyright (c) 2024 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import datetime

def chop(string, sep=None):
    '''Chop a list of strings, separated by sep and 
    strips individual string items from leading and trailing blanks'''
    chopped = tuple(elem.strip() for elem in string.split(sep) )
    if len(chopped) == 1 and chopped[0] == '':
    	chopped = tuple()
    return chopped

def measurements_session_id() -> int:
	'''returns a unique session Id for meassurements'''
	return datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')
