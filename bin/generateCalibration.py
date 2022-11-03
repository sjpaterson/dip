#!/usr/bin/env python3

import os
import sys
#import wget
import subprocess
import gleamx.crop_catalogue as cc
import gleamx.vo2model as vo2m
import gleamx.aocal_diff as aocal_diff
import gleamx.aocal_phaseref as aocal_phaseref
import gleamx.calc_optimum_pointing as optPointing
import gleamx.check_assign_solutions as checkSolutions

from astropy.io import fits


if len(sys.argv) != 3:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

projectdir = sys.argv[1]
obsid = sys.argv[2]

# Define relavant file names and paths.
metafits = obsid + '.metafits'
catGGSM = os.path.join(projectdir, 'models/GGSM.fits')
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

    argts = ' -t ' + str(ts)
    arg1  = ' -j ' + str(cores)
    arg2  = ' -absmem ' + str(mem)
    arg3  = ' -m "' + calibrationModel + '"'
    arg4  = ' -minuv ' + str(minuvm)
    arg5  = ' -maxuv ' + str(maxuvm)
    arg6  = ' -applybeam -mwa-path "' + os.path.join(projectdir, 'beamdata') + '"'
    arg7  = ' "' + localMeasurementSet + '" "' + solution + '"'

    if ts == None:
        calibrateCmd = 'calibrate ' + arg1 + arg2 + arg3 + arg4 + arg5 + arg6 + arg7
    else:
        calibrateCmd = 'calibrate ' + argts + arg1 + arg2 + arg3 + arg4 + arg5 + arg6 + arg7

    subprocess.run(calibrateCmd, shell=True, check=True)


# Run the aocal_plot.py script from the mwa-calplots GitHub project.
# https://github.com/MWATelescope/mwa-calplots
def aocal_plot(solution, localRefant):
    plotCmd = 'aocal_plot.py --refant=' + str(localRefant) + ' --amp_max=2 "' + solution + '"'
    subprocess.run(plotCmd, shell=True, check=True)



# Check to see if the metafits file has been downloaded, if not, download it.
# Would prefer to use the wget library, but must wait until new container is made.
if not os.path.exists(metafits):
    # wget.download('http://ws.mwatelescope.org/metadata/fits?obs_id=' + obsid, metafits)
    metaDownload = subprocess.run('wget -O "' + metafits + '" http://ws.mwatelescope.org/metadata/fits?obs_id=' + obsid, shell=True)
    # The above creates a 0b file if it fails, need to remove this before erroring out.
    if metaDownload.returncode != 0:
        subprocess.run('rm "' + metafits + '"', shell=True)
        exit(-1)



# Import header information from the metafits file.
metaHdu = fits.open(metafits)
metadata = metaHdu[0].header
metaHdu.close()

# Crop the GGSM catalogue to the 250 brightest sources near the pointing location and bulld the calibration model from them.
cc.run(ra=metadata['RA'], dec=metadata['DEC'], radius=30, top_bright=250, metafits=metafits, cat=catGGSM, fluxcol='S_200', plotFile=obsid + '_local_gleam_model.png', output=catCropped)
vo2m.run(catalogue=catCropped, point=True, output=calibrationModel, racol='RAJ2000', decol='DEJ2000', acol='a', bcol='b', pacol='pa', fluxcol='S_200', alphacol='alpha')


# Check whether the phase centre has already changed
# Calibration will fail if it has, so measurement set must be shifted back to its original position
chgcentreResult = subprocess.run('chgcentre ' + measurementSet, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
if 'shift' in chgcentreResult.stdout.decode('utf-8'):
    coords = optPointing.calc_peak_beam(metafits)
    subprocess.run('chgcentre ' + measurementSet + ' ' + coords, shell=True, check=True)


# Ionospheric triage.
ts = 10  # Interval for ionospheric triage (in time steps).
solution = obsid + '_local_gleam_model_solutions_ts' + str(ts) + '.bin'
calibrate(measurementSet, solution, ts)
aocal_plot(solution, refant)
aocal_diff.run(solution, obsid, metafits=metafits, refant=refant)


# Assume the ionosphere is ok and derive a calibration solution.
solution = obsid + '_local_gleam_model_solutions_initial.bin'
solutionRef = obsid + '_local_gleam_model_solutions_initial_ref.bin'
calibrate(measurementSet, solution)
# Create a version divided through by the reference antenna, so that all observations have the same relative XY phase, allowing polarisation calibration solutions to be transferred.
# This also sets the cross-terms to zero by default.
aocal_phaseref.run(solution, solutionRef, refant, xy=-2.806338586067941065e+01, dxy=-4.426533296449057023e-07, ms=measurementSet)
aocal_plot(solutionRef, refant)


# Test to see if the calibration solution meets minimum quality control. This is a simple check based on the number of flagged solutions.
if not checkSolutions.check_solutions(aofile=solutionRef):
    print('Solution Failed') 
    subprocess.run('mv "' + solutionRef + '" "' + obsid + '_local_gleam_model_solutions_initial_ref_failed.bin"', shell=True)
    exit(-1)

