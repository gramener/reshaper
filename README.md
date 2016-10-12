# Reshaper

Splits and recombines shapefiles based on lat-long data.

## Installation

    pip install reshaper

## Usage

To split a state map based on a branch list, use:

    reshaper state.shp branch.csv output.shp --id branchname --lat lat_col --lng lng_col

This takes 3 arguments:

- `state.shp`: path to the original shapefile
- `branch.csv`: path to the CSV file with points data. The output shapefile will
  have one shape per row of this file
- `output.shp`: path to the output shapefile

`branch.csv` should have at least these 3 indicators:

- `--id branchname`: indicates that the `branchname` column holds the branch
  identifier. The values in this column must be unique
- `--lat lat_col`: the `lat_col` column holds the latitude in degrees
- `--lng lng_col`: the `lng_col` column holds the longitude in degrees

The program splits and re-combines shapes based the following logic:

- If a state does not have a branch, assign it fully to the nearest branch
- If a state has only one branch, assign it fully to that branch
- If a state has multiple branches, split it between the branches and assign each broken state to the respective branch

The output shapefile has an `id` column holding the `--id` value.


## Building

To [distribute](https://packaging.python.org/en/latest/distributing.html), run:

    rm -rf build dist
    flake8 .
    python setup.py test
    python setup.py sdist bdist_wheel --universal
    twine upload dist/*
