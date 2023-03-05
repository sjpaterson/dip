#!/usr/bin/env python3

import os
import sys
import pandas as pd

sampleSize = 0

if len(sys.argv) != 4 and len(sys.argv) != 5:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

reportCsv = sys.argv[1]
mosaicObsDir = sys.argv[2]
# mode: beam for the files required for the beam convolution and swarp for the files required for the mosaic by swarp.
mode = sys.argv[3]

if len(sys.argv) == 5:
    sampleSize = int(sys.argv[4])

report = pd.read_csv(reportCsv, index_col='obsid')

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
report = report[report['coord_rms_MFS'] < 0.02]
report = report[report['dist_point_cent'] < 10]

if mode == 'beam':
    # Sample size to use if specified.
    if sampleSize > 0:
        report = report.sample(n=sampleSize)

    # The list of observations to convolve (obslist). A CSV (beaminfo.csv) containing the obs and the beaminfo for the Nextflow workflow.

    fileObs = open('obslist', 'w')
    beamCsv = pd.DataFrame(columns=['obsid', 'obspath', 'bmaj', 'bmin', 'bpa'])
    beamCsv.set_index('obsid', inplace=True)

    for obsid, row in report.iterrows():
        fileObs.write(row['obsDir'] + '/' + str(obsid) + '/' + str(obsid) + '_deep-MFS-image-pb_warp.fits\n')
        beamCsv.at[obsid, 'obspath'] = row['obsDir'] + '/' + str(obsid) + '/' + str(obsid) + '_deep-MFS-image-pb_warp.fits'

    fileObs.close()
    beamCsv.to_csv('beaminfo.csv', index=True)


if mode == 'swarp':
    # The list of filenames to convolve (imagelist), used by both racs-tools and swarp,
    # and the list of weight images (weightlist) used by swarp for the weighting.
    # Only use observations that were successfully convoled.
    fileImage = open('imagelist', 'w')
    fileWeight = open('weightlist', 'w')

    for obsid, row in report.iterrows():
        obsFile = mosaicObsDir + '/' + str(obsid) + '_deep-MFS-image-pb_warp.sm.fits'
        if os.path.exists(obsFile):
            fileImage.write(obsFile + '\n')
            fileWeight.write(row['obsDir'] + '/' + str(obsid) + '/' + str(obsid)  + '_deep-MFS-image-pb_warp_weight.fits\n')

    fileImage.close()
    fileWeight.close()


