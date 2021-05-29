"""
I/O functions for supernova data
"""
import os
import numpy as np
from astropy.table import Table
from rotseproc import rlogger

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

    # Add TLA to field if not present
    if len(field) == 9:
        field = os.path.split(images[0])[1][7:19]

    log.info("Found data in {} for {} nights".format(field, len(set(founddata))))

    return images, prods, field

