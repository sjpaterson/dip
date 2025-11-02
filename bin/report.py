import os
import sys
import time
import fcntl
import pandas as pd

def clearLock(lockFile):
    with open(lockFile, 'w+') as filelock:
        filelock.write('Available')

def setLock(lockFile, obsid):
    if not os.path.exists(lockFile):
        clearLock(lockFile)
    with open(lockFile, 'r') as filelock:
        contents = filelock.read()
    if contents == 'Available':
        with open(lockFile, 'w') as filelock:
            filelock.write(f'{obsid}')
        return True
    else:
        return False

def checkLock(lockFile, obsid):
    with open(lockFile, 'r') as filelock:
        contents = filelock.read()
    if contents == obsid:
        return True
    else:
        return False


def updateObs(reportFile, obsid, action, val, quiet=False):
    obsid = str(obsid)
    obsid = obsid[0:10]

    # Create a lock file in the same directory as the report.
    lockFile = os.path.join(os.path.dirname(reportFile), '.lock')

    # Attempt to obtain exclusive access to the report every 5 seconds for 10 minutes.
    reportUpdated = False
    if not quiet:
        print(f'Updating Report - ObsID: {obsid} - Action: {action} - Value: {val}')
    for i in range(120):
        if setLock(lockFile, obsid):
            if not checkLock(lockFile, obsid): # Check to make sure the lock is correct.
                continue
            # Open and update the report.
            #report = pd.read_csv(reportFile, dtype=str, index_col='obsid')
            report = pd.read_csv(reportFile, dtype=str)
            #report.index = report.index.map(str)
            report['obsid'] = report['obsid'].apply(str)
            report['obsid'] = report['obsid'].str.slice(0,10)
            report.set_index('obsid', inplace=True)

            # Check to ensure the column exists, if not, create it.
            if action not in report.columns:
                report[action] = ''
                
            report.at[obsid, action] = val
            report.to_csv(reportFile)
            reportUpdated = True
            clearLock(lockFile)
            break
        else:
            time.sleep(5) 

    if (reportUpdated == False):
        print('Report Update Unsuccessful.')


def startObs(reportFile, obsid, obsDir):
    obsid = str(obsid)
    obsid = obsid[0:10]

    report = pd.read_csv(reportFile, dtype=str)
    print('Successfully Opened and Read Report.')
    report['obsid'] = report['obsid'].apply(str)
    report['obsid'] = report['obsid'].str.slice(0,10)
    report.set_index('obsid', inplace=True)

    attempts = 0
    if 'attempts' in report.columns:
        attempts = int(report.at[obsid, 'attempts'])
    attempts += 1

    updateObs(reportFile, obsid, 'attemps', attempts)
    updateObs(reportFile, obsid, 'status', 'Queued')
    updateObs(reportFile, obsid, 'obsDir', obsDir)
    