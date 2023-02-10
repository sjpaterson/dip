#!/usr/bin/env python3

import sys
import report


if len(sys.argv) != 4:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

reportCsv = sys.argv[1]
obsid = sys.argv[2]
obsDir = sys.argv[3]

report.startObs(reportCsv, obsid, obsDir)
