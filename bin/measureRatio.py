import os
import pandas as pd
import numpy as np
import astropy.units as u
from astropy.io import fits
from astropy.coordinates import SkyCoord

gleamCatFile = 'models/GGSM_sparse_unresolved.fits'

def measureRatio(obsCatFile, projectDir):
    obsHdu = fits.open(obsCatFile)
    obsFits = obsHdu[1].data
    obsCat = pd.DataFrame(np.array(obsFits).byteswap().newbyteorder())

    gleamHdu = fits.open(os.path.join(projectDir, gleamCatFile))
    gleamFits = gleamHdu[1].data
    gleamCat = pd.DataFrame(np.array(gleamFits).byteswap().newbyteorder())

    #primarySource = SkyCoord(ra=135*u.degree, dec=0.5*u.degree)

    # Find the distance to the primary source.
    #objectCoord = SkyCoord(ra=obsCat['ra'].to_numpy()*u.degree, dec=obsCat['dec'].to_numpy()*u.degree)
    #sep = primarySource.separation(objectCoord)
    #obsCat['G9 distance'] = sep.arcsec

    cF = SkyCoord(ra=obsCat['ra'].to_numpy()*u.degree, dec=obsCat['dec'].to_numpy()*u.degree)
    gleamCoords = SkyCoord(ra=gleamCat['RAJ2000'].to_numpy()*u.degree, dec=gleamCat['DEJ2000'].to_numpy()*u.degree)
    gleamidx, gleamd2d, gleamd3d = cF.match_to_catalog_sky(gleamCoords)

    j=0
    for index, currenObs in obsCat.iterrows():
        obsCat.at[index, 'gleam name'] = gleamCat['Name'].iloc[gleamidx[j]]
        obsCat.at[index, 'gleam flux'] = gleamCat['S_200'].iloc[gleamidx[j]] * (215.68 / 200.0) ** gleamCat['alpha'].iloc[gleamidx[j]]
        obsCat.at[index, 'gleam S200'] = gleamCat['S_200'].iloc[gleamidx[j]] 
        obsCat.at[index, 'gleam alpha'] = gleamCat['alpha'].iloc[gleamidx[j]]

        #c = SkyCoord(ra=currenObs['ra']*u.degree, dec=currenObs['dec']*u.degree)
        #d2d = c.separation(objectCoord)
        #obsCat.at[index, 'near'] = len(d2d[d2d < 3*u.arcmin])

        j = j+1
        
    obsCat['gleam distance']=gleamd2d.degree

    obsCat = obsCat[obsCat['gleam distance'] <= 0.01]
    obsCat = obsCat.sort_values('gleam distance').drop_duplicates(subset='gleam name', keep='first')

    obsCat['ratio'] = obsCat['int_flux'] / obsCat['gleam flux']

    return obsCat['ratio'].mean()

