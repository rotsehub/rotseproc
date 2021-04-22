""" 
Monitoring algorithms for the ROTSE-III pipeline
"""

import os, sys
import numpy as np
import datetime
import rotseproc.qa.qa_plots as plot
from astropy.io import fits
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
    else: inputs["paname"]=None

    if "flavor" in kwargs: inputs["flavor"] = kwargs["flavor"]
    else: inputs["flavor"]=None

    if "program" in kwargs: inputs["program"] = kwargs["program"]
    else: inputs["program"]=None

    if "qafile" in kwargs: inputs["qafile"] = kwargs["qafile"]
    else: inputs["qafile"]=None

    if "qafig" in kwargs: inputs["qafig"]=kwargs["qafig"]
    else: inputs["qafig"]=None

    if "param" in kwargs: inputs["param"]=kwargs["param"]
    else: inputs["param"]=None

    if "refmetrics" in kwargs: inputs["refmetrics"]=kwargs["refmetrics"]
    else: inputs["refmetrics"]=None

    return inputs

class Get_RMS(MonitoringAlg):
    def __init__(self, name, config, logger=None):
        if name is None or name.strip() == "":
            name="Get_RMS"
        kwargs=config['kwargs']
        parms=kwargs['param']
        key=kwargs['refKey'] if 'refKey' in kwargs else "NOISE"
        status=kwargs['statKey'] if 'statKey' in kwargs else "NOISE_STATUS"
        kwargs["RESULTKEY"]=key
        kwargs["QASTATUSKEY"]=status
        if "ReferenceMetrics" in kwargs:
            r=kwargs["ReferenceMetrics"]
            if key in r:
                kwargs["REFERENCE"]=r[key]
        if "NOISE_WARN_RANGE" in parms and "NOISE_NORMAL_RANGE" in parms:
            kwargs["RANGES"]=[(np.asarray(parms["NOISE_WARN_RANGE"]),QASeverity.WARNING),
                              (np.asarray(parms["NOISE_NORMAL_RANGE"]),QASeverity.NORMAL)]
        im = fits.hdu.hdulist.HDUList
        MonitoringAlg.__init__(self,name,im,config,logger)
    def run(self, *args, **kwargs):
        if len(args) == 0 :
            log.critical("No parameter is found for this QA")
            sys.exit("Update the configuration file for the parameters")

        if not self.is_compatible(type(args[0])):
            log.critical("Incompatible input!")
            sys.exit("Was expecting {} got {}".format(type(self.__inpType__),type(args[0])))

        image = args[0]
        inputs = get_inputs(*args,**kwargs)

        return self.run_qa(image, inputs)

    def run_qa(self, image, inputs):
        paname = inputs['paname']
        flavor = inputs['flavor']
        program = inputs['program']
        param = inputs['param']
        refmetrics = inputs['refmetrics']
        
        #- QA dictionary 
        retval = {}
        retval["PANAME"] = paname
        retval["FLAVOR"] = flavor
        retval["PROGRAM"] = program
        retval["QATIME"] = datetime.datetime.now().isoformat()
        kwargs = self.config['kwargs']

        if param is None:
                log.critical("No parameter is found for this QA")
                sys.exit("Update the configuration file for the parameters")

        # Calculate noise
        noise = 0.

        retval["METRICS"] = {"NOISE":noise}
        retval["PARAMS"] = param

        return retval

    def get_default_config(self):
        return {}

