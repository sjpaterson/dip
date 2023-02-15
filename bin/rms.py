import numpy as np
from astropy.io import fits
from astropy.stats import sigma_clip, mad_std

# Calculate the thermal noise for the image.
def calcRMS(obsFile):
    halfWindowSize = 20

    obsFits = fits.open(obsFile)
    obsImage = obsFits[0].data
    obsImage = obsImage[0,0,:,:]
    obsImageShape = obsImage.shape
    obsImageCentre = [int(obsImageShape[0]/2), int(obsImageShape[1]/2)]
    obsFits.close()

    # Calculate the RMS at the center of the final image.
    window = obsImage[obsImageCentre[0]-halfWindowSize:obsImageCentre[0]+halfWindowSize, obsImageCentre[1]-halfWindowSize:obsImageCentre[1]+halfWindowSize]
    window = sigma_clip(window, masked=False, stdfunc=mad_std, sigma=3)

    obsRms = np.sqrt(np.mean(np.square(window)))

    return obsRms
