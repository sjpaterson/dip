#!/usr/bin/env python3

import os
import sys
#import wget
import report
import subprocess
import astropy.units as u
import gleamx.generate_ateam_subtract_model as genUVSub
import gleamx.calc_optimum_pointing as optPointing
from pathlib import Path


if len(sys.argv) != 4:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

projectdir = sys.argv[1]
obsid = sys.argv[2]
reportCsv = sys.argv[3]

# Define relavant file names and paths.
metafits = obsid + '.metafits'
catGGSM = os.path.join(projectdir, 'models/GGSM.fits')
measurementSet = obsid + '.ms'
submodel = obsid + '.ateam_outlier'


# Check to see if the metafits file has been downloaded, if not, download it.
# Would prefer to use the wget library, but must wait until new container is made.
if not os.path.exists(metafits):
    # wget.download('http://ws.mwatelescope.org/metadata/fits?obs_id=' + obsid, metafits)
    metaDownload = subprocess.run('wget -O "' + metafits + '" http://ws.mwatelescope.org/metadata/fits?obs_id=' + obsid, shell=True)
    # The above creates a 0b file if it fails, need to remove this before erroring out.
    if metaDownload.returncode != 0:
        subprocess.run('rm "' + metafits + '"', shell=True)
        report.updateObs(reportCsv, obsid, 'generateCalibration', 'Fail - Unable to download metadata.')
        exit(-1)


# Check whether the phase centre has already changed
# Calibration will fail if it has, so measurement set must be shifted back to its original position
chgcentreResult = subprocess.run('chgcentre ' + measurementSet, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
if 'shift' in chgcentreResult.stdout.decode('utf-8'):
    coords = optPointing.calc_peak_beam(metafits)
    subprocess.run('chgcentre ' + measurementSet + ' ' + coords, shell=True, check=True)

min_elevation = 0.0
search_radius = 10.0

min_elevation = genUVSub.attach_units_or_None(min_elevation, u.degree)
search_radius = genUVSub.attach_units_or_None(search_radius, u.degree)

# Create a script for weclean to subtract a-team sources from the visibility dataset.
result = genUVSub.ateam_model_creation(metafits, 'wsclean', ggsm=catGGSM, search_radius=search_radius, min_flux=5.0, check_fov=False, model_output=submodel, pixel_border=0, max_response=None, min_response=None, min_elevation=min_elevation, apply_beam=False, corrected_data=False, source_txt_path=None)

if not os.path.exists(submodel):
    report.updateObs(reportCsv, obsid, 'uvSub', 'Fail - Script not Generated.')

# Run the generate UV sub wsclean script.
subprocess.run('chmod +x ' + submodel, shell=True, check=True)
subprocess.run('./' + submodel, shell=True, check=True)

# Cleanup, remove all the outlier*.fits files.
for outlierFile in Path('.').glob('outlier*.fits'):
    outlierFile.unlink()

report.updateObs(reportCsv, obsid, 'uvSub', 'Success')
