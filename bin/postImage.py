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
import measureRatio as mRatio
import gleamx.mask_image as mask_image
import gleamx.generate_weight_map as gwm
from astropy.io import fits
from astropy.coordinates import SkyCoord
from beam import calcBeamCentre


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
    # Linear polarizations produced by WSCLEAN.
    xx = filePrefix + '-XX-image.fits',
    yy = filePrefix + '-YY-image.fits',
    # Linear polarizations with primary beam applied.
    xx_pb = filePrefix + '-XX-image-pb.fits',
    yy_pb = filePrefix + '-YY-image-pb.fits',
    xx_pb_rms = filePrefix + '-XX-image-pb_rms.fits',
    yy_pb_rms = filePrefix + '-YY-image-pb_rms.fits',
    # Stokes I conversion from linear polarizations with pb appleid.
    ipb = filePrefix + '-image-pb.fits',
    ipb_rms = filePrefix + '-image-pb_rms.fits',
    ipb_bkg = filePrefix + '-image-pb_bkg.fits',
    ipb_warp = filePrefix + '-image-pb_warp.fits',
    ipb_warp_rms = filePrefix + '-image-pb_warp_rms.fits',
    ipb_warp_bkg = filePrefix + '-image-pb_warp_bkg.fits',
    ipb_warp_scaled = filePrefix + '-image-pb_warp_scaled.fits',
    ipb_warp_scaled_rms = filePrefix + '-image-pb_warp_scaled_rms.fits',
    ipb_warp_scaled_bkg = filePrefix + '-image-pb_warp_scaled_bkg.fits',
    # Primary beam information.
    beam_xx = filePrefix + '-XX-beam.fits',
    beam_yy = filePrefix + '-YY-beam.fits',
    # Additional operations perfromed on Stokes I with PB applied.
    ipb_mask = filePrefix + '-image-pb_mask.fits',
    ipb_orig = filePrefix + '-image-pb_original.fits',
    ipb_warp_scaled_weight = filePrefix + '-image-pb_warp_scaled_weight.fits',
    xm_complete = obsid + '_' + subchan + '_complete_sources_xm.fits',
    xm = obsid + '_' + subchan + '_fits_warp_xm.fits',
    xx_xm = obsid + '_' + subchan + '_xx_xm.fits',
    yy_xm = obsid + '_' + subchan + '_yy_xm.fits',
    i_xm = obsid + '_' + subchan + '_i_complete_xm.fits',
    i_isolated_xm = obsid + '_' + subchan + '_i_isolated_xm.fits',
    # Source catalgoues.
    xx_pb_cat = filePrefix + '-XX-image-pb_comp.fits',
    yy_pb_cat = filePrefix + '-YY-image-pb_comp.fits',
    ipb_cat = filePrefix + '-image-pb_comp.fits',
    ipb_reduced_cat = filePrefix + '-image-pb_reduced_comp.fits',
    ipb_cat_corrected = filePrefix + '-image-pb_comp_warp-corrected.fits',
    ipb_warp_cat = filePrefix + '-image-pb_warp_comp.fits',
    ipb_warp_scaled_cat = filePrefix + '-image-pb_warp_scaled_comp.fits',
    xx_pb_reduced_cat = filePrefix + '-XX-image-pb_reduced_comp.fits',
    yy_pb_reduced_cat = filePrefix + '-YY-image-pb_reduced_comp.fits',
    ipb_warp_reduced_cat = filePrefix + '-image-pb_warp_reduced_comp.fits',
)


# Sky model
POS_MODEL_CATALOGUE = os.path.join(projectdir, 'models/NVSS_SUMSS_psfcal.fits')
FLUX_MODEL_CATALOGUE = os.path.join(projectdir, 'models/GGSM_sparse_unresolved.fits')

separation = 60 / 3600      # Max separation for flux_warp crossmatch as ~ 1' -- unlikely that the ionosphere would be that brutal.
exclusion = 180 / 3600      # Exclusion for flux_warp internal exclusive crossmatch as ~ 3'.
minsrcs = 500               # Minimum number of sources to accept for observation.
radius = 50                 # Radius to match sources to in degrees.
radiusScaling = 6           # Radius to match sources to in degrees to calculate the scaling factor.
isolationDistance = 0.1     # Min distance between sources to be considered isolated in degrees.

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


# Load beam data.
if not os.path.exists(obsFiles['beam_xx']) or not os.path.exists(obsFiles['beam_yy']):
    subprocess.run(f'lookup_beam.py {obsid} _deep-{subchan}-XX-image.fits {obsid}_deep-{subchan}- -c {chans[chanStart]}-{chans[chanEnd]} --beam_path "{os.path.join(projectdir, "beamdata/gleam_xx_yy.hdf5")}"', shell=True, check=True)

# Calculate the location of the beam centre.
beamCentXX = calcBeamCentre(obsFiles['beam_xx'])
beamCentYY = calcBeamCentre(obsFiles['beam_yy'])

# Apply the primary beam to each polarization.
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


