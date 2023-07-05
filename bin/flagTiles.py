import os
import sys
import pandas as pd
from astropy.time import Time

tilesFile = 'data/bad_tiles.csv'

flags = ''

# Convert from GPS time (obsid) to ISO and return the date as a stribg,
def convGPS(timeGPS):
    timeGPS = Time(timeGPS, format='gps')
    timeUTC = Time(timeGPS, format='iso', scale='utc')
    dateStr = str(timeUTC.datetime.date())
    return dateStr

def findBadTiles(obsid, projectDir):
    print('Finding Bad Tiles')
    tileCsv = os.path.join(projectDir, tilesFile)
    badTilesStr = ''

    if not os.path.exists(tileCsv):
        print(f'No tile datafile found: {tileCsv}')
        return badTilesStr
    
    tileDF = pd.read_csv(tileCsv, dtype=str)
    tileDF.set_index('date', inplace=True)

    day = convGPS(obsid)
    if day in tileDF.index:
        badTilesStr = tileDF.at[day, 'tiles']
    
    return badTilesStr

def flagNight(obsid, projectDir, badTiles):
    print('Flagging Night')
    
    tileCsv = os.path.join(projectDir, tilesFile)
    if not os.path.exists(tileCsv):
        tileDF = pd.DataFrame(columns=['date', 'tiles'])
    else:
         tileDF = pd.read_csv(tileCsv, dtype=str)
    tileDF.set_index('date', inplace=True)

    day = convGPS(obsid)
    if day in tileDF.index:
        existingTiles = set(tileDF.at[day, 'tiles'].split())    
        badTiles = badTiles.union(existingTiles)
    
    badTilesStr = ' '.join(map(str, badTiles))
    tileDF.at[day, 'tiles'] = badTilesStr
    
    print(f'Flagging Tiles for {day}: ' + tileDF.at[day, 'tiles'])

    tileDF.to_csv(tileCsv)
    

