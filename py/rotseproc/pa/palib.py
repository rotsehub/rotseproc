"""
rotseproc.palib
Low level functions to be from top level PAs
"""
import os
import numpy as np
from rotseproc import exceptions, rlogger
rlog = rlogger.rotseLogger("ROTSE-III",20)
log = rlog.getlog()

def get_light_curve_data(lcfile):
    """
    Get mjd, mag, and magerr from light curve file
    """
    

    return mjd, mag, magerr

