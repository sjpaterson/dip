import math
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
