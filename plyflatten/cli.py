import argparse
import os
import sys

import rasterio

from plyflatten import plyflatten_from_plyfiles_list
from plyflatten.__about__ import __description__, __title__


def main():
    parser = argparse.ArgumentParser(description=(f"{__title__}: {__description__}"))
    parser.add_argument("list_plys", nargs="+", help=("Space-separated list of .ply files"))
    parser.add_argument("dsm_path", help=("Path to output DSM file"))
    parser.add_argument(
        "--resolution",
        default=1,
        type=float,
        help=("Resolution of the DSM in meters (defaults to 1m)"),
    )
    args = parser.parse_args()
    raster, raster_std, profile = plyflatten_from_plyfiles_list(args.list_plys, args.resolution)
    raster = raster[:, :, 0]
    profile["dtype"] = raster.dtype
    profile["height"] = raster.shape[0]
    profile["width"] = raster.shape[1]
    profile["count"] = 1
    profile["driver"] = "GTiff"

    with rasterio.open(args.dsm_path, "w", **profile) as f:
        f.write(raster, 1)

    raster_std = raster_std[:, :, 0]
    dsm_path_id, dsm_path_extension = os.path.splitext(os.path.basename(args.dsm_path))
    std_path = os.path.join(
        os.path.dirname(args.dsm_path), dsm_path_id + "_std" + dsm_path_extension
    )
    with rasterio.open(std_path, "w", **profile) as f:
        f.write(raster_std, 1)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
