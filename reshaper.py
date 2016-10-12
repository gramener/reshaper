'''
Splits and recombines shapefiles based on lat-long data.

Setup:

    # Install the GDAL library to process shapefiles
    conda install gdal

'''
import os
import logging
import argparse
import pandas as pd
import scipy.spatial
from tqdm import trange
from osgeo import ogr
from collections import defaultdict, Counter


def find_feature(layer, lng, lat):
    '''Return the first feature that contains (lng, lat) in the layer'''
    pt = ogr.Geometry(ogr.wkbPoint)
    pt.SetPoint_2D(0, lng, lat)
    layer.SetSpatialFilter(pt)
    for feature in layer:
        ply = feature.GetGeometryRef()  # ???
        if ply.Contains(pt):
            return feature


def split(geometry, coords):
    # Add points at infinity
    m = max(abs(coords.max()), abs(coords.min())) * 1000
    inf_coords = pd.np.append(coords, [[m, m], [m, -m], [-m, -m], [-m, m]], axis=0)
    voronoi = scipy.spatial.Voronoi(inf_coords)

    # Compute the voronoi shapes for each coord
    for region_index in voronoi.point_region[:len(coords)]:
        ring = ogr.Geometry(ogr.wkbLinearRing)
        region = voronoi.regions[region_index]
        for vertex_index in region:
            ring.AddPoint(*voronoi.vertices[vertex_index])
        ring.AddPoint(*voronoi.vertices[region[0]])     # Close the ring
        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)
        yield geometry.Intersection(poly)


def main(infile, points, outfile, group, lat='latitude', lon='longitude'):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    shape = driver.Open(infile)
    # shape = driver.Open('Export_Output_2.shp')
    layer = shape.GetLayer()

    # If any of the groups are not present, ignore those rows
    points = points.dropna(subset=[group])

    logging.info('Get centroids of features to locate nearest feature...')
    feature_coords = []
    for index in trange(layer.GetFeatureCount()):
        feature = layer.GetFeature(index)
        feature_coords.append(feature.GetGeometryRef().Centroid().GetPoints()[0])
    feature_tree = scipy.spatial.cKDTree(feature_coords)

    # feature_points[id] - lists all points in a shape
    # point.feature - the shape a given point is in
    logging.info('Find nearest feature for each point...')
    feature_points = defaultdict(list)
    outside_points = []
    for index in trange(len(points)):
        point = points.iloc[index, :]
        feature = find_feature(layer, point[lon], point[lat])
        # If the point is not in any feature, find the nearest
        if feature is None:
            feature_index = feature_tree.query([[point[lon], point[lat]]])[1][0]
            feature = layer.GetFeature(feature_index)
            outside_points.append([feature, point])
        feature_points[feature.GetFID()].append(point)
    logging.warn('%d points were outside shape. Using nearest features', len(outside_points))

    point_coords = points[[lon, lat]].values
    point_tree = scipy.spatial.cKDTree(point_coords)

    logging.info('Splitting features by group')
    layer.SetSpatialFilter(None)
    group_freq = Counter()          # group_freq[0] = # of features with 0 groups, etc
    target = defaultdict(list)      # target[group] = [geometries corresponding to group]
    for index in trange(layer.GetFeatureCount()):
        pts = feature_points.get(index, [])
        groups = {point[group] for point in pts}
        feature = layer.GetFeature(index)
        geometry = feature.GetGeometryRef().Clone()
        group_freq[len(groups)] += 1
        # For features that don't have a group, pick the nearest point's group
        if len(groups) == 0:
            centroid = geometry.Centroid()
            p = centroid.GetPoints()
            feature_centroid = p[:2]
            nearest_point_index = point_tree.query(feature_centroid)[1][0]
            target[points.iloc[nearest_point_index][group]].append(geometry)
        # # For features with exactly 1 group, assign the group to that feature
        if len(groups) == 1:
            target[list(groups)[0]].append(geometry)
        # For features that have multiple points, split them
        elif len(groups) > 1:
            coords = pd.np.array([[pt[lon], pt[lat]] for pt in pts])
            for index, new_geometry in enumerate(split(geometry, coords)):
                target[pts[index][group]].append(new_geometry)

    # Save into shapefile
    logging.info('Merging broken features by group')
    if os.path.exists(outfile):
        driver.DeleteDataSource(outfile)
    data_source = driver.CreateDataSource(outfile)
    out_layer = data_source.CreateLayer('target', geom_type=ogr.wkbPolygon)
    feature_defn = out_layer.GetLayerDefn()
    id_field = ogr.FieldDefn('id', ogr.OFTString)
    out_layer.CreateField(id_field)
    groups = list(target.keys())
    for index in trange(len(groups)):
        group = groups[index]
        geometries = target[group]
        geom = geometries[0]
        for geometry in geometries[1:]:
            geom = geom.Union(geometry)
        feature = ogr.Feature(feature_defn)
        feature.SetGeometry(geom)
        feature.SetField('id', str(group))
        out_layer.CreateFeature(feature)

    data_source.Destroy()
    logging.info('Created %s', outfile)


def cmdline():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        description=__doc__.strip().splitlines()[0],                # First line of the docstring
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,     # Print default values
    )
    parser.add_argument('input', help='input shape file')
    parser.add_argument('points', help='CSV file with lat-lng data')
    parser.add_argument('output', help='output shape file')

    parser.add_argument('--id', default='id',
                        help='CSV column to create shapes for (e.g. branchname)')
    parser.add_argument('--lat', default='latitude', help='Latitude column in points CSV file')
    parser.add_argument('--lng', default='longitude', help='Longitude column in points CSV file')

    args = parser.parse_args()

    points_data = pd.read_csv(args.points, encoding='cp1252')
    main(args.input, points_data, args.output, args.id, args.lat, args.lng)


if __name__ == '__main__':
    cmdline()
