import numpy as np
import astropy.units as u
from astropy.io import fits
from astropy.wcs import WCS
from astropy.stats import sigma_clip, mad_std


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

# Estimate the RMS of the observation when BANE has not been run on it.
def estimateRMS(obsFile):
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

def timeDiffRMS(obsFileT1, obsFileT2):
    obsFitsT1 = fits.open(obsFileT1)
    obsFitsT2 = fits.open(obsFileT2)
    obsImageT1 = obsFitsT1[0].data
    obsImageT2 = obsFitsT2[0].data
    obsFitsT1[0].data = np.std(np.vstack((obsImageT1, obsImageT2)), axis=0, ddof=1).reshape(obsFitsT1[0].data.shape)
    width = obsFitsT1[0].data.shape[-1]
    sigma = np.mean(obsFitsT1[0].data[..., width//4:3*width//4, width//4:3*width//4])
    print('Thermal Noise Level: ' + str(sigma))
    return sigma