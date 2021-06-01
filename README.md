# Photometric pipeline for processing ROTSE-III data

## Example run for generating a supernova light curve in ManeFrame:

### Must first run source ```/scratch/group/astro/rotse/environment/rotse_environ.sh```

This sets up your ROTSE environment:

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

* Find_Data          : find data for the appropriate dates and coordinates
* Coaddition         : coadd the preprocessed images for each night
* Source_Extraction  : run sextractor and calibration to generate sobj and then cobj files
* Make_Subimages     : make images into smaller subimages around the supernova
* Image_Differencing : perform image differencing using a template image
* Choose_Refstars    : choose reference stars for photometry
* Photometry         : so photometry on all images and produce a light curve

