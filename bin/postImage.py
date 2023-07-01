#!/usr/bin/env python3

import os
import sys
import rms
import beam
import shutil
import report
import catCalcs
import subprocess
import astropy.units as u
import gleamx.mask_image as mask_image
import gleamx.generate_weight_map as gwm
from astropy.io import fits
from astropy.coordinates import SkyCoord


if len(sys.argv) != 7:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

projectdir = sys.argv[1]
obsid = sys.argv[2]
subchan = sys.argv[3]
reportCsv = sys.argv[4]
ra = float(sys.argv[5])
dec = float(sys.argv[6])


# Define relavant file names and paths.
filePrefix = obsid + '_deep-' + subchan
obsFiles = dict(
    # Metafits file and measurement set.
    metafits = obsid + '.metafits',
    measurementSet = obsid + '.ms',
    # Linear polarizations produced by WSCLEAN.
    xx = filePrefix + '-XX-image.fits',
    yy = filePrefix + '-YY-image.fits',
    xx_rms = filePrefix + '-XX-image_rms.fits',
    yy_rms = filePrefix + '-YY-image_rms.fits',
    # Linear polarizations with primary beam applied.
    xx_pb = filePrefix + '-XX-image-pb.fits',
    yy_pb = filePrefix + '-YY-image-pb.fits',
    # Stokes I conversion from linear polarizations with pb appleid.
    ipb = filePrefix + '-image-pb.fits',
    ipb_rms = filePrefix + '-image-pb_rms.fits',
    ipb_bkg = filePrefix + '-image-pb_bkg.fits',
    ipb_warp = filePrefix + '-image-pb_warp.fits',
    ipb_warp_rms = filePrefix + '-image-pb_warp_rms.fits',
    ipb_warp_bkg = filePrefix + '-image-pb_warp_bkg.fits',
    # Primary beam information.
    beam_xx = filePrefix + '-XX-beam.fits',
    beam_yy = filePrefix + '-YY-beam.fits',
    # Additional operations perfromed on Stokes I with PB applied.
    ipb_mask = filePrefix + '-image-pb_mask.fits',
    ipb_orig = filePrefix + '-image-pb_original.fits',
    ipb_warp_weight = filePrefix + '-image-pb_warp_weight.fits',
    xm = obsid + '_' + subchan + '_complete_sources_xm.fits',
    xx_xm = obsid + '_' + subchan + '_complete_sources_xx_xm.fits',
    yy_xm = obsid + '_' + subchan + '_complete_sources_yy_xm.fits',
    # Source catalgoues.
    ipb_cat_corrected = filePrefix + '-image-pb_comp_warp-corrected.fits',
    xx_pb_cat = filePrefix + '-XX-image-pb_comp.fits',
    yy_pb_cat = filePrefix + '-YY-image-pb_comp.fits',
    ipb_cat = filePrefix + '-image-pb_comp.fits',
    ipb_warp_cat = filePrefix + '-image-pb_warp_comp.fits',
)


# Sky model
POS_MODEL_CATALOGUE = os.path.join(projectdir, 'models/NVSS_SUMSS_psfcal.fits')
FLUX_MODEL_CATALOGUE = os.path.join(projectdir, 'models/GGSM_sparse_unresolved.fits')

separation = 60 / 3600      # Max separation for flux_warp crossmatch as ~ 1' -- unlikely that the ionosphere would be that brutal.
exclusion = 180 / 3600      # Exclusion for flux_warp internal exclusive crossmatch as ~ 3'.
minsrcs = 500               # Minimum number of sources to accept for observation.
radius = 50                 # Radius to match sources to.

# Import header information from the metafits file.
with fits.open(obsFiles['metafits']) as metaHdu:
    metadata = metaHdu[0].header

# Channel information for creating the weight maps.
chans = metadata['CHANNELS'].split(',')
if subchan == 'MFS':
    chanStart = 0
    chanEnd = 23
