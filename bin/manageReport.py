#!/usr/bin/env python3

import os
import sys
import shutil
import pandas as pd
import report
import subprocess
from mantaray.api import Session


asvoPath = '/scratch/mwasci/asvo/'
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
            reportCsv = os.path.expandvars(reportCsv)
        if 'obsdir=' in line.replace(' ', ''):
            obsDir = line.split('=',1)[1].strip()
            obsDir = obsDir.replace('"', '')
            obsDir = obsDir.replace("'", "")
            obsDir = os.path.expandvars(obsDir)

if reportCsv == '' or obsDir == '':
    print('Error: Unable to find the data entries in the nextflow.config.')
    exit()


# Verify the download data is there, return True if it is, False if it is missing.
def verifyDownload(obsid, jobid, quietMode=False):
    asvoObsPath = os.path.join(asvoPath, str(jobid))
    msPath = os.path.join(asvoObsPath, str(obsid) + '.ms')
    # Check the measurement set in the ASVO path is there, if not flag to redownload when possible.
    if not os.path.exists(msPath):
        report.updateObs(reportCsv, obsid, 'status', 'Error - Missing Measurement Set', quiet=quietMode)
        report.updateObs(reportCsv, obsid, 'job_status', 'Missing Data', quiet=quietMode)
        return False

    # Check the measurement set if the FLAG_CMD table is present, if not flag to redownload when possible.
    if not os.path.exists(os.path.join(msPath, 'FLAG_CMD/table.dat')):
        report.updateObs(reportCsv, obsid, 'status', 'Error - Missing FLAG_CMD Table.', quiet=quietMode)
        report.updateObs(reportCsv, obsid, 'job_status', 'Missing Data', quiet=quietMode)
        return False
    
    return True


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

    if 'status' not in reportDF.columns:
        reportDF['status'] = ''
    if 'attempts' not in reportDF.columns:
        reportDF['attempts'] = 0

    # Filter the reportDF to remove any bad observations.
    reportDF.dropna(subset=['jobid'], inplace=True)
    reportDF = reportDF[reportDF['status'] != 'Success']
    #reportDF = reportDF[reportDF['status'] != 'Failed']
    reportDF = reportDF[reportDF['jobid'] != '']
    reportDF = reportDF[reportDF['job_status'] == 'Downloaded']
 

    # Create a maximum of 120 symlinks but still run through the entire operation to ensure old symlinks,
    # such as those that have reached their attempt limit, are removed.
    count = 0
    for obsid, row in reportDF.iterrows():
        asvoObsPath = os.path.join(asvoPath, reportDF.at[obsid, 'jobid'])
        msPath = os.path.join(asvoObsPath, str(obsid) + '.ms')
        obsPath = os.path.join(obsDir, str(obsid))

        # Is the folder or symlink already exists, delete and recreate.
        if os.path.exists(obsPath):
            if os.path.isdir(obsPath) and not os.path.islink(obsPath):
                shutil.rmtree(obsPath)
            if os.path.islink(obsPath):
                os.unlink(obsPath)

        # If the measurement set data is not there or incomplete, skip.
        if verifyDownload(obsid, reportDF.at[obsid, 'jobid']) == False:
            continue

        # If it is a failed observation, skip.
        if row['status'] == 'Failed':
            continue

        report.updateObs(reportCsv, obsid, 'status', '')

        # IF attempt field is empty, treat it as 0.
        reportDF['attempts'] = reportDF['attempts'].fillna(0)
        # If < 3 attempts, create the new symlink.
        if int(reportDF.at[obsid, 'attempts']) < 3 and count < numberObs:
            os.symlink(asvoObsPath, obsPath)
            report.updateObs(reportCsv, obsid, 'status', 'Initiated')
            count = count + 1

        if int(reportDF.at[obsid, 'attempts']) >= 3:
            report.updateObs(reportCsv, obsid, 'status', 'Failed')

    print('Created ' + str(count) + ' symlinks.')


