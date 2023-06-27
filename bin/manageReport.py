#!/usr/bin/env python3

import os
import sys
import shutil
import pandas as pd
import report


asvoPath = '/astro/mwasci/asvo/'
numberObs = 120

if not (len(sys.argv) >= 2 and len(sys.argv) <= 4):
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

action = sys.argv[1]

configFile = 'nextflow.config'
if len(sys.argv) >= 3:
    for i in range(2,len(sys.argv)):
        if sys.argv[i].isnumeric():
            numberObs = int(sys.argv[i])
        else:
            configFile = sys.argv[i]


reportCsv = ''
obsDir = ''
with open(configFile) as f:
    for line in f:
        if 'reportCsv=' in line.replace(' ', ''):
            reportCsv = line.split('=',1)[1].strip()
            reportCsv = reportCsv.replace('"', '')
            reportCsv = reportCsv.replace("'", "")
        if 'obsdir=' in line.replace(' ', ''):
            obsDir = line.split('=',1)[1].strip()
            obsDir = obsDir.replace('"', '')
            obsDir = obsDir.replace("'", "")

if reportCsv == '' or obsDir == '':
    print('Error: Unable to find the data entries in the nextflow.config.')
    exit()

print('Report: ' + reportCsv)
print('Observation Directory: ' + obsDir)


if action == 'create':
    # Otherwise check the report and verify.
    reportDF = pd.read_csv(reportCsv, dtype=str, index_col='obsid')

    # Filter the reportDF to remove any bad observations.
    reportDF.dropna(subset=['jobid'], inplace=True)
    reportDF = reportDF[reportDF['status'] != 'Success']
    reportDF = reportDF[reportDF['status'] != 'Failed']
    reportDF = reportDF[reportDF['jobid'] != '']
 

    # Create a maximum of 120 symlinks but still run through the entire operation to ensure old symlinks,
    # such as those that have reached their attempt limit, are removed.
    count = 0
    for obsid, row in reportDF.iterrows():
        asvoObsPath = os.path.join(asvoPath, reportDF.at[obsid, 'jobid'])
        msPath = os.path.join(asvoObsPath, str(obsid) + '.ms')
        obsPath = os.path.join(obsDir, str(obsid))

        # Check the measurement set in the ASVO path is there.
        if not os.path.exists(msPath):
            report.updateObs(reportCsv, obsid, 'status', 'Error - Missing Measurement Set')
            continue

        # Is the folder or symlink already exists, delete and recreate.
        if os.path.exists(obsPath):
            if os.path.isdir(obsPath) and not os.path.islink(obsPath):
                shutil.rmtree(obsPath)
            if os.path.islink(obsPath):
                os.unlink(obsPath)

        # IF attempt field is empty, treat it as 0.
        reportDF['attempts'] = reportDF['attempts'].fillna(0)
        # If < 3 attempts, create the new symlink.
        if int(reportDF.at[obsid, 'attempts']) < 3 and count < numberObs:
            os.symlink(asvoObsPath, obsPath)
            report.updateObs(reportCsv, obsid, 'status', 'Initiated')
            count = count + 1

    print('Created ' + str(count) + ' symlinks.')


if action == 'verify':
    print('Loading ' + reportCsv)
    reportDF = pd.read_csv(reportCsv, dtype=str, index_col='obsid')

    # Filter the reportDF to remove any bad observations.
    reportDF = reportDF[reportDF['calibration'] == 'Success']
    #reportDF = reportDF[reportDF['flagUV'] == 'Success']
    #reportDF = reportDF[reportDF['uvSub'] == 'Success']
    reportDF = reportDF[reportDF['image'] == 'Success']
    reportDF = reportDF[reportDF['postImage_0000'] == 'Success']
    reportDF = reportDF[reportDF['postImage_0001'] == 'Success']
    reportDF = reportDF[reportDF['postImage_0002'] == 'Success']
    reportDF = reportDF[reportDF['postImage_0003'] == 'Success']
    reportDF = reportDF[reportDF['postImage_MFS'] == 'Success']
    reportDF = reportDF[reportDF['status'] != 'Success']

    print('Validating ' + str(len(reportDF.index)) + ' observations.')

    count = 0
    for obsid, row in reportDF.iterrows():
        missing = False

        # Check to ensure the files for the subchans have been published as reported.
        for subchan in ['0000', '0001', '0002', '0003', 'MFS']:
            file = row['obsDir'] + '/' + str(obsid) + '/' + str(obsid) + '_deep-' + subchan + '-image-pb_warp.fits'
            if not os.path.exists(file):
                missing = True
                break
        
        # If any subchan for obsid missing, Clear the report entry (updating error count), delete the folder, recreate symlink if erorr count < 3.
        if missing == False:
            report.updateObs(reportCsv, obsid, 'status', 'Success')
        else:
            report.updateObs(reportCsv, obsid, 'status', 'Missing Data')

    print('Found ' + str(count) + ' errors.')