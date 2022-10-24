#!/usr/bin/env python
from __future__ import print_function

__author__ = "Natasha Hurley-Walker"
__date__ = "12/09/2018"

import os, sys

import numpy as np
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText

from astropy.io import fits
from calplots import aocal

def get_tile_info(metafits):
    hdus = fits.open(metafits)
    inputs = hdus[1].data
    tiles = inputs[inputs['pol'] == 'X']
    tiles = tiles[np.argsort(tiles['Tile'])]
    Names = tiles["TileName"]
    North = tiles["North"]
    East = tiles["East"]
    return Names, North, East

def diff(ao, metafits, refant):
    diffs = []
    non_nan_intervals = np.where([not np.isnan(ao[i, refant, :, 0]).all() for i in range(ao.n_int)])[0]
    t_start = non_nan_intervals.min()
    t_end = non_nan_intervals.max()
    
    # Divide through by refant
    ao = ao / ao[:, refant, :, :][:, np.newaxis, :, :]
    ant_iter = np.arange(ao.n_ant)
    for a, antenna in enumerate(ant_iter):
        temp = []
        # Only XX and YY
        for pol in 0, 3:
            # Difference the complex gains, then convert to angles
           temp.append(np.angle(ao[t_end, antenna, :, pol] / ao[t_start, antenna, :, pol], deg=True))
        diffs.append(temp)
    return diffs

def phi_rms(ao, metafits, refant):
    phi_rmss = []
    non_nan_intervals = np.where([not np.isnan(ao[i, refant, :, 0]).all() for i in range(ao.n_int)])[0]
    t_start = non_nan_intervals.min()
    t_end = non_nan_intervals.max()
    # Calculate middle interval
    t_mid = int((t_end - t_start)/2.0)
    print(t_mid)

    # Divide through by refant
    # (Probably unnecessary)
    ao = ao / ao[:, refant, :, :][:, np.newaxis, :, :]
    ant_iter = np.arange(ao.n_ant)
    for a, antenna in enumerate(ant_iter):
        temp = []
        # Only XX and YY
        for pol in 0, 3:
            # Difference the complex gains
            # Divide all gains by t_mid value so central phase is zero (solves wrapping problem)
           temp_gains = ao[:, antenna, :, pol] / ao[t_mid, antenna, :, pol]
            
            # then convert to angles
           temp_angles = np.angle(ao[:, antenna, :, pol], deg=True)
            
            # Then find RMS -- over time axis only
           phi_rmss.append(np.std(temp_angles, axis=0))
        #    print(np.std(ao[:, antenna, :, pol], axis=0))
           print(temp_angles.shape)
           print(np.std(temp_angles, axis=0).shape)
    return phi_rmss

def histo_diffs(diffs, obsid, outdir):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = ax.hist(diffs, bins = 60, range=[-180, 180])
    peak = bins[np.where(n == n.max())][0]
    ax.axvline(x=np.median(diffs), color="red")
    ax.axvline(x=peak, color="orange")
    ax.set_xlabel("Phase change / degrees")
    at = AnchoredText("Median: {0:3.0f}deg\nPeak: {1:3.0f}deg\nStdev: {2:3.0f}deg".format(np.median(diffs), peak, np.std(diffs)),
                  prop=dict(size=8), frameon=True,
                  loc=1,
                  )
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
    ax.add_artist(at)
    outname = obsid+"_histogram.png"
    fig.savefig(os.path.join(outdir, outname))

    return np.median(diffs), peak, np.std(diffs)

def histo_rmss(rmss, obsid, outdir):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    n, bins, patches = ax.hist(rmss, bins = 60) #, range=[0, 1.0])
    peak = bins[np.where(n == n.max())][0]
    ax.axvline(x=np.median(rmss), color="red")
    ax.axvline(x=peak, color="orange")
    ax.set_xlabel("Phase change / degrees")
#    at = AnchoredText("Median: {0:3.3f}deg\nPeak: {1:3.3f}deg\nStdev: {2:3.3f}deg".format(np.median(rmss), peak, np.std(rmss)),
    at = AnchoredText("Median: {0}deg\nPeak: {1}deg\nStdev: {2}deg".format(np.median(rmss), peak, np.std(rmss)),
                  prop=dict(size=8), frameon=True,
                  loc=1,
                  )
    at.patch.set_boxstyle("round,pad=0.,rounding_size=0.2")
    ax.add_artist(at)
    outname = obsid+"_rms_histogram.png"
    fig.savefig(os.path.join(outdir, outname))

    return np.median(rmss), peak, np.std(rmss)

def phase_map(diffs, metafits, names, obsid, outdir):
    fig = plt.figure(figsize = (10,8))
    Names, North, East = get_tile_info(metafits)
    ax = fig.add_axes([0.15, 0.1, 0.65, 0.75])
    ax.axis("equal")
    sc = ax.scatter(North, East, marker='o', s=150, linewidths=4, c=diffs, cmap='hsv', vmin = -180., vmax = 180.)
    ax.set_xlabel("East / m")
    ax.set_ylabel("North / m")
    if names is True:
        for i, txt in enumerate(Names):
            ax.annotate(txt, (North[i], East[i]))

    cbaxes = fig.add_axes([0.82, 0.1, 0.02, 0.75])
    cb = plt.colorbar(sc, cax = cbaxes, orientation="vertical")
    cb.set_label('Phase change / degrees')
    outname = obsid+"_phasemap.png"
    fig.savefig(os.path.join(outdir, outname))
    
def phase_wrt_East(diffs, metafits, names, obsid, outdir):
    fig = plt.figure(figsize = (10,8))
    Names, North, East = get_tile_info(metafits)
    ax = fig.add_subplot(111)
    sc = ax.scatter(East, diffs, marker='o')
    ax.set_xlabel("East / m")
    ax.set_ylabel("diffs / degrees")
    outname = obsid+"_wrt_East.png"
    fig.savefig(os.path.join(outdir, outname))

def csv_out(obsid, median, peak, std, outdir):
    outformat = "{0},{1},{2},{3}\n"
    outvars = [obsid, median, peak, std ]
    outputfile = os.path.join(outdir, obsid+"_ionodiff.csv")
    if not os.path.exists(outputfile):
        with open(outputfile, 'w') as output_file:
           output_file.write("#obsid,median,peak,std\n")
           output_file.write(outformat.format(*outvars))


def run(filename, obsid, metafits=None, refant=127, outdir=None, names=True, rms=False):

    
    if os.path.exists(filename):
        ao = aocal.fromfile(filename)
    else:
        print(filename+" does not exist!")
        sys.exit(1)

    diffs = np.array(diff(ao, metafits, refant))
    
    # Flatten array and delete NaNs for histogram
    median, peak, std = histo_diffs(diffs[np.logical_not(np.isnan(diffs))].flatten(), obsid, outdir)
    csv_out(obsid, median, peak, std, outdir)

    if metafits is not None:
        if os.path.exists(metafits):
            # Plotting on a single frequency, single pol on map because it's impossible otherwise
            diffs = diffs[:, 0, 15]
            # Could also take the average of a few frequencies, but it doesn't change anything
            # diffs = np.average(diffs[:, 0, 12:20], axis=1)
            phase_map(diffs, metafits, names, obsid, outdir)
            phase_wrt_East(diffs, metafits, names, obsid, outdir)
    # New option: plot RMS
    if rms is True:
        rmss = np.array(phi_rms(ao, metafits, refant))
        median, peak, std = histo_rmss(rmss[np.logical_not(np.isnan(rmss))].flatten(), obsid, outdir)