# Verbose output for the verify method.
# For check status, silently update the spreadsheet.
if action == 'verify' or action == 'status':
    print('Loading ' + reportCsv)
    reportDF = pd.read_csv(reportCsv, dtype=str)
    reportDF.set_index('obsid', inplace=True)

    # if 'status' not in reportDF.columns:
    #     reportDF['status'] = ''
    # if 'calibration' not in reportDF.columns:
    #     reportDF['calibration'] = ''
    # if 'image' not in reportDF.columns:
    #     reportDF['image'] = ''
    # if 'postImage_0000' not in reportDF.columns:
    #     reportDF['postImage_0000'] = ''
    # if 'postImage_0001' not in reportDF.columns:
    #     reportDF['postImage_0001'] = ''
    # if 'jobid' not in reportDF.columns:
    #     reportDF['jobid'] = ''
    # if 'postImage_0002' not in reportDF.columns:
    #     reportDF['postImage_0002'] = ''
    # if 'postImage_0003' not in reportDF.columns:
    #     reportDF['postImage_0003'] = ''
    # if 'postImage_MFS' not in reportDF.columns:
    #     reportDF['postImage_MFS'] = ''


    quietMode = False
    if action == 'status':
        quietMode = True

    apiKey = os.getenv('MWA_ASVO_API_KEY')
    # If the API key is set, check if any new downloads have been completed.
    if apiKey != None:
        print('Downloading ASVO Job Information.')
        session = Session.login('1', 'asvo.mwatelescope.org', '443', apiKey)
        jobList = session.get_jobs()

        for job in jobList:
            obsID = job['row']['job_params']['obs_id']
            jobID = job['row']['id']
            jobState = job['row']['job_state']
            if obsID in reportDF.index:
                report.updateObs(reportCsv, obsID, 'jobid', jobID, quiet=quietMode)

                if jobState != 'completed':
                    report.updateObs(reportCsv, obsID, 'job_status', f'{jobState}', quiet=quietMode)
                if jobState == 'completed':
                    # Ensure the mesaurement set data is there and complete and mark as downloaded if it is.
                    if reportDF.at[obsID, 'job_status'] != 'Downloaded':
                        if verifyDownload(obsID, jobID, quietMode) == True:
                            report.updateObs(reportCsv, obsID, 'job_status', 'Downloaded', quiet=quietMode)
                        else:
                            report.updateObs(reportCsv, obsID, 'job_status', 'Download Error', quiet=quietMode)
    

    # Filter the reportDF to remove any bad observations.
    processingStarted = False
    if 'calibration' in reportDF.columns:
        reportDF = reportDF[reportDF['calibration'] == 'Success']
        processingStarted = True
    if 'image' in reportDF.columns:
        reportDF = reportDF[reportDF['image'] == 'Success']
    if 'postImage_0000' in reportDF.columns:
        reportDF = reportDF[reportDF['postImage_0000'] == 'Success']
    if 'postImage_0001' in reportDF.columns:
        reportDF = reportDF[reportDF['postImage_0001'] == 'Success']
    if 'postImage_0002' in reportDF.columns:
        reportDF = reportDF[reportDF['postImage_0002'] == 'Success']
    if 'postImage_0003' in reportDF.columns:
        reportDF = reportDF[reportDF['postImage_0003'] == 'Success']
    if 'postImage_MFS' in reportDF.columns:
        reportDF = reportDF[reportDF['postImage_MFS'] == 'Success']
    if 'status' in reportDF.columns:
        reportDF = reportDF[reportDF['status'] != 'Success']


    if not quietMode:
        print('Validating ' + str(len(reportDF.index)) + ' observations.')


    if processingStarted:
        count = 0
        for obsid, row in reportDF.iterrows():
            missing = False

            # Check to ensure the files for the subchans have been published as reported.
            #for subchan in ['0000', '0001', '0002', '0003', 'MFS']:for subchan in ['0000', '0001', '0002', '0003', 'MFS']:
            for subchan in ['MFS']:
                reportObsDir = row['obsDir']
                # If the observation directory entry is missing, try the oneb in the nextflow.config.
                if pd.isna(reportObsDir):
                    reportObsDir = obsDir
                    report.updateObs(reportCsv, obsid, 'obsDir', obsDir, quiet=quietMode)

                file = f'{reportObsDir}/{obsid}/{obsid}_deep-{subchan}-image-pb_warp_scaled.fits'
                if not os.path.exists(file):
                    missing = True
                    break
            
            # If any subchan for obsid missing, Clear the report entry (updating error count), delete the folder, recreate symlink if erorr count < 3.
            if missing == False:
                report.updateObs(reportCsv, obsid, 'status', 'Success', quiet=quietMode)
            else:
                report.updateObs(reportCsv, obsid, 'status', 'Missing Data', quiet=quietMode)

        if not quietMode:
            print('Found ' + str(count) + ' errors.')


