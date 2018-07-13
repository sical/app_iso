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
from shapely.geometry import Point, MultiPolygon as shap_multi
from bokeh.models import GeoJSONDataSource, ColumnDataSource
from pyproj import transform, Proj
import pandas as pd

from functions import _cutoffs, _palette, _convert_epsg, create_pts, create_polys, convert_GeoPandas_to_Bokeh_format, buildings_to_datasource, network_to_datasource, gdf_to_geojson, colors_blend, get_stats, explode, measure_differential, simplify

#SPEEDS (km/h)
#Sources:
# ADEME: https://www.ademe.fr/expertises/mobilite-transports/passer-a-laction/report-modal
# URBALYON: http://www.urbalyon.org/AffichePDF/Observatoire_Deplacements_-_Publication_n-6_-_les_chiffres-cles_en_2010-3136
CAR = 14
BICYCLE = 15
TRANSIT = 20

#PROJECTIONS
p_4326 = Proj(init='epsg:4326')
p_3857 = Proj(init='epsg:3857')


def overlay(gdf_poly, gdf_overlay, how, coeff_ampl, coeff_conv, color_switch):
    if gdf_overlay is not None:
            intersection = gpd.overlay(gdf_poly, gdf_overlay, how=how)
            print ("1")
            if how == "union":
                poly = intersection.geometry.unary_union
                intersection["geometry"] = [poly for i in range(0, intersection["geometry"].count())]
                intersection = intersection.loc[[0], intersection.columns]
            
            c1 = gdf_poly["color"][0]
            c2 = gdf_overlay["color"][0]
            
            if color_switch is not None:
                color_blended = color_switch
            else:
                color_blended = colors_blend(c1, c2)
            
            intersection_json, intersection_geojson = gdf_to_geojson(intersection, ['time'])
            intersection = gpd.GeoDataFrame.from_features(intersection_geojson['features'])
            print ("2")
            if intersection.empty is False:
                intersection["color"] = [color_blended for i in range(0,intersection["geometry"].size)]
                gdf_overlay = intersection.copy().drop("time", axis=1)
                stats_intersection, intersection = get_stats(intersection, coeff_ampl, coeff_conv)
                source_intersections = convert_GeoPandas_to_Bokeh_format(intersection)
            else:
                source_intersections = ColumnDataSource(
                        data=dict(
                                xs=[], 
                                ys=[], 
                                time=[],
                                color=[],
                                area=[],
                                perimeter=[],
                                amplitude=[],
                                convex=[],
                                norm_notches=[],
                                complexity=[]
                                )
                        )
                gdf_overlay = gdf_poly.copy()
                
    else:
        source_intersections = ColumnDataSource(
                        data=dict(
                                xs=[], 
                                ys=[], 
                                time=[],
                                color=[],
                                area=[],
                                perimeter=[],
                                amplitude=[],
                                convex=[],
                                norm_notches=[],
                                complexity=[]
                                )
                        )
        gdf_overlay = gdf_poly.copy()
        
    return source_intersections, gdf_overlay

def get_iso(params, gdf_poly_mask, id_):
    """
    Request on OTP server to get isochrone via API
    Get also buildings and network on OSM via osmnx
    Build color palette depending on isochrones' number
    
    @param params (dict): dict of parameters
    
        params list:
            - from_place: string, latitude and longitude ex=> "48.842021, 2.349900"
            - time_in: string, departure or arrival time ex=> "08:00"
            - min_date: datetime object
            - step: integer, number of seconds for an isochrone's step ex=> 600 
            - nb_iter: string, number of isochrone's step=> "3"
            - inProj: string, epsg of input =>"epsg:4326" 
            - outProj: string, epsg for output => "epsg:3857"
            - how: string, type of intersection => "union"
    
    Returns dict with isochronic polygons, isochronic points, colors,
    buildings and network
    """
    global alert
    
    TOKEN = params['token']
    from_place = params['from_place']
    time_in = params['time_in']
    min_date = params['min_date']  #format YYYYMMDDThhmmss
    step = params['step']
    step_mn = params['step_mn']
    nb_iter = params['nb_iter']
    shape = params['shape']
    inProj = params['inProj']
    outProj = params['outProj']
    how = params['how']
    color = params['color']
    color_switch = params['color_switch']
    coeff_ampl = 0.8 # See Brinkhoff et al. paper
    coeff_conv = 0.2 # See Brinkhoff et al. paper
    tolerance = params["tolerance"]
    
    color = colors_blend(color, color)
    
    date_time = min_date.isoformat() + "T" + time_in
    
    if step_mn != 0:
        step = int(step)
        nb_iter = step//(step_mn*60)
        cutoffs, list_time = _cutoffs(nb_iter, step_mn*60)
    else:
        nb_iter = 1
        cutoffs, list_time = _cutoffs(nb_iter, step)
