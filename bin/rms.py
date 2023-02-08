import numpy as np
from astropy.io import fits


halfWindowSize = 8

# Calculate the thermal noise for the image.
def calcRMS(obsFile):
    obsFits = fits.open(obsFile)
    obsImage = obsFits[0].data
    obsImage = obsImage[0,0,:,:]
    obsImageShape = obsImage.shape
    obsImageCentre = [int(obsImageShape[0]/2), int(obsImageShape[1]/2)]
    obsFits.close()

    # Calculate the RMS at the center of the final image.
    window = obsImage[obsImageCentre[0]-halfWindowSize:obsImageCentre[0]+halfWindowSize, obsImageCentre[1]-halfWindowSize:obsImageCentre[1]+halfWindowSize]
    obsRms = np.sqrt(np.mean(np.square(window)))

    return obsRms
