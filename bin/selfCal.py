import os
import sys
import report
import subprocess
import astropy.units as u
from astropy.io import fits


def selfCal(obsid, robust, tukey):

    # Define relavant file names and paths.
    metafits = obsid + '.metafits'
    measurementSet = obsid + '.ms'

    # Import header information from the metafits file.
    metaHdu = fits.open(metafits)
    metadata = metaHdu[0].header
    metaHdu.close()

    # Calculate min uvw in metres
    minuv=75
    minuvm = 234 * minuv / metadata['CENTCHAN']
    maxuvm= 390000 / (metadata['CENTCHAN'] + 11)

    # Removing any previous model column to make sure its not accidentally included in the model for selfcal
    subprocess.run(f'taql alter table {obsid}.ms drop column MODEL_DATA', shell=True, check=True)

    # Popular the DATA column with a shallow clean.
    populateCmd = f'''wsclean \
            -gridder wgridder \
            -abs-mem 100 \
            -multiscale -mgain 0.85 -multiscale-gain 0.15 \
            -nmiter 1 \
            -niter 40000 \
            -stop-negative \
            -name {obsid}_initial \
            -size 10000 10000 \
            -scale 0.0035503 \
            -weight briggs {robust} \
            -taper-inner-tukey {tukey} -minuv-l 0 \
            -pol XX,YY,XY,YX \
            -link-polarizations XX,YY \
            -channels-out 4 \
            "{measurementSet}"'''
    subprocess.run(populateCmd, shell=True, check=True)

    # Generate Selfcal Solution
    selfCalSolution = f'{obsid}_selfsolutions.bin'
    calibrateCmd = f'calibrate -j 48 -absmem 100 -minuv {minuvm} -maxuv {maxuvm} -datacolumn DATA "{measurementSet}" "{selfCalSolution}"'
    print(calibrateCmd)
    subprocess.run(calibrateCmd, shell=True, check=True)

    # Apply SelfCal Solution
    subprocess.run(f'applysolutions -nocopy "{measurementSet}" "{selfCalSolution}"', shell=True, check=True)
