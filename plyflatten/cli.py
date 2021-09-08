import argparse
import sys

import rasterio

from plyflatten import plyflatten_from_plyfiles_list
from plyflatten.__about__ import __description__, __title__


def main():
    parser = argparse.ArgumentParser(description=(f"{__title__}: {__description__}"))
    parser.add_argument("list_plys", nargs="+", help=("Space-separated list of .ply files"))
    parser.add_argument("dsm_path", help=("Path to output average height DSM file (average heights)"))
    parser.add_argument("--std", help=("Path to (optional) output standard deviation DSM file"))
    parser.add_argument("--min", help=("Path to (optional) output minimum height DSM file"))
    parser.add_argument("--max", help=("Path to (optional) output maximum height DSM file"))
    parser.add_argument(
        "--resolution",
        default=1,
        type=float,
        help=("Resolution of the DSM in meters (defaults to 1m)"),
    )
    args = parser.parse_args()
    std_ = args.std is not None
    min_ = args.min is not None
    max_ = args.min is not None

    raster, profile = plyflatten_from_plyfiles_list(
        args.list_plys, args.resolution, std=std_, min=min_, max=max_
    )
    profile["dtype"] = raster.dtype
    profile["height"] = raster.shape[0]
    profile["width"] = raster.shape[1]
    profile["count"] = 1
    profile["driver"] = "GTiff"

    # 1. write avg DSM
    # plyflatten outputs a height DSM by default, but extra_col_idx can be hardcoded to change the magnitude
    # e.g. if the input clouds have format [x y z r g b], set extra_col_idx = 1 to compute avg/std/min/max of r channel
    extra_col_idx = 0
    with rasterio.open(args.dsm_path, "w", **profile) as f:
        f.write(raster[:, :, extra_col_idx], 1)

    # 2. (optional) write std, min and max DSM
    extra_stats_total = 1 + std_ + min_ + max_
    nb_extra_columns = raster.shape[2] // extra_stats_total
    assert raster.shape[2] % extra_stats_total == 0
    extra_stats_count = 1
    for b, extra_stat_path in zip([std_, min_, max_], [args.std, args.min, args.max]):
        if b:
            with rasterio.open(extra_stat_path, "w", **profile) as f:
                f.write(raster[:, :, extra_stats_count * nb_extra_columns + extra_col_idx], 1)
            extra_stats_count += 1

if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
