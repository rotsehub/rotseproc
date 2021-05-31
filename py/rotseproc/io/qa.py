"""
I/O functions for QAs
"""
import os
import json

def write_qa_file(filename, retval):
    """
    Write JSON file for QA
    """
    outfile = open(filename, 'w')
    json.dump(retval, outfile, sort_keys=True, indent=4)

    return

def write_qa_fig(filename, retval):
    """
    Write PDF file for QA
    """

    return

