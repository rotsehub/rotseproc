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

        night = kwargs['Night']
        if night is None:
            log.critical("Must provide night as a command line argument!")
            sys.exit("The Find_Data PA requires nights to find data...")

        program   = kwargs['Program']
        telescope = kwargs['Telescope']
        field     = kwargs['Field']
        ra        = kwargs['RA']
        dec       = kwargs['DEC']
        outdir    = kwargs['outdir']
        datadir   = kwargs['datadir']

        return self.run_pa(night, telescope, field, ra, dec, program, datadir, outdir)

    def run_pa(self, night, telescope, field, ra, dec, program, datadir, outdir):
        # Get data
        if program == 'supernova':
            from rotseproc.io.supernova import find_supernova_field, find_supernova_data
            from rotseproc.io.preproc import match_image_prod
            log.info("Finding supernova data from {} to {}".format(night[0],night[1]))

            # Find supernova data
            if field is None:
                if ra is None or dec is None:
                    log.critical("Must provide either the supernova field or coordinates!")
                else:
                    field = find_supernova_field(ra, dec)
                if field is None:
                    log.critical("No supernova fields contain data for these coordinates.")

            allimages, allprods, field = find_supernova_data(night, telescope, field, datadir)

            # Remove image files without corresponding prod file
            images, prods = match_image_prod(allimages, allprods, telescope, field)

        else:
            log.critical("Program {} is not valid, can't find data...".format(program))
            sys.exit()

        # Copy preprocessed images to output directory
        from rotseproc.io.preproc import copy_preproc
        copy_preproc(images, prods, outdir)

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

        outdir = kwargs['outdir']

        return self.run_pa(outdir)

    def run_pa(self, outdir):
        # Set up IDL commands
        idl = "singularity run --bind /scratch /hpc/applications/idl/idl_8.0.simg"
        preprocdir = outdir + '/preproc/'
        imagedir = preprocdir + 'image/'
        files = "file_search('{}*')".format(imagedir)

        # Run coaddition
        os.chdir(preprocdir)
        os.system('{} -32 -e "coadd_all,{}"'.format(idl,files))

        # Make coadd directories
        coadds = glob.glob('*000-000_c.fit')
        coadddir = outdir + '/coadd/'
        os.mkdir(coadddir)
        os.mkdir(coadddir + 'image')
        os.mkdir(coadddir + 'prod')

        # Move coadds to coadd directory
        coadds = glob.glob('*000-000_c.fit')
        for c in coadds:
            os.replace(c, os.path.join(coadddir, 'image', c))

        return


class Source_Extraction(pas.PipelineAlg):
    """
    This PA uses SExtractor to extract sources (to do: return cobj files)
    """
    def __init__(self, name, config, logger=None):
        if name is None or name.strip() == "":
            name="Source_Extraction"

        datatype = fits.hdu.hdulist.HDUList
        pas.PipelineAlg.__init__(self, name, datatype, datatype, config, logger)

    def run(self,*args,**kwargs):
        if len(args) == 0 :
            log.critical("Missing input parameter!")
            sys.exit()
        if not self.is_compatible(type(args[0])):
            log.critical("Incompatible input!")
            sys.exit("Was expecting {} got {}".format(type(self.__inpType__),type(args[0])))

        outdir = kwargs['outdir']

        return self.run_pa(outdir)

    def run_pa(self, outdir):
        # Set up sextractor environment
        extract_par = '/scratch/group/astro/rotse/software/products/idltools/umrotse_idl/tools/sex/'
        extract_config = '/scratch/group/astro/rotse/software/products/idltools/umrotse_idl/tools/sex/'

        # Run sextractor on each coadded image
        coadddir = outdir + '/coadd'
        coadds = os.listdir(coadddir+'/image')
        n_files = len(coadds)
        for i in range(n_files):
            # Set up output files
            conf = {'sobjdir':'', 'root':'', 'cimg':'', 'sobj':'', 'cobj':''}
            conf['sobjdir'] = coadddir+'/prod/'
            basename = coadds[i].split('000-000')[0]
            coaddname = basename + '000-000'
            conf['root'] = coaddname
            conf['cimg'] = coadddir + '/image/' + coaddname + '_c.fit'
            conf['sobj'] = coadddir + '/prod/' + coaddname + '_sobj.fit'
            conf['cobj'] = coadddir + '/prod/' + coaddname + '_cobj.fit'
            skyname = coadddir + '/prod/' + coaddname + '_sky.fit'

            # Get saturation level
            chdr = fits.open(conf['cimg'])[0].header
            satlevel = str(chdr['SATCNTS'])

            # Run sextractor
            cmd = 'sex ' + conf['cimg'] + ' -c ' + extract_par + '/rotse3.sex -PARAMETERS_NAME ' + extract_par + '/rotse3.par -FILTER_NAME ' + extract_config + '/gauss_2.0_5x5.conv -PHOT_APERTURES 7 -SATUR_LEVEL ' + satlevel + ' -CATALOG_NAME ' + conf['sobj'] + ' -CHECKIMAGE_NAME ' + skyname
            os.system(cmd)

            # Calibrate sobj file
           # idl = "singularity run --bind /scratch /hpc/applications/idl/idl_8.0.simg"
           # os.chdir(coadddir)
           # os.system('{} -32 -e "run_cal,{}"'.format(idl,[coadds[i]]))

        return