else:
    n = int(subchan)
    chanStart = n * 6
    chanEnd = chanStart + 5

# Calculate the RMS for each polarization.
rmsEstXX = rms.estimateRMS(obsFiles['xx'])
rmsEstYY = rms.estimateRMS(obsFiles['yy'])
report.updateObs(reportCsv, obsid, 'rms_estimate_xx_' + subchan, rmsEstXX)
report.updateObs(reportCsv, obsid, 'rms_estimate_yy_' + subchan, rmsEstYY)
subprocess.run('BANE --cores 1 --compress --noclobber "' + obsFiles['xx'] + '"', shell=True, check=True)
subprocess.run('BANE --cores 1 --compress --noclobber "' + obsFiles['yy'] + '"', shell=True, check=True)
rmsXX = rms.calcRMS(obsFiles['xx_rms'])
rmsYY = rms.calcRMS(obsFiles['yy_rms'])
report.updateObs(reportCsv, obsid, 'rms_xx_' + subchan, rmsXX)
report.updateObs(reportCsv, obsid, 'rms_yy_' + subchan, rmsYY)

# Load beam data.
if not os.path.exists(obsFiles['beam_xx']) or not os.path.exists(obsFiles['beam_yy']):
    subprocess.run('lookup_beam.py ' + obsid + ' _deep-' + subchan + '-XX-image.fits ' + obsid + '_deep-' + subchan + '- -c ' + chans[chanStart] + '-' + chans[chanEnd] + ' --beam_path "' + os.path.join(projectdir, 'beamdata/gleam_xx_yy.hdf5') + '"', shell=True, check=True)

with fits.open(obsFiles['beam_xx']) as beamXXHdu:
    beamXX = beamXXHdu[0].data

with fits.open(obsFiles['beam_yy']) as beamYYHdu:
    beamYY = beamYYHdu[0].data

# Apply the primary beam to the linear polarizations.
with fits.open(obsFiles['xx']) as obsHdu:
    obsHdu[0].data = obsHdu[0].data / beamXX
    obsHdu.writeto(obsFiles['xx_pb'])

with fits.open(obsFiles['yy']) as obsHdu:
    obsHdu[0].data = obsHdu[0].data / beamYY
    obsHdu.writeto(obsFiles['yy_pb'])


# Find sources for each polization.
subprocess.run('aegean --autoload --table="' + obsFiles['xx_pb'] + '" "' + obsFiles['xx_pb'] + '"', shell=True, check=True)
subprocess.run('aegean --autoload --table="' + obsFiles['yy_pb'] + '" "' + obsFiles['yy_pb'] + '"', shell=True, check=True)
subprocess.run('match_catalogues "' + obsFiles['xx_pb_cat'] + '" "' + FLUX_MODEL_CATALOGUE + '" --separation "' + str(separation) + '" --exclusion_zone "' + str(exclusion) + '" --outname "' + obsFiles['xx_xm'] + '" --threshold 0.5 --nmax 1000 --coords ' + str(metadata['RA']) + ' ' + str(metadata['DEC']) + ' --radius "' + str(radius) + '" --ra2 "RAJ2000" --dec2 "DEJ2000" --ra1 "ra" --dec1 "dec" -F "int_flux" --eflux "err_int_flux" --localrms "local_rms"', shell=True, check=True)
subprocess.run('match_catalogues "' + obsFiles['yy_pb_cat'] + '" "' + FLUX_MODEL_CATALOGUE + '" --separation "' + str(separation) + '" --exclusion_zone "' + str(exclusion) + '" --outname "' + obsFiles['yy_xm'] + '" --threshold 0.5 --nmax 1000 --coords ' + str(metadata['RA']) + ' ' + str(metadata['DEC']) + ' --radius "' + str(radius) + '" --ra2 "RAJ2000" --dec2 "DEJ2000" --ra1 "ra" --dec1 "dec" -F "int_flux" --eflux "err_int_flux" --localrms "local_rms"', shell=True, check=True)

