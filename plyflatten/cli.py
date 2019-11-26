import argparse
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
    raster, profile = plyflatten_from_plyfiles_list(args.list_plys, args.resolution)
    raster = raster[:, :, 0]
    profile["dtype"] = raster.dtype
    profile["height"] = raster.shape[0]
    profile["width"] = raster.shape[1]
    profile["count"] = 1
    profile["driver"] = "GTiff"

    with rasterio.open(args.dsm_path, "w", **profile) as f:
        f.write(raster, 1)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
