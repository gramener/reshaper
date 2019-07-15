'''
Merge attributes from the source shapefile into the target scaling by area.

conda install -c conda-forge geopandas
export GDAL_DATA="C:/anaconda/3.6/Library/share/gdal/"
'''
import logging
import argparse
import geopandas as gpd


def map_merge(left, right, metrics=''):
    '''
    left is a shapefile (e.g. village shapes).
    right is a similar shapefile with data attributes (e.g. constituencies, voronoi shape file).

    This function returns left shapefile with specified attributes from right shapefile added.
    Numeric  attributes are distributed based on an area weightage.
    (In the future, we may want to tweak the weightages.)
    '''
    shp_left = gpd.GeoDataFrame.from_file(left)
    shp_right = gpd.GeoDataFrame.from_file(right)
    # Precompute the areas
    shp_left['AREA'] = shp_left.geometry.area
    shp_right['AREA'] = shp_right.geometry.area

    # Filter None values from shp_right, shp_left
    # shp_left.dropna(inplace=True)
    # shp_right.dropna(inplace=True)

    # Join the shapes. This creates a GeoDataFrame with one polygon per
    # intersection. Attributes from both DataFrames are present, suffixed with
    # _left and _right where there's an ovelap
    merged = gpd.sjoin(shp_left, shp_right).reset_index().rename(
        columns={'index': 'index_left'})

    # sjoin does not create a new geometry column. It uses the left.geometry
    # We create a new geometry that is the intersection of the left and right.
    # TODO: optimize, or find a way to do this natively in geopandas
    def get_intersection(row):
        left_geom = shp_left['geometry'][row['index_left']]
        right_geom = shp_right['geometry'][row['index_right']]
        return left_geom.intersection(right_geom)

    merged['geometry'] = merged.apply(get_intersection, axis=1)
    merged['AREA'] = merged.geometry.area

    # Move a metric from the right shapefile to the left by weighting it by AREA
    # default to all columns except geometry and AREA
    if not metrics:
        # append all columns except geometry and area
        metrics = list(shp_right.columns)
        for m in ['geometry', 'AREA']:
            metrics.remove(m)

    for metric in metrics:
        dtype = shp_right[metric].dtype.type
        print('Processing metric', metric, 'type:', dtype)
        # could be preferable to use a test based on dtype
        if gpd.np.issubdtype(dtype, gpd.np.number):
            # scale numeric attributes
            shp_left[metric] = 0.0
            for index, group in merged.groupby('index_left'):
                scale = group['AREA'] / group['AREA_right']
                shp_left.loc[index, metric] = (scale * group[metric]).sum()
        else:
            # copy non-numeric attributes
            shp_left[metric] = shp_right[metric]
    return {
        'shape': shp_left,
        'data': merged,
    }


def cmdline():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        # First line of the docstring
        description=__doc__.strip().splitlines()[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter  # Print default values
    )
    parser.add_argument('left', help='left shape file')
    parser.add_argument('right', help='second shape file')
    parser.add_argument('output', help='output folder name')
    parser.add_argument('-m', '--metrics', nargs='+', default=[],
                        help='metrics from second file to include in first. Expects a comma separated string')

    args = parser.parse_args()

    output = args.output
    if not output:
        output = args.left + '-out'
    res = map_merge(args.left, args.right, args.metrics)
    res['shape'].to_file(output)
    res['data'].to_excel(output + '.xlsx')
    return res


if __name__ == '__main__':
    cmdline()
