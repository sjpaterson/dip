#!/usr/bin/env python

import logging

import numpy as np 
from astropy.io import fits 


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(module)s:%(levelname)s:%(lineno)d %(message)s")
#logger.setLevel(logging.INFO)
logger.setLevel(logging.DEBUG)

def derive_apply_beam_cut(image, xx_beam, yy_beam, apply_mask=False, level=5.):
    logger.info(f"Creating the stokes I beam")
    with fits.open(xx_beam, memmap=True) as xx_fits, fits.open(yy_beam, memmap=True) as yy_fits:
        logger.debug('Assiging the xx fits beam data')
        xx_data = xx_fits[0].data
        logger.debug('Assiging the yy fits beam data')
        yy_data = yy_fits[0].data

        logger.debug('Forming the stokes i beam')
        i_data = (xx_data + yy_data) / 2

        logger.info('Writing stokes I beam')
        xx_fits[0].data = i_data 
        xx_fits.writeto(xx_beam.replace('XX','I'), overwrite=True)

    logger.debug(f"Stokes I beam formed, data shape is {i_data.shape}")

    logger.info(f"Flagging below level {level} percent")

    i_mask = i_data*100. < level 
    logger.info(f"Flagging {np.sum(i_mask)} of {np.prod(i_data.shape)} pixels")

    if apply_mask:
        logger.info(f"Applying the mask")
        with fits.open(image) as in_img:
            in_img[0].data[i_mask] = np.nan

            in_img.writeto(image.replace('.fits','_mask.fits'), overwrite=True)

    else:
        logger.info('Not applying mask')



