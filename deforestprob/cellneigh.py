#!/usr/bin/python

# ==============================================================================
# author          :Ghislain Vieilledent
# email           :ghislain.vieilledent@cirad.fr, ghislainv@gmail.com
# web             :https://ghislainv.github.io
# python_version  :2.7
# license         :GPLv3
# ==============================================================================

# Import
import numpy as np
import sys
from osgeo import gdal


# cellneigh
def cellneigh(raster=None, region=None, csize=10, rank=1):
    """
    Compute number of spatial cells and neighbours.

    :param raster: Path to raster file to compute region.
    :param region: List/tuple of region coordinates (east, west, south, north).
    :param csize: Spatial cell size (in km).
    :param rank: Rank of the neighborhood (1 for chess king's move).
    :return: List of length 2 with number of neighbours for each cell \
    and adjacent cells.
    """

    # Region
    if raster is not None:
        r = gdal.Open(raster)
        ncol_r = r.RasterXSize
        nrow_r = r.RasterYSize
        gt = r.GetGeoTransform()
        Xmin = gt[0]
        Xmax = gt[0] + gt[1] * ncol_r
        Ymin = gt[3] + gt[5] * nrow_r
        Ymax = gt[3]
    elif region is not None:
        Xmin = region[0]
        Xmax = region[1]
        Ymin = region[2]
        Ymax = region[3]
    else:
        print("raster or region must be specified")
        sys.exit(1)

    # Cell number from region
    print("Compute number of %d x %d km spatial cells" % (csize, csize))
    csize = csize * 1000  # Transform km in m
    ncol = np.int(np.ceil((Xmax - Xmin) / csize))
    nrow = np.int(np.ceil((Ymax - Ymin) / csize))
    ncell = ncol * nrow
    print("... %d cells (%d x %d)" % (ncell, nrow, ncol))

    # Adjacent cells and number of neighbors
    print("Identify adjacent cells and compute number of neighbors")
    nneigh = []
    adj = []
    around = np.arange(-rank, rank + 1)
    for i in range(nrow):
        for j in range(ncol):
            I = i + around
            Iprim = I[(I >= 0) & (I < nrow)]
            J = j + around
            Jprim = J[(J >= 0) & (J < ncol)]
            # Disregard the center cell
            nneigh.append(len(Iprim) * len(Jprim) - 1)
            for cy in Iprim:
                for cx in Jprim:
                    if not (cy == i and cx == j):
                        adj.append(cy * ncol + cx)
    nneigh = np.array(nneigh)
    adj = np.array(adj)

    return(nneigh, adj)


# cellneigh
def cellneigh_ctry(raster=None, region=None, vector=None,
                   csize=10, rank=1):
    """
    Compute number of spatial cells and neighbours.

    :param raster: Path to raster file to compute region.
    :param vector: Path to vector file with country borders.
    :param region: List/tuple of region coordinates (east, west, south, north).
    :param csize: Spatial cell size (in km).
    :param rank: Rank of the neighborhood (1 for chess king's move).
    :return: List of length 2 with number of neighbours for each cell \
    and adjacent cells.
    """

    # Region
    if raster is not None:
        r = gdal.Open(raster)
        ncol_r = r.RasterXSize
        nrow_r = r.RasterYSize
        gt = r.GetGeoTransform()
        Xmin = gt[0]
        Xmax = gt[0] + gt[1] * ncol_r
        Ymin = gt[3] + gt[5] * nrow_r
        Ymax = gt[3]
    elif region is not None:
        Xmin = region[0]
        Xmax = region[1]
        Ymin = region[2]
        Ymax = region[3]
    else:
        print("raster or region must be specified")
        sys.exit(1)

    # Cell number from region
    print("Compute number of %d x %d km spatial cells" % (csize, csize))
    csize = csize * 1000  # Transform km in m
    ncol = np.int(np.ceil((Xmax - Xmin) / csize))
    nrow = np.int(np.ceil((Ymax - Ymin) / csize))
    Xmax_new = Xmin + ncol * csize
    Ymin_new = Ymax + nrow * (-csize)
    ncell = ncol * nrow
    print("... %d cells (%d x %d)" % (ncell, nrow, ncol))

    # Cells within country borders (rasterizing method)
    cb_ds = gdal.OpenEx(vector, gdal.OF_VECTOR)
    rOptions = gdal.RasterizeOptions(xRes=csize, yRes=-csize,
                                     allTouched=True,
                                     outputBounds=[Xmin, Ymin_new,
                                                   Xmax_new, Ymax],
                                     burnValues=1, noData=0)
    outfile = "/vsimem/tmpfile"
    ds = gdal.Rasterize(outfile, cb_ds, options=rOptions)
    mask = ds.ReadAsArray()
    ds = None
    gdal.Unlink(outfile)
    y_in, x_in = np.where(mask == 1)
    cell_in = y_in * ncol + x_in

    # Adjacent cells and number of neighbors
    print("Identify adjacent cells and compute number of neighbors")
    nneigh = []
    adj = []
    adj_sort = []
    around = np.arange(-rank, rank + 1)
    for i in range(nrow):
        for j in range(ncol):
            if mask[i, j] == 1:
                I = i + around
                Iprim = I[(I >= 0) & (I < nrow)]
                J = j + around
                Jprim = J[(J >= 0) & (J < ncol)]
                # Loop on potential neighbors
                nneighbors = 0
                for cy in Iprim:
                    for cx in Jprim:
                        if (not (cy == i and cx == j)) and (mask[cy, cx] == 1):
                            adj.append(cy * ncol + cx)
                            nneighbors += 1
                nneigh.append(nneighbors)
    nneigh = np.array(nneigh)
    adj = np.array(adj)
    for i in adj:
        adj_sort.append(np.flatnonzero(cell_in == i)[0])
    adj_sort = np.array(adj_sort)

    return(nneigh, adj_sort, cell_in)

# End
