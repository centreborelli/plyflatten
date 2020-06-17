import re
from distutils.version import LooseVersion

import numpy as np
import plyfile
import pyproj
import rasterio
from pyproj.enums import WktVersion
from rasterio.crs import CRS as RioCRS


class InvalidPlyCommentsError(Exception):
    pass


def rasterio_crs(proj_crs):
    """
    Return a rasterio.crs.CRS object that corresponds to the given parameters.
    See: https://pyproj4.github.io/pyproj/stable/crs_compatibility.html#converting-from-pyproj-crs-crs-to-rasterio-crs-crs

    Args:
        proj_crs (pyproj.crs.CRS): pyproj CRS object

    Returns:
        rasterio.crs.CRS: object that can be used with rasterio
    """
    if LooseVersion(rasterio.__gdal_version__) < LooseVersion("3.0.0"):
        rio_crs = RioCRS.from_wkt(proj_crs.to_wkt(WktVersion.WKT1_GDAL))
    else:
        rio_crs = RioCRS.from_wkt(proj_crs.to_wkt())
    return rio_crs


def crs_proj(crs_params, crs_type="UTM"):
    """
    Return a pyproj.Proj object that corresponds
    to the given UTM zone string or the CRS parameters

    Args:
        crs_params (int, str, dict): UTM zone number + hemisphere (eg: '30N') or an authority
            string (EPSG:xxx) or any other format supported by pyproj
        crs_type (str): 'UTM' (default) or 'CRS'

    Returns:
        pyproj.Proj or pyproj.crs.CRS: object that can be used to transform coordinates
    """
    if crs_type == "UTM":
        zone_number = crs_params[:-1]
        hemisphere = crs_params[-1]
        crs_params = {
            "proj": "utm",
            "zone": zone_number,
            "ellps": "WGS84",
            "datum": "WGS84",
            "south": (hemisphere == "S"),
        }
    elif crs_type == "CRS":
        if isinstance(crs_params, str):
            try:
                crs_params = int(crs_params)
            except (ValueError, TypeError):
                pass
    return pyproj.crs.CRS(crs_params)


def crs_code_from_comments(comments, crs_type="UTM"):
    re_type = "[0-9]{1,2}[NS]" if crs_type == "UTM" else ".*"
    regex = r"^projection: {} ({})".format(crs_type, re_type)
    crs_code = None
    for comment in comments:
        s = re.search(regex, comment)
        if s:
            crs_code = s.group(1)
    return crs_code


def crs_from_ply(ply_path):
    _, comments = read_3d_point_cloud_from_ply(ply_path)
    crs_params = crs_code_from_comments(comments, crs_type="CRS")

    utm_zone = None
    if not crs_params:
        utm_zone = crs_code_from_comments(comments, crs_type="UTM")

    if not crs_params and not utm_zone:
        raise InvalidPlyCommentsError(
            "Invalid header comments {} for ply file {}".format(comments, ply_path)
        )

    crs_type = "CRS" if crs_params else "UTM"

    return crs_params or utm_zone, crs_type


def read_3d_point_cloud_from_ply(path_to_ply_file):
    """
    Read a 3D point cloud from a ply file and return a numpy array.

    Args:
        path_to_ply_file (str): path to a .ply file

    Returns:
        numpy array with the list of 3D points, one point per line
        list of strings with the ply header comments
    """
    plydata = plyfile.PlyData.read(path_to_ply_file)
    d = np.asarray(plydata["vertex"].data)
    array = np.column_stack([d[p.name] for p in plydata["vertex"].properties])
    return array, plydata.comments
