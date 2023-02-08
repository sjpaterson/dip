import os
import sys
import time
import fcntl
import pandas as pd

def updateObs(reportFile, obsid, action, val):
    obsid = str(obsid)

    # Attempt to obtain exclusive access to the report every 10 seconds for 5 minutes.
    for i in range(30):
        try:
            with open('.lock', 'w') as filelock:
                # Set the file lock.
                fcntl.flock(filelock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Open and update the report.
                report = pd.read_csv(reportFile, dtype=str, index_col='obsid')
                report.index = report.index.map(str)
                report.loc[obsid, action] = val
                report.to_csv(reportFile)
                break
        except:
            time.sleep(10) 
