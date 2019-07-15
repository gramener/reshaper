# Reshaper

Splits and recombines shapefiles based on lat-long data.

## Installation

    conda install -c conda-forge gdal
    pip install reshaper

## Usage

To split a state map based on a branch list, use:

    reshaper state.shp branch.csv output.shp \
        --id <ID column> \
        --lat <Latitude column> \
        --lng <Longitude column> \
        --col <Any additional columns to add>

The arguments are:

- `state.shp`: path to the original shapefile
- `branch.csv`: path to the CSV file with points data. The output shapefile will
  have one shape per row of this file
- `output.shp`: path to the output shapefile
- `--id branchname`: indicates that the `branchname` column holds the branch
  identifier. The values in this column must be unique
- `--lat col1`: the `col1` column holds the latitude in degrees
- `--lng col2`: the `col2` column holds the longitude in degrees
- `--col col3`: add `col3` column to the Shapefile attributes. You can specify
  multiple columns via `--col`

The CSV file should have at least these 3 columns: ID, latitude and longitude.

The program splits and re-combines shapes based the following logic:

- If a state does not have a branch, assign it fully to the nearest branch
- If a state has only one branch, assign it fully to that branch
- If a state has multiple branches, split it between the branches and assign each broken state to the respective branch

The output shapefile attributes include the `--id` column and any other columns
specified via `--col`.

## Release

Change the `"version"` in `setup.py` to `"x.x.x"`, commit and tag:

    git commit . -m"Describe features / bug fixes"
    git tag -a vx.x.x -m"one-line summary of release"

To [distribute](https://packaging.python.org/en/latest/distributing.html), run:

    rm -rf build dist
    flake8 .
    python setup.py test
    python setup.py sdist bdist_wheel --universal
    twine upload dist/*
