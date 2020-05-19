import re

import numpy as np
import plyfile
import pyproj


class InvalidPlyCommentsError(Exception):
    pass


def crs_proj(utm_zone, crs_type="UTM"):
    """
    Return a pyproj.Proj object that corresponds
    to the given utm_zone string or EPSG code

    Args:
        crs_type (str): 'UTM' (default) or 'EPSG'
        utm_zone (str): UTM zone number + hemisphere (eg: '30N') or EPSG code

    Returns:
        pyproj.Proj: object that can be used to transform coordinates
    """
    if crs_type == "UTM":
        zone_number = utm_zone[:-1]
        hemisphere = utm_zone[-1]
        return pyproj.Proj(
            proj="utm", zone=zone_number, ellps="WGS84", datum="WGS84", south=(hemisphere == "S")
        )
    elif crs_type == "EPSG":
        return pyproj.Proj("epsg:{}".format(utm_zone))


def epsg_code_from_comments(comments):
    regex = r"^projection: EPSG ([0-9]{4,5})"
    epsg_code = None
    for comment in comments:
        s = re.search(regex, comment)
        if s:
            epsg_code = s.group(1)
    return epsg_code


def crs_from_ply(ply_path):
    _, comments = read_3d_point_cloud_from_ply(ply_path)
    regex = r"^projection: UTM (\d{1,2}[NS])"
    utm_zone = None
    for comment in comments:
        s = re.search(regex, comment)
        if s:
            utm_zone = s.group(1)

    epsg_code = None
    if not utm_zone:
        epsg_code = epsg_code_from_comments(comments)

    if not utm_zone and not epsg_code:
        raise InvalidPlyCommentsError(
            "Invalid header comments {} for ply file {}".format(comments, ply_path)
        )

    crs_type = "UTM" if utm_zone else "EPSG"

    return utm_zone or epsg_code, crs_type


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
