import re

import numpy as np
import plyfile
import pyproj


class InvalidPlyCommentsError(Exception):
    pass


def utm_proj(utm_zone):
    """
    Return a pyproj.Proj object that corresponds
    to the given utm_zone string

    Args:
        utm_zone (str): UTM zone number + hemisphere (eg: '30N')

    Returns:
        pyproj.Proj: object that can be used to transform coordinates
    """
    zone_number = utm_zone[:-1]
    hemisphere = utm_zone[-1]
    return pyproj.Proj(
        proj="utm", zone=zone_number, ellps="WGS84", datum="WGS84", south=(hemisphere == "S")
    )


def utm_zone_from_ply(ply_path):
    _, comments = read_3d_point_cloud_from_ply(ply_path)
    regex = r"^projection: UTM (\d{1,2}[NS])"
    utm_zone = None
    for comment in comments:
        s = re.search(regex, comment)
        if s:
            utm_zone = s.group(1)

    if not utm_zone:
        raise InvalidPlyCommentsError(
            "Invalid header comments {} for ply file {}".format(comments, ply_path)
        )

    return utm_zone


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
