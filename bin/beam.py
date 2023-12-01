import os
import math
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord

def calcBeamSize(psfFile):
    # Import the PSF header to read the BMAJ and BMIN for the restoring beam.
    psfFits = fits.open(psfFile)
    psfHeader = psfFits[0].header
    psfFits.close()

    # Convert BMAJ and BMIN from degrees to arcmin.
    bmaj = psfHeader['BMAJ']*3600
    bmin = psfHeader['BMIN']*3600

    # Beam solid angle.
    omega_b = (math.pi*bmaj*bmin) / (4 * math.log(2))

    return omega_b

def applyPB(obsid, subchan, pol, beam):
    # Apply the primary beam to each linear polarization.
    inFits = obsid + '_deep-' + subchan + '-' + pol + '-image.fits'
    outFits = obsid + '_deep-' + subchan + '-' + pol + '-image-pb.fits'

    obsHdu = fits.open(inFits)
    obsHdu[0].data = obsHdu[0].data / beam
    obsHdu.writeto(outFits)
    obsHdu.close()

# Calculate the location of the beam centre either from the beam.fits or weight.fits.
def calcBeamCentre(beamFile):
    if not os.path.exists(beamFile):
        print(f'Error, {beamFile} does not exist.')
        exit()

    obsFits = fits.open(beamFile)
    obsWCS = WCS(obsFits[0].header).celestial
    obsImage = obsFits[0].data
    obsFits.close()
    if obsImage.ndim > 2:
        obsImage = obsImage[0,0,:,:]

    centPos = np.unravel_index(np.argmax(obsImage), obsImage.shape)    
    centreBeam = SkyCoord.from_pixel(centPos[1], centPos[0], obsWCS)
    
    return centreBeam