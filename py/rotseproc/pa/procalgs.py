"""
ROTSE-III Pipeline Algorithms
"""
import os, sys
import numpy as np
from astropy.io import fits 
from rotseproc import pas
from rotseproc import exceptions, rlogger

rlog = rlogger.rotseLogger("ROTSE-III",20)
log = rlog.getlog()

class Find_Data(pas.PipelineAlg):
    """
    This PA finds preprocessed images for each night
    """
    def __init__(self, name, config, logger=None):
        if name is None or name.strip() == "":
            name = "Find_Data"
        datatype = fits.hdu.hdulist.HDUList
        pas.PipelineAlg.__init__(self, name, datatype, datatype, config, logger)

    def run(self, *args, **kwargs):
        if len(args) == 0 :
            log.critical("Missing input parameter!")
            sys.exit()
        if not self.is_compatible(type(args[0])):
            log.critical("Incompatible input!")
            sys.exit("Was expecting {} got {}".format(type(self.__inpType__),type(args[0])))

        night = kwargs['Night']
        field = kwags['Field']
        telescope = kwargs['Telescope']

        return self.run_pa(night, field, telescope)

    def run_pa(self, night, field, telescope):
        # Find images
        images = []

        return images

class Coaddition(pas.PipelineAlg):
    """
    This PA coadds preprocessed images for each night
    """
    def __init__(self, name, config, logger=None):
        if name is None or name.strip() == "":
            name = "Coaddition"
        datatype = fits.hdu.hdulist.HDUList
        pas.PipelineAlg.__init__(self, name, datatype, datatype, config, logger)

    def run(self, *args, **kwargs):
        if len(args) == 0 :
            log.critical("Missing input parameter!")
            sys.exit()
        if not self.is_compatible(type(args[0])):
            log.critical("Incompatible input!")
            sys.exit("Was expecting {} got {}".format(type(self.__inpType__),type(args[0])))

        night = kwargs['Night']
        telescope = kwargs['Telescope']

        return self.run_pa(night, telescope)

    def run_pa(self, night, telescope):
        # Coadd files

        # Return coadds
        coadds = []

        return coadds


class Extract_Sources(pas.PipelineAlg):
    """
    This PA uses SExtractor to extract sources and return cobj files
    """
    def __init__(self, name, config, logger=None):
        if name is None or name.strip() == "":
            name="Extract_Sources"

        datatype = fits.hdu.hdulist.HDUList
        pas.PipelineAlg.__init__(self, name, datatype, datatype, config, logger)

    def run(self,*args,**kwargs):

        coadds = args[0]

        return self.run_pa(coadds)

    def run_pa(self, coadds):
        # Extract sources

        # Get cobj files
        cobj = []

        return cobj

class Make_Subimages(pas.PipelineAlg):
    """
    This PA makes subimages centered around transient
    """
    def __init__(self,name,config,logger=None):
        if name is None or name.strip() == "":
            name="Extract_Sources"

        datatype = fits.hdu.hdulist.HDUList
        pas.PipelineAlg.__init__(self, name, datatype, datatype, config, logger)

    def run(self,*args,**kwargs):

        coadds = args[0]

        return self.run_pa(coadds)

    def run_pa(self, coadds):
        # Define corrdinates and image size

        # Make subimages
        sub = []

        return sub

