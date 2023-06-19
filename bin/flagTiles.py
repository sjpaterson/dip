#!/usr/bin/env python3

import os
import sys
import report
import subprocess

if len(sys.argv) != 4:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

projectdir = sys.argv[1]
obsid = int(sys.argv[2])
reportCsv = sys.argv[3]

# Define relavant file names and paths.
measurementSet = f'{obsid}.ms'

flags = ''

# Many antennae issues in this range, for now don't process, will look into including later.
if (obsid >= 1272277982) and (obsid <= 1272286862):
    print('Major Antennae Error')
    report.updateObs(reportCsv, obsid, 'flagged', 'Major Antennae Error')
    report.updateObs(reportCsv, obsid, 'status', 'Failed')
    exit(-1)

if (obsid >= 1272450752) and (obsid <= 1272546032):
    flags = '85'

if (obsid >= 1272623552) and (obsid <= 1272805232):
    flags = '35 36 85'

if (obsid >= 1272882752) and (obsid <= 1272888872):
    flags = '35 36'

if (obsid >= 1273833152) and (obsid <= 1274441462):
    flags = '47 48 49 50 51 52 53 54'

if (obsid >= 1274869982) and (obsid <= 1275303662):
    flags = '50 108'


if flags != '':
    subprocess.run(f'flagantennae {measurementSet} {flags}', shell=True, check=True)

report.updateObs(reportCsv, obsid, 'flagged', flags)
