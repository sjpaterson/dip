import numpy as np
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS


# Calculate the thermal noise for the image.
def calcRMS(obsFile):
    obsFits = fits.open(obsFile)
    obsWCS = WCS(obsFits[0].header).celestial
    obsImage = obsFits[0].data
    obsImageShape = obsImage.shape
    obsFits.close()

    return obsImage[int(obsImageShape[1]/2), int(obsImageShape[0]/2)]

# Calculate the RMS at the cooreds specified by ra and dec in degrees.
def calcRMSCoords(obsFile, ra, dec):
    obsFits = fits.open(obsFile)
    obsWCS = WCS(obsFits[0].header).celestial
    obsImage = obsFits[0].data
    obsFits.close()

    raPixel, decPixel = obsWCS.all_world2pix(ra*u.degree, dec*u.degree, 0)
    raPixel = int(np.round(raPixel))
    decPixel = int(np.round(decPixel))

    return obsImage[decPixel, raPixel]