if action == 'status':
    reportDF = pd.read_csv(reportCsv, dtype=str)
    reportDF.set_index('obsid', inplace=True)

    if 'status' not in reportDF.columns:
        reportDF['status'] = ''

    # Count of: Total observations, jobs needing to be downloaded, submitted/queued/processing jobs, completed jobs, obs processed, obs queued/running, obs failed, obs successful.
    totalObs = len(reportDF.index)

    jobsNotDownloaded = len(reportDF[pd.isnull(reportDF['jobid'])].index)
    jobsSubmitted = len(reportDF[pd.notnull(reportDF['job_status']) & (reportDF['job_status'] != 'Downloaded') & (reportDF['job_status'] != 'Missing Data')].index)
    jobsErrors = len(reportDF[reportDF['job_status'] == 'Missing Data'].index)
    jobsDownloaded = len(reportDF[reportDF['job_status'] == 'Downloaded'].index)
    obsProcessed = len(reportDF[pd.notnull(reportDF['status']) | reportDF['status'] == ''].index)

    obsQueued = len(reportDF[reportDF['status'] == 'Queued'].index)
    obsFailed = len(reportDF[reportDF['status'] == 'Failed'].index)
    obsMissing = len(reportDF[reportDF['status'] == 'Missing Data'].index)
    obsReady = len(reportDF[(reportDF['status'] != 'Success') & (reportDF['status'] != 'Failed') & (reportDF['job_status'] == 'Downloaded')].index)
    obsSuccess = len(reportDF[reportDF['status'] == 'Success'].index)

    print(f'DIP Status: {reportCsv}\n')
    print(f'Total Observations: {totalObs}\n')

    print(f'ASVO Jobs Requiring Download: {jobsNotDownloaded}')
    print(f'ASVO Jobs Queued: {jobsSubmitted}')
    print(f'ASVO Jobs Download Errors: {jobsErrors}')
    print(f'ASVO Jobs Downloaded Successfully: {jobsDownloaded}\n')

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

    # Create a list of Obs IDs with jobs currently submitted.
    obsIDList = []
    for job in jobList:
        obsIDList.append(job['row']['job_params']['obs_id'])

    print('Loading ' + reportCsv)
    reportDF = pd.read_csv(reportCsv, dtype=str)
    reportDF.set_index('obsid', inplace=True)

    # Check to ensure columns required exist, if not, create them.
    if 'jobid' not in reportDF.columns:
        reportDF['jobid'] = ''
    if 'job_status' not in reportDF.columns:
        reportDF['job_status'] = ''

    # Check how many observations are currently being downloaded.
    jobsSubmitted = len(reportDF[pd.notnull(reportDF['job_status']) & (reportDF['job_status'] != '') & (reportDF['job_status'] != 'Downloaded') & (reportDF['job_status'] != 'Missing Data')].index)
    maxObs = numberObs
    numberObs = numberObs - jobsSubmitted

    # If already downloading the max number, quit.
    if numberObs < 1:
        print(f'Maximum number of concurrent downloads already submitted: {maxObs}')
        exit()

    # Filter for only obs left to download.
    reportDF = reportDF[pd.isnull(reportDF['jobid']) | (reportDF['job_status'] == '') | (reportDF['job_status'] == 'Missing Data')]
    print(f'Total observations left to download: {len(reportDF.index)}')
    print(f'Queueing a maximum of {numberObs} observations.')

    params = dict()
    params['avg_time_res'] = '4'
    params['avg_freq_res'] = '40'
    params['flag_edge_width'] = '80'
    params['output'] = 'ms'
    params['delivery'] = 'scratch'

    count = 0
    for obsID, row in reportDF.iterrows():
        # Check if a job already exists for the Obs ID, if so skip it.
        if obsID in obsIDList:
            continue

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

        # If the maximum number of jobs have been reached, break.
        if count >= numberObs:
            break

    print(f'Submitted {count} observations.')

