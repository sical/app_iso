# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 13:31:04 2018

@author: thomas
"""

import pandas as pd
import geopandas as gpd
from geopy.geocoders import Nominatim
import osmnx as ox
import json
import numpy as np

from bokeh.models import ColumnDataSource, GeoJSONDataSource, HoverTool

geolocator = Nominatim()


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
    
    geojson_ = {"type":"FeatureCollection", "features":[]}
    for line in gdf.itertuples():
        feature = {"type":"Feature",
                   "properties":{},
                   "geometry":{
                           "type":"MultiPolygon",
                           "coordinates":[]
                           }
                   }
        
        l_tmp = []
        for poly in line.geometry:
            l_poly = []
            for pt in poly.exterior.coords:
                l_poly.extend([[pt[0],pt[1]]])
            l_tmp.append(l_poly)
        feature["geometry"]["coordinates"] = [list(reversed(l_tmp))]
        
        if (properties != []) or (properties is not None):
            for prop in properties:
                feature["properties"][prop] = line[properties.index(prop)]
        
            geojson_["features"].append(feature)
        else:
            feature.pop(properties, None)
    return json.dumps(geojson_)
    
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
    

def geocode(adress):
    """
    Use geopy.geolocator (Nominatim) to get latitude and longitude (EPSG 4326) 
    of an adress
    
    @param adress (str): postal adress
    
    Returns latitude and longitude
    
    """
    location = geolocator.geocode(adress)
    
    return location.longitude, location.latitude 


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


def _cutoffs(nb_iter, step):
    """
    Returns a string for Navitia API for step and seconds by step
    Returns a list of time values
    
    @param nb_iter (number): numer of iterations
    @param step (number): number of steps
    """
    end = step*(nb_iter+1)
    list_time = []
    cutoffs = ""

    for i in range(step, end, step):
        cutoffs += "&boundary_duration[]=" + str(i)
        list_time.append(i)
    
    return cutoffs, list_time


def create_pts(gdf_poly):
    """
    Create points ColumnDataSource from GeoDataFrame of polygons
    
    @param gdf_poly (GeoDataFrame): GeoDataFrame polygonss
    
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

def _convert_GeoPandas_to_Bokeh_format(gdf):
    """
    Function to convert a GeoPandas GeoDataFrame to a Bokeh
    ColumnDataSource object.
    
    @param gdf (GeoDataFrame): GeoPandas GeoDataFrame with polygon(s) under
                                the column name 'geometry.'
                                
    Returns ColumnDataSource for Bokeh.
    """
#    gdf_new = gdf.drop('geometry', axis=1).copy()
    gdf['xs'] = gdf.apply(
            getCoords, 
            geom_col="geometry", 
            coord_type="x", 
            axis=1
            )
    
    gdf['ys'] = gdf.apply(
            getCoords, 
            geom_col="geometry", 
            coord_type="y", 
            axis=1
            )

    return ColumnDataSource(gdf)


#def getPolyCoords(line, geom, coord_type):
#    """
#    @param line (Shapely LineString): line
#    @param geom (str): geometry column name
#    @param coord_type (str): x or y 
#    
#    Returns the list of coordinates ('x' or 'y') of edges of a Polygon exterior
#    Source: https://automating-gis-processes.github.io/2016/Lesson5-interactive-map-bokeh.html
#    
#    """
#
#    # Parse the exterior of the coordinate
#    exterior = line[geom].exterior
#
#    if coord_type == 'x':
#        # Get the x coordinates of the exterior
#        return list( exterior.coords.xy[0] )
#    elif coord_type == 'y':
#        # Get the y coordinates of the exterior
#        return list( exterior.coords.xy[1] )


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
        exterior = line[geom].geoms[0].exterior
        
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