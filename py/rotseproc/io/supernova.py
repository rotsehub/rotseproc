"""
I/O functions for supernova data
"""
import os, sys
import glob
from shutil import copyfile
import numpy as np
from astropy.table import Table
import matplotlib.pyplot as plt
from rotseproc import exceptions, rlogger

rlog = rlogger.rotseLogger("ROTSE-III",20)
log = rlog.getlog()

def load_supernova_fields():
    """
    Load supernova fields and their respective coordinates
    """
    # Find supernova fields file
    if 'ROTSE_SOFTWARE' in os.environ:
        data_path = os.path.join(os.getenv('ROTSE_SOFTWARE'), 'rotsehub/rotseproc/py/rotseproc/data')
        data_file = os.path.join(data_path, 'sksname_rac_decc.fit')
        data = Table.read(data_file)
    else:
        os.log.critical("Can't find find supernova fields, must set $ROTSE_SOFTWARE!")

    # Get field information
    fields = data['SKSNAME']
    ras    = data['RAC']
    decs   = data['DECC']

    return fields, ras, decs

def find_supernova_field(ra, dec):
    """
    Use RA and DEC to find supernova field
    """
    # Load supernova fields
    fields, ras, decs = load_supernova_fields()

    # Calculate offset between supernova and field centers
    found_field = None
    for i in range(len(fields)):
        ra_offset = ra - ras[i]
        dec_offset = dec - decs[i]

        ra_cut = 1. / np.cos((dec_offset * np.pi) / 180.)
        dec_cut = 1.
        if np.abs(ra_offset) <= ra_cut and np.abs(dec_offset) <= dec_cut:
            found_field = fields[i]

    return found_field

def find_supernova_data(night, telescope, field, t_before, t_after, datadir):
    """
    Get image and prod files for a range of dates
    """
    # Define first and last date to find data
    if len(night) == 1:
        night = night[0]

        if night[2:4] == '01':
            startyear = str(int(night[:2]) - 1).zfill(2)
            startdate = startyear + '12' + night[4:6]
        else:
            startmonth = str(int(night[2:4]) - t_before).zfill(2)
            startdate = night[:2] + startmonth + night[4:6]

        stopyear = str(int(night[:2]) + t_after).zfill(2)
        stopdate = stopyear + night[2:4] + night[4:6]

    elif len(night) == 2:
        startdate = night[0]
        stopdate = night[1]

    else:
        log.critical("Wrong night format!")
        sys.exit("Must provide either discovery date or first/last date to search.")

    log.info("Finding supernova data from {} to {}".format(startdate, stopdate))

    # Define full date range of data
    years = np.arange(int(startdate[:2]), int(stopdate[:2])+1)
    months = np.arange(12,dtype=int) + 1
    days = np.arange(31,dtype=int) + 1

    dates = []
    for ye in years:
        for mo in months:
            for da in days:
                yearstring = str(ye).zfill(2)
                monthstring = str(mo).zfill(2)
                daystring = str(da).zfill(2)
                datestring = yearstring + monthstring + daystring
                dates.append(datestring)

    # Cut dates to start and stop dates
    date_ints = np.array(dates).astype(int)
    start = np.where(date_ints == int(startdate))[0][0]
    stop = np.where(date_ints == int(stopdate))[0][0] + 1
    dates = dates[start:stop]

    # Find image and prod files
    images = []
    prods = []
    founddata = []
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

    if len(images) == 0:
        log.critical("No images were found for this supernova.")
        sys.exit()

    if len(prods) == 0:
        log.critical("No cobj files were found for this supernova.")
        sys.exit()

    # Add TLA to field if not present
    if len(field) == 9:
        field = os.path.split(images[0])[1][7:19]

    log.info("Found data in {} for {} nights".format(field, len(set(founddata))))

    return images, prods, field

def find_reference_image(telescope, field, tempdir, outdir):
    """
    Find reference image for provided supernova field and copy to coadd dir
    """
    # Make coadd directories
    coadddir = outdir + '/coadd/'
    os.mkdir(coadddir)
    os.mkdir(coadddir + 'image')
    os.mkdir(coadddir + 'prod') 

    # Find reference directory
    refdir = os.path.join(tempdir, telescope, 'reference')
    imdir = os.path.join(refdir, 'image')
    proddir = os.path.join(refdir, 'prod')

    # Find reference image
    try:
        imfile = glob.glob(imdir + '/*{}*'.format(field))[0]
        im = os.path.split(imfile)[1]
        imout = os.path.join(coadddir, 'image', im)
        copyfile(imfile, imout)

        prodfile = glob.glob(proddir + '/*{}*'.format(field))[0]
        prod = os.path.split(prodfile)[1]
        prodout = os.path.join(coadddir, 'prod', prod)
        copyfile(prodfile, prodout)

        log.info("Found reference image {}".format(im))

        return

    except:
        raise exceptions.ReferenceException("No reference image for {}".format(field))
        return

