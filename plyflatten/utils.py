import re

import numpy as np
import plyfile
import pyproj


class InvalidPlyCommentsError(Exception):
    pass


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
        return pyproj.Proj(
            proj="utm", zone=zone_number, ellps="WGS84", datum="WGS84", south=(hemisphere == "S")
        )
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
    utm_zone = crs_code_from_comments(comments, crs_type="UTM")

    crs_params = None
    if not utm_zone:
        crs_params = crs_code_from_comments(comments, crs_type="CRS")

    if not utm_zone and not crs_params:
        raise InvalidPlyCommentsError(
            "Invalid header comments {} for ply file {}".format(comments, ply_path)
        )

    crs_type = "UTM" if utm_zone else "CRS"

    return utm_zone or crs_params, crs_type


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
