import os, sys
import json
import yaml
import numpy as np
from rotseproc.io.findfile import findfile
from rotseproc import exceptions, rlogger

class Config(object):
    """ 
    A class to generate ROTSE configurations for a given exposure. 
    expand_config will expand out to full format as needed by rotse.setup
    """
    def __init__(self, configfile, night, telescope, field, ra, dec, datadir=None, outdir=None, tempdir=None, plots=False):
        """
        configfile : ROTSE-III configuration file (e.g. rotseproc/config/config_science.yaml)
        night      : night for the data to process (e.g. 20130101)
        telescope  : instrument to process (e.g. 3b)
        field      : observed field on the sky (e.g. sks0246+3652)
        ra         : target RA
        dec        : target DEC
        datadir    : directory containing data
        outdir     : output directory
        """
        rlog = rlogger.rotseLogger(name="RotseConfig")
        self.log = rlog.getlog()

        with open(configfile, 'r') as f:
            self.conf = yaml.safe_load(f)
            f.close()

        self.program   = self.conf["Program"]
        self.log.info("Expanding configuration for {} program".format(self.program))

        self.night     = night
        self.telescope = telescope
        self.field     = field
        self.datadir   = datadir 
        self.outdir    = outdir
        self.flavor    = self.conf["Flavor"]
        self.datadir   = datadir
        self.outdir    = outdir
        self.tempdir   = tempdir

        # Convert RA and DEC to floating point numbers
        if ra is None:
            self.ra = ra
            self.dec = dec
        elif ':' in ra:
            ra_split = ra.split(':')
            dec_split = dec.split(':')
    
            self.ra = float(ra_split[0])*15. + float(ra_split[1])/4. + float(ra_split[2])/240.
    
            if float(dec_split[0]) >= 0.:
                self.dec = float(dec_split[0]) + float(dec_split[1])/60. + float(dec_split[2])/3600.
            else:
                self.dec = float(dec_split[0]) - float(dec_split[1])/60. - float(dec_split[2])/3600.
        elif float(ra) > 0. and float(ra) < 360.:
            self.ra = float(ra)
            self.dec = float(dec)
        else:
            self.log.warning("RA and DEC are not in the right format, this could cause downstream issues.")

        self.plotconf = None
        self.hardplots = False
        #- Load plotting configuration file
        if plots != 'noplots' and plots is not None:
            with open(plots, 'r') as pf:
                self.plotconf = yaml.safe_load(pf)
                pf.close()
        #- Use hard coded plotting algorithms
        elif plots is None:
            self.hardplots = True

        self.pipeline   = self.conf["Pipeline"]
        self.algorithms = self.conf["Algorithms"]
        self._palist    = Palist(self.pipeline,self.algorithms)
        self.pamodule   = self._palist.pamodule
        self.qamodule   = self._palist.qamodule
        
        algokeys = self.algorithms.keys()

        # Extract mapping of scalar/refence key names for each QA
        qaRefKeys = {}
        for i in algokeys: 
            for k in self.algorithms[i]["QA"].keys():
                qaparams=self.algorithms[i]["QA"][k]["PARAMS"]
                for par in qaparams.keys():
                    if "NORMAL_RANGE" in par:
                        scalar = par.replace("_NORMAL_RANGE","")
                        qaRefKeys[k] = scalar

        # Get pixel radius for subimages
        self.pixrad = None
        if "Make_Subimages" in self.algorithms.keys():
            self.pixrad = self.algorithms["Make_Subimages"]["PixelRadius"]

        self._qaRefKeys = qaRefKeys

    @property
    def palist(self): 
        """ palist for this config
            see :class: `Palist` for details.
        """
        return self._palist.palist

    @property
    def qalist(self):
        """ qalist for the given palist
        """
        return self._palist.qalist

    @property
    def paargs(self):
        """
        Many arguments for the PAs are taken default. Some of these may need to be variable
        """
        paopt_find     = {'Night':self.night, 'Telescope':self.telescope, 'Field':self.field, 'RA':self.ra,
                          'DEC':self.dec, 'Program':self.program, 'datadir':self.datadir, 'outdir':self.outdir}
        paopt_coadd    = {'outdir':self.outdir}
        paopt_extract  = {'outdir':self.outdir}
        paopt_subimage = {'Program':self.program, 'Field':self.field, 'Telescope':self.telescope, 'RA':self.ra,
                          'DEC':self.dec, 'PixelRadius':self.pixrad, 'outdir':self.outdir, 'tempdir':self.tempdir}
        paopt_imdiff   = {'outdir':self.outdir}
        paopt_refstars = {'RA':self.ra, 'DEC':self.dec, 'outdir':self.outdir}
        paopt_phot     = {'outdir':self.outdir, 'dumpfile':self.dump_pa('Photometry')}

        paopts={}
        defList={'Find_Data'          : paopt_find,
                 'Coaddition'         : paopt_coadd,
                 'Source_Extraction'  : paopt_extract,
                 'Make_Subimages'     : paopt_subimage,
                 'Image_Differencing' : paopt_imdiff,
                 'Choose_Refstars'    : paopt_refstars,
                 'Photometry'         : paopt_phot
                }

        def getPAConfigFromFile(PA,algs):
            def mergeDicts(source,dest):
                for k in source:
                    if k not in dest:
                        dest[k]=source[k]
            userconfig={}
            if PA in algs:
                fc=algs[PA]
                for k in fc: #do a deep copy leave QA config out
                    if k != "QA":
                        userconfig[k]=fc[k]
            defconfig={}
            if PA in defList:
                defconfig=defList[PA]
            mergeDicts(defconfig,userconfig)
            return userconfig

        for PA in self.palist:
            paopts[PA]=getPAConfigFromFile(PA,self.algorithms)
        #- Ignore intermediate dumping and write explicitly the outputfile for 
        # Ignore PA outputs for now
        self.outputfile=self.dump_pa(self.palist[-1]) 

        return paopts 
        
    def dump_pa(self,paname):
        """
        dump the PA outputs to respective files
        """
        pafilemap = {'Photometry': 'lightcurve'}
        if paname in pafilemap:
            filetype = pafilemap[paname]
        else:
            raise IOError("PA name does not match any file type. Check PA name in config file.") 

        pafile = findfile(filetype, self.outdir)

        return pafile

    def dump_qa(self): 
        """ 
        yaml outputfile for the set of qas for a given pa
        Need to define name and default locations of files
        """
        #- QA level outputs
        #qa_outfile = {}
        qa_outfig = {}
        for PA in self.palist:
            for QA in self.qalist[PA]:
                #qa_outfile[QA] = self.io_qa(QA)[0]
                qa_outfig[QA] = self.io_qa(QA)[1]
                
                #- make path if needed
                path = os.path.normpath(os.path.dirname(qa_outfig[QA]))
                if not os.path.exists(path):
                    os.makedirs(path)

        return (qa_outfig)
