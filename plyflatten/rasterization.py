# Copyright (C) 2019, David Youssefi (CNES) <david.youssefi@cnes.fr>


import ctypes
import os

import affine
import numpy as np
from numpy.ctypeslib import ndpointer

from plyflatten import utils

# TODO: This is kind of ugly. Cleaner way to do this is to update
# LD_LIBRARY_PATH, which we should do once we have a proper config file
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lib = ctypes.CDLL(os.path.join(parent_dir, "lib", "libplyflatten.so"))

class Raster:

    def __init__(self, xoff, yoff, resolution, xsize, ysize, radius, sigma, nb_extra_columns):

        # roi, resolution, etc
        self.xoff = xoff
        self.yoff = yoff
        self.resolution = resolution
        self.xsize = xsize
        self.ysize = ysize
        self.radius = radius
        self.sigma = sigma
        self.nb_extra_columns = nb_extra_columns

        # statistics we want to extract from the point clouds
        raster_shape = (xsize * ysize, nb_extra_columns)
        self.avg = np.zeros(raster_shape, dtype="float32")
        self.std = np.zeros(raster_shape, dtype="float32")
        self.min = np.inf * np.ones(raster_shape, dtype="float32")
        self.max = -np.inf * np.ones(raster_shape, dtype="float32")
        self.cnt = np.zeros((xsize * ysize, 1), dtype="float32")


def compute_roi_from_ply_list(clouds_list, resolution):

    xmin, xmax = np.inf, -np.inf
    ymin, ymax = np.inf, -np.inf

    for cloud in clouds_list:
        cloud_data, _ = utils.read_3d_point_cloud_from_ply(cloud)
        current_cloud = cloud_data.astype(np.float64)
        xx, yy = current_cloud[:, 0], current_cloud[:, 1]
        xmin = np.min((xmin, np.amin(xx)))
        ymin = np.min((ymin, np.amin(yy)))
        xmax = np.max((xmax, np.amax(xx)))
        ymax = np.max((ymax, np.amax(yy)))

    xoff = np.floor(xmin / resolution) * resolution
    xsize = int(1 + np.floor((xmax - xoff) / resolution))

    yoff = np.ceil(ymax / resolution) * resolution
    ysize = int(1 - np.floor((ymin - yoff) / resolution))

    return xoff, yoff, xsize, ysize


def plyflatten(cloud, xoff, yoff, resolution, xsize, ysize, radius, sigma, raster=None):
    """
    Projects a points cloud into the raster band(s) of a raster image

    Args:
        cloud: A nb_points x (2+nb_extra_columns) numpy array:
            | x0 y0 [z0 r0 g0 b0 ...] |
            | x1 y1 [z1 r1 g1 b1 ...] |
            | ...                     |
            | xN yN [zN rN gN bN ...] |
            x, y give positions of the points into the final raster, the "extra
            columns" give the values
        xoff, yoff: offset position (upper left corner) considering the georeferenced image
        resolution: resolution of the output georeferenced image
        xsize, ysize: size of the georeferenced image
        radius: controls the spread of the blob from each point
        sigma: radius of influence for each point (unit: pixel)
        std (bool): if True, return additional channels with standard deviations

    Returns;
        A numpy array of shape (ysize, xsize, n) where n is nb_extra_columns if
            std=False and 2*nb_extra_columns if std=True
    """
    nb_points, nb_extra_columns = cloud.shape[0], cloud.shape[1] - 2
    if raster is None:
        raster = Raster(xoff, yoff, resolution, xsize, ysize, radius, sigma, nb_extra_columns)
    else:
        assert nb_extra_columns == raster.nb_extra_columns

    # Set expected args and return types
    raster_shape = (raster.xsize * raster.ysize, raster.nb_extra_columns)
    lib.rasterize_cloud.argtypes = (
        ndpointer(dtype=ctypes.c_double, shape=np.shape(cloud)),
        ndpointer(dtype=ctypes.c_float, shape=raster_shape),
        ndpointer(dtype=ctypes.c_float, shape=raster_shape),
        ndpointer(dtype=ctypes.c_float, shape=raster_shape),
        ndpointer(dtype=ctypes.c_float, shape=raster_shape),
        ndpointer(dtype=ctypes.c_float, shape=(raster.xsize * raster.ysize, 1)),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_double,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_float,
    )

    # Call rasterize_cloud function from libplyflatten.so
    lib.rasterize_cloud(
        np.ascontiguousarray(cloud.astype(np.float64)),
        raster.avg,
        raster.std,
        raster.min,
        raster.max,
        raster.cnt,
        nb_points,
        raster.nb_extra_columns,
        raster.xoff,
        raster.yoff,
        raster.resolution,
        raster.xsize,
        raster.ysize,
        raster.radius,
        raster.sigma,
    )

    return raster


