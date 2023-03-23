#!/usr/bin/env python3

import os
import sys
import report


if len(sys.argv) != 4:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

reportCsv = sys.argv[1]
obsid = sys.argv[2]
obsDir = sys.argv[3]

# Check to ensure the obsid has not already been processed.
# IF it has not been processed, it will be a symoblic link.
if not os.path.islink(os.path.join(obsDir, obsid)):
    print(obsid + ' has already been processed.')
    exit(-1)

# Hasn't been processed, clear the entry in the report for the obsid.
report.startObs(reportCsv, obsid, obsDir)
