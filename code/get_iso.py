# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 16:55:25 2018

@author: thomas
"""

import requests
from geojson import Feature, MultiPolygon, FeatureCollection, Polygon
import geojson
import json
import geopandas as gpd
from shapely.ops import unary_union, cascaded_union
from bokeh.models import GeoJSONDataSource


from functions import _cutoffs, _palette, _convert_epsg, create_pts, create_polys, convert_GeoPandas_to_Bokeh_format, buildings_to_datasource, network_to_datasource, gdf_to_geojson, get_stats

def get_iso(params, gdf_poly_mask):
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
            - inProj: string, epsg of input =>"epsg:4326" 
            - outProj: string, epsg for output => "epsg:3857"
    
    Returns dict with isochronic polygons, isochronic points, colors,
    buildings and network
    """
    
    TOKEN = params['token']
    from_place = params['from_place']
    time_in = params['time_in']
    min_date = params['min_date']  #format YYYYMMDDThhmmss
    step = params['step']
    nb_iter = params['nb_iter']
    shape = params['shape']
    inProj = params['inProj']
    outProj = params['outProj']
    coeff_ampl = 0.8 # See Brinkhoff et al. paper
    coeff_conv = 0.2 # See Brinkhoff et al. paper
    
    print (min_date)
    
    date_time = min_date.isoformat() + "T" + time_in
    
    step = int(step)
    nb_iter = int(nb_iter)
    if nb_iter > 11:
        print ("Please select a number of iterations inferior to 11")
        return
    
    cutoffs, list_time = _cutoffs(nb_iter, step)
#    list_time = [step*i for i in range(1, nb_iter+1)]
    gdf_polys = []

    url='https://api.navitia.io/v1/coverage/fr-idf/isochrones?from={}&datetime={}{}'.format(
            from_place,
            date_time,
            cutoffs
            )
    headers = {
            'accept': 'application/json',
            'Authorization': TOKEN
            }
    
    r = requests.get(url, headers=headers)
    code = r.status_code
    
    print (url, code)

    if code == 200:
        json_response = json.dumps(r.json())
    else:
        print ('ERROR:', code)
        return

    geojson_ = geojson.loads(json_response)
    
    for iso,duration in zip(geojson_['isochrones'], list_time):
        multi = Feature(
                geometry=MultiPolygon(
                        iso["geojson"]["coordinates"]
                        ), 
                properties={"time":duration}
                )
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
    
    if gdf_poly_mask is not None:
        intersection = gpd.overlay(gdf_poly, gdf_poly_mask, how='intersection')
        gdf_poly_mask = gdf_poly.copy()
        print ("CHIASSE")
        print (type(intersection), intersection)
        intersection_json, intersection_geojson = gdf_to_geojson(intersection, ['time'])
        print ("CHIASSE2")
        intersection = gpd.GeoDataFrame.from_features(intersection_geojson['features'])
        print ("CHIASSE3")
        stats_intersection, intersection = get_stats(intersection, coeff_ampl, coeff_conv)
        
        for key,value in stats_intersection.items():
            intersection[key] = value
    
            source_intersections = convert_GeoPandas_to_Bokeh_format(intersection)
    else:
        source_intersections = None
        gdf_poly_mask = gdf_poly.copy()
    
    poly_json, _geojson = gdf_to_geojson(gdf_poly, ['time'])
    
    #STATS
    gdf_stats = gpd.GeoDataFrame.from_features(_geojson['features'])
    stats, gdf_stats = get_stats(gdf_stats, coeff_ampl, coeff_conv)
    
    for key,value in stats.items():
        gdf_stats[key] = value
    
    source_polys = convert_GeoPandas_to_Bokeh_format(gdf_stats)
    
    #INTEGRER TOUT CA A LA SOURCE POUR AFFICHAGE AVEC TABLEAU !
    
#    gdf_poly['area'] = stats['area']
#    gdf_poly['nb'] = stats['nb']
#    gdf_poly['distance'] = stats['distance']s
    
    if shape == "poly" or shape == "line":
#        source = GeoJSONDataSource(geojson=str(poly_json))
        source = source_polys
    else:
        source = create_pts(gdf_poly)
    
    
#    datasource_poly = _convert_GeoPandas_to_Bokeh_format(gdf_poly)
    
    
#    poly_for_osmnx = gdf_poly.copy().to_crs({"init":"epsg:4326"})
    
#    polygon = poly_for_osmnx["geometry"].iloc[0].envelope
    
#    buildings = buildings_to_datasource(polygon)
    
#    network = network_to_datasource(polygon)
    
    return {
            'source':source,
            'shape':shape,
            'intersection':source_intersections,
            'gdf_poly_mask': gdf_poly_mask
#            'buildings':buildings,
#            'network':network
            }