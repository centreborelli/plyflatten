import re

import numpy as np
import plyfile
import pyproj


class InvalidPlyCommentsError(Exception):
    pass


def crs_proj(crs_code, crs_type="UTM"):
    """
    Return a pyproj.Proj object that corresponds
    to the given UTM zone string or EPSG code

    Args:
        crs_code (str): UTM zone number + hemisphere (eg: '30N') or EPSG code
        crs_type (str): 'UTM' (default) or 'EPSG'

    Returns:
        pyproj.Proj: object that can be used to transform coordinates
    """
    if crs_type == "UTM":
        zone_number = crs_code[:-1]
        hemisphere = crs_code[-1]
        return pyproj.Proj(
            proj="utm", zone=zone_number, ellps="WGS84", datum="WGS84", south=(hemisphere == "S")
        )
    elif crs_type == "EPSG":
        return pyproj.Proj("epsg:{}".format(crs_code))


def crs_code_from_comments(comments, crs_type="UTM"):
    re_type = "[0-9]{1,2}[NS]" if crs_type == "UTM" else "[0-9]{4,5}"
    regex = r"^projection: {} ({})".format(crs_type, re_type)
    crs_code = None
    for comment in comments:
        s = re.search(regex, comment)
        if s:
            crs_code = s.group(1)
    return crs_code


def crs_from_ply(ply_path):
    _, comments = read_3d_point_cloud_from_ply(ply_path)
    utm_zone = crs_code_from_comments(comments, crs_type="UTM")

    epsg_code = None
    if not utm_zone:
        epsg_code = crs_code_from_comments(comments, crs_type="EPSG")

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
