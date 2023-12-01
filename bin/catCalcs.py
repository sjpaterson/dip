import math
import numpy as np
import pandas as pd
import astropy.units as u
from astropy.io import fits
from astropy.coordinates import SkyCoord



# Compare to a catalogue to calculate the scaling factor A.
def calcA(name, matchedCatFile, freq, method='snr'):

    with fits.open(matchedCatFile) as obsHdu:
        matchedCat = pd.DataFrame(np.array(obsHdu[1].data).byteswap().newbyteorder())

    matchedCat.sort_values('flux', ascending=False, inplace=True)

    matchedCat['gleam_flux'] = matchedCat['S_200'] * (float(freq) / 200.0) ** matchedCat['alpha']
    matchedCat['flux_ratio'] = matchedCat['flux'] / matchedCat['gleam_flux']

    f = open(f'acalc_{name}.txt', 'w')

    f.write(f'Count All: {len(matchedCat.index)}\n')
    # Only keep sources above 5 sigma.
    matchedCat = matchedCat[matchedCat['flux'] > 5 * matchedCat['eflux']]
    f.write(f'Count 5sig: {len(matchedCat.index)}\n')

    # Set weighting based on brightness.
    matchedCat['SNR'] = matchedCat['flux'] / matchedCat['eflux']
    matchedCat['weightBright'] = matchedCat['flux'] / matchedCat['flux'].max()
    matchedCat['weightRMS'] = matchedCat['eflux'] / matchedCat['eflux'].max()
    matchedCat['weightSNR'] = matchedCat['SNR'] / matchedCat['SNR'].max()


    matchedCat.to_csv(f'matched_{name}.csv')

    AWeightRMS = np.average(matchedCat['flux_ratio'], weights=matchedCat['weightRMS'])
    AWeightSNR = np.average(matchedCat['flux_ratio'], weights=matchedCat['weightSNR'])
    ANoWeight = np.average(matchedCat['flux_ratio'])
    ABrightest = np.average(matchedCat['flux_ratio'].head(20))

    f.write('\n')
    if method == 'snr':
        f.write('Using SNR')
        A = AWeightSNR
    elif method == 'all':
        f.write('Using All')
        A = ANoWeight
    else:
        f.write('Using SNR')
        A = AWeightSNR

    f.write('\n')
    f.write(f'Weighted RMS: {AWeightRMS}\n')
    f.write(f'Weighted SNR: {AWeightSNR}\n')
    f.write(f'No Weight All: {ANoWeight}\n')
    f.write(f'No Weight 20 Brightest: {ABrightest}\n')
    f.close()

    return A


# Reduce the catalogue to only isolated sources. Sources without another sounce within {distance} degrees.
def reduceCat(inCat, outCat, distance=0.05):
    print(f'Reducing {inCat} to only include isolated sources with a minimum separation distance of {distance} degrees.')
    catHdu = fits.open(inCat)
    catData = catHdu[1].data

    cat = SkyCoord(ra=catData['ra']*u.degree, dec=catData['dec']*u.degree)  
    idx, d2d, d3d = cat.match_to_catalog_sky(cat, nthneighbor=2)
    reducedCat = catData[d2d > distance*u.degree]
    print(f'Reduced catalogue from {len(cat)} sources to {len(reducedCat)} sources.')

    print(f'Writting: {outCat}')
    catHdu[1].data = reducedCat
    catHdu.writeto(outCat, overwrite=True)
