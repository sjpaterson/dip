#!/usr/bin/env python
# Convert fits and VO catalogues to Andre's sky model format
from __future__ import print_function

import os, sys

# from string import replace

import numpy as np

# tables and votables
import astropy.io.fits as fits
from astropy.io.votable import parse_single_table
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.table import Table



def run(catalogue, output='test.txt', namecol='Name', racol='ra_str', decol='dec_str', acol='a_wide', bcol='b_wide', pacol='pa_wide', fluxcol='int_flux_wide', freq=200.0, alphacol='alpha', betacol='beta', alpha=-0.83, beta=0.0, point=False, resolution=1.2, intflux='int_flux_wide', peakflux='peak_flux_wide'):

    if catalogue is None:
        print("must specify input catalogue")
        sys.exit(1)
    else:
        filename, file_extension = os.path.splitext(catalogue)
        if file_extension == ".fits":
            data = Table.read(catalogue).to_pandas()
            data["Name"] = data["Name"].str.decode("utf-8")

        elif file_extension == ".vot":
            temp = parse_single_table(catalogue)
            data = temp.array

    if fluxcol is None:
        print("Must have a valid flux density column")
        sys.exit(1)
    try:
        names = data[namecol]
    except KeyError:
        names = np.array(
            [
                "J" + (data[racol][i][:-3] + data[decol][i][:-3]).replace(":", "")
                for i in range(len(data[racol]))
            ]
        )
    try:
        alpha = data[alphacol]
    except KeyError:
        alpha = alpha * np.ones(shape=data[fluxcol].shape)
    try:
        beta = data[betacol]
    except KeyError:
        beta = beta * np.ones(shape=data[fluxcol].shape)

    if type(data[racol][0]) == str:
        rastr = True
    else:
        rastr = False

    # Generate an output in Andre's sky model format
    # formatter="source {{\n  name \"{Name:s}\"\n  component {{\n    type gaussian\n    position {RA:s} {Dec:s}\n    shape {a:s} {b:s} {pa:s}\n    sed {{\n      frequency {freq:3.0f} MHz\n      fluxdensity Jy {flux:s} 0 0 0\n      spectral-index {{ {alpha:s} {beta:2.2f} }}\n    }}\n  }}\n}}\n"
    gformatter = 'source {{\n  name "{Name:s}"\n  component {{\n    type {shape:s}\n    position {RA:s} {Dec:s}\n    shape {a:2.1f} {b:2.1f} {pa:4.1f}\n    sed {{\n      frequency {freq:3.0f} MHz\n      fluxdensity Jy {flux:4.7f} 0 0 0\n      spectral-index {{ {alpha:2.2f} {beta:2.2f} }}\n    }}\n  }}\n}}\n'
    pformatter = 'source {{\n  name "{Name:s}"\n  component {{\n    type {shape:s}\n    position {RA:s} {Dec:s}\n    sed {{\n      frequency {freq:3.0f} MHz\n      fluxdensity Jy {flux:4.7f} 0 0 0\n      spectral-index {{ {alpha:2.2f} {beta:2.2f} }}\n    }}\n  }}\n}}\n'

    shape = np.array(["gaussian"] * data.shape[0])

    if point:
        try:
            srcsize = data[intflux] / data[peakflux]
            indices = np.where(srcsize < resolution)
        except KeyError:
            indices = np.where(np.isnan(data[acol]))
        shape[indices] = "point"

    bigzip = zip(
        names,
        data[racol],
        data[decol],
        data[acol],
        data[bcol],
        data[pacol],
        data[fluxcol],
        alpha,
        beta,
        shape,
    )

    with open(output, "w") as f:
        f.write("skymodel fileformat 1.1\n")
        for Name, RA, Dec, a, b, pa, flux, alpha, beta, shape in bigzip:

            if rastr is True:
                coords = SkyCoord(RA, Dec, frame="fk5", unit=(u.hour, u.deg))
            else:
                coords = SkyCoord(RA, Dec, frame="fk5", unit=(u.deg, u.deg))

            RA = coords.ra.to_string(u.hour)
            Dec = coords.dec.to_string(u.deg)

            if shape == "gaussian":
                f.write(
                    gformatter.format(
                        Name=Name,
                        RA=RA,
                        Dec=Dec,
                        a=a,
                        b=b,
                        pa=pa,
                        flux=flux,
                        alpha=alpha,
                        beta=beta,
                        freq=freq,
                        shape=shape,
                    )
                )

            elif shape == "point":
                f.write(
                    pformatter.format(
                        Name=Name,
                        RA=RA,
                        Dec=Dec,
                        flux=flux,
                        alpha=alpha,
                        beta=beta,
                        freq=freq,
                        shape=shape,
                    )
                )

