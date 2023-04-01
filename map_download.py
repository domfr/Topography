import os
import time
import math
import rasterio
import urllib.request as urllib2

from application.config import DATA_DIR, MAPS, ELEVATION
from pathlib import Path


download_maps = False

max_coord = 7000000
source = MAPS if download_maps else ELEVATION

for map in source:
    Path(DATA_DIR + str(map[0])).mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR + map[1], 'r') as f:
        files = f.read().split('\n')
    for file in files:
        filepath = DATA_DIR + str(map[0]) + '/' + file.split('/')[-1]
        if not os.path.isfile(filepath):
            try:
                time.sleep(1)
                rq = urllib2.Request(file)
                res = urllib2.urlopen(rq)
                pdf = open(filepath, 'wb')
                pdf.write(res.read())
                pdf.close()
                print('Downloaded: ' + file)
            except:
                print('Download error: ' + file)

    tif = None
    minx = max_coord
    maxx = -1
    miny = max_coord
    maxy = -1
    with open(DATA_DIR + str(map[0]) + '/coordinates.txt', 'w') as f:
        for file in files:
            filepath = DATA_DIR + str(map[0]) + '/' + file.split('/')[-1]
            if not os.path.isfile(filepath):
                print('Missing: ' + file)
            else:
                tif = rasterio.open(filepath)
                if tif.bounds[0] < minx:
                    minx = tif.bounds[0]
                if tif.bounds[2] > maxx:
                    maxx = tif.bounds[2]
                if tif.bounds[1] < miny:
                    miny = tif.bounds[1]
                if tif.bounds[3] > maxy:
                    maxy = tif.bounds[3]
            f.write(filepath + ',' + str(int(tif.bounds[0])) + ',' + str(int(tif.bounds[1])) + '\n')

    if tif is not None:
        with open(DATA_DIR + str(map[0]) + '/stats.txt', 'w') as f:
            f.write(str(int(minx)) + '\n')
            f.write(str(int(maxx)) + '\n')
            f.write(str(int(miny)) + '\n')
            f.write(str(int(maxy)) + '\n')
            f.write(str(int(tif.bounds[2] - tif.bounds[0])) + '\n')
            f.write(str(int(tif.bounds[3] - tif.bounds[1])) + '\n')
            f.write(str(int((maxx - minx) / (tif.bounds[2] - tif.bounds[0]))) + '\n')
            f.write(str(int((maxy - miny) / (tif.bounds[3] - tif.bounds[1]))) + '\n')
            f.write(str(int(tif.read(1).shape[1])) + '\n')
            f.write(str(int(tif.read(1).shape[0])) + '\n')

for map in source:
    with open(DATA_DIR + str(map[0]) + '/stats.txt', 'r') as f:
        stats = f.read().split('\n')
    xtiles = int(int(stats[8]) / (200 * 2))
    ytiles = int(int(stats[9]) / (200 * 2))
    xpixels = int(math.ceil(int(stats[8]) / (xtiles * 2)))
    ypixels = int(math.ceil(int(stats[9]) / (ytiles * 2)))

    print('map: ' + str(map))
    print('zoom dimensions: ' + str(xtiles) + ' * ' + str(stats[6]) + ', ' + str(ytiles) + ' * ' + str(stats[7]))
    print('tile size: ' + str(xpixels) + ', ' + str(ypixels))

print('done')
