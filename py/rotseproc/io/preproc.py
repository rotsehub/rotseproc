"""
I/O functions for preprocessed files
"""
import os
from shutil import copyfile
from rotseproc import rlogger

rlog = rlogger.rotseLogger("ROTSE-III",20)
log = rlog.getlog()

def match_image_prod(images, prods, telescope, field):
    """
    Remove image files without corresponding prod file
    """
    # Remove path from prod files
    prodfiles = []
    for p in prods:
        pfile = os.path.split(p)[1]
        if 'cobj' in pfile:
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

def copy_preproc(images, prods, outdir):
    """
    Copy preprocessed files to output directory
    """
    log.info("Copying preprocessed files to {}".format(outdir))
    # Define directories
    preprocdir = os.path.join(outdir, 'preproc')
    imagedir = os.path.join(preprocdir, 'image')
    proddir = os.path.join(preprocdir, 'prod')

    # Make directories
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

    return

