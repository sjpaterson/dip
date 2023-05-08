import os
import math
import subprocess
from astropy.io import fits

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

