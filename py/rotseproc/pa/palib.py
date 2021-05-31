"""
Low level functions to be from top level PAs
"""
import numpy as np
from rotseproc import exceptions, rlogger
rlog = rlogger.rotseLogger("ROTSE-III",20)
log = rlog.getlog()

def get_light_curve_data(lc_data_file):
    """
    Get mjd, mag, and magerr from light curve file
    """
    # Get data from light curve from file
    data   = np.loadtxt(lc_data_file, unpack=True)
    mjd    = data[0]
    mag    = data[2]
    magerr = mag - data[3]

    return mjd, mag, magerr

