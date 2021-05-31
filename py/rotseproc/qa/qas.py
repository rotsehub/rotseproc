import collections
import numpy as np
from rotseproc import rlogger 
from rotseproc import exceptions
from enum import Enum
from astropy.io import fits

def check_QA_status(metric, reference, norm_range, warn_range):
    """
    Compare QA metric to reference value and return status
    """
    # Calculate difference between reference value and metric
    diff = reference - metric

    # Check QA status
    if diff >= norm_range[0] and diff <= norm_range[1]:
        status = 'NORMAL'
    elif diff >= warn_range[0] and diff <= warn_range[1]:
        status = 'WARNING'
    else:
        status = 'ALARM'

    return status

class QASeverity(Enum):
    ALARM=30
    WARNING=20
    NORMAL=0

class MonitoringAlg:
    """ Simple base class for monitoring algorithms """
    def __init__(self,name,inptype,config,logger=None):
        if logger is None:
            self.m_log=rlogger.rotseLogger().getlog(name)
        else:
            self.m_log=logger
        self.__inpType__=type(inptype)
        self.name=name
        self.config=config
        self.__deviation = None
        self.m_log.debug("initializing Monitoring alg {}".format(name))

    def __call__(self,*args,**kwargs):
        res=self.run(*args,**kwargs)
        cargs=self.config['kwargs']
        params=cargs['param']

        metrics=res["METRICS"] if 'METRICS' in res else None
        if metrics is None:
            metrics={}
            res["METRICS"]=metrics

        reskey="RESULT"
        QARESULTKEY="QA_STATUS"
        REFNAME = cargs["RESULTKEY"]+'_REF'

        NORM_range = cargs["RESULTKEY"]+'_NORMAL_RANGE'
        WARN_range = cargs["RESULTKEY"]+'_WARN_RANGE'
        norm_range_val = [0,0]
        warn_range_val = [0,0]

        if "QASTATUSKEY" in cargs: 
            QARESULTKEY=cargs["QASTATUSKEY"]
        if "RESULTKEY" in cargs:
            reskey=cargs["RESULTKEY"]

        if cargs["RESULTKEY"] == 'CHECKHDUS':
             stats=[]    
             stats.append(metrics['CHECKHDUS_STATUS'])
             stats.append(metrics['EXPNUM_STATUS'])
             if  np.isin(stats,'NORMAL').all():
                    metrics[QARESULTKEY]='NORMAL'
             elif np.isin(stats,'ALARM').any():  
                    metrics[QARESULTKEY] = 'ALARM'

             self.m_log.info("{}: {}".format(QARESULTKEY,metrics[QARESULTKEY])) 

        if reskey in metrics:
            current = metrics[reskey]


            if REFNAME in params:  # Get the REF value/ranges from params

                refval=params[REFNAME]

                if len(refval) == 1:
                    refval = refval[0]

                refval = np.asarray(refval)
                current = np.asarray(current)
                norm_range_val=params[NORM_range]
                warn_range_val=params[WARN_range]

                # Just in case any nan value sneaks in the array of the scalar metrics
                ind = np.argwhere(np.isnan(current))

                if (ind.shape[0] > 0 and refval.shape[0] == current.shape[0]):
                   self.m_log.critical("{} : elements({}) of the result are returned as NaN! STATUS is determined for the real values".format(self.name,str(ind)))
                   
                   ind = list(np.hstack(ind))
                   for index in sorted(ind, reverse=True):
                       del current[index]
                       del refval[index]
 
            else: 
                self.m_log.warning("No reference given. Update the configuration file to include reference value for QA: {}".format(self.name))

            currlist=isinstance(current,(np.ndarray,collections.Sequence))
            reflist=isinstance(refval,(np.ndarray,collections.Sequence))

            if currlist != reflist:
                self.m_log.critical("{} : REFERENCE({}) and RESULT({}) are of different types!".format(self.name,type(refval),type(current)))
            elif currlist: 

                if refval.size == current.size and current.size >1:

                    self.__deviation=[c-r for c,r in zip(np.sort(current),np.sort(refval))]
                elif refval.size == current.size and current.size and current.size == 1:
                    self.__deviation =  current - refval
                elif np.size(current) == 0 or np.size(refval) == 0:
                    self.m_log.warning("No measurement is done or no reference is available for this QA!- check the configuration file for references!")
                    metrics[QARESULTKEY]='UNKNOWN'
                    self.m_log.info("{}: {}".format(QARESULTKEY,metrics[QARESULTKEY])) 
                elif refval.size != current.size:
                    self.m_log.critical("{} : REFERENCE({}) and RESULT({}) are of different length!".format(self.name,refval.size,current.size))
                    metrics[QARESULTKEY]='UNKNOWN'
                    self.m_log.info("{}: {}".format(QARESULTKEY,metrics[QARESULTKEY]))   

            else: 
                # "sorting" eliminate the chance of randomly shuffling items in the list that we observed in the past
                self.__deviation=(np.sort(current)-np.sort(refval))/np.sort(current)

        def findThr(d,t):
            if d != None and len(list(t)) >1:
               val=QASeverity.ALARM
               for l in list(t):

                 if d>=l[0][0] and d<l[0][1]:
                    val=l[1]
            else:
                 if d>=l and d<l:
                    val=l
            return val

        devlist = self.__deviation
        thr = norm_range_val
        wthr = warn_range_val

        if devlist is None:
            pass
        # Temporarily here until we know OBJLIST is ['SCIENCE', 'STD'] or anything else----------- line below should only be "elif len(thr)==2 and len(wthr)==2:"

        # If one fit fails SNR but the rest pass, return normal
        elif (cargs["RESULTKEY"] == 'FIDSNR_TGT'):
            devlist = current
            stats = []
            nofit = np.where(devlist==0.0)[0]
            if len(nofit) >= 2:
                stats.append('ALARM')
            else:
                for i,val in enumerate(devlist):
                    if len(nofit) != 0 and i == nofit[0]:
                        stats.append('NORMAL')
                    else:
                        diff = refval[i] - val
                        if thr[0]<= diff <= thr[1]:
                            stats.append('NORMAL')
                        elif wthr[0] <= diff <= wthr[1]:
                            stats.append('WARNING')
                        else:
                            stats.append('ALARM')

            if  np.isin(stats,'NORMAL').all():
                metrics[QARESULTKEY]='NORMAL'
            elif np.isin(stats,'WARNING').any() and np.isin(stats,'ALARM').any():
                metrics[QARESULTKEY] = 'ALARM'
            elif np.isin(stats,'ALARM').any():
                metrics[QARESULTKEY] = 'ALARM'
            elif np.isin(stats,'WARNING').any():
                metrics[QARESULTKEY] = 'WARNING'

            self.m_log.info("{}: {}".format(QARESULTKEY,metrics[QARESULTKEY]))

        elif  (len(thr)==2 and len(wthr)==2):

                    if np.size(devlist)== 1:
                        d=[]
                        d.append(devlist)
                        devlist = d
                    stats = []   
                    for val in devlist:
                      if thr[0] <= val <= thr[1]:
                        stats.append('NORMAL')
                      elif wthr[0] <= val <= wthr[1]:
                          stats.append('WARNING')
                      else:
                          stats.append('ALARM')

                    if  np.isin(stats,'NORMAL').all():
                        metrics[QARESULTKEY]='NORMAL'
                    elif np.isin(stats,'WARNING').any() and np.isin(stats,'ALARM').any():
                        metrics[QARESULTKEY] = 'ALARM'
                    elif np.isin(stats,'ALARM').any():
                        metrics[QARESULTKEY] = 'ALARM'
                    elif np.isin(stats,'WARNING').any():  
                        metrics[QARESULTKEY] = 'WARNING'
                    self.m_log.info("{}: {}".format(QARESULTKEY,metrics[QARESULTKEY]))   

        return res

    def run(self,*argv,**kwargs):
        pass
    def is_compatible(self,Type):
        return isinstance(Type,self.__inpType__)
    def check_reference():
        return self.__deviation
    def get_default_config(self):
        return None
