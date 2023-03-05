#!/usr/bin/env python3

import os
import sys
import subprocess

if len(sys.argv) != 3:
    print('ERROR: Incorrect number of parameters.')
    exit(-1)

projectdir = sys.argv[1]
imagelist = sys.argv[2]
tempImagelist = 'worklist'
tempWeightlist = 'weightlist'
workImage = 'deep_work.fits'
workImageWeight = 'deep_work.weight.fits'

firstFile = True

os.rename('weightlist', 'weightlist_all')

with open(imagelist) as f, open('weightlist_all') as wlf: 
    #for x, y in zip(f, wlf):
        #x = x.strip()
        #y = y.strip()
#with open(imagelist) as f:
    #for line in f:
    for x, y in zip(f, wlf):
        obspath = x.rstrip()
        #weightpath = obspath[:-8] + '_weight.fits'
        weightpath = y.rstrip()
        if not (os.path.exists('deep.fits') or os.path.exists(workImage)):
            if firstFile:
                firstFile = False
                with open(tempImagelist, 'w') as tempfile:
                    tempfile.write(obspath + '\n')
                with open(tempWeightlist, 'w') as tempfile:
                    tempfile.write(weightpath + '\n')
                continue
            else:
                with open(tempImagelist, 'a') as tempfile:
                    tempfile.write(obspath)
                with open(tempWeightlist, 'a') as tempfile:
                    tempfile.write(weightpath)
        else:
            # Delete the previous mosaic.
            if os.path.exists(workImage):
                os.remove(workImage)
            if os.path.exists(workImageWeight):
                os.remove(workImageWeight)

            # Rename the new mosaic.
            os.rename('deep.fits', workImage)
            os.rename('deep.weight.fits', workImageWeight)

            # Clean mosiack
            #subprocess.run('wsclean -abs-mem 50 -multiscale -mgain 0.85 -multiscale-gain 0.15 -nmiter 5 -niter 10000000 -reuse-primary-beam -apply-primary-beam -auto-mask ' + str(msigma) + ' -auto-threshold ' + str(tsigma) + ' -name ' + obsid + '_deep -size ' + str(imsize) + ' ' + str(imsize) + ' -scale ' + str(scale) + ' -weight briggs ' + str(robust) + tukey_cmd + ' -pol I -join-channels -channels-out 4 -save-source-list -fit-spectral-pol 2 -data-column DATA ' + obsid + '.ms', shell=True, check=True)
            with open(tempImagelist, 'w') as tempfile:
                tempfile.write(workImage + '\n')
                tempfile.write(obspath)
            with open(tempWeightlist, 'w') as tempfile:
                tempfile.write(workImageWeight + '\n')
                tempfile.write(weightpath)

        with open('deep.fits', 'w') as tempfile:
            tempfile.write(obspath + '\n')
        with open('deep.weight.fits', 'w') as tempfile:
            tempfile.write(obspath + '\n')

        # SWARP
        swarpCmd = 'swarp -c "' + projectdir + '/swarp.config" @"' + tempImagelist + '"'
        subprocess.run(swarpCmd, shell=True, check=True)
        #print(swarpCmd)

# Cleanup the old mosaic.
if os.path.exists(workImage):
    os.remove(workImage)
if os.path.exists(workImageWeight):
    os.remove(workImageWeight)