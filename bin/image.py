#!/usr/bin/env python3

import os
import sys
import report
import subprocess

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

msigma=3                            # S/N Level at which to choose masked pixels for deepclean
autoThreshold = 1                   # S/N Threshold at which to stop cleaning
min_uv = 0
nmitter = 10
basescale=0.6
imsize=10000
chans = 4
mgain = 0.75


# Import header information from the metafits file.
metaHdu = fits.open(metafits)
metadata = metaHdu[0].header
metaHdu.close()


scale = basescale / metadata['CENTCHAN']
scale = round(scale, 8)


# Clean the two main linear polizations.
cleanCmd = f'''wsclean \
    -gridder wgridder \
    -abs-mem 100 \
    -multiscale \
    -mgain {mgain} \
    -multiscale-gain 0.15 \
    -nmiter {nmitter} \
    -niter 10000000 \
    -mf-weighting \
    -auto-mask {msigma} \
    -auto-threshold {autoThreshold} \
    -name {obsid}_deep \
    -size {imsize} {imsize} \
    -scale {scale} \
    -weight briggs {robust} \
    -taper-inner-tukey {tukey} \
    -minuv-l {min_uv} \
    -pol xx,yy \
    -link-polarizations xx,yy \
    -join-channels \
    -channels-out {chans} \
    -fit-spectral-pol 2 \
    -data-column DATA \
    {measurementSet}'''

print(cleanCmd)
subprocess.run(cleanCmd, shell=True, check=True)

report.updateObs(reportCsv, obsid, 'image', 'Success')