class Make_Subimages(pas.PipelineAlg):
    """
    This PA makes subimages centered around transient
    """
    def __init__(self,name,config,logger=None):
        if name is None or name.strip() == "":
            name="Make_Subimages"

        datatype = fits.hdu.hdulist.HDUList
        pas.PipelineAlg.__init__(self, name, datatype, datatype, config, logger)

    def run(self,*args,**kwargs):
        if len(args) == 0 :
            log.critical("Missing input parameter!")
            sys.exit()
        if not self.is_compatible(type(args[0])):
            log.critical("Incompatible input!")
            sys.exit("Was expecting {} got {}".format(type(self.__inpType__),type(args[0])))

        program   = kwargs['Program']
        telescope = kwargs['Telescope']
        field     = kwargs['Field']
        ra        = kwargs['RA']
        dec       = kwargs['DEC']
        pixrad    = kwargs['PixelRadius']
        outdir    = kwargs['outdir']
        tempdir   = kwargs['tempdir']

        return self.run_pa(program, telescope, field, ra, dec, pixrad, outdir, tempdir)

    def run_pa(self, program, telescope, field, ra, dec, pixrad, outdir, tempdir):
        # If running on a supernova, find template file
        if program == 'supernova':
            from shutil import copyfile

            coadddir = outdir + '/coadd/'
            refdir = os.path.join(tempdir, telescope, 'reference')
            imdir = os.path.join(refdir, 'image')
            proddir = os.path.join(refdir, 'prod')

            # Find field if not provided
            if field is None:
                ims = os.listdir(coadddir+'image')
                field = ims[0][7:19]

            try:
                imfile = glob.glob(imdir+'/*{}*'.format(field))[0]
                im = os.path.split(imfile)[1]
                imout = os.path.join(coadddir, 'image', im)
                copyfile(imfile, imout)
    
                prodfile = glob.glob(proddir+'/*{}*'.format(field))[0]
                prod = os.path.split(prodfile)[1]
                prodout = os.path.join(coadddir, 'prod', prod)
                copyfile(prodfile, prodout)
    
                log.info("Found reference image {}".format(im))

            except:
                raise exceptions.ReferenceException("No reference image for {}".format(field))

        # Make subimages
        idl = "singularity run --bind /scratch /hpc/applications/idl/idl_8.0.simg"
        files = os.listdir(coadddir+'/image')
        os.chdir(coadddir)
        os.system('{} -32 -e "make_rotse3_subimage,{},racent={},deccent={},pixrad={}"'.format(idl, files, ra, dec, pixrad))

        # Move subimages to sub directory
        subdir = os.path.join(outdir, 'sub')
        os.mkdir(subdir)
        os.mkdir(os.path.join(subdir, 'image'))
        os.mkdir(os.path.join(subdir, 'prod'))

        images = glob.glob('*_c.fit')
        for i in images:
            os.replace(i, os.path.join(subdir, 'image', i))
        prods = glob.glob('*_cobj.fit')
        for p in prods:
            os.replace(p, os.path.join(subdir, 'prod', p))

        return


