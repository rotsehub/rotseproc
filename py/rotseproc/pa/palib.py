"""
rotseproc.palib
Low level functions to be from top level PAs
"""
import os
import numpy as np
from rotseproc import exceptions, rlogger
rlog = rlogger.rotseLogger("ROTSE-III",20)
log = rlog.getlog()

def find_supernova_data(night, telescope, field):
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
            datapath = os.path.join(os.environ['ROTSE_DATA'], telescope, year, month, day)
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


