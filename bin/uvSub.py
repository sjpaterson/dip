#!/usr/bin/env python3

import os
import sys
import report
import subprocess
import selfCal
import astropy.units as u
import gleamx.generate_ateam_subtract_model as genUVSub
import gleamx.calc_optimum_pointing as optPointing
from pathlib import Path


if len(sys.argv) != 6:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

projectdir = sys.argv[1]
obsid = sys.argv[2]
robust = sys.argv[3]
tukey = sys.argv[4]
reportCsv = sys.argv[5]

# Define relavant file names and paths.
metafits = obsid + '.metafits'
catGGSM = os.path.join(projectdir, 'models/GGSM.fits')
measurementSet = obsid + '.ms'
submodel = obsid + '.ateam_outlier'

min_elevation = 0.0
search_radius = 10.0

min_elevation = genUVSub.attach_units_or_None(min_elevation, u.degree)
search_radius = genUVSub.attach_units_or_None(search_radius, u.degree)

# Create a script for weclean to subtract a-team sources from the visibility dataset.
brightSources = genUVSub.ateam_model_creation(metafits, 'wsclean', ggsm=catGGSM, search_radius=search_radius, min_flux=5.0, check_fov=False, model_output=submodel, pixel_border=0, max_response=None, min_response=None, min_elevation=min_elevation, apply_beam=False, corrected_data=False, source_txt_path=None)

numSources = len(brightSources['imagename'])
print('Number of Sources: ' + str(numSources))

if numSources > 0:
    for c, (imagename, phasecenter, imsize) in enumerate(zip(brightSources["imagename"], brightSources["phasecenter"], brightSources["imsize"])):
        print('Name: ' + imagename)
        print('Coords: ' + phasecenter)

        cleanCmd = f'''wsclean \
            -gridder wgridder \
            -shift {phasecenter} \
            -mgain 0.8 \
            -abs-mem 100 \
            -nmiter 10 \
            -niter 100000 \
            -size 128 128 \
            -pol xx,yy \
            -data-column DATA \
            -name {imagename} \
            -scale 10arcsec \
            -weight briggs {robust} \
            -taper-inner-tukey {tukey} \
            -minuv-l 0 \
            -auto-mask 3 \
            -auto-threshold 1  \
            -join-channels \
            -channels-out 64 \
            -fit-spectral-pol 4 \
            {measurementSet}'''

        # Clean the bright source and update the measurement set.
        subprocess.run(f'taql alter table {obsid}.ms drop column MODEL_DATA', shell=True, check=True)
        subprocess.run(cleanCmd, shell=True, check=True)
        subprocess.run(f'taql update {obsid}.ms set DATA=DATA-MODEL_DATA', shell=True, check=True)

    # Self Calibrate.
    selfCal.selfCal(obsid, robust, tukey)

report.updateObs(reportCsv, obsid, 'uvSub', 'Success')
report.updateObs(reportCsv, obsid, 'uvSub_SourceCount', str(numSources))
