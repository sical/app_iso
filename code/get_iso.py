# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 16:55:25 2018

@author: thomas
"""

import requests
import geojson
import json


from functions import _cutoffs, _palette, _convert_epsg, create_pts, _convert_GeoPandas_to_Bokeh_format, buildings_to_datasource, network_to_datasource

def get_iso(params):
    """
    Request on OTP server to get isochrone via API
    Get also buildings and network on OSM via osmnx
    Build color palette depending on ischrones' number
    
    @param params (dict): dict of parameters
    
        params list:
            - router: string, name of the router
            - from_place: string, latitude and longitude ex=> "48.842021, 2.349900"
            - time_in: string, departure or arrival time ex=> "08:00"
            - min_date: datetime object
            - modes: string, authorized modes ex=> "TRANSIT, WALK"
            - max_dist: string, maximum walking distance ex=> "800"
            - step: integer, number of seconds for an isochrone's step ex=> 600 
            - nb_iter: string, number of isochrone's step=> "3"
            - dict_palette: dict, key=name, value=colors palette
            - inProj: string, epsg of input =>"epsg:4326" 
            - outProj: string, epsg for output => "epsg:3857"
    
    Returns dict with isochronic polygons, isochronic points, colors,
    buildings and network
    """
    
    router = params['router']
    from_place = params['from_place']
    time_in = params['time_in']
    min_date = params['min_date']
    modes = params['modes']
    max_dist = params['max_dist']
    step = params['step']
    nb_iter = params['nb_iter']
    dict_palette = params['dict_palette']
    inProj = params['inProj']
    outProj = params['outProj']
    
    step = int(step)
    nb_iter = int(nb_iter)
    if nb_iter > 11:
        print ("Please select a number of iterations inferior to 11")
        return
    cut_time = _cutoffs(nb_iter, step)
    cutoffs = cut_time[0]
    list_time = cut_time[1]
    
    colors = _palette(list_time, dict_palette)
    
    url = "http://localhost:8080/otp/routers/{}/isochrone?fromPlace={}&mode={}&date={}&time={}&maxWalkDistance={}{}".format(
        router,
        from_place,
        modes,
        min_date,
        time_in,
        max_dist,
        cutoffs)
    

    headers = {'accept': 'application/json'}
    r = requests.get(url, headers=headers)
    code = r.status_code

    if code == 200:
        json_response = json.dumps(r.json())
    else:
        print ('ERROR:', code)
        return
    
    geojson_ = geojson.loads(json_response)
    gdf_poly = _convert_epsg(inProj, outProj, geojson_)
    
    points = create_pts(gdf_poly)
    
    datasource_poly = _convert_GeoPandas_to_Bokeh_format(gdf_poly, 'polygon')
    
#    poly_for_osmnx = gdf_poly.copy().to_crs({"init":"epsg:4326"})
    
#    polygon = poly_for_osmnx["geometry"].iloc[-1]
    
#    buildings = buildings_to_datasource(polygon)
#    
#    network = network_to_datasource(polygon)
    
    return {'poly':datasource_poly, 
            'points':points,
            'colors':colors,
#            'buildings':buildings,
#            'network':network
            }