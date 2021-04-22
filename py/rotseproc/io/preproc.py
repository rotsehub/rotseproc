"""
I/O functions for preprocessed files
"""
import os
from shutil import copyfile
import numpy as np
from rotseproc import exceptions, rlogger
rlog = rlogger.rotseLogger("ROTSE-III",20)
log = rlog.getlog()

def find_supernova_data(night, telescope, field, datadir):
    """
    Get image and prod files for a range of dates
    """
    # Define first and last day to find data
    startdate = night[0]
    stopdate = night[1]

    # Define full date range of data
    years = [startdate[:2], stopdate[:2]]
    months = np.arange(12,dtype=int) + 1
    for m, mm in enumerate(months):
        months[m] = '{:02d}'.format(mm)
    days = np.arange(31,dtype=int) + 1
    for d, dd in enumerate(days):
        days[d] = '{:02d}'.format(dd)

    dates = []
    for ye in years:
        for mo in months:
            for da in days:
                yearstring = str('{:02d}'.format(int(ye)))
                monthstring = str('{:02d}'.format(int(mo)))
                daystring = str('{:02d}'.format(int(da)))
                datestring = yearstring+monthstring+daystring
                if datestring not in dates:
                    dates.append(datestring)
                else:
                    break

    # Cut dates to start and stop dates
    date_ints = np.array(dates).astype(int)
    start = np.where(date_ints == int(startdate))[0][0]
    stop = np.where(date_ints == int(stopdate))[0][0] + 1
    dates = dates[start:stop]

    # Find image and prod files
    images=[]
    prods=[]
    founddata=[]
    for date in dates:
        year, month, day = date[:2], date[2:4], date[4:]

        try:
            datapath = os.path.join(datadir, telescope, year, month, day)
            imagedir = os.path.join(datapath, 'image')
            proddir = os.path.join(datapath, 'prod')
    
            # Load images
            for im in os.listdir(imagedir):
                if field in im:
                    image = os.path.join(imagedir, im)
                    images.append(image)
                    founddata.append(date)
    
            # Load prods
            for pr in os.listdir(proddir):
                if field in pr:
                    prod = os.path.join(proddir, pr)
                    prods.append(prod)

        except: # No data for this night
            pass

    log.info("Found data for {} nights".format(len(set(founddata))))

    return images, prods

def match_image_prod(images, prods, field, telescope):
    """
    Remove image files without corresponding prod file
    """
    # Remove path from prod files
    prodfiles = []
    for p in prods:
        pfile = os.path.split(p)[1]
        prodfiles.append(pfile)

    noprods = []
    for i in images:
        imagefile = os.path.split(i)[1]
        night = imagefile[:6]
        expnum = imagefile[22:25]
        prodfile = night + '_' + field + '_' + telescope + expnum + '_cobj.fit'
        if prodfile in prodfiles:
            pass
        else:
            noprods.append(i)

    log.info("Removing {} images without prod files".format(len(noprods)))

    for n in noprods:
        images.remove(n)

    return (images, prods)

def copy_preproc(outdir, images, prods):
    """
    Copy preprocessed files to output directory
    """
    log.info("Copying preprocessed files to {}".format(outdir))
    # Define directories
    preprocdir = os.path.join(outdir, 'preproc')
    imagedir = os.path.join(preprocdir, 'image')
    proddir = os.path.join(preprocdir, 'prod')

    # Make directories
    os.makedirs(outdir)
    os.makedirs(preprocdir)
    os.makedirs(imagedir)
    os.makedirs(proddir)

    # Copy files
    for i in images:
        imageout = os.path.join(imagedir, os.path.split(i)[1])
        copyfile(i, imageout)
    for p in prods:
        prodout = os.path.join(proddir, os.path.split(p)[1])
        copyfile(p, prodout)


