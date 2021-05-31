"""
Functions to make plots based on QA output
"""
import numpy as np
from matplotlib import pyplot as plt

def plot_Count_Pixels(outfile, im_count):
    """
    Plot metrics

    Args:
        qa_dict: dictionary of QA outputs from running qaalgs.Count_Pixels
        outfile: name of output figure figure
    """
    fig = plt.figure()

    xdata = np.arange(len(im_count))
    ydata = np.array(im_count)

    plt.suptitle("Average counts per coadded image")
    plt.xlabel("Image #")
    plt.ylabel("Average Pixel Count")
    plt.plot(xdata, ydata, '.')
    fig.savefig(outfile)

    return

