#!/usr/bin/env python3

import os
import sys
import pandas as pd

sampleSize = 0

if len(sys.argv) != 2 and len(sys.argv) != 3:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

reportCsv = sys.argv[1]

if len(sys.argv) == 3:
    sampleSize = int(sys.argv[2])

report = pd.read_csv(reportCsv, dtype=str, index_col='obsid')

# Filter the report to remove any bad observations.
report = report[report['generateCalibration'] == 'Success']
report = report[report['applyCalibration'] == 'Success']
report = report[report['flagUV'] == 'Success']
report = report[report['uvSub'] == 'Success']
report = report[report['image'] == 'Success']
report = report[report['postImage_0000'] == 'Success']
report = report[report['postImage_0001'] == 'Success']
report = report[report['postImage_0002'] == 'Success']
report = report[report['postImage_0003'] == 'Success']
report = report[report['postImage_MFS'] == 'Success']

# Sample size to use if specified.
if sampleSize > 0:
    report = report.sample(n=sampleSize)

# The list of observations to convolve (obslist). A CSV (beaminfo.csv) containing the obs and the beaminfo for the Nextflow workflow.
# The list of filenames to convolve to (imagelist), used by both racs-tools and swarp,
# and the list of weight images (weightlist) used by swarp for the weighting.
fileObs = open('obslist', 'w')
fileImage = open('imagelist', 'w')
fileWeight = open('weightlist', 'w')
beamCsv = pd.DataFrame(columns=['obsid', 'obspath', 'bmaj', 'bmin', 'bpa'])
beamCsv.set_index('obsid', inplace=True)

for obsid, row in report.iterrows():
    fileObs.write(row['obsDir'] + '/' + str(obsid) + '/' + str(obsid) + '_deep-MFS-image-pb_warp.fits\n')
    fileImage.write(row['obsDir'] + '/' + str(obsid) + '/' + str(obsid) + '_deep-MFS-image-pb_warp.sm.fits\n')
    fileWeight.write(row['obsDir'] + '/' + str(obsid) + '/' + str(obsid)  + '_deep-MFS-image-pb_warp_weight.fits\n')
    beamCsv.at[obsid, 'obspath'] = row['obsDir'] + '/' + str(obsid) + '/' + str(obsid) + '_deep-MFS-image-pb_warp.fits'

fileImage.close()
fileWeight.close()
fileObs.close()

beamCsv.to_csv('beaminfo.csv', index=True)
