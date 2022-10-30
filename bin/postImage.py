#!/usr/bin/env python3

import os
import sys
import subprocess
import astropy.units as u
import gleamx.mask_image as mask_image
import gleamx.generate_weight_map as gwm
from astropy.io import fits
from astropy.coordinates import SkyCoord



if len(sys.argv) != 4:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

projectdir = sys.argv[1]
obsid = sys.argv[2]
subchan = sys.argv[3]

# Define relavant file names and paths.
metafits = obsid + '.metafits'
measurementSet = obsid + '.ms'


# Sky model
POS_MODEL_CATALOGUE = os.path.join(projectdir, 'models/NVSS_SUMSS_psfcal.fits')
FLUX_MODEL_CATALOGUE = os.path.join(projectdir, 'models/GGSM_sparse_unresolved.fits')

separation = 60 / 3600      # Max separation for flux_warp crossmatch as ~ 1' -- unlikely that the ionosphere would be that brutal.
exclusion = 180 / 3600      # Exclusion for flux_warp internal exclusive crossmatch as ~ 3'


# Import header information from the metafits file.
metaHdu = fits.open(metafits)
metadata = metaHdu[0].header
metaHdu.close()

b = SkyCoord(metadata['RA']*u.deg, metadata['DEC']*u.deg).galactic.b.deg
minsrcs = 500

if (metadata['CENTCHAN'] == 69) and (b < 10):
    minsrcs=50


# Some file definitions for the channel.
pb = obsid + '_deep-' + subchan + '-image-pb.fits'
pbxx = obsid + '_deep-' + subchan + '-image-pb-XX-beam.fits'
pbyy = obsid + '_deep-' + subchan + '-image-pb-YY-beam.fits'
pbmask = obsid + '_deep-' + subchan + '-image-pb_mask.fits'
pb_orig = obsid + '_deep-' + subchan + '-image-pb_original.fits'
pb_warp = obsid + '_deep-' + subchan + '-image-pb_warp.fits'

chanHdu = fits.open(pb)
chanHead = chanHdu[0].header
chanHdu.close()
if chanHead['BMAJ'] == 0:
    print('ERROR: Zero-Size PSF')
    exit(-1)

# Channel information for creating the weight maps.
chans = metadata['CHANNELS'].split(',')
if subchan == 'MFS':
    chanStart = 0
    chanEnd = 23
else:
    n = int(subchan)
    chanStart = n * 6
    chanEnd = chanStart + 5

# As the mask_image.py operation will destructively remove the pixels, create a backup or restore from backup when required.
if not os.path.exists(obsid + '_deep-' + subchan + '-image-pb_comp.fits'):
    
    if not os.path.exists(pb_orig):
        subprocess.run('cp -v "' + pb + '" "' + pb_orig + '"', shell=True)
    if not os.path.exists(pb):
        if not os.path.exists(pb_orig):
            print('ERROR: Missing ' + pb + ' and ' + pb_orig + '.')
            exit(-1)
        else:
            subprocess.run('cp -v "' + pb_orig + '" "' + pb + '"', shell=True)

    # Generate a weight map for mosaicking
    subprocess.run('lookup_beam.py ' + obsid + ' _deep-' + subchan + '-image-pb.fits ' + obsid + '_deep-' + subchan + '-image-pb- -c ' + chans[chanStart] + '-' + chans[chanEnd] + ' --beam_path "' + os.path.join(projectdir, 'beamdata/gleam_xx_yy.hdf5') + '"', shell=True, check=True)
    mask_image.derive_apply_beam_cut(image=pb, xx_beam=pbxx, yy_beam=pbyy, apply_mask=True)

    # Move the new masked image into place.
    subprocess.run('rm "' + pb + '" && mv "' + pbmask + '" "' + pb + '"', shell=True)

    subprocess.run('BANE --cores 48 --compress --noclobber "' + pb + '"', shell=True, check=True)
    subprocess.run('aegean --cores 1 --autoload --table="' + pb + '" "' + pb + '"', shell=True, check=True)
    
    
# Check that a sufficient number of sources were detected.
catHdu = fits.open(obsid + '_deep-' + subchan + '-image-pb_comp.fits')
cat = catHdu[1].data
nsrc = len(cat)
catHdu.close()

if nsrc < minsrcs:
    print('ERROR: Not enough sources detected.')
    exit(-1)

radius = 50
freqq = str(int(round(chanHead['CRVAL3']/1e6)))

if not os.path.exists(obsid + '_' + subchan + '_complete_sources_xm.fits'):
    subprocess.run('fits_warp.py --incat "' + obsid + '_deep-' + subchan + '-image-pb_comp.fits" --refcat "' + POS_MODEL_CATALOGUE + '" --xm "' + obsid + '_' + subchan + '_complete_sources_xm.fits" --plot --ra1 ra --dec1 dec --ra2 RAJ2000 --dec2 DEJ2000 --infits "' + pb + '"', shell=True, check=True)

