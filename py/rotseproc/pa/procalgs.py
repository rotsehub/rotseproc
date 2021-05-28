"""
ROTSE-III Pipeline Algorithms
"""
import os, sys
import glob
import numpy as np
from astropy.io import fits 
from rotseproc.pa import pas
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

        outdir=kwargs["outdir"]
        datadir=kwargs["datadir"]

        night = kwargs['Night']
        telescope = kwargs['Telescope']
        field = kwargs['Field']
        program = kwargs['Program']

        return self.run_pa(night, telescope, field, program, datadir, outdir)

    def run_pa(self, night, telescope, field, program, datadir, outdir):
        # Get data
        if program == 'supernova':
            from rotseproc.io.preproc import find_supernova_data, match_image_prod
            log.info("Finding supernova data for {} from {} to {}".format(field,night[0],night[1]))
            # Find supernova data
            allimages, allprods = find_supernova_data(night, telescope, field, datadir)
            # Remove image files without corresponding prod file
            images, prods = match_image_prod(allimages, allprods, field, telescope)
        else:
            log.critical("Program {} is not valid, can't find data...".format(program))
            sys.exit()

        # Copy preprocessed images to output directory
        from rotseproc.io.preproc import copy_preproc
        copy_preproc(outdir, images, prods)

        return


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

        outdir=kwargs["outdir"]

        return self.run_pa(outdir)

    def run_pa(self, outdir):
        # Setup IDL commands
        idl = "singularity run --bind /scratch /hpc/applications/idl/idl_8.0.simg"
        preprocdir = outdir + '/preproc/'
        imagedir = preprocdir + 'image/'
        files = "file_search('{}*')".format(imagedir)

        # Run coaddition
        os.chdir(preprocdir)
        os.system('{} -e "coadd_all,{}"'.format(idl,files))

        # Make coadd directories
        coadds = glob.glob('*000-000_c.fit')
        coadddir = outdir + '/coadd/'
        os.mkdir(coadddir)
        os.mkdir(coadddir + 'image')
        os.mkdir(coadddir + 'prod')

        # Move coadds to coadd directory
        coadds = glob.glob('*000-000_c.fit')
        for c in coadds:
            os.replace(c,os.path.join(coadddir,'image',c))

        return


class Source_Extraction(pas.PipelineAlg):
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

