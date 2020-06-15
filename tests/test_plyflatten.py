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
def expected_raster():
    here = os.path.abspath(os.path.dirname(__file__))

    with rasterio.open(os.path.join(here, "data", "result.tiff")) as f:
        raster = f.read(1)

    return raster


@pytest.fixture()
def ply_file_with_crs():
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(here, "data", "crs.ply")


def test_plyflatten_from_plyfiles_list(clouds_list, expected_raster):
    raster, _ = plyflatten_from_plyfiles_list(clouds_list, resolution=2)
    raster = raster[:, :, 0]

    np.testing.assert_allclose(expected_raster, raster, equal_nan=True)


def test_resolution(clouds_list, expected_raster):
    raster, _ = plyflatten_from_plyfiles_list(clouds_list, resolution=4)
    raster = raster[:, :, 0]

    assert raster.shape[0] == expected_raster.shape[0] / 2
    assert raster.shape[1] == expected_raster.shape[1] / 2


def test_ply_comment_crs(ply_file_with_crs):
    crs_params, crs_type = utils.crs_from_ply(ply_file_with_crs)
    assert crs_type == "CRS"

    pyproj_crs = utils.crs_proj(crs_params, crs_type)
    assert isinstance(pyproj_crs, pyproj.crs.CRS)
