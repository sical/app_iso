# -*- coding: utf-8 -*-
"""
Created on Thu Apr 12 13:31:04 2018

@author: thomas
"""

import requests
import pandas as pd
from pandas.io.json import json_normalize
import geopandas as gpd
from pyproj import Proj, transform
import geojson
from geopy.geocoders import Nominatim
from shapely.geometry import MultiPoint

from bokeh.palettes import Viridis, Spectral, Plasma
from bokeh.io import show, output_notebook, output_file
from bokeh.plotting import figure, show, output_file
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import ColumnDataSource, GeoJSONDataSource, HoverTool, LinearColorMapper
from bokeh.layouts import row, widgetbox, gridplot

geolocator = Nominatim()

def geocode(adress):
    location = geolocator.geocode(adress)
    
    return location.latitude, location.longitude


def _convert_epsg(inProj, outProj, geojson_):
    gdf = gpd.GeoDataFrame.from_features(geojson_["features"])
    gdf.crs = {'init': inProj}
    gdf = gdf.to_crs({'init': outProj})
    
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
    list_pts = []
    for x in multipoly:
        list_pts.extend(list(x.exterior.coords))      
    
    x = [pt[0] for pt in list_pts]
    y = [pt[1] for pt in list_pts]
    
    return x,y


def _cutoffs(nb_iter, step):    
    end = step*(nb_iter+1)
    list_time = []
    cutoffs = ""

    for i in range(step, end, step):
        cutoffs += "&cutoffSec=" + str(i)
        list_time.append(i)
    
    return cutoffs, list_time
    
def get_iso(router, from_place, time, date, modes, max_dist, step, nb_iter, dict_palette, inProj, outProj):
    
    step = int(step)
    nb_iter = int(nb_iter)
    if nb_iter > 11:
        print ("Please select a number of iterations inferior to 11")
        return
    cut_time = _cutoffs(nb_iter, step)
    cutoffs = cut_time[0]
    list_time = cut_time[1]
    
#    dict_color = _palette(list_time, palette)[0]
    colors = _palette(list_time, dict_palette)
    
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
    gdf_poly = _convert_epsg(inProj, outProj, geojson_)
    
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
    
    datasource_poly = _convert_GeoPandas_to_Bokeh_format(gdf_poly, 'polygon')
    
    return datasource_poly, points, colors
    

def _palette(list_time, dict_palette):
    
    palette_nb = len(list_time)
    
    dict_colors = {}
    
    for item,value in dict_palette.items():
        if palette_nb > 11 or palette_nb < 3:
            print ("Please select a number inferior to 11 and superior to 3")
            return

        colors = value[palette_nb]
    
        #Create time/colors dict
#        dict_color = {time:color for time, color in zip(list_time, colors)}
        
        dict_colors[item] = colors
    
    return dict_colors

def _convert_GeoPandas_to_Bokeh_format(gdf, shape_type):
    """
    Function to convert a GeoPandas GeoDataFrame to a Bokeh
    ColumnDataSource object.
    
    Source: http://michael-harmon.com/blog/IntroToBokeh.html
    
    :param: (GeoDataFrame) gdf: GeoPandas GeoDataFrame with polygon(s) under
                                the column name 'geometry.'
                                
    :return: ColumnDataSource for Bokeh.
    """
    gdf_new = gdf.drop('geometry', axis=1).copy()
    gdf_new['xs'] = gdf.apply(_getGeometryCoords, 
                             geom='geometry', 
                             coord_type='x', 
                             shape_type=shape_type, 
                             axis=1)
    
    gdf_new['ys'] = gdf.apply(_getGeometryCoords, 
                             geom='geometry', 
                             coord_type='y', 
                             shape_type=shape_type, 
                             axis=1)

    return ColumnDataSource(gdf_new)


def _getGeometryCoords(line, geom, coord_type, shape_type):
    """
    Returns the coordinates ('x' or 'y') of edges of a Polygon exterior.
    
    Source: http://michael-harmon.com/blog/IntroToBokeh.html
    
    :param: (GeoPandas Series) line : The row of each of the GeoPandas DataFrame.
    :param: (str) geom : The column name.
    :param: (str) coord_type : Whether it's 'x' or 'y' coordinate.
    :param: (str) shape_type
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
        
def make_plot(colors, 
             palette_name, 
             params, 
             TOOLS, 
             source_polys,
             source_pts,
             tile_provider,
             x_range=None,
             y_range=None):
    
    color_mapper = LinearColorMapper(palette=colors[palette_name])
    
    
    # SURFACE
    if x_range is None and y_range is None:
        p_surface_cat = figure(
                title= palette_name.upper() + " categorized surface", 
                tools=TOOLS, 
                x_axis_location=None, 
                y_axis_location=None, 
                width=params["fig_params"]["width"], 
                height=params["fig_params"]["height"])
                
    else:
        p_surface_cat = figure(
                title= palette_name.upper() + " categorized surface", 
                tools=TOOLS, 
                x_axis_location=None, 
                y_axis_location=None, 
                width=params["fig_params"]["width"], 
                height=params["fig_params"]["height"],
                x_range=x_range,
                y_range=y_range)
    
    p_surface_cat.grid.grid_line_color = None
    p_surface_cat.patches('xs', 
                          'ys', 
                          fill_alpha= params["fig_params"]["alpha_surf"], 
                          fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
                          line_color='white', 
                          line_width=params["fig_params"]["line_width_surf"], 
                          source=source_polys)
    
    p_surface_cat.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"])
    ########
    
    x_range = p_surface_cat.x_range
    y_range = p_surface_cat.y_range
    
    # CONTOUR 
    p_contour_cat = figure(
            title=palette_name.upper() + " categorized contour",  
            tools=TOOLS, 
            x_axis_location=None, 
            y_axis_location=None, 
            width=params["fig_params"]["width"], 
            height=params["fig_params"]["height"],
            x_range=x_range,
            y_range=y_range)
    p_contour_cat.grid.grid_line_color = None
    p_contour_cat.multi_line('xs', 
                             'ys', 
                             line_alpha= params["fig_params"]["alpha_cont"], 
                             color={'field': 'time', 'transform': color_mapper},
                             line_width=params["fig_params"]["line_width_cont"], 
                             source=source_polys)
    
    p_contour_cat.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"])
    
    
    # POINTS 
    p_points_cat = figure(
            title=palette_name.upper() + " categorized points",  
            tools=TOOLS, 
            x_axis_location=None, 
            y_axis_location=None, 
            width=params["fig_params"]["width"], 
            height=params["fig_params"]["height"],
            x_range=x_range,
            y_range=y_range)
    
    p_points_cat.grid.grid_line_color = None
    p_points_cat.circle(
            'x', 
            'y', 
            line_alpha= params["fig_params"]["alpha_surf"], 
            color={'field': 'time', 'transform': color_mapper},
            line_width=params["fig_params"]["line_width_surf"], 
            size=3,
            source=source_pts
            )

    
    p_points_cat.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"])
    
    list_plot = [p_surface_cat, p_contour_cat, p_points_cat]
    
    return list_plot
    