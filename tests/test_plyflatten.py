# pylint: disable=redefined-outer-name, missing-docstring
import os

import pytest
import rasterio

from plyflatten import plyflatten_from_plyfiles_list


@pytest.fixture()
def clouds_list():
    here = os.path.abspath(os.path.dirname(__file__))

    clouds_list = []
    for i in [1, 2]:
        clouds_list.append(os.path.join(here, "data", f"{i}.ply"))

    return clouds_list


def test_plyflatten_from_plyfiles_list(clouds_list):
    raster, profile = plyflatten_from_plyfiles_list(clouds_list, resolution=1)

    assert 1
