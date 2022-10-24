#!/usr/bin/env python
from __future__ import print_function

import os, logging
from calplots.aocal import fromfile
import numpy as np
from pyrap import tables


def run(infilename, outfilename, refant, xy=0.0, dxy=0.0, ms=None, store_true=False, verbose=0, incremental=None, preserve_xterms=None, no_preserve_mask=False):

    if verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbose > 1:
        logging.basicConfig(level=logging.DEBUG)
    if (xy != 0.0 or dxy != 0.0) and preserve_xterms:
        print("XY phase cannot be set if preserving xterms")
        exit(-1)

    ao = fromfile(infilename)

    ref_phasor = (ao[0, refant, ...] / np.abs(ao[0, refant, ...]))[
        np.newaxis, np.newaxis, ...
    ]
    if incremental:
        logging.warn("incremental solution untested!")
        ao = ao / (ao * ref_phasor)
    else:
        ao = ao / ref_phasor

    if not preserve_xterms:
        zshape = (1, ao.n_ant, ao.n_chan)
        ao[..., 1] = np.zeros(zshape, dtype=np.complex128)
        ao[..., 2] = np.zeros(zshape, dtype=np.complex128)
    if xy != 0.0 or dxy != 0.0:
        assert ms is not None, "A measurment set has not be specified"

        tab = tables.table(f"{ms}/SPECTRAL_WINDOW")
        freqs = np.squeeze(np.array(tab.CHAN_FREQ))
        tab.close()

        print(
            f"Frequencies have been read in, spanning {np.min(freqs)/1e6} to {np.max(freqs)/1e6} MHz. "
        )

        assert (
            len(freqs) == ao.n_chan
        ), f"Number of frequency solutions in the calibration file does not match the number of channels in {ms}"

        xy_phasor0 = np.complex(np.cos(np.radians(xy)), np.sin(np.radians(xy)))
        xy_phasor1 = np.zeros((1, 1, ao.n_chan), dtype=np.complex128)
        xy_phasor1.real += np.cos(np.radians(dxy * freqs)).reshape(1, 1, ao.n_chan)
        xy_phasor1.imag += np.sin(np.radians(dxy * freqs)).reshape(1, 1, ao.n_chan)
        ao[..., 3] = ao[..., 3] * xy_phasor0 * xy_phasor1


    if not no_preserve_mask:
        print("Carrying forward NaN mask")
        initial_ao = fromfile(infilename)
        ao[np.isnan(initial_ao)] = np.nan

    ao.tofile(outfilename)
