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
                    report[action] = ''
                    
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
                print('Successfully Opened and Read Report.')
                report['obsid'] = report['obsid'].apply(str)
                report['obsid'] = report['obsid'].str.slice(0,10)
                report.set_index('obsid', inplace=True)

                if 'attempts' not in report.columns:
                    report['attempts'] = 0
                if 'obsDir' not in report.columns:
                    report['obsDir'] = ''
                if 'status' not in report.columns:
                    report['status'] = ''
                
                # Quick ugly implementation to get the run going, to revisit and redo with a much nicer method.
                report.loc[obsid, 'status'] = 'Queued'
                if 'generateCalibration' in report.columns:
                    report.loc[obsid, 'generateCalibration'] = 'Queued'
                if 'applyCalibration' in report.columns:
                    report.loc[obsid, 'applyCalibration'] = 'Queued'
                if 'flagUV' in report.columns:
                    report.loc[obsid, 'flagUV'] = 'Queued'
                if 'uvSub' in report.columns:
                    report.loc[obsid, 'uvSub'] = 'Queued'
                if 'image' in report.columns:
                    report.loc[obsid, 'image'] = 'Queued'
                if 'postImage_0000' in report.columns:
                    report.loc[obsid, 'postImage_0000'] = 'Queued'
                if 'postImage_0001' in report.columns:
                    report.loc[obsid, 'postImage_0001'] = 'Queued'
                if 'postImage_0002' in report.columns:
                    report.loc[obsid, 'postImage_0002'] = 'Queued'
                if 'postImage_0003' in report.columns:
                    report.loc[obsid, 'postImage_0003'] = 'Queued'
                if 'postImage_MFS' in report.columns:
                    report.loc[obsid, 'postImage_MFS'] = 'Queued'
                if 'beamsize' in report.columns:
                    report.loc[obsid, 'beamsize'] = ''
                if 'uvSub_SourceCount' in report.columns:
                    report.loc[obsid, 'uvSub_SourceCount'] = ''
                if 'sourcecount_0000' in report.columns:
                    report.loc[obsid, 'sourcecount_0000'] = ''
                if 'sourcecount_0001' in report.columns:
                    report.loc[obsid, 'sourcecount_0001'] = ''
                if 'sourcecount_0002' in report.columns:
                    report.loc[obsid, 'sourcecount_0002'] = ''
                if 'sourcecount_0003' in report.columns:
                    report.loc[obsid, 'sourcecount_0003'] = ''
                if 'sourcecount_MFS' in report.columns:
                    report.loc[obsid, 'sourcecount_MFS'] = ''
                if 'coord_rms_0000' in report.columns:
                    report.loc[obsid, 'coord_rms_0000'] = ''
                if 'coord_rms_0001' in report.columns:
                    report.loc[obsid, 'coord_rms_0001'] = ''
                if 'coord_rms_0002' in report.columns:
                    report.loc[obsid, 'coord_rms_0002'] = ''
                if 'coord_rms_0003' in report.columns:
                    report.loc[obsid, 'coord_rms_0003'] = ''
                if 'coord_rms_MFS' in report.columns:
                    report.loc[obsid, 'coord_rms_MFS'] = ''
                if 'rms_0000' in report.columns:
                    report.loc[obsid, 'rms_0000'] = ''
                if 'rms_0001' in report.columns:
                    report.loc[obsid, 'rms_0001'] = ''
                if 'rms_0002' in report.columns:
                    report.loc[obsid, 'rms_0002'] = ''
                if 'rms_0003' in report.columns:
                    report.loc[obsid, 'rms_0003'] = ''
                if 'rms_MFS' in report.columns:
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

