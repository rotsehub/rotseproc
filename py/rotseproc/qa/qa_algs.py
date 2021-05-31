""" 
Monitoring algorithms for the ROTSE-III pipeline
"""

import os, sys
import numpy as np
import datetime
import rotseproc.qa.qa_plots as plot
from astropy.io import fits
from rotseproc.io.qa import write_qa_file, write_qa_fig
from rotseproc.qa.qas import MonitoringAlg, QASeverity
from rotseproc import exceptions, rlogger
from astropy.time import Time
from rotseproc.qa import qalib

rlog = rlogger.rotseLogger("ROTSE-III",0)
log = rlog.getlog()

def get_inputs(*args,**kwargs):
    """
    Get inputs required for each QA
    """
    inputs={}

    if "paname" in kwargs: inputs["paname"] = kwargs["paname"]
    else: inputs["paname"] = None

    if "flavor" in kwargs: inputs["flavor"] = kwargs["flavor"]
    else: inputs["flavor"] = None

    if "program" in kwargs: inputs["program"] = kwargs["program"]
    else: inputs["program"] = None

    if "qafile" in kwargs: inputs["qafile"] = kwargs["qafile"]
    else: inputs["qafile"] = None

    if "qafig" in kwargs: inputs["qafig"] = kwargs["qafig"]
    else: inputs["qafig"] = None

    if "param" in kwargs: inputs["param"]=kwargs["param"]
    else: inputs["param"] = None

    if "refmetrics" in kwargs: inputs["refmetrics"] = kwargs["refmetrics"]
    else: inputs["refmetrics"] = None

    return inputs

class Count_Pixels(MonitoringAlg):
    def __init__(self, name, config, logger=None):
        if name is None or name.strip() == "":
            name="Count_Pixels"
        kwargs = config['kwargs']
        parms = kwargs['param']
        key = kwargs['refKey'] if 'refKey' in kwargs else "NOISE"
        status = kwargs['statKey'] if 'statKey' in kwargs else "NOISE_STATUS"
        kwargs["RESULTKEY"] = key
        kwargs["QASTATUSKEY"] = status
        if "ReferenceMetrics" in kwargs:
            r = kwargs["ReferenceMetrics"]
            if key in r:
                kwargs["REFERENCE"] = r[key]
        if "NOISE_WARN_RANGE" in parms and "NOISE_NORMAL_RANGE" in parms:
            kwargs["RANGES"] = [(np.asarray(parms["NOISE_WARN_RANGE"]),QASeverity.WARNING),
                               (np.asarray(parms["NOISE_NORMAL_RANGE"]),QASeverity.NORMAL)]
        im = fits.hdu.hdulist.HDUList
        MonitoringAlg.__init__(self, name, im, config, logger)
    def run(self, *args, **kwargs):
        if len(args) == 0 :
            log.critical("No parameter is found for this QA")
            sys.exit("Update the configuration file for the parameters")

        if not self.is_compatible(type(args[0])):
            log.critical("Incompatible input!")
            sys.exit("Was expecting {} got {}".format(type(self.__inpType__),type(args[0])))

        images = args[0]
        inputs = get_inputs(*args,**kwargs)

        return self.run_qa(images, inputs)

    def run_qa(self, images, inputs):
        # Get relevant inputs
        param = inputs['param']
        if param is None:
                log.critical("No parameter is found for this QA")
                sys.exit("Update the configuration file for the parameters")
        paname     = inputs['paname']
        program    = inputs['program']
        refmetrics = inputs['refmetrics']
        qafile     = inputs['qafile']
        qafig      = inputs['qafig']

        # Calculate average pixel value per image
        im_count = []
        for i in range(len(images)):
            pixdata = fits.open(images[i])[0].data
            pixmed = np.median(pixdata)
            im_count.append(pixmed)

        # Calculate average pixel value of all images
        count = np.median(im_count)

        # Set up output dictionary 
        retval = {}
        retval["PROGRAM"] = program
        retval["PANAME"]  = paname
        retval["PARAMS"]  = param
        retval["METRICS"] = {"COUNT" : str(count),
                             "COUNT_PER_IMAGE" : str(im_count)}

        # Write QA output files
        write_qa_file(qafile, retval)
        write_qa_fig(qafig, retval)

        return retval

    def get_default_config(self):
        return {}

