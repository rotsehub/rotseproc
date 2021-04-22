"""
This includes routines to make plots based on QA output
"""

import numpy as np
from matplotlib import pyplot as plt

def plot_Get_RMS(qa_dict, outfile, plotconf=None, hardplots=False):
    """
    Plot metrics

    Args:
        qa_dict: dictionary of QA outputs from running qa_algs.Get_RMS
        outfile: name of figure
    """
    fig=plt.figure()

    if plotconf:
        hardplots = qaplot(fig, plotconf, qa_dict, outfile)

    if not hardplots:
        pass
    else:
        x_metric = [] # Get from qa_dict
        y_metric = []

        plt.suptitle("Example Plot")
        plt.plot(x_metric, y_metric)
        plt.tight_layout()
        fig.savefig(outfile)


