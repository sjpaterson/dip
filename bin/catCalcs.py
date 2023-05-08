import math
import numpy as np
import pandas as pd
import astropy.units as u
from astropy.io import fits
from astropy.coordinates import SkyCoord


# Compare the defined number of brightest sources to the GLEAM catalogue
# to calculate the scaling factor A.
def calcA(matchedCatFile, numSources, freq):

    with fits.open(matchedCatFile) as obsHdu:
        matchedCat = pd.DataFrame(np.array(obsHdu[1].data).byteswap().newbyteorder())
    matchedCat.sort_values('flux', ascending=False, inplace=True)
    matchedCat = matchedCat[:numSources]

    matchedCat['gleam_flux'] = matchedCat['S_200'] * (np.float(freq) / 200.0) ** matchedCat['alpha']
    fluxMean = matchedCat['flux'].mean()
    gleamMean = matchedCat['gleam_flux'].mean()

    A = fluxMean/gleamMean
        
    return A
