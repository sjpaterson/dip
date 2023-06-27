import math
import numpy as np
import pandas as pd
import astropy.units as u
from astropy.io import fits
from astropy.coordinates import SkyCoord


# Compare the defined number of brightest sources to the GLEAM catalogue
# to calculate the scaling factor A.
#def calcA(matchedCatFile, numSources, freq):
def calcA(matchedCatFile, freq):

    with fits.open(matchedCatFile) as obsHdu:
        matchedCat = pd.DataFrame(np.array(obsHdu[1].data).byteswap().newbyteorder())
    matchedCat.sort_values('flux', ascending=False, inplace=True)

    matchedCat['gleam_flux'] = matchedCat['S_200'] * (float(freq) / 200.0) ** matchedCat['alpha']
    matchedCat['flux_ratio'] = matchedCat['flux'] / matchedCat['gleam_flux']

    A = matchedCat['flux_ratio'].mean()
        
    return A
