# PlyFlatten

Take a series of ply files and produce a digital elevation map

## Installation

```
pip install plyflatten
```

## Usage

This package comes with a command-line tool:
```
$ plyflatten --help
usage: plyflatten [-h] [--resolution RESOLUTION]
                  list_plys [list_plys ...] dsm_path

plyflatten: Take a series of ply files and produce a digital elevation map

positional arguments:
  list_plys             Space-separated list of .ply files
  dsm_path              Path to output DSM file

optional arguments:
  -h, --help            show this help message and exit
  --resolution RESOLUTION
                        Resolution of the DSM in meters (defaults to 1m)
```

Try using it on the test data provided with the repository:
```
plyflatten tests/data/{1,2}.ply out.tiff --resolution 2
```

## Contributing

To work on this project, install the development requirements by running:
```
make install
```

The tests can be run with:
```
make test
```
