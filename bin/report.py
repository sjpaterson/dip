import os
import sys
import time
import fcntl
import pandas as pd

def updateObs(reportFile, obsid, action, val):
    obsid = str(obsid)

    # Create a lock file in the same directory as the report.
    lockFile = os.path.join(os.path.dirname(reportFile), '.lock')

    # Attempt to obtain exclusive access to the report every 5 seconds for 10 minutes.
    reportUpdated = False
    print('Updating Report.\nObsID: ' + str(obsid) + ' - Action: ' + str(action) + ' - Value: ' + str(val))
    for i in range(120):
        try:
            with open(lockFile, 'w') as filelock:
                # Set the file lock.
                fcntl.flock(filelock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Open and update the report.
                report = pd.read_csv(reportFile, dtype=str, index_col='obsid')
                report.index = report.index.map(str)
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
                report = pd.read_csv(reportFile, dtype=str, index_col='obsid')
                report.index = report.index.map(str)
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
                report.loc[obsid, 'sourcecount_0000'] = ''
                report.loc[obsid, 'sourcecount_0001'] = ''
                report.loc[obsid, 'sourcecount_0002'] = ''
                report.loc[obsid, 'sourcecount_0003'] = ''
                report.loc[obsid, 'sourcecount_MFS'] = ''
                report.loc[obsid, 'rms_0000'] = ''
                report.loc[obsid, 'rms_0001'] = ''
                report.loc[obsid, 'rms_0002'] = ''
                report.loc[obsid, 'rms_0003'] = ''
                report.loc[obsid, 'rms_MFS'] = ''
                report.loc[obsid, 'obsDir'] = obsDir
                report.to_csv(reportFile)
                reportUpdated = True
                break
        except:
            time.sleep(5) 

    if (reportUpdated == False):
        print('Report Update Unsuccessful.')    