class Image_Differencing(pas.PipelineAlg):
    """
    This PA performs image differencing
    """
    def __init__(self,name,config,logger=None):
        if name is None or name.strip() == "":
            name="Image_Differencing"

        datatype = fits.hdu.hdulist.HDUList
        pas.PipelineAlg.__init__(self, name, datatype, datatype, config, logger)

    def run(self,*args,**kwargs):
        if len(args) == 0 :
            log.critical("Missing input parameter!")
            sys.exit()
        if not self.is_compatible(type(args[0])):
            log.critical("Incompatible input!")
            sys.exit("Was expecting {} got {}".format(type(self.__inpType__),type(args[0])))

        outdir = kwargs['outdir']

        return self.run_pa(outdir)

    def run_pa(self, outdir):
        # Run image differencing on all subimages
        subdir = os.path.join(outdir, 'sub')
        imdir = os.path.join(subdir, 'image')
        os.chdir(subdir)
        os.system('module swap python/2; difference_all.py -i {}; module swap python/3'.format(imdir))

        return


class Choose_Refstars(pas.PipelineAlg):
    """
    This PA chooses reference stars
    """
    def __init__(self,name,config,logger=None):
        if name is None or name.strip() == "":
            name="Choose_Refstars"

        datatype = fits.hdu.hdulist.HDUList
        pas.PipelineAlg.__init__(self, name, datatype, datatype, config, logger)

    def run(self,*args,**kwargs):
        if len(args) == 0 :
            log.critical("Missing input parameter!")
            sys.exit()
        if not self.is_compatible(type(args[0])):
            log.critical("Incompatible input!")
            sys.exit("Was expecting {} got {}".format(type(self.__inpType__),type(args[0])))

        ra     = kwargs['RA']
        dec    = kwargs['DEC']
        outdir = kwargs['outdir']

        return self.run_pa(ra, dec, outdir)

    def run_pa(self, ra, dec, outdir):
        # Find template subimage
        subdir = os.path.join(outdir, 'sub')
        images = sorted(os.listdir(os.path.join(subdir, 'image')))
        # Check whether template was taken before or after supernova
        if images[0][:2] != images[1][:2] and images[0][2:6] != '1231':
            template = images[0]
        elif images[0][2:6] == '1231' and int(images[0][:2]) == int(images[1][:2]) - 1:
            template = images[-1]
        else:
            template = images[-1]

        # Open rphot GUI and choose ref stars
        idl = "singularity run --bind /scratch /hpc/applications/idl/idl_8.0.simg"
        os.chdir(subdir)
        ref = "file_search('image/{}')".format(template)
        os.system('{} -32 -e "rphot,data,imlist={},refname={},targetra={},targetdec={},/small"'.format(idl, ref, ref, ra, dec))

        return


class Photometry(pas.PipelineAlg):
    """
    This PA performs image differencing
    """
    def __init__(self,name,config,logger=None):
        if name is None or name.strip() == "":
            name="Photometry"

        datatype = fits.hdu.hdulist.HDUList
        pas.PipelineAlg.__init__(self, name, datatype, datatype, config, logger)

    def run(self,*args,**kwargs):
        if len(args) == 0 :
            log.critical("Missing input parameter!")
            sys.exit()
        if not self.is_compatible(type(args[0])):
            log.critical("Incompatible input!")
            sys.exit("Was expecting {} got {}".format(type(self.__inpType__),type(args[0])))

        outdir   = kwargs['outdir']
        dumpfile = kwargs['dumpfile']

        return self.run_pa(outdir, dumpfile)

    def run_pa(self, outdir, dumpfile):
        # Do photometry
        idl = "singularity run --bind /scratch /hpc/applications/idl/idl_8.0.simg"
        subdir = os.path.join(outdir, 'sub')
        imdir = os.path.join(subdir, 'image')
        images = "file_search('{}/*sub*')".format(imdir)
        os.chdir(subdir)
        os.system('{} -32 -e "run_phot,{}"'.format(idl, images))

        # Output light curve
        from rotseproc.io.supernova import plot_light_curve
        lc_data_file = os.path.join(subdir, 'lightcurve_subtract_target_psf.dat')
        plot_light_curve(lc_data_file, dumpfile)

        return


