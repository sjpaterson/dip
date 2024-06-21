#!/usr/bin/env python3

import sys
import report


if len(sys.argv) != 5:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

reportCsv = sys.argv[1]
obsid = sys.argv[2]
action = sys.argv[3]
val = sys.argv[4]

report.updateObs(reportCsv, obsid, action, val)
