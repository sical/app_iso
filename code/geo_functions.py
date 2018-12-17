# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 11:11:10 2018

@author: thomas
"""

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon, Point, LineString
import numpy as np
import json
import geojson
from bokeh.models import GeoJSONDataSource


def load_geojson(geojson_file):
    """
    Load a geojson object from a GeoJSON file
    """
    return geojson.loads(
            json.dumps(
                    json.load(
                            open(geojson_file)
                            )
                    )
            )

def geosource(geojson_file):
    """
    Make a GeoJSONDataSource Bokeh object from a GeoJSON file
    """
    geo_dump = json.dumps(
            load_geojson(
                    geojson_file
                    )
            )
    return GeoJSONDataSource(geojson=geo_dump)

def reproject_geojson(geojson_path_file, inProj, outProj, bokeh_=False):
    """
    Reproject a GeoJSON file and returns GeoJSON object
    
    @param geojson_path_file(str): path file to geojson
    @param inProj (str): epsg string
    @param outProj (str): epsg string
    
    """
    gdf = gpd.read_file(geojson_path_file)
    gdf.crs = {'init': inProj}
    gdf = gdf.to_crs({'init': outProj})
    
    properties = gdf.columns.tolist()
    properties.remove("geometry")
    epsg = outProj.split(":")[1]
    
    geojson_ = gdf_to_geojson(gdf, properties, epsg)
    
    if bokeh_ is False:
        return geojson_
    else:
        return GeoJSONDataSource(geojson=json.dumps(geojson_))


def gdf_to_geojson(gdf, properties, epsg):
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
            "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::{}".format(epsg) } },
            }
#    style_col = ["fill", "fill-opacity", "stroke", "stroke-width", "stroke-opacity"]
    
    if "geometry" in properties:
        properties.remove("geometry")
    
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
        elif (isinstance(line.geometry, Polygon)):
            l_poly = []
            for pt in line.geometry.exterior.coords:
                l_poly.extend([[pt[0],pt[1]]])
            feature = {"type":"Feature",
                   "properties":{},
                   "geometry":{
                           "type":"Polygon",
                           "coordinates":[]
                           },
                   "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::{}".format(epsg) } },
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
                
        elif (isinstance(line.geometry, LineString)):
            l_poly = [[x[0],x[1]] for x in list(line.geometry.coords)]

            feature = {"type":"Feature",
                   "properties":{},
                   "geometry":{
                           "type":"LineString",
                           "coordinates":[]
                           },
                   "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::{}".format(epsg) } },
                   }
            feature["geometry"]["coordinates"] = l_poly
            if (properties != []) or (properties is not None):
                for prop in properties:
                    value_prop = gdf.at[line.Index, prop]
                    if type(value_prop) == np.int64 or type(value_prop) == np.int32:
                        value_prop = int(value_prop)
                    feature["properties"][prop] = value_prop
            
                geojson_["features"].append(feature)
            else:
                feature.pop(properties, None)
        
        elif (isinstance(line.geometry, Point)):
            l_poly = [[x[0],x[1]] for x in list(line.geometry.coords)]

            feature = {"type":"Feature",
                   "properties":{},
                   "geometry":{
                           "type":"Point",
                           "coordinates":[]
                           },
                   "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:EPSG::{}".format(epsg) } },
                   }
            feature["geometry"]["coordinates"] = [line.geometry.x,line.geometry.y]
            if (properties != []) or (properties is not None):
                for prop in properties:
                    value_prop = gdf.at[line.Index, prop]
                    if type(value_prop) == np.int64 or type(value_prop) == np.int32:
                        value_prop = int(value_prop)
                    feature["properties"][prop] = value_prop
            
                geojson_["features"].append(feature)
            else:
                feature.pop(properties, None)
    
    return geojson.dumps(geojson_, ensure_ascii=False)

def get_poly_coords(poly):
    
    if poly.geom_type == "Polygon":
        if poly.interiors:
            xs_coords = [
                [poly.exterior.xy[0].tolist()],
                [[xy[0] for xy in p.coords] for p in poly.interiors]
            ]

            ys_coords =  [
                [poly.exterior.xy[1].tolist()],
                [[xy[1] for xy in p.coords] for p in poly.interiors]
            ]
        else:
            xs_coords = [
                [poly.exterior.xy[0].tolist()]
            ]

            ys_coords =  [
                [poly.exterior.xy[1].tolist()]
            ]
        
    elif poly.geom_type == "MultiPolygon":
        xs_coords = []
        ys_coords = []
        for po in poly:
            if po.interiors:
                xs_coords.extend([
                    [po.exterior.xy[0].tolist()],
                    [[xy[0] for xy in p.coords] for p in po.interiors]]
                )

                ys_coords.extend([
                    [po.exterior.xy[1].tolist()],
                    [[xy[1] for xy in p.coords] for p in po.interiors]]
                )
            else:
                xs_coords.extend([
                    [po.exterior.xy[0].tolist()]
                ])

                ys_coords.extend([
                    [po.exterior.xy[1].tolist()]
                ])
    
    return [xs_coords], [ys_coords]

def multi_gdf_to_multi_bokeh(gdf):
    xs, ys = [], []
    gdf["coords"] = gdf.apply(lambda x: get_poly_coords(x["geometry"]), axis=1)
    l = gdf["coords"].values.tolist()
    
    for coord in l:
        xs.append(coord[0][0])
        ys.append(coord[1][0])
        
    return {
        "xs": xs,
        "ys": ys
    }