#    if nb_iter > 11:
#        print ("Please select a number of iterations inferior to 11")
#        return
    
    print ("CUT", cutoffs)
    gdf_polys = []

    url='https://api.navitia.io/v1/coverage/{}/isochrones?from={}&datetime={}{}'.format(
            id_,
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

    if (code == 200 and step_mn == 0):
        json_response = json.dumps(r.json())
        geojson_ = geojson.loads(json_response)
    
        for iso,duration in zip(geojson_['isochrones'], list_time):
            multi = Feature(
                    geometry=MultiPolygon(
                            iso["geojson"]["coordinates"]
                            ), 
                    properties={"time":duration}
                    )
            gdf_polys.append(multi)
 
        collection = FeatureCollection(gdf_polys)
        gdf_poly = gpd.GeoDataFrame.from_features(collection['features'])
        
        gdf_poly.crs = {'init': inProj}
        gdf_poly = gdf_poly.to_crs({'init': outProj})
        gdf_poly = gdf_poly.sort_values(by='time', ascending=False)
        
        gdf_poly['color'] = [color for i in range(0, gdf_poly["geometry"].count())]
        
        source_intersections, gdf_poly_mask = overlay(
                gdf_poly, 
                gdf_poly_mask, 
                how, 
                coeff_ampl, 
                coeff_conv,
                color_switch
                )
        
        poly_json, _geojson = gdf_to_geojson(gdf_poly, ['time', 'color'])
        
        #MEASURE DIFFERENTIAL
        source_buffer,source_buffer_geojson = measure_differential(from_place, step, gdf_poly)
        poly_json, _geojson = gdf_to_geojson(gdf_poly, ['time', 'color'])
        
        #STATS
        gdf_stats = gpd.GeoDataFrame.from_features(_geojson['features'])
        stats, gdf_stats = get_stats(gdf_stats, coeff_ampl, coeff_conv)
        
        for key,value in stats.items():
            gdf_stats[key] = value
        
        #SOURCE POLYS BASIC
        ## Simplify
        source_convex, source_envelope, source_simplified = simplify(gdf_stats, tolerance)
        
        source_polys = convert_GeoPandas_to_Bokeh_format(gdf_stats)
        
        #GEOJSON POLY
        gdf_json, gdf_geojson = gdf_to_geojson(gdf_stats, ['time', 'color'])
        source_polys_geojson = json.dumps(gdf_geojson)
        
        
        if shape == "poly" or shape == "line":
            source = source_polys
        else:
            source = create_pts(gdf_poly)
        
        status = ""
        
    elif (code == 200 and step_mn != 0):
        json_response = json.dumps(r.json())
        geojson_ = geojson.loads(json_response)
    
        for iso,duration in zip(geojson_['isochrones'], list_time):
            multi = Feature(
                    geometry=MultiPolygon(
                            iso["geojson"]["coordinates"]
                            ), 
                    properties={"time":duration}
                    )
            gdf_polys.append(multi)
 
        collection = FeatureCollection(gdf_polys)
        gdf_poly = gpd.GeoDataFrame.from_features(collection['features'])
        
        gdf_poly.crs = {'init': inProj}
        gdf_poly = gdf_poly.to_crs({'init': outProj})
        gdf_poly = gdf_poly.sort_values(by='time', ascending=False)
        poly_json, _geojson = gdf_to_geojson(gdf_poly, ['time'])
        gdf_stats = gpd.GeoDataFrame.from_features(_geojson['features'])
        source = convert_GeoPandas_to_Bokeh_format(gdf_stats)
        gdf_json, gdf_geojson = gdf_to_geojson(gdf_stats, ['time'])
        source_polys_geojson = json.dumps(gdf_geojson)
        source_buffer,source_buffer_geojson = measure_differential(from_place, step, gdf_poly)
        
#        source_buffer = measure_differential(from_place, step)
        gdf_poly_mask = None
        source_buffer = None
        status = ""
        source_intersections = None
        
        
    else:
        if r.json()["error"]["message"]:
            status = str(r.json()["error"]["message"]) + ": " + "Measure not possible"
            print ('ERROR:', status)
        else:
            status = str(code) + ": " + "Measure not possible"
            print ('ERROR:', status)
        source, shape, source_intersections, gdf_poly_mask = None, None, None, None

    return {
            'status': status,
            'source':source,
            'source_geojson':source_polys_geojson,
            'shape':shape,
            'intersection':source_intersections,
            'gdf_poly_mask': gdf_poly_mask,
            'gdf_poly': gdf_poly,
            'source_buffer': source_buffer,
            'source_buffer_geojson': source_buffer_geojson,
            'source_convex': source_convex,
            'source_simplified': source_simplified,
            'source_envelope': source_envelope
            }
     