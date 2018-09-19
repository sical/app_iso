# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 13:31:04 2018

@author: thomas
"""
import os
import math
import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim, Photon
import geojson
import osmnx as ox
import json
import numpy as np
from shapely.geometry import MultiPolygon, Point, Polygon
from pyproj import transform, Proj 
import copy
import time

from bokeh.models import ColumnDataSource, GeoJSONDataSource, HoverTool

geolocator = Nominatim(user_agent="app") #https://operations.osmfoundation.org/policies/nominatim/
#https://geopy.readthedocs.io/en/stable/#nominatim

geolocator = Nominatim()


#def gdf_to_geojson(gdf, properties):
#    """
#    @param gdf (GeoPandas GeoDataframe): GeoDataframe (polygons) 
#    @param properties (list): list of property columns
#    
#    Explanations for reverse and nested lists: 
#        - https://tools.ietf.org/html/rfc7946#section-3.1.6
#        - https://tools.ietf.org/html/rfc7946#appendix-A.3
#    
#    Inspired by: http://geoffboeing.com/2015/10/exporting-python-data-geojson/
#    
#    Returns GeoJson object that could be used in bokeh as GeoJsonDataSource
#    """
#    
#    geojson_ = {"type":"FeatureCollection", "features":[]}
#    for line in gdf.itertuples():
#        feature = {"type":"Feature",
#                   "properties":{},
#                   "geometry":{
#                           "type":"MultiPolygon",
#                           "coordinates":[]
#                           }
#                   }
#        
#        l_tmp = []
#        for poly in line.geometry:
#            l_poly = []
#            for pt in poly.exterior.coords:
#                l_poly.extend([[pt[0],pt[1]]])
#            l_tmp.append(l_poly)
#        feature["geometry"]["coordinates"] = [list(reversed(l_tmp))]
#        
#        if (properties != []) or (properties is not None):
#            for prop in properties:
#                feature["properties"][prop] = line[properties.index(prop)]
#        
#            geojson_["features"].append(feature)
#        else:
#            feature.pop(properties, None)
#    return json.dumps(geojson_)