# Calculate the difference of the 20 brightest sources compared to GLEAM to prdouce the scaling factor A.
Axx = catCalcs.calcA(obsFiles['xx_xm'], metadata['FREQCENT'])
Ayy = catCalcs.calcA(obsFiles['yy_xm'], metadata['FREQCENT'])

# Convert the linear polarizations to Stokes I.
obsXXHdu = fits.open(obsFiles['xx'])
obsYYHdu = fits.open(obsFiles['yy'])

Nxx = obsXXHdu[0].data * Axx * beamXX / rmsXX**2
Nyy = obsYYHdu[0].data * Ayy * beamYY / rmsYY**2
Dxx = Axx**2 * beamXX**2 / rmsXX**2
Dyy = Ayy**2 * beamYY**2 / rmsYY**2
obsXXHdu[0].data =  (Nxx + Nyy) / (Dxx + Dyy)
obsXXHdu.writeto(obsFiles['ipb'])

obsXXHdu.close()
obsYYHdu.close()

# Create a backup of the Stokes I as mask_image will destructively remove pixel then apply the mask to the original.
shutil.copyfile(obsFiles['ipb'], obsFiles['ipb_orig'])
mask_image.derive_apply_beam_cut(image=obsFiles['ipb'], xx_beam=obsFiles['beam_xx'], yy_beam=obsFiles['beam_yy'], apply_mask=True)

# Move the new masked image into place.
os.remove(obsFiles['ipb'])
os.rename(obsFiles['ipb_mask'], obsFiles['ipb'])

# Calculate RMS and detect sources on the image.
subprocess.run('BANE --cores 1 --compress --noclobber "' + obsFiles['ipb'] + '"', shell=True, check=True)
subprocess.run('aegean --autoload --table="' + obsFiles['ipb'] + '" "' + obsFiles['ipb'] + '"', shell=True, check=True)
    
# Check that a sufficient number of sources were detected.
with fits.open(obsFiles['ipb_cat']) as catHdu:
    cat = catHdu[1].data
    nsrc = len(cat)

report.updateObs(reportCsv, obsid, 'sourcecount_' + subchan, 'Initial - ' + str(nsrc))
if nsrc < minsrcs:
    print('ERROR: Not enough sources detected.')
    report.updateObs(reportCsv, obsid, 'postImage_' + subchan, 'Fail - Not enough sources detected.')
    report.updateObs(reportCsv, obsid, 'status', 'Failed')
    exit(-1)

subprocess.run('fits_warp.py --incat "' + obsFiles['ipb_cat'] + '" --refcat "' + POS_MODEL_CATALOGUE + '" --xm "' + obsFiles['xm'] + '" --plot --ra1 ra --dec1 dec --ra2 RAJ2000 --dec2 DEJ2000 --infits "' + obsFiles['ipb'] + '"', shell=True, check=True)
subprocess.run('fits_warp.py --incat "' + obsFiles['ipb_cat'] + '" --refcat "' + POS_MODEL_CATALOGUE + '" --corrected "' + obsFiles['ipb_cat_corrected'] + '" --xm "' + obsFiles['xm'] + '" --suffix warp --infits "' + obsFiles['ipb'] + '" --ra1 ra --dec1 dec --ra2 RAJ2000 --dec2 DEJ2000 --plot --nsrcs 750 --vm 10 --progress --cores 24 --signal peak_flux_1 --enforce-min-srcs 100', shell=True, check=True)

# Flux_warp dependency, match the image catalogue to the model table.
subprocess.run('match_catalogues "' + obsFiles['ipb_cat_corrected'] + '" "' + FLUX_MODEL_CATALOGUE + '" --separation "' + str(separation) + '" --exclusion_zone "' + str(exclusion) + '" --outname "' + obsFiles['xm'] + '" --threshold 0.5 --nmax 1000 --coords ' + str(metadata['RA']) + ' ' + str(metadata['DEC']) + ' --radius "' + str(radius) + '" --ra2 "RAJ2000" --dec2 "DEJ2000" --ra1 "ra" --dec1 "dec" -F "int_flux" --eflux "err_int_flux" --localrms "local_rms"', shell=True, check=True)

