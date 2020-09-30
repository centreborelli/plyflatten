# pylint: disable=redefined-outer-name, missing-docstring
import os

import numpy as np
import pyproj
import pytest
import rasterio

from plyflatten import plyflatten_from_plyfiles_list, utils


@pytest.fixture()
def clouds_list():
    here = os.path.abspath(os.path.dirname(__file__))

    clouds_list = []
    for i in [1, 2]:
        clouds_list.append(os.path.join(here, "data", f"{i}.ply"))

    return clouds_list


@pytest.fixture()
def expected_dsm():
    here = os.path.abspath(os.path.dirname(__file__))

    with rasterio.open(os.path.join(here, "data", "result.tiff")) as f:
        raster = f.read(1)
        gsd = f.res

    return raster, gsd


@pytest.fixture()
def expected_std():
    here = os.path.abspath(os.path.dirname(__file__))

    with rasterio.open(os.path.join(here, "data", "std.tiff")) as f:
        raster = f.read(1)

    return raster


@pytest.fixture()
def ply_file_with_crs():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, "data", "crs.ply")


def test_plyflatten_from_plyfiles_list(clouds_list, expected_dsm):
    raster, _ = plyflatten_from_plyfiles_list(clouds_list, resolution=2)
    raster = raster[:, :, 0]

    expected_raster, _ = expected_dsm
    np.testing.assert_allclose(expected_raster, raster, equal_nan=True)


def test_std(clouds_list, expected_std):
    raster, _ = plyflatten_from_plyfiles_list(clouds_list, resolution=1, std=True)
    assert raster.shape[2] == 2
    raster = raster[:, :, 1]

    np.testing.assert_allclose(expected_std, raster, equal_nan=True)


def test_resolution(clouds_list, expected_dsm, r=4):
    raster, _ = plyflatten_from_plyfiles_list(clouds_list, resolution=r)
    raster = raster[:, :, 0]

    reference, (rx, ry) = expected_dsm
    assert abs(raster.shape[0] * r - reference.shape[0] * rx) <= 2 * max(r, rx)
    assert abs(raster.shape[1] * r - reference.shape[1] * ry) <= 2 * max(r, ry)


def test_ply_comment_crs(ply_file_with_crs):
    crs_params, crs_type = utils.crs_from_ply(ply_file_with_crs)
    assert crs_type == "CRS"

    pyproj_crs = utils.crs_proj(crs_params, crs_type)
    assert isinstance(pyproj_crs, pyproj.crs.CRS)
