#!/usr/bin/env python3

from enum import Flag
import os
import sys
import wget
import report
import flagTiles
import subprocess
import gleamx.crop_catalogue as cc
import gleamx.vo2model as vo2m
import gleamx.aocal_diff as aocal_diff
import gleamx.aocal_phaseref as aocal_phaseref
import gleamx.calc_optimum_pointing as optPointing
import gleamx.check_assign_solutions as checkSolutions
import gleamx.ms_flag_by_uvdist as flagUV

from astropy.io import fits
from calplots import aocal, aocal_plot


if len(sys.argv) != 4:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

projectdir = sys.argv[1]
obsid = sys.argv[2]
reportCsv = sys.argv[3]

# Define relavant file names and paths.
metafits = obsid + '.metafits'
catGGSM = os.path.join(projectdir, 'models/GGSM_updated.fits')
catCropped = obsid + '_cropped_catalogue.fits'
calibrationModel = obsid + '_local_gleam_model.txt'
measurementSet = obsid + '.ms'

# Set reference antenna.
if int(obsid) > 1342950000:
    refant = 8
elif int(obsid) > 1300000000:
    refant = 0
else:
    refant = 127

# Calibration Shell
def calibrate(localMeasurementSet, solution, ts=None):
    # Processing options.
    cores = 48  # Number of cores to use.
    mem   = 50  # Amount of memory to use.
    minuv = 75  # Minimum baseline of 75 lambda (=250m at 88 MHz) for calibration.

    minuvm = 234 * minuv / int(metadata['CENTCHAN'])
    maxuvm = 390000 / (int(metadata['CENTCHAN']) + 11)

    argts = f'-t {ts}'
    args = f'''-j {cores} \
        -absmem {mem} \
        -m "{calibrationModel}" \
        -minuv {minuvm} \
        -maxuv {maxuvm} \
        -applybeam \
        -mwa-path "{os.path.join(projectdir, 'beamdata')}" \
        "{localMeasurementSet}" \
        "{solution}"'''

    if ts == None:
        calibrateCmd = f'calibrate {args}'
    else:
        calibrateCmd = f'calibrate {argts} {args}'

    subprocess.run(calibrateCmd, shell=True, check=True)
    print(calibrateCmd)



# Check to see if the metafits file has been downloaded, if not, download it.
if not os.path.exists(metafits):
    wget.download('http://ws.mwatelescope.org/metadata/fits?obs_id=' + obsid, metafits)
    

# Import header information from the metafits file.
metaHdu = fits.open(metafits)
metadata = metaHdu[0].header
metaHdu.close()


# Flag any previously recorded bad tiles.
knownBadTiles = flagTiles.findBadTiles(obsid, projectdir)
if len(knownBadTiles) > 0:
    subprocess.run(f'flagantennae {measurementSet} {knownBadTiles}', shell=True, check=True)
    report.updateObs(reportCsv, obsid, 'flagged', knownBadTiles)

# If more than 50 bad tiles, fail the processing,
if knownBadTiles.count(' ') >= 49:
    report.updateObs(reportCsv, obsid, 'calibration', 'Fail - Too Many Bad Tiles.')
    report.updateObs(reportCsv, obsid, 'status', 'Failed')
    exit(-1)


# Crop the GGSM catalogue to the 250 brightest sources near the pointing location and bulld the calibration model from them.
cc.run(ra=metadata['RA'], dec=metadata['DEC'], radius=30, top_bright=250, metafits=metafits, cat=catGGSM, fluxcol='S_200', plotFile=obsid + '_local_gleam_model.png', output=catCropped)
vo2m.run(catalogue=catCropped, point=True, output=calibrationModel, racol='RAJ2000', decol='DEJ2000', acol='a', bcol='b', pacol='pa', fluxcol='S_200', alphacol='alpha')


# Ionospheric triage.
ts = 10  # Interval for ionospheric triage (in time steps).
solution = obsid + '_local_gleam_model_solutions_ts' + str(ts) + '.bin'
calibrate(measurementSet, solution, ts)
#aocal_plot(solution, refant)
plotFilename = solution[:-4]
ao = aocal.fromfile(solution)
aocal_plot.plot(ao, plotFilename, refant=refant, amp_max=2, testTiles=False)
aocal_diff.run(solution, obsid, metafits=metafits, refant=refant)


# Assume the ionosphere is ok and derive a calibration solution.
solution = obsid + '_local_gleam_model_solutions_initial.bin'
solutionRef = obsid + '_local_gleam_model_solutions_initial_ref.bin'
calibrate(measurementSet, solution)
# Create a version divided through by the reference antenna, so that all observations have the same relative XY phase, allowing polarisation calibration solutions to be transferred.
# This also sets the cross-terms to zero by default.
aocal_phaseref.run(solution, solutionRef, refant, xy=-2.806338586067941065e+01, dxy=-4.426533296449057023e-07, ms=measurementSet)
#aocal_plot(solutionRef, refant)
plotFilename = solutionRef[:-4]
ao = aocal.fromfile(solutionRef)
badTiles = aocal_plot.plot(ao, plotFilename, refant=refant, amp_max=2)

# Report all tiles flagged.
badTilesStr = ' '.join(map(str, badTiles))
allBadTiles = f'{badTilesStr} {knownBadTiles}'
report.updateObs(reportCsv, obsid, 'flagged', allBadTiles.strip())

# Flag any bad tiles detected.
if len(badTiles) > 0:
    # Flag the tiles for the rest of the night.
    flagTiles.flagNight(obsid, projectdir, badTiles)
    # Flag the bad tiles for this observation.
    subprocess.run(f'flagantennae {measurementSet} {badTilesStr}', shell=True, check=True)
    
    # Recalibrate
    calibrate(measurementSet, solution)
    aocal_phaseref.run(solution, solutionRef, refant, xy=-2.806338586067941065e+01, dxy=-4.426533296449057023e-07, ms=measurementSet)
    plotFilename = solutionRef[:-4] + '_recal'
    ao = aocal.fromfile(solutionRef)
    badTiles = aocal_plot.plot(ao, plotFilename, refant=refant, amp_max=2)


# Test to see if the calibration solution meets minimum quality control. This is a simple check based on the number of flagged solutions.
if not checkSolutions.check_solutions(aofile=solutionRef):
    print('Solution Failed') 
    subprocess.run('mv "' + solutionRef + '" "' + obsid + '_local_gleam_model_solutions_initial_ref_failed.bin"', shell=True)
    report.updateObs(reportCsv, obsid, 'calibration', 'Fail - Solution does not meet min quality.')
    report.updateObs(reportCsv, obsid, 'status', 'Failed')
    exit(-1)

# Apply the solution
subprocess.run(f'applysolutions -nocopy "{measurementSet}" "{solutionRef}"', shell=True, check=True)

# Flag by UV dist.
flagUV.run(measurementSet, 'DATA', apply=True)

report.updateObs(reportCsv, obsid, 'calibration', 'Success')