# Changed to 2-D linear radial basis function interpolation and removed the bscale update.
subprocess.run('flux_warp "' + obsFiles['xm'] + '" "' + obsFiles['ipb_warp'] + '" --mode rbf --freq "' + str(metadata['FREQCENT']) + '" --threshold 0.5 --nmax 400 --flux_key "flux" --smooth 5.0 --ignore_magellanic --localrms_key "local_rms" --add-to-header --ra_key "RAJ2000" --dec_key "DEJ2000" --index "alpha" --curvature "beta" --ref_flux_key "S_200" --ref_freq 200.0 --alpha -0.77 --plot --cmap "gnuplot2" --order 2 --ext png --nolatex', shell=True, check=True)
    
# Get the header info from the flux warped image.
with fits.open(obsFiles['ipb_warp']) as warpHdu:
    warpHead = warpHdu[0].header
    factor = warpHead['BSCALE']


# The RMS and BKG maps will not have changed much from the ionospheric warping, therefore rename them and update BSCALE.
os.rename(obsFiles['ipb_rms'], obsFiles['ipb_warp_rms'])
os.rename(obsFiles['ipb_bkg'], obsFiles['ipb_warp_bkg'])
fits.setval(obsFiles['ipb_warp_rms'], 'BSCALE', value=factor)
fits.setval(obsFiles['ipb_warp_bkg'], 'BSCALE', value=factor)


# Rerun the source finding on the flux warped image.
subprocess.run('aegean --autoload --table="' + obsFiles['ipb_warp'] + '" "' + obsFiles['ipb_warp'] + '"', shell=True, check=True)

# Generate a weight map for mosaicking.
#subprocess.run('lookup_beam.py ' + obsFiles['ipb_warp'] + ' ' + filePrefix + '-image-pb_warp- -c ' + chans[chanStart] + '-' + chans[chanEnd] + ' --beam_path "' + os.path.join(projectdir, 'beamdata/gleam_xx_yy.hdf5') + '"', shell=True, check=True)
#gwm.genWeightMap(obsid + '_deep-' + subchan + '-image-pb_warp-XX-beam.fits', obsid + '_deep-' + subchan + '-image-pb_warp-YY-beam.fits', obsid + '_deep-' + subchan + '-image-pb_warp_rms.fits', obsid + '_deep-' + subchan + '-image-pb_warp_weight.fits')
gwm.genWeightMap(obsFiles['beam_xx'], obsFiles['beam_yy'], obsFiles['ipb_warp_rms'], obsFiles['ipb_warp_weight'])

# Update the source count in the report.
with fits.open(obsFiles['ipb_warp_cat']) as catHdu:
    cat = catHdu[1].data
    nsrc = len(cat)
report.updateObs(reportCsv, obsid, 'sourcecount_' + subchan, str(nsrc))

# Calculate the thermal RMS at the center of the observation.
obsRms = rms.calcRMS(obsFiles['ipb_warp_rms'])
report.updateObs(reportCsv, obsid, 'rms_' + subchan, str(obsRms))

# Calculate the thermal RMS at the coords specified.
obsCoordRms = rms.calcRMSCoords(obsFiles['ipb_warp_rms'], ra, dec)
report.updateObs(reportCsv, obsid, 'coord_rms_' + subchan, str(obsCoordRms))
report.updateObs(reportCsv, obsid, 'postImage_' + subchan, 'Success')
if subchan == 'MFS':
    report.updateObs(reportCsv, obsid, 'beamsize', beam.calcBeamSize(obsFiles['ipb_warp']))
