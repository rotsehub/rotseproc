"""
simple low level library functions for QAs
"""
import numpy as np
from astropy.io import fits

def count_avg_pixels(images):
    """
    Count pixels for each coadded image
    """
    # Calculate average pixel value per image
    im_count = []
    for i in range(len(images)):
        pixdata = fits.open(images[i])[0].data
        pixmed = np.median(pixdata)
        im_count.append(pixmed)

    return im_count

