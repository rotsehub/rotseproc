"""
Function for mapping output files to correct location
"""
import os

def findfile(filetype, outdir):
    """
    Find output files for PAs and QAs
    """
    # Set up dictionary for file locations
    filedict = {'lightcurve' : '{}/{}.pdf'}

    # Return file for specific filetype
    outfile = filedict[filetype].format(filetype, outdir)
    outfile = os.path.normpath(outfile)

    return outfile

