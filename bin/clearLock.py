#!/usr/bin/env python3

import os
import report


configFile = 'nextflow.config'
reportCsv = ''
obsDir = ''
with open(configFile) as f:
    for line in f:
        if 'reportCsv=' in line.replace(' ', ''):
            reportCsv = line.split('=',1)[1].strip()
            reportCsv = reportCsv.replace('"', '')
            reportCsv = reportCsv.replace("'", "")
            reportCsv = os.path.expandvars(reportCsv)

if reportCsv == '':
    print('Error: Unable to find the data entries in the nextflow.config.')
    exit()

lockFile = os.path.join(os.path.dirname(reportCsv), '.lock')

report.clearLock(lockFile)
print('Cleared Lock File')
