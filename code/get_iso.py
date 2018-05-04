# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 16:55:25 2018

@author: thomas
"""

import requests
from geojson import Feature, MultiPolygon, FeatureCollection
import geojson
import json
import geopandas as gpd
from shapely.ops import unary_union, cascaded_union
from bokeh.models import GeoJSONDataSource


from functions import _cutoffs, _palette, _convert_epsg, create_pts, create_polys, _convert_GeoPandas_to_Bokeh_format, buildings_to_datasource, network_to_datasource, gdf_to_geojson

def get_iso(params):
    """
    Request on OTP server to get isochrone via API
    Get also buildings and network on OSM via osmnx
    Build color palette depending on ischrones' number
    
    @param params (dict): dict of parameters
    
        params list:
            - from_place: string, latitude and longitude ex=> "48.842021, 2.349900"
            - time_in: string, departure or arrival time ex=> "08:00"
            - min_date: datetime object
            - step: integer, number of seconds for an isochrone's step ex=> 600 
            - nb_iter: string, number of isochrone's step=> "3"
            - dict_palette: dict, key=name, value=colors palette
            - inProj: string, epsg of input =>"epsg:4326" 
            - outProj: string, epsg for output => "epsg:3857"
    
    Returns dict with isochronic polygons, isochronic points, colors,
    buildings and network
    """
    
    token = params['token']
    from_place = params['from_place']
    time_in = params['time_in']
    min_date = params['min_date']  #format YYYYMMDDThhmmss
    step = params['step']
    nb_iter = params['nb_iter']
    dict_palette = params['dict_palette']
    inProj = params['inProj']
    outProj = params['outProj']
    
    date_time = min_date.isoformat() + "T" + time_in
    
    step = int(step)
    nb_iter = int(nb_iter)
    if nb_iter > 11:
        print ("Please select a number of iterations inferior to 11")
        return
    
    cutoffs, list_time = _cutoffs(nb_iter, step)
#    list_time = [step*i for i in range(1, nb_iter+1)]
    colors = _palette(list_time, dict_palette)
    gdf_polys = []

    url='https://api.navitia.io/v1/coverage/fr-idf/isochrones?from={}&datetime={}{}'.format(
            from_place,
            date_time,
            cutoffs
            )

    headers = {
            'accept': 'application/json',
            'Authorization': token
            }
    
    r = requests.get(url, headers=headers)
    code = r.status_code

    if code == 200:
        json_response = json.dumps(r.json())
    else:
        print ('ERROR:', code)
        return

    geojson_ = geojson.loads(json_response)
    
    for iso,duration in zip(geojson_['isochrones'], list_time):
        multi = Feature(geometry=MultiPolygon(iso["geojson"]["coordinates"]), properties={"time":duration})
        gdf_polys.append(multi)
        
#    geojson_ = geojson.loads(json_response)
#    poly_json = geojson_['isochrones'][0]
##        coord = [[[[x[0],x[1]] for x in poly_json["geojson"]["coordinates"][0][0]]]]
#    multi = Feature(geometry=MultiPolygon(poly_json["geojson"]["coordinates"]), properties={"time":duration})
#    gdf_polys.append(multi)
#        
    collection = FeatureCollection(gdf_polys)
    gdf_poly = gpd.GeoDataFrame.from_features(collection['features'])
    
    gdf_poly.crs = {'init': inProj}
    gdf_poly = gdf_poly.to_crs({'init': outProj})
    gdf_poly = gdf_poly.sort_values(by='time', ascending=False)
    
    poly_json = gdf_to_geojson(gdf_poly, ['time'])
    
    points = create_pts(gdf_poly)
    polys = GeoJSONDataSource(geojson=str(poly_json))
    
#    datasource_poly = _convert_GeoPandas_to_Bokeh_format(gdf_poly)
    
    
#    poly_for_osmnx = gdf_poly.copy().to_crs({"init":"epsg:4326"})
    
#    polygon = poly_for_osmnx["geometry"].iloc[0].envelope
    
#    buildings = buildings_to_datasource(polygon)
    
#    network = network_to_datasource(polygon)
    
    return {
            'poly':polys, 
            'points':points,
            'colors':colors,
#            'buildings':buildings,
#            'network':network
            }