#!/usr/bin/env python3

import os
import sys
import pandas as pd

sampleSize = 0

if len(sys.argv) != 2:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

beamFile = sys.argv[1]

# Read the beamlog, space separated with # escape character on first two lines.
# First line is the header, the seocnd line is the units which can be ignored.
beamInfo = pd.read_csv(beamFile, delim_whitespace=True, escapechar='#')
beamInfo.columns = beamInfo.columns.str.strip()

# Get info from the first real record, the second line.
bmaj = float(beamInfo['Target BMAJ'].iloc[1]) * 3600 # Convert from degrees to arcsec.
bmin = float(beamInfo['Target BMIN'].iloc[1]) * 3600 # Convert from degrees to arcsec.
bpa = beamInfo['Target BPA'].iloc[1]

finalBeam = pd.DataFrame([[bmaj, bmin, bpa]], columns=[['bmaj', 'bmin', 'bpa']])
finalBeam.to_csv('beaminfo.csv', index=False)

print('BMAJ: ' + str(bmaj))
print('BMIN: ' + str(bmin))
print('BPA: ' + str(bpa))
