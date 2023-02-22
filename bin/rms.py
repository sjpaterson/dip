import numpy as np
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
from astropy.stats import sigma_clip, mad_std

# Calculate the thermal noise for the image.
def calcRMS(obsFile):
    halfWindowSize = 20

    obsFits = fits.open(obsFile)
    obsImage = obsFits[0].data
    if obsImage.ndim > 2:
        obsImage = obsImage[0,0,:,:]
    obsImageShape = obsImage.shape
    obsImageCentre = [int(obsImageShape[0]/2), int(obsImageShape[1]/2)]
    obsFits.close()

    # Calculate the RMS at the center of the final image.
    window = obsImage[obsImageCentre[0]-halfWindowSize:obsImageCentre[0]+halfWindowSize, obsImageCentre[1]-halfWindowSize:obsImageCentre[1]+halfWindowSize]
    window = sigma_clip(window, masked=False, stdfunc=mad_std, sigma=3)

    obsRms = np.sqrt(np.mean(np.square(window)))

    return obsRms

# Calculate the RMS at the cooreds specified by ra and dec in degrees.
def calcRMSCoords(obsFile, ra, dec):
    halfWindowSize = 20

    obsFits = fits.open(obsFile)
    obsWCS = WCS(obsFits[0].header).celestial
    obsImage = obsFits[0].data
    if obsImage.ndim > 2:
        obsImage = obsImage[0,0,:,:]
    obsFits.close()

    raPixel, decPixel = obsWCS.all_world2pix(ra*u.degree, dec*u.degree, 0)
    raPixel = int(np.round(raPixel))
    decPixel = int(np.round(decPixel))

    # Calculate the RMS at the center of the final image.
    window = obsImage[raPixel-halfWindowSize:raPixel+halfWindowSize, decPixel-halfWindowSize:decPixel+halfWindowSize]
    window = sigma_clip(window, masked=False, stdfunc=mad_std, sigma=3)

    obsRms = np.sqrt(np.mean(np.square(window)))

    return obsRms
