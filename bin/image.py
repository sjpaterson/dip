#!/usr/bin/env python3

import os
import sys
import report
import subprocess
import gleamx.calc_pointing as calcPointing
from astropy.io import fits


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
measurementSet = obsid + '.ms'

minuv=75                            # Minimum uvw for self-calibration (in lambda)
msigma=3                            # S/N Level at which to choose masked pixels for deepclean
tsigma=1                            # S/N Threshold at which to stop cleaning


# Set reference antenna.
if int(obsid) > 1191580576:
    telescope="MWALB"
    basescale=0.6
    imsize=8000
elif int(obsid) > 1151402936:
    telescope="MWAHEX"
    basescale=2.0
    imsize=2000
else:
    telescope="MWA128T"
    basescale=1.1
    imsize=4000

# Import header information from the metafits file.
metaHdu = fits.open(metafits)
metadata = metaHdu[0].header
metaHdu.close()


chans = metadata['CHANNELS'].split(',')
scale = basescale / metadata['CENTCHAN']
scale = round(scale, 8)


# Calculate min uvw in metres
minuvm = 234 * minuv / metadata['CENTCHAN']


# Check whether the phase centre has already changed, if not shift the pointing centre to point straight up, which approximates minw without making the phase centre rattle around.
chgcentreResult = subprocess.run('chgcentre ' + measurementSet, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
if 'shift' not in chgcentreResult.stderr.decode('utf-8'):
    # Determine whether to shift the pointing centre to be more optimally-centred on the peak of the primary beam sensitivity.
    coords = calcPointing.calc_optimal_ra_dec(metafits).to_string("hmsdms")
    subprocess.run('chgcentre ' + measurementSet + ' ' + coords, shell=True, check=True)
    # Shift to point straight up.
    subprocess.run('chgcentre -zenith -shiftback ' + measurementSet, shell=True, check=True)



if not os.path.exists(obsid + '_template.fits'):
    subprocess.run('wsclean -abs-mem 50 -mgain 1.0 -nmiter 1 -niter 0 -name ' + obsid + '_template -size ' + str(imsize) + ' ' + str(imsize) + ' -scale ' + str(scale) + ' -pol XX -data-column DATA -channel-range 4 5 -interval 4 5 -nwlayers 48 "' + measurementSet + '"', shell=True, check=True)
    subprocess.run('rm "' + obsid + '_template-dirty.fits' + '"', shell=True)
    subprocess.run('mv "' + obsid + '_template-image.fits' + '" "' + obsid + '_template.fits' + '"', shell=True)


# Hardcoding John's PB script location for now
# Also hardcoding creating four sub-band beams
pols = ['XX', 'XXi', 'XY', 'XYi', 'YX', 'YXi', 'YY', 'YYi']

for n in range(0,4):
    i = n * 6
    cstart = chans[i]
    j = i + 5
    cend = chans[j]

    for pol in pols:        
        # Check if the first pol exists, if not look it up.
        if not os.path.exists(obsid + '_000' + str(n) + '-' + pol + '-beam.fits'):
            subprocess.run('lookup_jones.py ' + obsid + ' _template.fits ' + obsid + '_000' + str(n) + '- -c ' + str(cstart) + '-' + str(cend) + ' --wsclean_names --beam_path "' + os.path.join(projectdir, 'beamdata/gleam_jones.hdf5') + '"', shell=True, check=True)
        subprocess.run('ln -s "' + obsid + '_000' + str(n) + '-' + str(pol) + '-beam.fits' + '" "' + obsid + '_deep-000' + str(n) + '-beam-' + str(pol) + '.fits' + '"', shell=True)  

# Set the tukey parameters.
min_uv = '0'
inner_width = str(tukey)

tukey_cmd = ' -taper-inner-tukey ' + inner_width + ' -minuv-l ' + min_uv
subprocess.run('wsclean -abs-mem 50 -multiscale -mgain 0.85 -multiscale-gain 0.15 -nmiter 5 -niter 10000000 -reuse-primary-beam -apply-primary-beam -auto-mask ' + str(msigma) + ' -auto-threshold ' + str(tsigma) + ' -name ' + obsid + '_deep -size ' + str(imsize) + ' ' + str(imsize) + ' -scale ' + str(scale) + ' -weight briggs ' + str(robust) + tukey_cmd + ' -pol I -join-channels -channels-out 4 -save-source-list -fit-spectral-pol 2 -data-column DATA ' + obsid + '.ms', shell=True, check=True)

report.updateObs(reportCsv, obsid, 'image', 'Success')
