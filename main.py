# -*- coding: utf-8 -*-
"""

"""

import requests
import pandas as pd
from pandas.io.json import json_normalize
import geopandas as gpd
from pyproj import Proj, transform

from bokeh.palettes import Viridis
from bokeh.io import show, output_notebook, output_file
from bokeh.plotting import figure, show, output_file
from bokeh.tile_providers import STAMEN_TONER
from bokeh.models import ColumnDataSource, GeoJSONDataSource, HoverTool, LinearColorMapper

import json
import geojson
import tempfile

params = "params.json"
params = json.load(open(params))

router = params["router"]

#Projections
#inProj = Proj(init=params["inProj"])
#outProj = Proj(init=params["outProj"])
inProj = params["inProj"]
outProj = params["outProj"]

router = "Paris"
from_place = 48.863043, 2.339759
time = "08:00" #HH:MM format
date = "04-05-2018" #MM-DD-YYYY format
modes = "TRANSIT,WALK"
max_dist = 800
step = 600
nb_iter = 3

def convert_epsg(inProj, outProj, geojson_):
    gdf = gpd.GeoDataFrame.from_features(geojson_["features"])
    gdf.crs = {'init': inProj}
    gdf.to_crs({'init': outProj})
    
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

def _cutoffs(nb_iter, step):
    end = step*(nb_iter+1)
    list_time = []
    cutoffs = ""
    
    for i in range(600, end, step):
        cutoffs += "&cutoffSec=" + str(i)
        list_time.append(i)
    
    return cutoffs, list_time
    
def get_iso(router, from_place, time, date, modes, max_dist, step, nb_iter, palette, inProj, outProj):
    
    if nb_iter > 11:
        print ("Please select a number of iterations inferior to 11")
        return
    cut_time = _cutoffs(nb_iter, step)
    cutoffs = cut_time[0]
    list_time = cut_time[1]
    
#    dict_color = _palette(list_time, palette)[0]
    colors = _palette(list_time, palette)[1]
    
    url = "http://localhost:8080/otp/routers/{}/isochrone?fromPlace={}&mode={}&date={}&time={}&maxWalkDistance={}{}".format(
        router,
        from_place,
        modes,
        date,
        time,
        max_dist,
        cutoffs)

    headers = {'accept': 'application/json'}

    r = requests.get(url, headers=headers)
    code = r.status_code

    if code == 200:
        json_response = r.json()
    else:
        print ('ERROR:', code)
        return
    
    str_json = str(json_response).replace("'", '"')
    
    geojson_ = geojson.loads(str_json)
    
    gdf = convert_epsg(inProj, outProj, geojson_)
    
    datasource = convert_GeoPandas_to_Bokeh_format(gdf)
    
    return datasource, colors, json_response
    
#df['features'][0]['properties']['time']

def _palette(list_time, palette):
    
    palette_nb = len(list_time)
    if palette_nb > 11 or palette_nb < 3:
        print ("Please select a number inferior to 11 and superior to 3")
        return
    
    colors = palette[palette_nb]

    #Create time/colors dict
    dict_color = {time:color for time, color in zip(list_time, colors)}
    
    return dict_color, colors

def convert_GeoPandas_to_Bokeh_format(gdf):
    """
    Function to convert a GeoPandas GeoDataFrame to a Bokeh
    ColumnDataSource object.
    
    Source: http://michael-harmon.com/blog/IntroToBokeh.html
    
    :param: (GeoDataFrame) gdf: GeoPandas GeoDataFrame with polygon(s) under
                                the column name 'geometry.'
                                
    :return: ColumnDataSource for Bokeh.
    """
    gdf_new = gdf.drop('geometry', axis=1).copy()
    gdf_new['xs'] = gdf.apply(getGeometryCoords, 
                             geom='geometry', 
                             coord_type='x', 
                             shape_type='polygon', 
                             axis=1)
    
    gdf_new['ys'] = gdf.apply(getGeometryCoords, 
                             geom='geometry', 
                             coord_type='y', 
                             shape_type='polygon', 
                             axis=1)
    
    return ColumnDataSource(gdf_new)


def getGeometryCoords(row, geom, coord_type, shape_type):
    """
    Returns the coordinates ('x' or 'y') of edges of a Polygon exterior.
    
    Source: http://michael-harmon.com/blog/IntroToBokeh.html
    
    :param: (GeoPandas Series) row : The row of each of the GeoPandas DataFrame.
    :param: (str) geom : The column name.
    :param: (str) coord_type : Whether it's 'x' or 'y' coordinate.
    :param: (str) shape_type
    """
    
    # Parse the exterior of the coordinate
    if shape_type == 'polygon':
        exterior = row[geom].geoms[0].exterior
        if coord_type == 'x':
            # Get the x coordinates of the exterior
            return list( exterior.coords.xy[0] )    
        
        elif coord_type == 'y':
            # Get the y coordinates of the exterior
            return list( exterior.coords.xy[1] )

    elif shape_type == 'point':
        exterior = row[geom]
    
        if coord_type == 'x':
            # Get the x coordinates of the exterior
            return  exterior.coords.xy[0][0] 

        elif coord_type == 'y':
            # Get the y coordinates of the exterior
            return  exterior.coords.xy[1][0]

data = get_iso(router, from_place, time, date, modes, max_dist, step, nb_iter, Viridis, inProj, outProj)

#geo_source = GeoJSONDataSource(geojson=str(data[0]))
geo_source = data[0]


color_mapper = LinearColorMapper(palette=data[1])

TOOLS = "pan,wheel_zoom,box_zoom,reset,hover,save"

p = figure(title="Iso_app_test", tools=TOOLS, x_axis_location=None, y_axis_location=None, width=800, height=800)
p.grid.grid_line_color = None

p.patches('xs', 'ys', fill_alpha=0.5, fill_color={'field': 'time', 'transform': color_mapper}, 
          line_color='white', line_width=0.5, source=geo_source)

p.add_tile(STAMEN_TONER)

#hover = p.select_one(HoverTool)
#hover.point_policy = "follow_mouse"
#hover.tooltips = [("Provincia:", "@provincia")]

output_file("Iso_app.html", title="Testing isochrone")

show(p)

#p = figure(
#           x_range=(-100000, 400000),
#           y_range=(6050000, 6300000),
#           width=800, 
#           height=800, 
#           title="Iso_app")
#p.add_tile(STAMEN_TONER)
#
#patch_source = ColumnDataSource(dict(x=[], y=[], color=[]))
#
#p.patches(xs='x',
#          ys='y',
#          source = patch_source,
#          color='color')
#
#patch_source.data = data
# 
#
#show(p)