# Calculate the RMS for each pn corrected polarization.
subprocess.run(f'BANE --cores 1 --compress "{obsFiles["xx_pb"]}"', shell=True, check=True)
subprocess.run(f'BANE --cores 1 --compress "{obsFiles["yy_pb"]}"', shell=True, check=True)
rmsXX = rms.calcRMSCoords(obsFiles['xx_pb_rms'], beamCentXX.ra.deg, beamCentXX.dec.deg)
rmsYY = rms.calcRMSCoords(obsFiles['yy_pb_rms'], beamCentYY.ra.deg, beamCentYY.dec.deg)
report.updateObs(reportCsv, obsid, 'rms_xx_' + subchan, rmsXX)
report.updateObs(reportCsv, obsid, 'rms_yy_' + subchan, rmsYY)


# Find sources for each polization.
subprocess.run('aegean --cores=1 --autoload --table="' + obsFiles['xx_pb'] + '" "' + obsFiles['xx_pb'] + '"', shell=True, check=True)
subprocess.run('aegean --cores=1 --autoload --table="' + obsFiles['yy_pb'] + '" "' + obsFiles['yy_pb'] + '"', shell=True, check=True)
# Reduce the catalgoue to isolated sources, match)catalgoues exclusion_zone does not do a satiffacory job.
catCalcs.reduceCat(obsFiles["xx_pb_cat"], obsFiles["xx_pb_reduced_cat"], distance=isolationDistance)
catCalcs.reduceCat(obsFiles["yy_pb_cat"], obsFiles["yy_pb_reduced_cat"], distance=isolationDistance)
# Cross match with GLEAM.
subprocess.run(f'match_catalogues "{obsFiles["xx_pb_reduced_cat"]}" "{FLUX_MODEL_CATALOGUE}" --separation "{separation}" --exclusion_zone "{exclusion}" --outname "{obsFiles["xx_xm"]}" --threshold 0.5 --nmax 1000 --coords {beamCentXX.ra.deg} {beamCentXX.dec.deg} --radius {radiusScaling} --ra2 "RAJ2000" --dec2 "DEJ2000" --ra1 "ra" --dec1 "dec" -F "int_flux" --eflux "err_int_flux" --localrms "local_rms"', shell=True, check=True)
subprocess.run(f'match_catalogues "{obsFiles["yy_pb_reduced_cat"]}" "{FLUX_MODEL_CATALOGUE}" --separation "{separation}" --exclusion_zone "{exclusion}" --outname "{obsFiles["yy_xm"]}" --threshold 0.5 --nmax 1000 --coords {beamCentYY.ra.deg} {beamCentYY.dec.deg} --radius {radiusScaling} --ra2 "RAJ2000" --dec2 "DEJ2000" --ra1 "ra" --dec1 "dec" -F "int_flux" --eflux "err_int_flux" --localrms "local_rms"', shell=True, check=True)


# Calculate the weighted mean difference of sources compared to GLEAM to prdouce the scaling factor A.
Axx = catCalcs.calcA(f'{obsid}_{subchan}_XX', obsFiles['xx_xm'], metadata['FREQCENT'])
Ayy = catCalcs.calcA(f'{obsid}_{subchan}_YY', obsFiles['yy_xm'], metadata['FREQCENT'])

report.updateObs(reportCsv, obsid, f'Axx_{subchan}', Axx)
report.updateObs(reportCsv, obsid, f'Ayy_{subchan}', Ayy)

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
subprocess.run('BANE --cores 1 --compress "' + obsFiles['ipb'] + '"', shell=True, check=True)
subprocess.run('aegean --cores=1 --autoload --table="' + obsFiles['ipb'] + '" "' + obsFiles['ipb'] + '"', shell=True, check=True)


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

# Reduce the catalgoue to isolated sources.
catCalcs.reduceCat(obsFiles['ipb_cat'], obsFiles['ipb_reduced_cat'], distance=isolationDistance)

subprocess.run('fits_warp.py --incat "' + obsFiles['ipb_reduced_cat'] + '" --refcat "' + POS_MODEL_CATALOGUE + '" --xm "' + obsFiles['xm_complete'] + '" --plot --ra1 ra --dec1 dec --ra2 RAJ2000 --dec2 DEJ2000 --infits "' + obsFiles['ipb'] + '"', shell=True, check=True)
subprocess.run('fits_warp.py --incat "' + obsFiles['ipb_reduced_cat'] + '" --refcat "' + POS_MODEL_CATALOGUE + '" --corrected "' + obsFiles['ipb_cat_corrected'] + '" --xm "' + obsFiles['xm'] + '" --suffix warp --infits "' + obsFiles['ipb'] + '" --ra1 ra --dec1 dec --ra2 RAJ2000 --dec2 DEJ2000 --plot --nsrcs 750 --vm 10 --progress --cores 19 --signal peak_flux_1 --enforce-min-srcs 100', shell=True, check=True)

