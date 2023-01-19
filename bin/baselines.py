# Adapted from https://colab.research.google.com/drive/1yP9jaolPFhkDbzbwhgBbMCRRNugx-sgk?usp=sharing#scrollTo=rQgoZUU47qjL

import os
import sys
import subprocess
import numpy as np
from matplotlib import pyplot as plt
from astropy.io import fits
from itertools import combinations
from scipy.constants import c
from scipy.signal import find_peaks



def inner_tukey_taper(x, min_uv_m, inner_taper_m):
    """
    for baseline length x in metres
    given inner cutoff, and taper width, return taper
    with zero values before taper, and unity after
    NB all values in m unlike wsclean (which uses lambda for taper cutoffs)
    """

    taper = np.where(x<=min_uv_m, 0.0, 1.0)
    taper = np.where(x<min_uv_m+inner_taper_m,
                     taper*0.5*(1-np.cos(np.pi*(x-min_uv_m)/(inner_taper_m))),
                     taper)
    return taper

def outer_tukey_taper(x, max_uv_m, outer_taper_m):
    """
    for baseline length x in metres
    given inner cutoff, and taper width, return taper
    with zero values before taper, and unity after
    NB all values in m unlike wsclean (which uses lambda for taper cutoffs)
    """

    taper = np.where(x>=max_uv_m, 0.0, 1.0)
    taper = np.where(x>max_uv_m-outer_taper_m,
                     taper*0.5*(1-np.cos(np.pi*(x-max_uv_m)/(outer_taper_m))),
                     taper)
    return taper

def iterbaselines(antlist):
    return combinations(antlist, 2)

def calcTukey(obsid, binSize=125, freq=215*10**6):
    metafits = obsid + '.metafits'
    w = c/freq # meters

    # Check to see if the metafits file has been downloaded, if not, download it.
    # Would prefer to use the wget library, but must wait until new container is made.
    if not os.path.exists(metafits):
        # wget.download('http://ws.mwatelescope.org/metadata/fits?obs_id=' + obsid, metafits)
        metaDownload = subprocess.run('wget -O "' + metafits + '" http://ws.mwatelescope.org/metadata/fits?obs_id=' + obsid, shell=True)
        # The above creates a 0b file if it fails, need to remove this before erroring out.
        if metaDownload.returncode != 0:
            subprocess.run('rm "' + metafits + '"', shell=True)
            exit(-1)

    metaHdu = fits.open(metafits)
    metadata = metaHdu[1].data
    metaHdu.close()

    # Get antenna coordinates.
    east = metadata['East'][metadata['Pol'] == 'X']
    north = metadata['North'][metadata['Pol'] == 'X']
    coords = np.hstack(((north, east,),))

    """Get length of each baseline in metres. 
    Also get its maximum in either U or V (useful for checking if it will be gridded
    """
    lengths = []
    for i, j in iterbaselines(range(coords.shape[1])):
        lengths.append(np.hypot(*(coords[:, i] - coords[:, j])))
    lengths = np.array(lengths)

    # Find the position of the peak.
    bins = np.arange(0, lengths.max(), binSize)
    plt.figure(figsize=(6, 4), dpi=240)
    ax = plt.subplot()
    n, _, _ = ax.hist(lengths, bins=bins, alpha=0.5, label=obsid, color='grey')
    peaks = find_peaks(n)

    inner_width = (peaks[0][0]+1)*binSize
    min_uv = 0

    x = np.linspace(0, 6000, 2001)
    inner_tukey = inner_tukey_taper(x, min_uv, inner_width)

    ax.set_title('Tukey')
    ax.set_xlabel('$\lambda$')
    ax.set_ylabel("Baseline Count")
    
    ax.plot(x, inner_tukey*n.max(), c='blue', label='Inner: ' + str(inner_width))
    ax.legend()

    plt.savefig(obsid + '_tukey.png')
    plt.cla()
    plt.clf()

    return str(min_uv), str(inner_width)