#        return ((qa_outfile,qa_outfig),(qa_pa_outfile,qa_pa_outfig))

    @property
    def qaargs(self):
        qaopts = {}
        referencemetrics=[]        
        for PA in self.palist:
            for qa in self.qalist[PA]: #- individual QA for that PA
                pa_yaml = PA.upper()
                params=self._qaparams(qa)
                qaopts[qa]={'night':self.night, 'telescope':self.telescope, 'flavor':self.flavor, 'program':self.program, 'param':params}

                if self.reference != None:
                    refkey=qaopts[qa]['refKey']
                    for padict in range(len(self.reference)):
                        pa_metrics=self.reference[padict].keys()
                        if refkey in pa_metrics:
                            qaopts[qa]['ReferenceMetrics']={'{}'.format(refkey): self.reference[padict][refkey]}
        return qaopts

    def _qaparams(self,qa):
        params={}
        if self.algorithms is not None:
            for PA in self.palist:
                if qa in self.qalist[PA]:
                    params[qa]=self.algorithms[PA]['QA'][qa]['PARAMS']
        else:
            # Need to settle optimal error handling in cases like this.
            raise exceptions.ParameterException("Run time PARAMs not provided for QA")

        return params[qa]

    def io_qa_pa(self,paname):
        """
        Specify the filenames: the pa level qa files"
        """
        filemap={'Find_Data'         : 'images',
                 'Coaddition'        : 'coadd',
                 'Source_Extraction' : 'extract',
                 'Make_Subimages'    : 'subimage'
                 }

        if paname in filemap:
            outfile = findfile() # Update when needed
            outfig = findfile()
        else:
            raise IOError("PA name does not match any file type. Check PA name in config for {}".format(paname))

        return (outfile, outfig)


    def io_qa(self,qaname):
        """
        Specify the filenames: files for the given qa output
        """
        filemap={'Get_RMS': 'getrms'
                 }

        if qaname in filemap:
            outfile = [] # Need findfile function
            outfig = []
        else:
            raise IOError("QA name does not match any file type. Check QA name in config for {}".format(qaname))

        return (outfile, outfig)

    def expand_config(self):
        """
        config: rotseproc.config.Config object
        """
        self.log.debug("Building Full Configuration")
        self.period = self.conf["Period"]
        self.timeout = self.conf["Timeout"]

        #- Get reference metrics from template json file
        self.reference=None

        outconfig={}
        outconfig['Night']     = self.night
        outconfig['Field']     = self.field
        outconfig['Telescope'] = self.telescope
        outconfig['Flavor']    = self.flavor
        outconfig['Program']   = self.program
        outconfig['Period']    = self.period

        pipeline = []
        for ii,PA in enumerate(self.palist):
            pipe={}
            pipe['PA'] = {'ClassName': PA, 'ModuleName': self.pamodule, 'kwargs': self.paargs[PA]}
            pipe['QAs']=[]
            for jj, QA in enumerate(self.qalist[PA]):
                pipe_qa={'ClassName': QA, 'ModuleName': self.qamodule, 'kwargs': self.qaargs[QA]}
                pipe['QAs'].append(pipe_qa)
            pipe['StepName']=PA
            pipeline.append(pipe)

        outconfig['Pipeline']   = pipeline
        outconfig['Timeout']    = self.timeout
        outconfig['PlotConfig'] = self.plotconf

        #- Check if all the files exist for this configuraion
       # check_config(outconfig)
        return outconfig

def check_config(outconfig):
    """
    Given the expanded config, check for all possible file existence etc...
    """
    self.log.info("Checking if all the necessary files exist.")

    # Perform necessary checks

    log.info("All necessary files exist for {} configuration.".format(outconfig["Flavor"]))

    return 

class Palist(object):
    """
    Generate PA list and QA list for the given exposure
    """
    def __init__(self,thislist=None,algorithms=None):
        """
        thislist: given list of PAs
        algorithms: Algorithm list coming from config file: e.g rotseproc/config/config_science.yaml
        flavor: only needed if new list is to be built.
        """
        self.thislist=thislist
        self.algorithms=algorithms
        self.palist=self._palist()
        self.qalist=self._qalist()

    def _palist(self):
        palist=self.thislist
        self.pamodule='rotseproc.pa.procalgs'
        return palist       

    def _qalist(self):
        qalist={}
        for PA in self.thislist:
            qalist[PA]=self.algorithms[PA]['QA'].keys()
        self.qamodule='rotseproc.qa.qa_algs'
        return qalist

