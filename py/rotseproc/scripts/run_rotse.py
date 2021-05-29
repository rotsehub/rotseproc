"""
rotseproc.scripts.run_rotse
===========================
Command line wrapper for running the ROTSE-III photometric pipeline

ROTSE team @ Southern Methodist University (SMU)
First version Spring 2021 (R. Staten)
Latest revision June 2021 (R. Staten)

Running pipeline:

    rotse_pipeline -i config_science.yaml -f sks0246+3652 -n 070810 071231 -o output

This requires setting the following environment variables:

    ROTSE_DATA     : directory containing preprocessed image and cobj files
    ROTSE_REDUX    : directory for output images
    ROTSE_TEMPLATE : directory containing template images (only needed for supernovae)

Necessary command line arguments:

    --config_file : path to ROTSE-III configuration file

Optional arguments:

    --night        : first and last nights to search for data (e.g. 070810 071231)
    --telescope    : which telescope to process (3a, 3b (default), 3c, 3d)
    --field        : field containing target object
    --ra           : RA of target object
    --dec          : DEC of target object
    --rawdata_dir  : directory containing data (overrides $ROTSE_DATA)
    --specprod_dir : directory for output (overrides $ROTSE_REDUX)
    --outdir       : output directory ($ROTSE_REDUX/{outdir})
    --tempdir      : directory containing template image
    --loglvl       : level of log information to show in the terminal
    
  Plotting options:

    -p (including path to plotting configuration file) : generate configured plots
    -p (only using -p with no configuration file) : generate hardcoded plots
"""
from __future__ import absolute_import, division, print_function
import argparse

def parse():
    """
        Should have either a pre existing config file, or need to generate one using config module
    """
    parser = argparse.ArgumentParser(description="Run pipeline on ROTSE-III data")
    parser.add_argument("-i", "--config_file", type=str, required=True, help="yaml file containing config dictionary", dest="config")
    parser.add_argument("-n", "--night", type=str, nargs='+', required=False, default=None, help="night(s) of data")
    parser.add_argument("-t", "--telescope", type=str, required=False, default="3b", help="which ROTSE-III telescope")
    parser.add_argument("-f", "--field", type=str, required=False, default=None, help="field containing transient", dest="field")
    parser.add_argument("-r", "--ra", type=str, required=False, default=None, help="target RA")
    parser.add_argument("-d", "--dec", type=str, required=False, default=None, help="target DEC")
    parser.add_argument("--datadir", type=str, required=False, help="data directory, overrides $ROTSE_DATA")
    parser.add_argument("--reduxdir", type=str, required=False, help="output directory, overrides $ROTSE_REDUX")
    parser.add_argument("-o", "--outdir", type=str, required=False, default=".", help="reduxdir/outdir directory")
    parser.add_argument("--tempdir", type=str, required=False, default=None, help="template directory, overrides $ROTSE_TEMPLATE")
    parser.add_argument("-p", nargs='?', default='noplots', help="generate static plots", dest='plots')
    parser.add_argument("--loglvl", default=20, type=int, help="log level (0=verbose, 50=Critical)")
    args = parser.parse_args()
    return args

def rotse_main(args=None):
    import os, sys
    from rotseproc import rotse, rlogger, rotse_config

    if args is None:
        args = parse()

    rlog = rlogger.rotseLogger(name="ROTSE-III",loglevel=args.loglvl)
    log = rlog.getlog()

    if args.config is not None:

        if args.datadir:
            datadir = args.datadir
        else:
            if 'ROTSE_DATA' not in os.environ:
                sys.exit("must set $ROTSE_DATA environment variable or provide rawdata_dir")
            datadir = os.getenv('ROTSE_DATA')

        if args.reduxdir:
            reduxdir = args.reduxdir
        else:
            if 'ROTSE_REDUX' not in os.environ:
                sys.exit("must set $ROTSE_REDUX environment variable or provide specprod_dir")
            reduxdir = os.getenv('ROTSE_REDUX')

        outdir = os.path.join(reduxdir, args.outdir)

        tempdir = None
        if args.tempdir:
            tempdir = args.tempdir
        else:
            if 'ROTSE_TEMPLATE' in os.environ:
                tempdir = os.getenv('ROTSE_TEMPLATE')

        log.debug("Running ROTSE-III pipeline using configuration file {}".format(args.config))
        if os.path.exists(args.config):
            if "yaml" in args.config:
                config = rotse_config.Config(args.config, args.night, args.telescope, args.field, args.ra, args.dec, datadir=datadir, outdir=outdir, tempdir=tempdir, plots=args.plots)
                configdict = config.expand_config()
            else:
                log.critical("Can't open configuration file {}".format(args.config))
                sys.exit("Can't open configuration file")
        else:
            sys.exit("File does not exist: {}".format(args.config))
    else:
        sys.exit("Must provide a valid configuration file. See rotseproc/config for an example")

    pipeline, convdict = rotse.setup_pipeline(configdict)
    res = rotse.runpipeline(pipeline, convdict, configdict)
    log.info("ROTSE-III Pipeline completed")

if __name__=='__main__':
    rotse_main()
