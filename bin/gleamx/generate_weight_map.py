from astropy.io import fits
import numpy as np
import sys

# Original GLEAM-X function modified to measure RMS at the centre of the beam instead of the centre of the image.
# Additional changes to how the weight is calculated from the RMS.

def genWeightMap(in_xx, in_yy, in_rms, out_weight):
    hdu_xx = fits.open(in_xx)
    hdu_yy = fits.open(in_yy)
    hdu_rms = fits.open(in_rms)
    
    stokesI = (hdu_xx[0].data[0,0,:,:] + hdu_yy[0].data[0,0,:,:]) / 2.0
    
    # Get the beam centre from the Stokes I beam image and scaling for the RMS image.
    stokesIShape = stokesI.shape
    rmsShape = hdu_rms[0].data.shape
    centreStokesI = np.unravel_index(np.argmax(stokesI), stokesIShape)
    scale = [rmsShape[0]/stokesIShape[0], rmsShape[1]/stokesIShape[1]]
    centPosition = [int(np.round(centreStokesI[0] * scale[0])), int(np.round(centreStokesI[1] * scale[1]))]
    
    # Calculate the delta size for 10% of the image (+/- 5%).
    shape = np.array(rmsShape)
    delta = np.ceil(shape * 0.05).astype(int)

    # Use a 10% region around the centre of the beam from the RMS map to calculate the weight via inverse variance.
    cen_rms = hdu_rms[0].data[centPosition[0] - delta[0] : centPosition[0] + delta[0], centPosition[1] - delta[1] : centPosition[1] + delta[1]]

    mean_cen_rms_squared = np.nanmean(cen_rms ** 2)
    weight = stokesI ** 2 / mean_cen_rms_squared
    hdu_xx[0].data = weight
    hdu_xx.writeto(out_weight, overwrite=True)

