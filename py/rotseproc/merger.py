"""
Merge rotse qa outputs

Only a few necessary functions included here, need to expand
"""
from __future__ import absolute_import, division, print_function
import yaml
import json
import numpy as np
import datetime
import pytz

def remove_task(myDict, Key):
    if Key in myDict:
        del myDict[Key]
    return myDict

def rename_task(myDict, oldKey, newKey):
    
    if oldKey in myDict:
        
        task_data = myDict[oldKey]
        del myDict[oldKey] 
        myDict[newKey] = task_data
        
    return myDict

def transferKEY(myDict, KeyHead, old_task, new_task, keyList):
    
    if old_task in myDict and new_task in myDict:
        for key in keyList:
            if key in myDict[old_task][KeyHead]:
                data = myDict[old_task][KeyHead][key]
                del myDict[old_task][KeyHead][key]
                myDict[new_task][KeyHead][key] = data
    
    return myDict

class QAMerger:
    def __init__(self, convdict):
        self.__stepsArr=[]
        self.__schema={'PIPELINE_STEPS':self.__stepsArr}

    class Rotse_Step:
        def __init__(self,paName,paramsDict,metricsDict):
            self.__paName=paName
            self.__pDict=paramsDict
            self.__mDict=metricsDict
        def getStepName(self):
            return self.__paName
        def addParams(self,pdict):
            self.__pDict.update(pdict)
        def addMetrics(self,mdict):
            self.__mDict.update(mdict)
    def addPipelineStep(self,stepName):
        metricsDict={}
        paramsDict={}
        stepDict={"PIPELINE_STEP":stepName.upper(),'METRICS':metricsDict,'PARAMS':paramsDict}
        self.__stepsArr.append(stepDict)
        return self.Rotse_Step(stepName,paramsDict,metricsDict)

