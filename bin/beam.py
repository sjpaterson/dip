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

def applyPB(obsid, subchan, channelStart, channelEnd, beamPath):
    # Look up beam info.
    subprocess.run('lookup_beam.py ' + obsid + ' _deep-' + subchan + '-XX-image.fits ' + obsid + '_deep-' + subchan + '- -c ' + channelStart + '-' + channelEnd + ' --beam_path "' + beamPath + '"', shell=True, check=True)

    # Apply the primary beam to each linear polarization.
    polarizations = ['XX', 'YY']
    for pol in polarizations:
        inFits = obsid + '_deep-' + subchan + '-' + pol + '-image.fits'
        outFits = obsid + '_deep-' + subchan + '-' + pol + '-image-pb.fits'
        beamFits = obsid + '_deep-' + subchan + '-' + pol + '-beam.fits'

        beamHdu = fits.open(beamFits)
        beam = beamHdu[0].data
        beamHdu.close()

        obsHdu = fits.open(inFits)
        obsHdu[0].data = obsHdu[0].data / beam
        obsHdu.writeto(outFits)