# Flux_warp dependency, match the image catalogue to the model table.
subprocess.run('match_catalogues "' + obsFiles['ipb_cat_corrected'] + '" "' + FLUX_MODEL_CATALOGUE + '" --separation "' + str(separation) + '" --exclusion_zone "' + str(exclusion) + '" --outname "' + obsFiles['xm'] + '" --threshold 0.5 --nmax 1000 --coords ' + str(metadata['RA']) + ' ' + str(metadata['DEC']) + ' --radius "' + str(radius) + '" --ra2 "RAJ2000" --dec2 "DEJ2000" --ra1 "ra" --dec1 "dec" -F "int_flux" --eflux "err_int_flux" --localrms "local_rms"', shell=True, check=True)


# Changed to 2-D linear radial basis function interpolation and removed the bscale update.
subprocess.run('flux_warp "' + obsFiles['xm'] + '" "' + obsFiles['ipb_warp'] + '" --mode quadratic_screen --freq "' + str(metadata['FREQCENT']) + '" --threshold 0.5 --nmax 400 --flux_key "flux" --smooth 5.0 --ignore_magellanic --localrms_key "local_rms" --add-to-header --ra_key "RAJ2000" --dec_key "DEJ2000" --index "alpha" --curvature "beta" --ref_flux_key "S_200" --ref_freq 200.0 --alpha -0.77 --plot --cmap "gnuplot2" --order 2 --ext png --nolatex', shell=True, check=True)
    

# Calculate the RMS and BKG maps for the warped image.
subprocess.run('BANE --cores 1 --compress "' + obsFiles['ipb_warp_scaled'] + '"', shell=True, check=True)

# Rerun the source finding on the flux warped image.
subprocess.run('aegean --cores=1 --autoload --table="' + obsFiles['ipb_warp_scaled'] + '" "' + obsFiles['ipb_warp_scaled'] + '"', shell=True, check=True)

# Generate a weight map for mosaicking.
gwm.genWeightMap(obsFiles['beam_xx'], obsFiles['beam_yy'], obsFiles['ipb_warp_scaled_rms'], obsFiles['ipb_warp_scaled_weight'])

# Update the source count in the report.
with fits.open(obsFiles['ipb_warp_scaled_cat']) as catHdu:
    cat = catHdu[1].data
    nsrc = len(cat)
report.updateObs(reportCsv, obsid, 'sourcecount_' + subchan, str(nsrc))

beamCentI = calcBeamCentre(obsFiles['ipb_warp_scaled_weight'])


# Calculate ratios for all sources.
subprocess.run(f'match_catalogues "{obsFiles["ipb_warp_scaled_cat"]}" "{FLUX_MODEL_CATALOGUE}" --separation "{separation}" --exclusion_zone "{exclusion}" --outname "{obsFiles["i_xm"]}" --threshold 0.5 --nmax 1000 --coords {beamCentI.ra.deg} {beamCentI.dec.deg} --radius {radiusScaling} --ra2 "RAJ2000" --dec2 "DEJ2000" --ra1 "ra" --dec1 "dec" -F "int_flux" --eflux "err_int_flux" --localrms "local_rms"', shell=True, check=True)
ratio = catCalcs.calcA(f'{obsid}_{subchan}_I', obsFiles['i_xm'], metadata['FREQCENT'], method='all')
report.updateObs(reportCsv, obsid, f'ratio_{subchan}', ratio)

# Calculate ratios for isolated sources.
catCalcs.reduceCat(obsFiles["ipb_warp_scaled_cat"], obsFiles["ipb_warp_reduced_cat"], distance=isolationDistance)
subprocess.run(f'match_catalogues "{obsFiles["ipb_warp_reduced_cat"]}" "{FLUX_MODEL_CATALOGUE}" --separation "{separation}" --exclusion_zone "{exclusion}" --outname "{obsFiles["i_isolated_xm"]}" --threshold 0.5 --nmax 1000 --coords {beamCentI.ra.deg} {beamCentI.dec.deg} --radius {radiusScaling} --ra2 "RAJ2000" --dec2 "DEJ2000" --ra1 "ra" --dec1 "dec" -F "int_flux" --eflux "err_int_flux" --localrms "local_rms"', shell=True, check=True)
ratioIso = catCalcs.calcA(f'{obsid}_{subchan}_I_isolated', obsFiles['i_isolated_xm'], metadata['FREQCENT'], method='all')
report.updateObs(reportCsv, obsid, f'ratio_isolated_{subchan}', ratioIso)


# Calculate the thermal RMS at the center of the beam.
obsRms = rms.calcRMSCoords(obsFiles['ipb_warp_scaled_rms'], beamCentI.ra.deg, beamCentI.dec.deg)
report.updateObs(reportCsv, obsid, 'rms_' + subchan, str(obsRms))

# Calculate the thermal RMS at the coords specified.
obsCoordRms = rms.calcRMSCoords(obsFiles['ipb_warp_scaled_rms'], ra, dec)
report.updateObs(reportCsv, obsid, 'coord_rms_' + subchan, str(obsCoordRms))
report.updateObs(reportCsv, obsid, 'postImage_' + subchan, 'Success')
if subchan == 'MFS':
    report.updateObs(reportCsv, obsid, 'beamsize', beam.calcBeamSize(obsFiles['ipb_warp_scaled']))
