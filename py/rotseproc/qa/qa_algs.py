""" 
Monitoring algorithms for the ROTSE-III pipeline
"""

import os, sys
import numpy as np
import datetime
import rotseproc.qa.qa_plots as plot
from astropy.io.fits import fits
from rotseproc.qas import MonitoringAlg, QASeverity
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

    if "qafile" in kwargs: inputs["qafile"] = kwargs["qafile"]
    else: inputs["qafile"]=None

    if "qafig" in kwargs: inputs["qafig"]=kwargs["qafig"]
    else: inputs["qafig"]=None

    inputs['night']=kwargs['Night']
    inputs['field']=kwargs['Field']
    inputs['telescope']=kwargs['Telescope']

    return inputs

class Example_QA(MonitoringAlg):
    def __init__(self, name, config, logger=None):
        if name is None or name.strip() == "":
            name="METRIC"
        kwargs=config['kwargs']
        parms=kwargs['param']
        key=kwargs['refKey'] if 'refKey' in kwargs else "METRIC"
        status=kwargs['statKey'] if 'statKey' in kwargs else "METRIC_STATUS"
        kwargs["RESULTKEY"]=key
        kwargs["QASTATUSKEY"]=status
        if "ReferenceMetrics" in kwargs:
            r=kwargs["ReferenceMetrics"]
            if key in r:
                kwargs["REFERENCE"]=r[key]
        if "METRIC_WARN_RANGE" in parms and "METRIC_NORMAL_RANGE" in parms:
            kwargs["RANGES"]=[(np.asarray(parms["METRIC_WARN_RANGE"]),QASeverity.WARNING),
                              (np.asarray(parms["METRIC_NORMAL_RANGE"]),QASeverity.NORMAL)]
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
        night = inputs['night']
        telescope = inputs['telescope']
        qafile = inputs['qafile']
        qafig = inputs['qafig']
        param = inputs['param']
        refmetrics = inputs['refmetrics']
        
        #- QA dictionary 
        retval = {}
        retval["PANAME" ] = paname
        retval["QATIME"] = datetime.datetime.now().isoformat()
        kwargs = self.config['kwargs']
        retval["NIGHT"] = night = image.meta["NIGHT"]

        if param is None:
                log.critical("No parameter is found for this QA")
                sys.exit("Update the configuration file for the parameters")

        # Calculate metrics
        metric = []

        retval["METRICS"] = {"METRIC":metric}
        retval["PARAMS"] = param

        return retval

    def get_default_config(self):
        return {}

