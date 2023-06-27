from astropy.io import fits
import numpy as np
import sys

def genWeightMap(in_xx, in_yy, in_rms, out_weight):

    hdu_xx = fits.open(in_xx)
    hdu_yy = fits.open(in_yy)
    hdu_rms = fits.open(in_rms)

    try:
        bscale = hdu_rms[0].header["BSCALE"]
    except IndexError:
        bscale = 1.0

    stokes_I = (hdu_xx[0].data + hdu_yy[0].data) / 2.0
    shape = np.array(hdu_rms[0].data.shape)
    cen = shape // 2
    delta = np.ceil(shape * 0.05).astype(int)


    # Use a central region of the RMS map to calculate the weight via inverse variance
    cen_rms = bscale * np.nanmean(
        hdu_rms[0].data[
            cen[0] - delta[0] : cen[0] + delta[0], cen[1] - delta[1] : cen[1] + delta[1],
        ]
    )

    weight = stokes_I ** 2 / cen_rms ** 2
    hdu_xx[0].data = weight
    hdu_xx.writeto(out_weight)

