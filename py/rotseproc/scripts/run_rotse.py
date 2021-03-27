"""
rotseproc.scripts.run_rotse
===========================
Command line wrapper for running the ROTSE-III photometric pipeline

ROTSE team @Southern Methodist University (SMU)
First version Spring 2021
Latest revision July 2021

Running pipeline:

    rotse_pipeline -i config_science.yaml -f sks0246+3652

This requires having necessary input files and setting the following environment variables:

    ROTSE_DATA: directory containing preprocessed image and cobj files (full path: $ROTSE_DATA/(fill in after data move))
    ROTSE_REDUX: directory for output images (full path: $ROTSE_REDUX/(fill in later))
    ROTSE_TEMPLATE: directory containing template images

Necessary command line arguments:

    -i,--config_file : path to ROTSE-III configuration file

Optional arguments:

    --telescope: which telescope to process (3a, 3b (default), 3c, 3d)
    --rawdata_dir : directory containing data (overrides $ROTSE_DATA)
    --specprod_dir : directory for output (overrides $ROTSE_REDUX)
    
  Plotting options:

    -p (including path to plotting configuration file) : generate configured plots
    -p (only using -p with no configuration file) : generate hardcoded plots
"""

from __future__ import absolute_import, division, print_function

import os, sys
import argparse
from rotseproc import rotse, rlogger, config

def parse():
    """
        Should have either a pre existing config file, or need to generate one using config module
    """
    parser = argparse.ArgumentParser(description="Run pipeline on ROTSE-III data")
    parser.add_argument("-i", "--config_file", type=str, required=True, help="yaml file containing config dictionary", dest="config")
    parser.add_argument("-f", "--field", type=str, required=False, default=None, help="field containing transient", dest="config")
    parser.add_argument("-n", "--night", type=str, required=False, help="night of data")
    parser.add_argument("-t", "--telescope", type=str, required=False, default="3b", help="which ROTSE-III telescope")
    parser.add_argument("--datadir", type=str, required=False, help="data directory, overrides $ROTSE_DATA")
    parser.add_argument("--outdir", type=str, required=False, help="output directory, overrides $ROTSE_REDUX")
    parser.add_argument("--tempdir", type=str, required=False, default= None, help="template directory, overrides $ROTSE_TEMPLATE")
    parser.add_argument("-p", nargs='?', default='noplots', help="generate static plots", dest='plots')
    parser.add_argument("--loglvl", default=20, type=int, help="log level (0=verbose, 50=Critical)")
    args = parser.parse_args()
    return args

def rotse_main(args=None):

    from rotseproc import rotse, logger, config

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

        if args.outdir:
            outdir = args.outdir
        else:
            if 'ROTSE_REDUX' not in os.environ:
                sys.exit("must set $ROTSE_REDUX environment variable or provide specprod_dir")
            outdir = os.getenv('ROTSE_REDUX')

        log.debug("Running ROTSE-III pipeline using configuration file {}".format(args.config))
        if os.path.exists(args.config):
            if "yaml" in args.config:
                config = config.Config(args.config, args.night, args.field, args.telescope, args.singqa, datadir=datadir, outdir=outdir, tempdir=tempdir, plots=args.plots)
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
