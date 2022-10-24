#!/usr/bin/env python3

import os
import sys
import subprocess
import astropy.units as u
import gleamx.mask_image as mask_image
from astropy.io import fits
from astropy.coordinates import SkyCoord

if len(sys.argv) != 4:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

projectdir = sys.argv[1]
obsdir = sys.argv[2]
obsid = sys.argv[3]

# Define relavant file names and paths.
obsdir = os.path.join(obsdir, obsid)
metafits = os.path.join(obsdir, obsid + '.metafits')
measurementSet = os.path.join(obsdir, obsid + '.ms')


# Sub-channels
subchans = ['0000', '0001', '0002', '0003', 'MFS']

# flux_warp method
#method=scaled

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

for subchan in subchans:
    chanHdu = fits.open(os.path.join(obsdir, obsid + '_deep-' + subchan + '-image-pb.fits'))
    chanHead = chanHdu[0].header
    chanHdu.close()
    if chanHead['BMAJ'] == 0:
        print('ERROR: Zero-Size PSF')
        exit(-1)

    # As the mask_image.py operation will destructively remove the pixels, create a backup or restore from backup when required.
    if not os.path.exists(os.path.join(obsdir, obsid + '_deep-' + subchan + '-image-pb_comp.fits')):
        pb = os.path.join(obsdir, obsid + '_deep-' + subchan + '-image-pb.fits')
        pbxx = os.path.join(obsdir, obsid + '_deep-' + subchan + '-image-pb-XX-beam.fits')
        pbyy = os.path.join(obsdir, obsid + '_deep-' + subchan + '-image-pb-YY-beam.fits')
        pbmask = os.path.join(obsdir, obsid + '_deep-' + subchan + '-image-pb_mask.fits')
        pb_orig = os.path.join(obsdir, obsid + '_deep-' + subchan + '-image-pb_original.fits')
        
        if not os.path.exists(pb_orig):
            subprocess.run('cp -v "' + pb + '" "' + pb_orig + '"', shell=True)
        if not os.path.exists(pb):
            if not os.path.exists(pb):
                print('ERROR: Missing ' + pb + ' and ' + pb_orig + '.')
                exit(-1)
            else:
                subprocess.run('cp -v "' + pb_orig + '" "' + pb + '"', shell=True)

        # Generate a weight map for mosaicking
        chans = metadata['CHANNELS'].split(',')
        if subchan == 'MFS':
            i = 0
            j = 23
        else:
            n = int(subchan)
            i = n * 6
            j = i + 5

        subprocess.run('lookup_beam.py ' + pb + ' ' + obsid + '_deep-' + subchan + '-image-pb-' + '-c "' + chans[i] + '-' + chans[j] + '"', shell=True, check=True)
        mask_image.derive_apply_beam_cut(image=pb, xx_beam=pbxx, yy_beam=pbyy, apply_mask=True)

        # Move into place the new masked image.
        subprocess.run('rm "' + pb + '" && mv "' + pbmask + '" "' + pb + '"', shell=True)

        subprocess.run('BANE --cores 48 --compress --noclobber "' + pb + '"', shell=True, check=True)
        subprocess.run('aegean --cores 1 --autoload --table="' + pb + '" "' + pb + '"', shell=True, check=True)

