#!/usr/bin/env python3

import os
import sys
import pandas as pd

sampleSize = 0

if len(sys.argv) != 3 and len(sys.argv) != 4:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

reportCsv = sys.argv[1]
# Output Style, 'm' to output the inputfile for the mosiac, 'c' to just print the filenames for the beam convolution.
outputStyle = sys.argv[2]

if len(sys.argv) == 4:
    sampleSize = int(sys.argv[3])

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

if outputStyle == 'm':
    fileImage = open('imagelist', 'w')
    fileWeight = open('weightlist', 'w')

    for obsid, row in report.iterrows():
        fileImage.write(row['obsDir'] + '/' + str(obsid) + '/' + str(obsid) + '_deep-MFS-image-pb_warp.sm.fits\n')
        fileWeight.write(row['obsDir'] + '/' + str(obsid) + '/' + str(obsid)  + '_deep-MFS-image-pb_warp_weight.fits\n')

    fileImage.close()
    fileWeight.close()

if outputStyle == 'c':
    fileObs = open('obslist', 'w')
    for obsid, row in report.iterrows():
        fileObs.write(row['obsDir'] + '/' + str(obsid) + '/' + str(obsid) + '_deep-MFS-image-pb_warp.fits\n')
    fileObs.close()
