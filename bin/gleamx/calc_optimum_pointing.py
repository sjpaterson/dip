#!/usr/bin/env python

from gleamx.beam_value_at_radec import beam_value, parse_metafits

from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy import units as u

import argparse
import numpy as np

def calc_peak_beam(metafits, gridsize = 8, cellsize = 1):
    t, delays, freq, gridnum = parse_metafits(metafits)
    hdu = fits.open(metafits)
    
    ra = hdu[0].header["RA"]
    dec = hdu[0].header["DEC"]
    ras = np.arange(ra - (gridsize/2), ra + (gridsize/2), cellsize)
    decs = np.arange(dec - (gridsize/2), dec + (gridsize/2), cellsize)
    val = 0
    
    for r in ras:
        for d in decs:
            bval = beam_value(r, d,  t, delays, freq, gridnum)
            bval = (bval[0] + bval[1])/2
            if bval > val:
                val = bval
                newra = r
                newdec = d

    newradec = SkyCoord(newra, newdec, unit = (u.deg, u.deg))
    
    return newradec.to_string("hmsdms")

