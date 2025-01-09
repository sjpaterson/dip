import os
import sys
import time
import fcntl
import pandas as pd

def updateObs(reportFile, obsid, action, val, quiet=False):
    obsid = str(obsid)
    obsid = obsid[0:10]

    # Create a lock file in the same directory as the report.
    lockFile = os.path.join(os.path.dirname(reportFile), '.lock')

    # Attempt to obtain exclusive access to the report every 5 seconds for 10 minutes.
    reportUpdated = False
    if not quiet:
        print('Updating Report.\nObsID: ' + str(obsid) + ' - Action: ' + str(action) + ' - Value: ' + str(val))
    for i in range(120):
        try:
            with open(lockFile, 'w') as filelock:
                # Set the file lock.
                fcntl.flock(filelock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Open and update the report.
                report = pd.read_csv(reportFile, dtype=str)
                #report.index = report.index.map(str)
                report['obsid'] = report['obsid'].apply(str)
                report['obsid'] = report['obsid'].str.slice(0,10)
                report.set_index('obsid', inplace=True)

                # Check to ensure the column exists, if not, create it.
                if action not in report.columns:
                    report['action'] = ''
                    
                report.loc[obsid, action] = val
                report.to_csv(reportFile)
                reportUpdated = True
                break
        except:
            time.sleep(5) 

    if (reportUpdated == False):
        print('Report Update Unsuccessful.')



def startObs(reportFile, obsid, obsDir):
    obsid = str(obsid)
    obsid = obsid[0:10]

    # Create a lock file in the same directory as the report.
    lockFile = os.path.join(os.path.dirname(reportFile), '.lock')

    # Attempt to obtain exclusive access to the report every 5 seconds for 10 minutes.
    reportUpdated = False
    print('Clearing Report Line for ObsID: ' + str(obsid))
    for i in range(120):
        try:
            with open(lockFile, 'w') as filelock:
                # Set the file lock.
                fcntl.flock(filelock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Open and update the report.
                report = pd.read_csv(reportFile, dtype=str)
                #report.index = report.index.map(str)
                report['obsid'] = report['obsid'].apply(str)
                report['obsid'] = report['obsid'].str.slice(0,10)
                report.set_index('obsid', inplace=True)
                
                report.loc[obsid, 'status'] = 'Queued'
                report.loc[obsid, 'generateCalibration'] = 'Queued'
                report.loc[obsid, 'applyCalibration'] = 'Queued'
                report.loc[obsid, 'flagUV'] = 'Queued'
                report.loc[obsid, 'uvSub'] = 'Queued'
                report.loc[obsid, 'image'] = 'Queued'
                report.loc[obsid, 'postImage_0000'] = 'Queued'
                report.loc[obsid, 'postImage_0001'] = 'Queued'
                report.loc[obsid, 'postImage_0002'] = 'Queued'
                report.loc[obsid, 'postImage_0003'] = 'Queued'
                report.loc[obsid, 'postImage_MFS'] = 'Queued'
                report.loc[obsid, 'beamsize'] = ''
                report.loc[obsid, 'uvSub_SourceCount'] = ''
                report.loc[obsid, 'sourcecount_0000'] = ''
                report.loc[obsid, 'sourcecount_0001'] = ''
                report.loc[obsid, 'sourcecount_0002'] = ''
                report.loc[obsid, 'sourcecount_0003'] = ''
                report.loc[obsid, 'sourcecount_MFS'] = ''
                report.loc[obsid, 'coord_rms_0000'] = ''
                report.loc[obsid, 'coord_rms_0001'] = ''
                report.loc[obsid, 'coord_rms_0002'] = ''
                report.loc[obsid, 'coord_rms_0003'] = ''
                report.loc[obsid, 'coord_rms_MFS'] = ''
                report.loc[obsid, 'rms_0000'] = ''
                report.loc[obsid, 'rms_0001'] = ''
                report.loc[obsid, 'rms_0002'] = ''
                report.loc[obsid, 'rms_0003'] = ''
                report.loc[obsid, 'rms_MFS'] = ''
                report.loc[obsid, 'obsDir'] = obsDir

                if pd.isna(report.loc[obsid, 'attempts']) or report.loc[obsid, 'attempts'] == '':
                    report.loc[obsid, 'attempts'] = 0
                report.loc[obsid, 'attempts'] = int(report.loc[obsid, 'attempts']) + 1
                report.to_csv(reportFile)
                reportUpdated = True
                break
        except:
            time.sleep(5) 

    if (reportUpdated == False):
        print('Report Update Unsuccessful.')

