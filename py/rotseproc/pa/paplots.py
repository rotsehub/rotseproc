"""
Functions to make plots based on PA output
"""
from matplotlib import pyplot as plt

def plot_light_curve(mjd, mag, magerr, dumpfile):
    """
    Plot supernova light curve and output to pdf
    """
    # Generate light curve pdf
    fig = plt.figure()
    ax  = fig.add_subplot(111)
    ax  = plot_2d(ax, mjd, mag, "MJD", "ROTSE Magnitude", yerr=magerr)
    plt.gca().invert_yaxis()
    fig.savefig(dumpfile)

    return

