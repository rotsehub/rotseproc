#!/usr/bin/env python

from __future__ import absolute_import, division, print_function

import sys,os,time,signal
import threading,string
import subprocess
import importlib
import yaml
import astropy.io.fits as fits
from rotseproc import rlogger
from rotseproc import heartbeat as HB
from rotseproc.merger import QAMerger
from rotseproc.pa import procalgs

def getobject(conf,log):
    rlog = rlogger.rotseLogger("ROTSE-III",20)
    log = rlog.getlog()
    log.debug("Running for {} {} {}".format(conf["ModuleName"],conf["ClassName"],conf))
    try:
        mod=__import__(conf["ModuleName"],fromlist=[conf["ClassName"]])
        klass=getattr(mod,conf["ClassName"])
        if "Name" in conf.keys():            
            return klass(conf["Name"],conf)
        else:
            return klass(conf["ClassName"],conf)
    except Exception as e:
        log.error("Failed to import {} from {}. Error was '{}'".format(conf["ClassName"],conf["ModuleName"],e))
        return None

def mapkeywords(kw,kwmap):
    """
    Maps the keyword in the configuration to the corresponding object
    e.g  Bias Image file is mapped to biasimage object... for the same keyword "BiasImage"
    """

    newmap={}
    for k,v in kw.items():
        if isinstance(v,str) and len(v)>=3 and  v[0:2]=="%%": #- For direct configuration
            if v[2:] in kwmap:
                newmap[k]=kwmap[v[2:]]
            else:
                log.warning("Can't find key {} in conversion map. Skipping".format(v[2:]))
        if k in kwmap: #- for configs generated via rotseproc.config
            newmap[k]=kwmap[k]          
        else:
            newmap[k]=v
    return newmap

def runpipeline(pl, convdict, conf):
    """
    Runs the rotse pipeline as configured

    Args:
        pl: is a list of [pa,qas] where pa is a pipeline step and qas the corresponding
            qas for that pa
        convdict: converted dictionary, details in setup_pipeline method below for examples.
        conf: a configured dictionary, read from the configuration yaml file.
            e.g: conf=configdict=yaml.safe_load(open('configfile.yaml','rb'))
    """

    rlog=rlogger.rotseLogger()
    log=rlog.getlog()
    hb=HB.Heartbeat(log,conf["Period"],conf["Timeout"])

    inp=None
    paconf=conf["Pipeline"]
    passqadict=None #- pass this dict to QAs downstream
    schemaMerger=QAMerger(convdict)
    QAresults=[] 
    import numpy as np
    qa=None
    qas=[[],['Count_Pixels'],[],[],[],[],[]]

    for s,step in enumerate(pl):
        log.info("Starting to run step {}".format(paconf[s]["StepName"]))
        pa=step[0]
        pargs=mapkeywords(step[0].config["kwargs"],convdict)
        schemaStep=schemaMerger.addPipelineStep(paconf[s]["StepName"])
        try:
            hb.start("Running {}".format(step[0].name))
            oldinp=inp #-  copy for QAs that need to see earlier input
            inp=pa(inp,**pargs)
        except Exception as e:
            log.critical("Failed to run PA {} error was {}".format(step[0].name,e),exc_info=True)
            sys.exit("Failed to run PA {}".format(step[0].name))
        qaresult={}
        for qa in step[1]:
            try:
                qargs=mapkeywords(qa.config["kwargs"],convdict)
                hb.start("Running {}".format(qa.name))
                qargs["dict_countbins"]=passqadict #- pass this to all QA downstream

                if isinstance(inp,tuple):
                    res=qa(inp[0],**qargs)
                else:
                    res=qa(inp,**qargs)

#                if "qafile" in qargs:
#                    qawriter.write_qa_file(qargs["qafile"],res)
                log.debug("{} {}".format(qa.name,inp))
                qaresult[qa.name]=res
                schemaStep.addParams(res['PARAMS'])
                schemaStep.addMetrics(res['METRICS'])
            except Exception as e:
                log.warning("Failed to run QA {}. Got Exception {}".format(qa.name,e),exc_info=True)
        hb.stop("Step {} finished.".format(paconf[s]["StepName"]))
        QAresults.append([pa.name,qaresult])
    hb.stop("Pipeline processing finished. Serializing result")


  #  # Merge QAs for this pipeline execution
  #  log.debug("Dumping mergedQAs")
  #  specprod_dir=os.environ['ROTSE_REDUX'] if 'ROTSE_REDUX' in os.environ else ""
  #  destFile=None
  #  schemaMerger.writeTojsonFile(destFile)
  #  log.info("Wrote merged QA file {}".format(destFile))
  #  if isinstance(inp,tuple):
  #     return inp[0]
  #  else:
  #     return inp

#- Setup pipeline from configuration

def setup_pipeline(config):
    """
    Given a configuration, this sets up a pipeline [pa,qa] and also returns a
    conversion dictionary from the configuration dictionary so that Pipeline steps (PA) can
    take them. This is required for runpipeline.
    """
    rlog=rlogger.rotseLogger()
    log=rlog.getlog()
    if config is None:
        return None
    log.debug("Reading Configuration")
    night=config["Night"]
    telescope=config["Telescope"]
    flavor=config["Flavor"]
    program=config["Program"]
    hbeat=HB.Heartbeat(log,config["Period"],config["Timeout"])
    if config["Timeout"] > 200.0:
        log.warning("Heartbeat timeout exceeding 200.0 seconds")
    dumpintermediates=False
    if "DumpIntermediates" in config:
        dumpintermediates=config["DumpIntermediates"]

    if "basePath" in config:
        basePath=config["basePath"]

    convdict={}

    if dumpintermediates:
        convdict["DumpIntermediates"]=dumpintermediates

    images=None
    pipeline=[]
    for step in config["Pipeline"]:
        pa=getobject(step["PA"],log)
        if len(pipeline) == 0:
            if not pa.is_compatible(type(images)):
                log.critical("Pipeline configuration is incorrect! check configuration {} {}".format(images,pa.is_compatible(images)))
                sys.exit("Wrong pipeline configuration")
        else:
            if not pa.is_compatible(pipeline[-1][0].get_output_type()):
                log.critical("Pipeline configuration is incorrect! check configuration")
                log.critical("Can't connect input of {} to output of {}. Incompatible types".format(pa.name,pipeline[-1][0].name))
                sys.exit("Wrong pipeline configuration")
        qas=[]
        for q in step["QAs"]:
            qa=getobject(q,log)
            if not qa.is_compatible(pa.get_output_type()):
                log.warning("QA {} can not be used for output of {}. Skipping expecting {} got {} {}".format(qa.name,pa.name,qa.__inpType__,pa.get_output_type(),qa.is_compatible(pa.get_output_type())))
            else:
                qas.append(qa)
        pipeline.append([pa,qas])
    return pipeline, convdict
