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

from functions import _cutoffs, _palette, _convert_epsg, create_pts, create_polys, convert_GeoPandas_to_Bokeh_format, buildings_to_datasource, network_to_datasource, gdf_to_geojson, colors_blend, get_stats, explode

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
    
    color = colors_blend(color, color)
    
    date_time = min_date.isoformat() + "T" + time_in
    
    if step_mn != 1:
        step = int(step)
        nb_iter = step//step_mn
    else:
        nb_iter = 1
#    if nb_iter > 11:
#        print ("Please select a number of iterations inferior to 11")
#        return
    
    cutoffs, list_time = _cutoffs(nb_iter, step_mn)
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

    if code == 200 and step_mn == 1:
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
        
        #DIFFERENCE BETWEEN THEORITICAL AND REAL ACCESSIBILITY
        point_4326 = from_place.split(sep=";")
        point_3857 = transform(p_4326, p_3857, point_4326[0], point_4326[1])
        distance = step * (TRANSIT*1000) // 3600
        buffer = Point(point_3857).buffer(distance, resolution=16, cap_style=1, join_style=1, mitre_limit=1.0)
        
        df = pd.DataFrame(
                {
                        "radius":[distance,],
                        "color":["grey",],
                        "geometry":[buffer,],
                        "time":[step,]
                }
        )
        
        gdf_buffer = gpd.GeoDataFrame(df,crs={'init': 'epsg:3857'}, geometry="geometry")
        how_buffer = "symmetric_difference"
       
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
        gdf_new = explode(gdf_poly)
        print ("plot")
#        print (type(gdf_new), type(gdf_buffer))
        print (gdf_new["geometry"][0])
        print (gdf_buffer["geometry"][0])
        gdf_new = gpd.overlay(gdf_buffer, gdf_new, how=how_buffer)
        print ("yes")
        source_buffer = convert_GeoPandas_to_Bokeh_format(gdf_new)
        
        print ("yep2")
        
        #STATS
        gdf_stats = gpd.GeoDataFrame.from_features(_geojson['features'])
        stats, gdf_stats = get_stats(gdf_stats, coeff_ampl, coeff_conv)
        
        for key,value in stats.items():
            gdf_stats[key] = value
        
        source_polys = convert_GeoPandas_to_Bokeh_format(gdf_stats)
        
        
        if shape == "poly" or shape == "line":
            source = source_polys
        else:
            source = create_pts(gdf_poly)
        
        status = ""
        
    elif code == 200 and step_mn != 1:
        print ("YYYYYYYYYYYYYYYY")
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
            'shape':shape,
            'intersection':source_intersections,
            'gdf_poly_mask': gdf_poly_mask,
            'gdf_poly': gdf_poly,
            'source_buffer': source_buffer
            }
     