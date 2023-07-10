#!/usr/bin/env python3

import os
import sys
import shutil
import pandas as pd
import report
from mantaray.api import Session


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


# Set mwa_client settings.
apiKey = os.getenv('MWA_ASVO_API_KEY')
host = 'asvo.mwatelescope.org'
port = '443'
https = '1'


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


# Verbose output for the verify method.
# For check status, silently update the spreadsheet.
if action == 'verify' or action == 'status':
    print('Loading ' + reportCsv)
    reportDF = pd.read_csv(reportCsv, dtype=str)
    reportDF.set_index('obsid', inplace=True)

    quietMode = False
    if action == 'status':
        quietMode = True

    apiKey = os.getenv('MWA_ASVO_API_KEY')
    # If the API key is set, check if any new downloads have been completed.
    if apiKey != None:
        print('Downloading AVSO Job Information.')
        session = Session.login('1', 'asvo.mwatelescope.org', '443', apiKey)
        jobList = session.get_jobs()

        for job in jobList:
            obsID = job['row']['job_params']['obs_id']
            jobID = job['row']['id']
            jobState = job['row']['job_state']
            if obsID in reportDF.index:
                report.updateObs(reportCsv, obsID, 'jobid', jobID, quiet=quietMode)
                if jobState == 0:
                    report.updateObs(reportCsv, obsID, 'job_status', 'Queued', quiet=quietMode)
                if jobState == 1:
                    report.updateObs(reportCsv, obsID, 'job_status', 'Processing', quiet=quietMode)
                if jobState == 2:
                    report.updateObs(reportCsv, obsID, 'job_status', 'Downloaded', quiet=quietMode)


    # Filter the reportDF to remove any bad observations.
    reportDF = reportDF[reportDF['calibration'] == 'Success']
    reportDF = reportDF[reportDF['image'] == 'Success']
    reportDF = reportDF[reportDF['postImage_0000'] == 'Success']
    reportDF = reportDF[reportDF['postImage_0001'] == 'Success']
    reportDF = reportDF[reportDF['postImage_0002'] == 'Success']
    reportDF = reportDF[reportDF['postImage_0003'] == 'Success']
    reportDF = reportDF[reportDF['postImage_MFS'] == 'Success']
    reportDF = reportDF[reportDF['status'] != 'Success']

    if action == 'verify':
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
            report.updateObs(reportCsv, obsid, 'status', 'Success', quiet=quietMode)
        else:
            report.updateObs(reportCsv, obsid, 'status', 'Missing Data', quiet=quietMode)

    if action == 'verify':
        print('Found ' + str(count) + ' errors.')


if action == 'status':
    reportDF = pd.read_csv(reportCsv, dtype=str)
    reportDF.set_index('obsid', inplace=True)

    # Count of: Total observations, jobs needing to be downloaded, submitted/queued/processing jobs, completed jobs, obs processed, obs queued/running, obs failed, obs successful.
    totalObs = len(reportDF.index)
    jobsNotDownloaded = len(reportDF[pd.isnull(reportDF['jobid'])].index)
    jobsSubmitted = len(reportDF[pd.notnull(reportDF['job_status']) & (reportDF['job_status'] != 'Downloaded')].index)
    jobsDownloaded = len(reportDF[reportDF['job_status'] == 'Downloaded'].index)
    obsProcessed = len(reportDF[pd.notnull(reportDF['status'])].index)
    obsQueued = len(reportDF[reportDF['status'] == 'Queued'].index)
    obsFailed = len(reportDF[reportDF['status'] == 'Failed'].index)
    obsMissing = len(reportDF[reportDF['status'] == 'Missing Data'].index)
    obsReady = len(reportDF[(reportDF['status'] != 'Success') & (reportDF['status'] != 'Failed') & (reportDF['job_status'] == 'Downloaded')].index)
    obsSuccess = len(reportDF[reportDF['status'] == 'Success'].index)

    print(f'DIP Status: {reportCsv}\n')
    print(f'Total Observations: {totalObs}')
    print(f'AVSO Jobs Requiring Download: {jobsNotDownloaded}')
    print(f'AVSO Jobs Submitted: {jobsSubmitted}')
    print(f'AVSO Jobs Downloaded: {jobsDownloaded}')
    print(f'Observations Processed: {obsProcessed}')
    print(f'Observations Queued: {obsQueued}')
    print(f'Observations Failed: {obsFailed}')
    print(f'Observations Missing Data: {obsMissing}')
    print(f'Observations Ready to be Processed: {obsReady}')
    print(f'Observations Completed Successfully: {obsSuccess}')


count = 0
if action == 'download':
    if apiKey == None:
        print('Error unable to submit download jobs, MWA_ASVO_API_KEY not set.')
        exit(-1)

    session = Session.login('1', 'asvo.mwatelescope.org', '443', apiKey)
    jobList = session.get_jobs()
    print('Loading ' + reportCsv)
    reportDF = pd.read_csv(reportCsv, dtype=str)
    reportDF.set_index('obsid', inplace=True)

    # Check how many observations are currently being downloaded.
    jobsSubmitted = len(reportDF[pd.notnull(reportDF['job_status']) & (reportDF['job_status'] != 'Downloaded')].index)
    maxObs = numberObs
    numberObs = numberObs - jobsSubmitted

    # If already downloading the max number, quit.
    if numberObs < 1:
        print(f'Maximum number of concurrent downloads already submitted: {maxObs}')
        exit()

    # Filter for only obs left to download.
    reportDF = reportDF[pd.isnull(reportDF['jobid'])]
    print(f'Total observations left to download: {len(reportDF.index)}')
    print(f'Queueing a total of {numberObs} observations.')

    params = dict()
    params['avg_time_res'] = '4'
    params['avg_freq_res'] = '40'
    params['flag_edge_width'] = '80'
    params['output'] = 'ms'
    params['delivery'] = 'astro'

    count = 0
    for obsID, row in reportDF.iterrows():
        params['obs_id'] = obsID
        # Submit job.
        try:
            jobResponse = session.submit_conversion_job_direct(params)
            jobID = jobResponse['job_id']
            report.updateObs(reportCsv, obsID, 'jobid', jobID, quiet=True)
            report.updateObs(reportCsv, obsID, 'job_status', 'Submitted', quiet=True)
            print(f'Submitted {obsID} with Job ID {jobID}.')
            count = count + 1
        except:
            print(f'Failled to submit {obsID}.')

        # If maximum jobs has been reached, break.
        if count >= numberObs:
            break

    print(f'Submitted {count} observations.')