def seconds_to_time(seconds, option="all"): 
    milliseconds = int(round(seconds * 1000))
    s, ms = divmod(milliseconds, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    time_format = "%02d:%02d:%02d:%02d" % (h, m, s, ms)
    
    if option == "all":
        return time_format, milliseconds
    elif option == "ms":
        return milliseconds
    elif option == "format":
        return time_format
    

def time_profile(start, option="all"):
    end = time.time()
    seconds = seconds_to_time(end - start, option=option)
    
    return seconds
    

def colors_blend(c1, c2):
    if "#" in str(c1):
        c1 = hex2rgb(c1)
    if "#" in str(c2):
        c2 = hex2rgb(c2)
    
    if c1 == c2:
        red = int(c1[0])
        green = int(c1[1])
        blue = int(c1[2])
    else:
        red = min((int(c1[0]) + int(c2[0]))//2, 255)
        green = min((int(c1[1]) + int(c2[1]))//2, 255)
        blue = min((int(c1[2]) + int(c2[2]))//2, 255)
    
    color = "#{:02x}{:02x}{:02x}".format(red,green,blue)

    return color

def hex2rgb(hexcode):
    """
    Source:https://stackoverflow.com/questions/29643352/converting-hex-to-rgb-value-in-python,
    Answer of John1024
    Adaptation: thom
    """
    hexcode = hexcode.lstrip('#')
    rgb = tuple(int(hexcode[i:i+2], 16) for i in (0, 2 ,4))
    return rgb

def gdf_to_geojson(gdf, properties):
    """
    @param gdf (GeoPandas GeoDataframe): GeoDataframe (polygons) 
    @param properties (list): list of property columns
    
    Explanations for reverse and nested lists: 
        - https://tools.ietf.org/html/rfc7946#section-3.1.6
        - https://tools.ietf.org/html/rfc7946#appendix-A.3
    
    Inspired by: http://geoffboeing.com/2015/10/exporting-python-data-geojson/
    
    Returns GeoJson object that could be used in bokeh as GeoJsonDataSource
    """
    
    geojson_ = {
            "type":"FeatureCollection", 
            "features":[],
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3857" } },
            }
#    style_col = ["fill", "fill-opacity", "stroke", "stroke-width", "stroke-opacity"]
    
    for line in gdf.itertuples():
        if (isinstance(line.geometry, MultiPolygon)):
            for poly in line.geometry:
                l_poly = []
                for pt in poly.exterior.coords:
                    l_poly.extend([[pt[0],pt[1]]])
                feature = {"type":"Feature",
                       "properties":{},
                       "geometry":{
                               "type":"Polygon",
                               "coordinates":[]
                               },
                       }
                feature["geometry"]["coordinates"] = [list(reversed(l_poly))]
            
                if (properties != []) or (properties is not None):
                    for prop in properties:
                        value_prop = gdf.at[line.Index, prop]
                        if type(value_prop) == np.int64 or type(value_prop) == np.int32:
                            value_prop = int(value_prop)
                        feature["properties"][prop] = value_prop
                
                    geojson_["features"].append(feature)
                else:
                    feature.pop(properties, None)
        else:
            l_poly = []
            for pt in line.geometry.exterior.coords:
                l_poly.extend([[pt[0],pt[1]]])
            feature = {"type":"Feature",
                   "properties":{},
                   "geometry":{
                           "type":"Polygon",
                           "coordinates":[]
                           },
                   "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::3857" } },
                   }
            feature["geometry"]["coordinates"] = [list(reversed(l_poly))]
        
            if (properties != []) or (properties is not None):
                for prop in properties:
                    value_prop = gdf.at[line.Index, prop]
                    if type(value_prop) == np.int64 or type(value_prop) == np.int32:
                        value_prop = int(value_prop)
                    feature["properties"][prop] = value_prop
            
                geojson_["features"].append(feature)
            else:
                feature.pop(properties, None)
    
    return json.dumps(geojson_), geojson_
    
def buildings_to_datasource(polygon):
    """
    Get buildings by requesting OSM via osmnx, perimeter: polygon and transform 
    them into Bokeh GeoJSONDataSource after a reprojection into EPSG 3857
    
    @param polygon (Shapely Polygon): Polygon for request's spatial bounds
    
    Returns Bokeh GeoJSONDataSource 
    
    """
    buildings = ox.buildings.buildings_from_polygon(polygon, retain_invalid=False)
    buildings.geometry.simplify(0.8, preserve_topology=False)
    buildings = buildings.to_crs({"init":"epsg:3857"})
    
    buildings_json = gdf_to_geojson(buildings, [])
    
    return GeoJSONDataSource(geojson=buildings_json)

def _line_xs_ys(line):
    """
    Get Shapely line and extracts coordinates to return a tuple of xs and ys
    
    @param line (Shapely Linestring): Linestring
    
    Returns tuple of xs and ys
    """
    
    xs = line.xy[0]
    ys = line.xy[1]
    
    return (xs,ys)

def network_to_datasource(polygon):
    """
    Osmx request (with polygon as perimeter) to get network graph, reprojection to EPSG 3857, extract
    coordinates via  _line_xs_ys and returns Bokeh ColumnDataSource
    
    @param polygon (Shapely Polygon): Polygon for request's spatial bounds
    
    Returns Bokeh ColumnDataSource
    """
    
    G = ox.graph_from_polygon(polygon)
    nodes, edges = ox.graph_to_gdfs(G)
    edges = edges.to_crs({"init":"epsg:3857"})
    edges['pts'] = edges["geometry"].apply(lambda x: _line_xs_ys(x))
    edges[['xs', 'ys']] = edges['pts'].apply(pd.Series)
    edges = edges.drop('geometry', axis=1)
    xs = []
    ys = []
    
    for x in edges['xs']:
        xs.append(x.tolist())
        
    for y in edges['ys']:
        ys.append(y.tolist())
    
    edges = ColumnDataSource(dict(
            xs = xs,
            ys = ys
            )
    )
    
    return edges
    

def geocode(adress, places_cache):
    """
    Use geopy.geolocator (Nominatim) to get latitude and longitude (EPSG 4326) 
    of an adress
    
    @param adress (str): postal adress
    
    Returns latitude and longitude
    
    """
    if adress not in places_cache:
        location = geolocator.geocode(adress)
        if location is None:
            print ('Error on : ' + adress)
        places_cache[adress] = location.longitude, location.latitude
        time.sleep(5)
        return location.longitude, location.latitude 
    else:
        location = places_cache[adress]
        return location[0], location[1]
    

def _convert_epsg(inProj, outProj, geojson_, duration):
    """
    Reprojection of a GeoDataFrame
    
    @param inProj (str): epsg string
    @param outProj (str): epsg string
    @geojson_ (geojson): geojson object
    
    Returns GeoDataFrame with changed coordinates
    """
    gdf = gpd.GeoDataFrame.from_features(geojson_["geojson"])
    gdf.crs = {'init': inProj}
    gdf = gdf.to_crs({'init': outProj})
    gdf['time'] = duration
    
    return gdf
    

#THIS FUNCTION DOES NOT SIMPLIFY THE ISO LIKE THE GPD ONE
    
#def convert_epsg(inProj, outProj, geojson_):
#    for feature in geojson_["features"]:
#        for coords in feature["geometry"]["coordinates"]:
#            for coord in coords:
#                for xy in coord:
#                    xy[0], xy[1] = transform(inProj, outProj, xy[0], xy[1])
#
#    return geojson_

def m_poly_to_pts(multipoly):
    """
    Transforms a Shapely MultiPolygon to a tuple of x and y points
    
    @param multipoly (Shapely MultiPolygon)
    
    Returns tuple of x and y points
    """
    list_pts = []
    for x in multipoly:
        list_pts.extend(list(x.exterior.coords))      
    
    x = [pt[0] for pt in list_pts]
    y = [pt[1] for pt in list_pts]
    
    return x,y


def _cutoffs(nb_iter, step, durations=[]):
    """
    Returns a string for Navitia API for step and seconds by step
    Returns a list of time values
    
    @param nb_iter (number): numer of iterations
    @param step (number): number of steps
    """
    list_time = []
    cutoffs = ""
    cuts = []
    
    if durations != []:
        for i in durations:
            cut = "&boundary_duration[]=" + str(i)
            cutoffs += cut
            cuts.append(cut)
            list_time.append(i)
    else:
        end = step*(nb_iter+1)
    
        for i in range(step, end, step):
            cut = "&boundary_duration[]=" + str(i)
            cutoffs += cut
            cuts.append(cut)
            list_time.append(i)
    
    return cutoffs, list_time, cuts


def create_pts(gdf_poly):
    """
    Create points ColumnDataSource from GeoDataFrame of polygons
    
    @param gdf_poly (GeoDataFrame): GeoDataFrame polygons
    
    Returns ColumnDataSource
    """
    gdf_point = gdf_poly.copy()
    
    gdf_point['pts'] = gdf_point["geometry"].apply(lambda x: m_poly_to_pts(x))
    gdf_point = gdf_point.drop(columns=["geometry"])
    gdf_point[['xs', 'ys']] = gdf_point['pts'].apply(pd.Series)
    gdf_point["new_time"] = None
    
    #Create points ColumnDataSource
    l_time = []
    l_xs = []
    l_ys = []
    
    for line in gdf_point.itertuples():
        l_xs.extend(line.xs)
        l_ys.extend(line.ys)
        l_time.extend([line.time,]*len(line.xs))
    
    l_time = [int(x) for x in l_time]        
    points = ColumnDataSource(data=dict(
            x=l_xs, 
            y=l_ys, 
            time=l_time
            )
        )
    
    return points

def create_polys(gdf_poly):
    """
    Create polys ColumnDataSource from GeoDataFrame of polygons
    
    @param gdf_poly (GeoDataFrame): GeoDataFrame polygons
    
    Returns ColumnDataSource
    """
    gdf_point = gdf_poly.copy()
    
    gdf_point['pts'] = gdf_point["geometry"].apply(lambda x: m_poly_to_pts(x))
    gdf_point = gdf_point.drop(columns=["geometry"])
    gdf_point[['xs', 'ys']] = gdf_point['pts'].apply(pd.Series)
    gdf_point["new_time"] = None
    
    #Create points ColumnDataSource
    l_time = []
    l_xs = []
    l_ys = []
    
    for line in gdf_point.itertuples():
        l_xs.append(line.xs)
        l_ys.append(line.ys)
        l_time.append([line.time,]*len(line.xs))
    
    polys = ColumnDataSource(data=dict(
            xs=l_xs, 
            ys=l_ys, 
            time=l_time
            )
        )
    
    return polys
    

def _palette(list_time, dict_palette):
    """
    Returns a dict of colors => key: number, value: hexcolor
    
    @param list_time (list): list of time values
    @param dict_palette (dict): dict of palette colors
    
    """
    
    palette_nb = len(list_time)
    dict_colors = {}
    
    for item,value in dict_palette.items():
        if palette_nb > 11 or palette_nb < 3:
            print ("Please select a number inferior to 11 and superior to 3")
            return

        colors = value[palette_nb]    
        dict_colors[item] = colors
    
    return dict_colors

def convert_GeoPandas_to_Bokeh_format(gdf):
    """
    Function to convert a GeoPandas GeoDataFrame to a Bokeh
    ColumnDataSource object.
    
    @param gdf (GeoDataFrame): GeoPandas GeoDataFrame with polygon(s) under
                                the column name 'geometry.'
                                
    Returns ColumnDataSource for Bokeh.
    """
    gdf_new = gdf.drop('geometry', axis=1).copy()
    gdf_new['xs'] = gdf.apply(
            _getGeometryCoords, 
            geom ="geometry", 
            coord_type="x", 
            shape_type="polygon",
            axis=1
            )
    
    gdf_new['ys'] = gdf.apply(
            _getGeometryCoords, 
            geom ="geometry", 
            coord_type="y", 
            shape_type="polygon",
            axis=1
            )

    return ColumnDataSource(gdf_new)


def _getGeometryCoords(line, geom, coord_type, shape_type):
    """
    Returns the coordinates ('x' or 'y') of edges of a Polygon exterior.
    
    Source: http://michael-harmon.com/blog/IntroToBokeh.html
    
    @param line (GeoPandas Series): The row of each of the GeoPandas DataFrame.
    @param geom (str): The column name.
    @param coord_type (str): Whether it's 'x' or 'y' coordinate.
    """
    
    # Parse the exterior of the coordinate
    if shape_type == 'polygon':
        exterior = line[geom].exterior
        
        if coord_type == 'x':
            # Get the x coordinates of the exterior
            return list(exterior.coords.xy[0] )    
        
        elif coord_type == 'y':
            # Get the y coordinates of the exterior
            return list(exterior.coords.xy[1] )

    elif shape_type == 'point':
        exterior = line[geom]
    
        if coord_type == 'x':
            # Get the x coordinates of the exterior
            return  exterior.coords.xy[0][0] 

        elif coord_type == 'y':
            # Get the y coordinates of the exterior
            return  exterior.coords.xy[1][0]

def getXYCoords(geometry, coord_type):
    """ 
    Returns either x or y coordinates from  geometry coordinate sequence. Used with LineString and Polygon geometries.
    Source: https://automating-gis-processes.github.io/CSC18/lessons/L5/advanced-bokeh.html
    """
    if coord_type == 'x':
        return geometry.coords.xy[0]
    elif coord_type == 'y':
        return geometry.coords.xy[1]

def getPolyCoords(geometry, coord_type):
    """ 
    Returns Coordinates of Polygon using the Exterior of the Polygon.
    Source: https://automating-gis-processes.github.io/CSC18/lessons/L5/advanced-bokeh.html
    """
    ext = geometry.exterior
    return getXYCoords(ext, coord_type)

def getLineCoords(geometry, coord_type):
    """ 
    Returns Coordinates of Linestring object.
    Source: https://automating-gis-processes.github.io/CSC18/lessons/L5/advanced-bokeh.html
    """
    return getXYCoords(geometry, coord_type)

def getPointCoords(geometry, coord_type):
    """ 
    Returns Coordinates of Point object.
    Source: https://automating-gis-processes.github.io/CSC18/lessons/L5/advanced-bokeh.html
    """
    if coord_type == 'x':
        return geometry.x
    elif coord_type == 'y':
        return geometry.y

def multiGeomHandler(multi_geometry, coord_type, geom_type):
    """
    Function for handling multi-geometries. Can be MultiPoint, MultiLineString or MultiPolygon.
    Returns a list of coordinates where all parts of Multi-geometries are merged into a single list.
    Individual geometries are separated with np.nan which is how Bokeh wants them.
    # Bokeh documentation regarding the Multi-geometry issues can be found here (it is an open issue)
    # https://github.com/bokeh/bokeh/issues/2321
    Source: https://automating-gis-processes.github.io/CSC18/lessons/L5/advanced-bokeh.html
    """

    for i, part in enumerate(multi_geometry):
        # On the first part of the Multi-geometry initialize the coord_array (np.array)
        if i == 0:
            if geom_type == "MultiPoint":
                coord_arrays = np.append(getPointCoords(part, coord_type), np.nan)
            elif geom_type == "MultiLineString":
                coord_arrays = np.append(getLineCoords(part, coord_type), np.nan)
            elif geom_type == "MultiPolygon":
                coord_arrays = np.append(getPolyCoords(part, coord_type), np.nan)
        else:
            if geom_type == "MultiPoint":
                coord_arrays = np.concatenate([coord_arrays, np.append(getPointCoords(part, coord_type), np.nan)])
            elif geom_type == "MultiLineString":
                coord_arrays = np.concatenate([coord_arrays, np.append(getLineCoords(part, coord_type), np.nan)])
            elif geom_type == "MultiPolygon":
                coord_arrays = np.concatenate([coord_arrays, np.append(getPolyCoords(part, coord_type), np.nan)])

    # Return the coordinates
    return coord_arrays


def getCoords(row, geom_col, coord_type):
    """
    Returns coordinates ('x' or 'y') of a geometry (Point, LineString or Polygon) as a list (if geometry is LineString or Polygon).
    Can handle also MultiGeometries.
    Source: https://automating-gis-processes.github.io/CSC18/lessons/L5/advanced-bokeh.html
    """
    # Get geometry
    geom = row[geom_col]

    # Check the geometry type
    gtype = geom.geom_type

    # "Normal" geometries
    # -------------------

    if gtype == "Point":
        return getPointCoords(geom, coord_type)
    elif gtype == "LineString":
        return list( getLineCoords(geom, coord_type) )
    elif gtype == "Polygon":
        return list( getPolyCoords(geom, coord_type) )

    # Multi geometries
    # ----------------

    else:
        return list( multiGeomHandler(geom, coord_type, gtype) )

def getAngle(pt1, pt2):
    x_diff = pt2.x - pt1.x
    y_diff = pt2.y - pt1.y
    return math.atan2(y_diff, x_diff)

def get_notches(poly):
    """
    Determine the number of notches in a polygon object and calculate 
    normalized notches of polygon
    
    Based on: 
        "Measuring the Complexity of Polygonal Objects" 
        (Thomas Brinkhoff, Hans-Peter Kriegel, Ralf Schneider, Alexander Braun)
        http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
        
        https://github.com/pondrejk/PolygonComplexity/blob/master/PolygonComplexity.py
    
    Returns normalized notches
    """
    notches = 0 
    coords = list(poly.exterior.coords)
    for i, pt in enumerate(coords[:-1]):
        x_diff = coords[i+1][0] - pt[0]
        y_diff = coords[i+1][1] - pt[1]
        angle = math.atan2(y_diff, x_diff)
        if angle > math.pi:
            notches += 1
            
    if notches != 0:
        notches_norm = notches / (len(coords)-3)
    else:
        notches_norm = 0 
        
    return notches_norm
    
def get_stats(gdf, coeff_ampl, coeff_conv): # TODO: FALSE RESULTS, NEED TO BE CHECKED !
    """
    Get polygon's amplitude of vibration:
    
    ampl(pol) = (boundary(pol) - boundary(convexhull(pol))) / boundary(pol)
    
    Get deviation from convex hull:
    conv(pol) = (area(convexhull(pol)) - area(pol)) / area(convexhull(pol))
    
    Measure complexity
    
     Based on: 
        "Measuring the Complexity of Polygonal Objects" 
        (Thomas Brinkhoff, Hans-Peter Kriegel, Ralf Schneider, Alexander Braun)
        http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
        
        https://github.com/pondrejk/PolygonComplexity/blob/master/PolygonComplexity.py
    
    Get area, centroid, distance from each others, boudary, convex hull, 
    perimeter, number of vertices
    
    Returns dict 
    
    """
    nb = gdf['geometry'].count()
    gdf['area'] = gdf['geometry'].area
    tot_area = gdf['area'].sum()
    gdf['centroid'] = gdf['geometry'].centroid
#    gdf['distance'] = gdf['geometry'].distance()
    gdf['boundary'] = gdf['geometry'].boundary
    gdf['convex_hull'] = gdf['geometry'].convex_hull
    gdf['convex_boundary'] = gdf['geometry'].convex_hull.boundary
    gdf['convex_area'] = gdf['geometry'].convex_hull.area
    gdf['nb_vertices'] = gdf['geometry'].apply(lambda x: len(list(x.exterior.coords)))
    gdf['norm_notches'] = gdf['geometry'].apply(lambda x: get_notches(x))
    
    gdf['amplitude'] = gdf.apply(
            lambda x:(
                    x['boundary'].length - x['convex_boundary'].length
                    ) / x['boundary'].length, 
                    axis=1)
    gdf['convex'] = gdf.apply(
            lambda x: (
                    x['convex_area'] - x['area']
                    ) / x['convex_area'],
                    axis=1)
    gdf['complexity'] = gdf.apply(
            lambda x: coeff_ampl*x['amplitude'] * x['norm_notches'] + coeff_conv * x['convex'],
            axis=1
            )
    
    mean_amplitude = gdf['amplitude'].mean()
    mean_convex = gdf['convex'].mean()
    mean_norm_notches = gdf['norm_notches'].mean()
    mean_complexity = gdf['complexity'].mean()
    
    gdf['perimeter'] = gdf['geometry'].length
    tot_perimeter = gdf['perimeter'].sum()
    
    columns_drop = ["boundary", "convex_hull", "convex_boundary", "convex_area", "centroid"]
    gdf = gdf.drop(columns_drop, axis=1)
    
    return {
            'area':tot_area,
            'perimeter':tot_perimeter,
#            'distance':mean_distance,
            'nb':nb,
            'amplitude': mean_amplitude,
            'convex': mean_convex,
            'norm_notches': mean_norm_notches,
            'complexity': mean_complexity
            }, gdf
            
            
def explode(gdf):
    """    
    Will explode the geodataframe's muti-part geometries into single 
    geometries. Each row containing a multi-part geometry will be split into
    multiple rows with single geometries, thereby increasing the vertical size
    of the geodataframe. The index of the input geodataframe is no longer
    unique and is replaced with a multi-index. 

    The output geodataframe has an index based on two columns (multi-index) 
    i.e. 'level_0' (index of input geodataframe) and 'level_1' which is a new
    zero-based index for each single part geometry per multi-part geometry
    
    Args:
        gdf (gpd.GeoDataFrame) : input geodataframe with multi-geometries
        
    Returns:
        gdf (gpd.GeoDataFrame) : exploded geodataframe with each single 
                                 geometry as a separate entry in the 
                                 geodataframe. The GeoDataFrame has a multi-
                                 index set to columns level_0 and level_1
                                 
    Source: rutgerhofste, https://github.com/geopandas/geopandas/pull/671#issuecomment-366243624
        
    """
    gs = gdf.explode()
    gdf2 = gs.reset_index().rename(columns={0: 'geometry'})
    gdf_out = gdf2.merge(gdf.drop('geometry', axis=1), left_on='level_0', right_index=True)
    gdf_out = gdf_out.set_index(['level_0', 'level_1']).set_geometry('geometry')
    gdf_out.crs = gdf.crs
    return gdf_out


def measure_differential(from_place, step, gdf_poly=None, color="grey"):
    TRANSIT = 20
    p_4326 = Proj(init='epsg:4326')
    p_3857 = Proj(init='epsg:3857')
    #DIFFERENCE BETWEEN THEORITICAL AND REAL ACCESSIBILITY
    point_4326 = from_place.split(sep=";")
    point_3857 = transform(p_4326, p_3857, point_4326[0], point_4326[1])
#    distance = step * (TRANSIT*1000) // 3600
#    buffer = Point(point_3857).buffer(distance, resolution=16, cap_style=1, join_style=1, mitre_limit=1.0)
    l_buffer = []
    l_distance = []
    l_color = []
    l_time = []
    l_width = []
    j = 1
    
    
    #TEST STEP
    for i in range (1,(step//60)+1, 1):
        distance = i*60 * (TRANSIT*1000) // 3600
        buffer = Point(point_3857).buffer(distance, resolution=16, cap_style=1, join_style=1, mitre_limit=1.0)
        l_buffer.append(buffer)
        l_distance.append(distance)
        l_color.append(color)
        l_time.append(i)
        
        if j == 10:
            l_width.append(1)
            j = 1
        elif j == 5:
            l_width.append(0.5)
            j+=1
        else:
            l_width.append(0.1)
            j+=1
        

    df = pd.DataFrame(
            {
                    "radius":l_distance,
                    "color":l_color,
                    "geometry":l_buffer,
                    "time":l_time,
                    "width":l_width
            }
    )
    
    
    #######################
    
#    df = pd.DataFrame(
#            {
#                    "radius":[distance,],
#                    "color":["grey",],
#                    "geometry":[buffer,],
#                    "time":[step,]
#            }
#    )
    
    gdf_buffer = gpd.GeoDataFrame(df,crs={'init': 'epsg:3857'}, geometry="geometry")
    
#    if gdf_poly is not None:
    
#        how_buffer = "symmetric_difference"
   
    #        source_buffer, gdf_mask_buffer = overlay(gdf_poly, gdf_buffer, how_buffer, coeff_ampl, coeff_conv, "grey")
    #        source_buffer, gdf_buffer_mask = overlay(
    #                gdf_buffer, 
    #                gdf_poly, 
    #                how_buffer, 
    #                coeff_ampl, 
    #                coeff_conv,
    #                "grey"
    #                )
        
    #        for x in gdf_buffer.geometry:
    #            print (x)
    #        print (gdf_buffer)
    #        print (gdf_poly)
    #        gdf_poly["new_geom"] = gpd.GeoSeries(unary_union(gdf_poly.geometry.tolist()))
    #        gdf_poly = gdf_poly.drop("geometry", axis=1)
    #        gdf_poly.rename(columns={'new_geom':'geometry'}, inplace=True)
    #        gdf_poly = gdf_poly.set_geometry("geometry")
    #        
    #        for x in gdf_poly.geometry:
    #            print (x)
    #        print ("================")
    #        gdf_buffer = gpd.overlay(gdf_poly, gdf_buffer, how=how_buffer)
    #        source_buffer = convert_GeoPandas_to_Bokeh_format(gdf_buffer)
    #        geoms_exploded = gdf_poly.explode().reset_index(level=1, drop=True)
    #        print ("BEFORE", gdf_poly.columns)
    #        gdf_new = gdf_poly.drop(columns='geometry')
    #        gdf_new["geometry"] = geoms_exploded
    #        gdf_new = gdf_new.set_geometry("geometry")
    #        gdf_new = gdf_poly.drop(columns='geometry').join(geoms_exploded.rename('geometry'))
    #        print ("AFTER", gdf_new.columns)
    #        gdf_new = gpd.GeoDataFrame(gdf_new)
        
    #        print (gdf_new)
    #        print ("########################")
    #        geoms_exploded = gpd.GeoDataFrame(gdf_poly.explode().reset_index(level=1, drop=True))
    #        geoms_exploded.rename(columns={0:'geometry'}, inplace=True)
    #        print (geoms_exploded)
    #        print (type(gdf_poly))
    #        gdf_new = gdf_poly.drop('geometry', axis=1).join(geoms_exploded)
    #        gdf_new = gdf_new.set_geometry("geometry")
    #        gdf_new = gpd.GeoDataFrame(gdf_new)
        
    #        for x in gdf_buffer.geometry:
    #            print (type(x))
    #        print ("=======================")
    #        for x in gdf_new.geometry:
    #            print (type(x))
    #        print ("TYPE BUFFER", gdf_buffer.geometry[0],gdf_new.geometry[0])
#        gdf_new = explode(gdf_poly)
#        gdf_new = gpd.overlay(gdf_buffer, gdf_new, how=how_buffer)
#        source_buffer = convert_GeoPandas_to_Bokeh_format(gdf_new)
#        source_buffer = convert_GeoPandas_to_Bokeh_format(gdf_buffer)
        
#    else:
#        gdf_new = explode(gdf_buffer)
#        print ("YOUPI")
#        source_buffer = convert_GeoPandas_to_Bokeh_format(gdf_buffer)
#        source_buffer = None
#    gdf_new = explode(gdf_buffer)
    source_buffer = convert_GeoPandas_to_Bokeh_format(gdf_buffer)
    buffer_json, buffer_geojson = gdf_to_geojson(gdf_buffer,[])
#    print ("##########################################")
#    print (buffer_geojson)
#    print ("##########################################")       
    
    source_buffer_geojson = json.dumps(buffer_geojson)
    
    return source_buffer, source_buffer_geojson

def create_buffers(params_buffer):
    TRANSIT = 20 # Source: (http://www.urbalyon.org/AffichePDF/Observatoire_Deplacements_-_Publication_n-6_-_les_chiffres-cles_en_2010-3136): 19,9 (20) km/h 
    p_in = params_buffer["inproj"]
    p_out = params_buffer["outproj"]
    
    colors = params_buffer["colors"]
    opacities = params_buffer["opacities"]
    times = params_buffer["times"]
    contours = params_buffer["contours"]
    from_place = params_buffer["from_place"]
    address = params_buffer["address"]
    
    buffers, distances = [], []
    
    point_out = transform(p_in, p_out, from_place[0], from_place[1])
    
    for time_ in times:
        distance = time_*60 * (TRANSIT*1000) // 3600
        buffer = Point(point_out).buffer(
                distance, 
                resolution=16, 
                cap_style=1, 
                join_style=1, 
                mitre_limit=1.0
                )
        buffers.append(buffer)
        distances.append(distance)
        
    df = pd.DataFrame(
            {
                    "radius":distances,
                    "colors":colors,
                    "geometry":buffers,
                    "times":times,
                    "width":contours,
                    "fill_alpha":opacities,
                    "address":address
            }
    )
    
    gdf_buffer = gpd.GeoDataFrame(df,crs={'init': 'epsg:3857'}, geometry="geometry")
    
    buffer_json, buffer_geojson = gdf_to_geojson(
            gdf_buffer,
            [
            "radius", "colors", "times", "width", "fill_alpha"
            ]
    )
    
    source = GeoJSONDataSource(geojson=buffer_json)
    
#    source = convert_GeoPandas_to_Bokeh_format(gdf_buffer)
    
    return source

def str_list_to_list(str_list):
    l = []
    for x in str_list:
        temp = []
        for y in x.split(","):
            try:
                temp.append(int(y))
            except:
                temp.append(float(y))
        l.append(temp)  
    
    return l

def list_excluded(modes):
    forbidden = "&forbidden_uris[]=physical_mode:"
    str_modes = ""
    for mode in modes:
        str_modes += forbidden + mode
    
    return str_modes

def simplify(gdf, tolerance, preserve_topology=True):
    ## Simplify
    convex_hull = gdf.geometry.convex_hull
    envelope = gdf.geometry.envelope
    simplified = gdf.geometry.simplify(tolerance,  preserve_topology=preserve_topology)
    buffered = gdf.geometry.buffer(50, resolution=30)
    
    convex_gdf = copy.deepcopy(gdf)
    envelope_gdf = copy.deepcopy(gdf)
    simplified_gdf = copy.deepcopy(gdf)
    buffered_gdf = copy.deepcopy(gdf)
    
    convex_gdf.geometry = convex_hull
    envelope_gdf.geometry = envelope
    simplified_gdf.geometry = simplified
    buffered_gdf.geometry = buffered
    
    source_convex = convert_GeoPandas_to_Bokeh_format(convex_gdf)
    source_envelope = convert_GeoPandas_to_Bokeh_format(envelope_gdf)
    source_simplified = convert_GeoPandas_to_Bokeh_format(simplified_gdf)
    source_buffered = convert_GeoPandas_to_Bokeh_format(buffered_gdf)
    
    return source_convex, source_envelope, source_simplified, source_buffered
    
def buffer_point(point, inProj, outProj, distance, precision):
    '''
    point: lat,lon tuple
    inProj: input projection Proj object
    outProj: output projection Proj object
    '''
    point = Point(transform(inProj, outProj, point[0], point[1]))
    buffer = point.buffer(distance, precision)
    coords = buffer.exterior.coords
    coords= [transform(outProj, inProj, lat, lon) for lat,lon in coords]
    del coords[-1]
    
    return coords
    
def cds_to_geojson(data):
    """
    Transform Bokeh ColumnDataSource to GeoJSON
    """
    #CDS TO DF
    df = pd.DataFrame.from_dict(data,orient='index').transpose()
    
    l_poly = []
    for xs,ys in zip(data["xs"], data["ys"]):
        poly = Polygon([(x,y) for x,y in zip(xs,ys)])
        l_poly.append(poly)
        
    df = df.drop(["xs","ys"], axis=1)
    crs = {"init": "epsg:3857"}
    gdf = gpd.GeoDataFrame(df, crs=crs, geometry=l_poly)
    properties = list(df.columns)
    properties.remove("geometry")
    
    geo_dump = gdf_to_geojson(gdf, properties)[1]
    
    return geo_dump

def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def write_geojson(cds, id_, unique_id, directory):
    geo = cds_to_geojson(cds)
    dir_json = os.path.join(directory,str(id_))
    create_dir(dir_json)
    name_geo = dir_json + "/" + str(unique_id) + ".geojson"
    with open(name_geo, 'w') as outfile:
        geojson.dump(geo, outfile)
        
def dict_geojson(options_dict, colors):
    dict_ = {}
    for k,v in options_dict["source"].data.items():
        dict_[k] = v
    nb = len(colors)
    tmp = {
            "fill": colors,
            "fill-opacity": [options_dict["fill_alpha"] for i in range(0,nb)],
            "stroke": colors,
            "stroke-opacity": [options_dict["line_alpha"] for i in range(0,nb)],
            "stroke-width": [options_dict["line_width"] for i in range(0,nb)]
            }
    dict_.update(tmp)
    
    return dict_
    
def df_stats_to_json(df, params, stats):
    if isinstance(df['id'].iloc[0], str):
        id_ = df['id'].iloc[0]
    else:
        id_ = int(df['id'].iloc[0])
    dict_params = df.loc[0,params].to_json()
    stats_details = [x for x in stats if x != "area_sum"]
    dict_stats_details = df.loc[:,stats_details].to_json()
    dict_stats_synth = df.loc[0,["area_sum","nb_poly"]]
#    dict_stats_synth["nb_poly"] = len(df.index)
    dict_stats_synth = dict_stats_synth.to_json()
    
    return {
            "id": id_,
            "parameters": json.loads(dict_params),
            "stats": {
                    "details": json.loads(dict_stats_details),
                    "synthesis": json.loads(dict_stats_synth)
                    }
            }
        