#!/usr/bin/env python3

import os
import sys
import pandas as pd

sampleSize = 0

if len(sys.argv) != 3:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

beamLog = sys.argv[1]
beamCsvFile = sys.argv[2]

# Read the beamlog, space separated with # escape character on first two lines.
# First line is the header, the seocnd line is the units which can be ignored.
beamInfo = pd.read_csv(beamLog, delim_whitespace=True, escapechar='#')
beamInfo.columns = beamInfo.columns.str.strip()

# Read the beam csv used for the workflow.
beamCsv = pd.read_csv(beamCsvFile, index_col='obsid')

# Get info from the first real record, the second line.
bmaj = float(beamInfo['Target BMAJ'].iloc[1]) * 3600 # Convert from degrees to arcsec.
bmin = float(beamInfo['Target BMIN'].iloc[1]) * 3600 # Convert from degrees to arcsec.
bpa = beamInfo['Target BPA'].iloc[1]

# Record the target beamsize in the csv to be used by the workflow.
beamCsv['bmaj'] = bmaj
beamCsv['bmin'] = bmin
beamCsv['bpa'] = bpa

beamCsv.to_csv('beaminfo.csv', index=True)

print('BMAJ: ' + str(bmaj))
print('BMIN: ' + str(bmin))
print('BPA: ' + str(bpa))