if not os.path.exists(pb_warp):
    subprocess.run('fits_warp.py --incat "' + obsid + '_deep-' + subchan + '-image-pb_comp.fits" --refcat "' + POS_MODEL_CATALOGUE + '" --corrected "' + obsid + '_deep-' + subchan + '-image-pb_comp_warp-corrected.fits" --xm "' + obsid + '_' + subchan + '_fits_warp_xm.fits" --suffix warp --infits "' + pb + '" --ra1 ra --dec1 dec --ra2 RAJ2000 --dec2 DEJ2000 --plot --nsrcs 750 --vm 10 --progress --cores 24 --signal peak_flux_1 --enforce-min-srcs 100', shell=True, check=True)

# Flux_warp dependency, match the image catalogue to the model table.
if not os.path.exists(obsid + '_' + subchan + '_xm.fits'):
    subprocess.run('match_catalogues "' + obsid + '_deep-' + subchan + '-image-pb_comp_warp-corrected.fits" "' + FLUX_MODEL_CATALOGUE + '" --separation "' + str(separation) + '" --exclusion_zone "' + str(exclusion) + '" --outname "' + obsid + '_' + subchan + '_xm.fits" --threshold 0.5 --nmax 1000 --coords ' + str(metadata['RA']) + ' ' + str(metadata['DEC']) + ' --radius "' + str(radius) + '" --ra2 "RAJ2000" --dec2 "DEJ2000" --ra1 "ra" --dec1 "dec" -F "int_flux" --eflux "err_int_flux" --localrms "local_rms"', shell=True, check=True)

if not os.path.exists(obsid + '_deep-' + subchan + '-image-pb_warp_scaled_cf_output.txt'):
    subprocess.run('flux_warp "' + obsid + '_' + subchan + '_xm.fits" "' + obsid + '_deep-' + subchan + '-image-pb_warp.fits" --mode mean --freq "' + freqq + '" --threshold 0.5 --nmax 400 --flux_key "flux" --smooth 5.0 --ignore_magellanic --localrms_key "local_rms" --add-to-header --ra_key "RAJ2000" --dec_key "DEJ2000" --index "alpha" --curvature "beta" --ref_flux_key "S_200" --ref_freq 200.0 --alpha -0.77 --plot --cmap "gnuplot2" --update-bscale --order 2 --ext png --nolatex', shell=True, check=True)

# Get the header info from the flux warped image.
warpHdu = fits.open(pb_warp)
warpHead = warpHdu[0].header
warpHdu.close()
factor = warpHead['BSCALE']


# The RMS and BKG maps will not have changed much from the ionospheric warping, therefore rename them and update BSCALE.
subprocess.run('mv "' + obsid + '_deep-' + subchan + '-image-pb_rms.fits' + '" "' + obsid + '_deep-' + subchan + '-image-pb_warp_rms.fits' + '"', shell=True)
subprocess.run('mv "' + obsid + '_deep-' + subchan + '-image-pb_bkg.fits' + '" "' + obsid + '_deep-' + subchan + '-image-pb_warp_bkg.fits' + '"', shell=True)
fits.setval(obsid + '_deep-' + subchan + '-image-pb_warp_rms.fits', 'BSCALE', value=factor)
fits.setval(obsid + '_deep-' + subchan + '-image-pb_warp_bkg.fits', 'BSCALE', value=factor)


# Rerun the source finding.
if not os.path.exists(obsid + '_deep-' + subchan + '-image-pb_warp_comp.fits'):
    subprocess.run('aegean --cores 1 --autoload --table="' + pb_warp + '" "' + pb_warp + '"', shell=True, check=True)

# Generate a weight map for mosaicking.
if not os.path.exists(obsid + '_deep-' + subchan + '-image-pb_warp_weight.fits'):
    subprocess.run('lookup_beam.py ' + obsid + ' _deep-' + subchan + '-image-pb_warp.fits ' + obsid + '_deep-' + subchan + '-image-pb_warp- -c ' + chans[chanStart] + '-' + chans[chanEnd] + ' --beam_path "' + os.path.join(projectdir, 'beamdata/gleam_xx_yy.hdf5') + '"', shell=True, check=True)
    gwm.genWeightMap(obsid + '_deep-' + subchan + '-image-pb_warp-XX-beam.fits', obsid + '_deep-' + subchan + '-image-pb_warp-YY-beam.fits', obsid + '_deep-' + subchan + '-image-pb_warp_rms.fits', obsid + '_deep-' + subchan + '-image-pb_warp_weight.fits')