def plyflatten_from_plyfiles_list(
    clouds_list, resolution, radius=0, roi=None, sigma=None, std=False, amin=False, amax=False
):
    """
    Projects a points cloud into the raster band(s) of a raster image (points clouds as files)

    Args:
        clouds_list: list of cloud.ply files
        resolution: resolution of the georeferenced output raster file
        roi: region of interest: (xoff, yoff, xsize, ysize), compute plyextrema if None
        std (bool): if True, return additional channels with standard deviations

    Returns:
        raster: georeferenced raster
        profile: profile for rasterio
    """

    # region of interest (compute plyextrema if roi is None)
    xoff, yoff, xsize, ysize = compute_roi_from_ply_list(clouds_list, resolution) if roi is None else roi

    raster = None
    for cloud in clouds_list:
        cloud_data, _ = utils.read_3d_point_cloud_from_ply(cloud)
        current_cloud = cloud_data.astype(np.float64)

        # The copy() method will reorder to C-contiguous order by default:
        cloud = current_cloud.copy()
        sigma = float("inf") if sigma is None else sigma
        raster = plyflatten(cloud, xoff, yoff, resolution, xsize, ysize, radius, sigma, raster)

    raster_shape = (raster.xsize * raster.ysize, raster.nb_extra_columns)
    lib.finishing_touches.argtypes = (
        ndpointer(dtype=ctypes.c_float, shape=raster_shape),
        ndpointer(dtype=ctypes.c_float, shape=raster_shape),
        ndpointer(dtype=ctypes.c_float, shape=raster_shape),
        ndpointer(dtype=ctypes.c_float, shape=raster_shape),
        ndpointer(dtype=ctypes.c_float, shape=(raster.xsize * raster.ysize, 1)),
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    )

    lib.finishing_touches(
        raster.avg,
        raster.std,
        raster.min,
        raster.max,
        raster.cnt,
        raster.nb_extra_columns,
        raster.xsize,
        raster.ysize,
    )

    # Transform result into a numpy array
    raster_ = raster.avg.reshape((raster.ysize, raster.xsize, raster.nb_extra_columns))
    if std:
        raster_std = raster.std.reshape((raster.ysize, raster.xsize, raster.nb_extra_columns))
        raster_ = np.dstack((raster_, raster_std))
    if amin:
        raster_min = raster.min.reshape((raster.ysize, raster.xsize, raster.nb_extra_columns))
        raster_ = np.dstack((raster_, raster_min))
    if amax:
        raster_max = raster.max.reshape((raster.ysize, raster.xsize, raster.nb_extra_columns))
        raster_ = np.dstack((raster_, raster_max))

    crs, crs_type = utils.crs_from_ply(clouds_list[0])
    crs_proj = utils.rasterio_crs(utils.crs_proj(crs, crs_type))

    # construct profile dict
    profile = dict()
    profile["tiled"] = True
    profile["compress"] = "deflate"
    profile["predictor"] = 2
    profile["nodata"] = float("nan")
    profile["crs"] = crs_proj
    profile["transform"] = affine.Affine(resolution, 0.0, xoff, 0.0, -resolution, yoff)

    return raster_, profile
