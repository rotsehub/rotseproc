# Photometric pipeline for processing ROTSE-III data

## Example run for generating a supernova light curve in ManeFrame:

### Set up your environment:

```source /scratch/group/astro/rotse/environment/rotse_environ.sh```

This loads the following environment variables and sets up your paths

* ```$ROTSE_DATA```     : data directory
* ```$ROTSE_REDUX```    : output directory
* ```$ROTSE_ENVIRON```  : directory containing environment files
* ```$ROTSE_TEMPLATE``` : supernova tempate directory
* ```$CONFIG_DIR```     : configuration file directory

### Run the pipeline:

```
rotse_pipeline -i $CONFIG_DIR/config_supernova.yaml -o sn2013ej -n 130725 -r 01:36:48.16 -d 15:45:31.00
```
This parses the configuration file ```config_supernova.yaml``` to set up the pipeline

Output is sent to ```$ROTSE_REDUX/sn2013ej```

Night ```130725``` (7-25-2013) is the explosion night of sn2013ej

```01:36:48.16``` is the RA of sn2013ej

```15:45:31.00``` is the DEC of sn2013ej

Using these inputs, the pipeline runs the following processes:

* **Find_Data**          : find data for the appropriate dates and coordinates
* **Coaddition**         : coadd the preprocessed images for each night
* **Source_Extraction**  : run sextractor and calibration to generate sobj and then cobj files
* **Make_Subimages**     : make images into smaller subimages around the supernova
* **Image_Differencing** : perform image differencing using a template image
* **Choose_Refstars**    : choose reference stars for photometry
* **Photometry**         : do photometry on all images and produce a light curve

#### You will have to do the following steps while the pipeline is running:

##### Generate cobj files:

This happens at the end of **Source_Extraction**, you will see a log message

The pipeline automatically logs you into singularity

```source $ROTSE_ENVIRON/rotse_environ_old.sh``` set up old environment

```idl -32``` log into idl

```f = file_search('image/*')``` find files

```run_cal, f``` run calibration

```exit``` log out of idl

```exit``` log out of singularity

##### Choose reference stars:

A GUI will pop up allowing you to choose stars

Click ```Object``` then ```Choose Target...```

Click ```Done``` on the new GUI

Click ```Object``` then ```Choose Refstars...```

Use either ```Select by Cursor``` or ```Auto Select``` to choose reference stars on the new GUI

You will want around 10 reference stars, you can toggle ```Radius (arcmin) and ```Minimum S/N```

Once you have about 10 reference stars, click ```Done```

Click ```File``` then ```Save Target/Refstar RA DEC...```

Click ```OK``` on the new GUI

Exit the GUI

##### The pipeline will take care of everything else

#### Outputs:

* ```preproc```         : preprocessed images directory
* ```coadd```           : coadded images directory
* ```sub```             : subimages and differenced images directory
* ```lightcurve.pdf```  : pdf showing supernova light curve
* ```lightcurve.fits``` : fits file containing light curve data
* ```countpix.json```   : example QA metric output
* ```countpix.pdf```    : example QA plot

