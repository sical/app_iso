# -*- coding: utf-8 -*-
"""Automate
Usage: automate.py  [<infile_csv>] [<outfile_json>] [<separator>]


Arguments:
  infile_csv        input file name (tsv or csv format) path, ex: ./params/params.tsv
  outfile_json      output json file name path, ex: ./params/params.json
  separator         separator used in the csv/tsv file
    
@author: thomas
"""
from datetime import datetime, timedelta, date
import os
import itertools
import time
import random

from bokeh.io import export_png, export_svgs
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA, CARTODBPOSITRON_RETINA
from bokeh.models import ColumnDataSource, Range1d, WheelZoomTool, PanTool
from bokeh.resources import CDN
from bokeh.embed import file_html
from shapely.geometry import Polygon
from geopandas import GeoDataFrame
from dotenv import load_dotenv
from pathlib import Path
import json
import rapidjson
import copy
from dateutil.relativedelta import relativedelta as rd
from pyproj import transform, Proj
import imageio
import numpy as np
import progressbar
from docopt import docopt
from selenium import webdriver
import geojson
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

from get_iso import get_iso, overlay
from make_plot import make_plot
from functions import geocode, colors_blend, hex2rgb, buffer_point, create_buffers, str_list_to_list, list_excluded, time_profile, seconds_to_time, convert_GeoPandas_to_Bokeh_format, cds_to_geojson, create_dir, write_geojson, dict_geojson, df_stats_to_json
from bokeh_tools import get_bbox
from csv_to_json import csv_to_json

#Set the provider
tile_provider = CARTODBPOSITRON_RETINA

#Set the webdriver 
my_webdriver = None

try:
    places_cache = "./params/places_cache.json"
    places_cache = json.load(open(places_cache))
except:
    places_cache = {} # dict to keep lat/lon if adress already been geocoded 
    
end_loop = False
tolerance = 400
value_max = 20

dict_all_times = {}
l_intersections_json = []

used_colors = [] #list of colors used to get unique color

columns_with_array_of_str = [
        "colors_iso",
        "adresses",
        "buffer_times",
        "buffer_opacity",
        "buffer_color",
        "buffer_contour_size",
        "excluded_modes",
        "durations"
        ]



def get_range_colors(color, value_max):
    if color - value_max < 0:
        color_start = 0
    else:
        color_start = color - value_max
        
    if color + value_max > 255:
        color_end = 255
    else:
        color_end = color + value_max
        
    range_color = [i for i in range(color_start, color_end, 1)]
    
    return range_color

def change_color(colors, used_colors, value_max):
        #Give each polygon a unique color
        l_colors = []
            
        nb = len(colors)
        r,g,b = hex2rgb(colors[0])
                
        reds = get_range_colors(r, value_max)
        greens = get_range_colors(g, value_max)
        blues = get_range_colors(b, value_max)
        
        if nb != 0:
            for i in range(0, nb):
                
#                new_color = random.choice(reds), random.choice(greens), random.choice(blues)
#                
#                if new_color in used_colors:
#                    while True:
#                        new_color = random.choice(reds), random.choice(greens), random.choice(blues)
#                        new_color = colors_blend(new_color, new_color)
#                        if new_color not in used_colors:
#                            l_colors.append(new_color)
#                            used_colors.append(new_color)
#                            break
#                else:
#                    new_color = colors_blend(new_color, new_color)
#                    l_colors.append(new_color)
#                    used_colors.append(new_color)
                    
                
                l_colors.append(colors[0])
                
            colors = np.array(l_colors)
        
        return colors
        

#def change_color(source, used_colors):
#        #Give each polygon a unique color
#        l_colors = []
#        nb = len(source.data['color'])
#        
#        if nb != 0:
#            r,g,b = hex2rgb(source.data['color'][0])
#            
#            if r + nb >= 255:
#                for i in range(0, nb):
#                    new_color = r - i, g, b
#                    new_color = colors_blend(new_color, new_color)
#                    l_colors.append(new_color)
#                
#            else:
#                for i in range(0, nb):
#                    new_color = r + i, g, b
#                    new_color = colors_blend(new_color, new_color)
#                    l_colors.append(new_color)
#            
#            source.data['color'] = np.array(l_colors)
#        
#        return source

def apply_color(x, dict_):
    return (dict_[x])

def change_color_again(cds):
    df = pd.DataFrame.from_dict(cds.data)
    dur_color = {}
    
    for dur in df["time"].unique():
        color = list(df["color"].loc[df["time"] == dur])[0]
        dur_color[dur] = color

    df['color'] = df["time"].apply(lambda x: apply_color(x, dur_color))
    new_cds = ColumnDataSource(df)
    
    return new_cds

def modify_color(duration, color):
    duration = duration//60
    color = color[:5]
    if len(str(duration)) < 2:
        duration = "0" + str(duration)
    return str(color) + str(duration)

def change_color_again_again(cds):
    df = pd.DataFrame.from_dict(cds.data)
    df['color'] = np.vectorize(modify_color)(df['time'], df['color'])
#    df['color'] = df.apply(lambda x: modify_color(x["time"], x["color"], axis=1))
    new_cds = ColumnDataSource(df)
    
    return new_cds
    
def pairwise(iterable):
    """
    source: https://stackoverflow.com/questions/5434891/iterate-a-list-as-pair-current-next-in-python
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    
    return zip(a, b)  

def run(params_iso,x,y,adress, color):
    global counter_polys
    global counter_lines
    global counter_points
    global counter_intersection
    global p_shape
    global gdf_poly_mask
    global alert
    global unique_id
    
    start_time = time.time()
    
    data = get_iso(params_iso, gdf_poly_mask, id_)
    dict_time["get_iso"] += time_profile(start_time, option="ms")
    start_time = time.time()
    
    gdf_poly_mask = data['gdf_poly_mask']

    source = data['source']
    shape = data['shape']
    data_intersection = data['intersection']
    status = data['status']
    gdf_poly = data['gdf_poly']
    source_buffer = data['source_buffer']
    source_convex = data['source_convex']
    source_envelope = data['source_envelope']
    source_simplified = data['source_simplified']
    source_buffered = data['source_buffered']
    
    list_gdf.append(gdf_poly)
    
    #Give each polygon a unique color 
    if step_mn == 0 and params_iso["durations"] == []:
        colors_iso = change_color(source.data['color'], used_colors, value_max)
        source.data['color'] = colors_iso
        if data_intersection.data['color'] != []:
            colors_intersection = change_color(data_intersection.data['color'], used_colors, value_max)
            data_intersection.data['color'] = colors_intersection
        for element in [source_convex, source_envelope, source_simplified, source_buffered]:
            if element is not None:
                element.data['color'] = colors_iso
        
        #DataSource to dict
        dict_source = {}
        for key,value in source.data.items():
            if type(value) is np.ndarray:
                new_value = value.tolist()
                dict_source[key] = new_value
            else:
                dict_source[key] = value
                
        dict_intersection = {}
        for key,value in source_intersection.data.items():
            if type(value) is np.ndarray:
                new_value = value.tolist()
                dict_intersection[key] = new_value
            else:
                dict_intersection[key] = value
        
        color = 'color' 
        
        colors_geo = colors_iso
#        print ("######## CASE 1 #############")
#        print (source.data['xs'])
#        print ("#############################")
    
    else:
        geo = json.loads(source.geojson)["features"]
        nb_colors = len(geo)
        colors = [params_iso['color'] for i in range(0, nb_colors)]
        color = change_color(colors, used_colors, value_max)
        colors_geo = color
        
        dict_poly = {}
        i_ = 0
        for poly, color_ in zip(geo, color):
            tmp = {}
            coords = poly["geometry"]["coordinates"][0]
            tmp["geometry"] = Polygon(coords)
            tmp["color"] = color_
            tmp["time"] = poly["properties"]["time"]
            dict_poly[i_] = tmp
            i_+=1
        
        df = pd.DataFrame.from_dict(dict_poly, orient="index")
        crs = {'init':'epsg:3857'}
        gdf = GeoDataFrame(df, crs=crs, geometry=df['geometry'])
        source = convert_GeoPandas_to_Bokeh_format(gdf)
        
        color = 'color'
        
        dict_source = {}
        dict_intersection = {}
    
    #CHANGE COLOR AGAIN
    source = change_color_again_again(source)
    colors_geo = source.data['color']
    
    if source is None:
        shape = ""
    
#        source_intersection.data.update(data_intersection.data)
        
    if only_overlay == 0:
        if shape == "poly":
            name = "polys" + str(counter_polys)
            options_iso_surf = dict(
                    fill_color='color', 
                    fill_alpha = params_iso['opacity_iso'],
                    line_color='color', 
                    line_alpha=params["fig_params"]["alpha_cont"],
                    line_width=params["fig_params"]["line_width_surf"], 
                    source=source,
                    legend="Isochrone_polys" + str(counter_polys)
                    )
            
            if simplify == "None":
                poly_patches = p_shape.patches(
                    'xs', 
                    'ys', 
                    **options_iso_surf,
                    name=name
                    )
                
                counter_polys += 1 
                
            #EXPORT TO GEOJSON
#            cds = dict_geojson(options_iso_surf, colors_geo)
#            print (cds)
#            write_geojson(cds, params_iso["id"], unique_id)
            
            ###########################################################
            # SIMPLIFIED VERSIONS
            ###########################################################
            # Convex_hull polygons
            if simplify == "convex" and source_convex is not None:
                options_iso_convex = dict(
                        fill_color = 'color', 
                        fill_alpha = options_iso_surf['fill_alpha'],
                        line_color=color, 
                        line_alpha=params["fig_params"]["alpha_cont"],
                        line_width=params["fig_params"]["line_width_surf"], 
                        source=source_convex,
                        legend=name + " (convex)"
                        )
                
                poly_convex = p_shape.patches(
                    'xs', 
                    'ys', 
                    **options_iso_convex,
                    name=name + " (convex)"
                    )
                
                #EXPORT TO GEOJSON
                cds = dict_geojson(options_iso_convex, colors_geo)
                write_geojson(cds, params_iso["id"], unique_id)
            
            # Envelope polygons
            if simplify == "envelope" and source_envelope is not None:
                options_iso_envelope = dict(
                        fill_color = 'color', 
                        fill_alpha = options_iso_surf['fill_alpha'],
                        line_color=color, 
                        line_alpha=params["fig_params"]["alpha_cont"],
                        line_width=params["fig_params"]["line_width_surf"], 
                        source=source_envelope,
                        legend=name + " (envelope)"
                        )
            
                poly_envelope = p_shape.patches(
                    'xs', 
                    'ys', 
                    **options_iso_envelope,
                    name=name + " (envelope)"
                    )
                
                #EXPORT TO GEOJSON
                cds = dict_geojson(options_iso_envelope, colors_geo)
                write_geojson(cds, params_iso["id"], unique_id)
                
            # Simplified polygons
            if simplify == "simplify" and source_simplified is not None:
                options_iso_simplified = dict(
                        fill_color = 'color', 
                        fill_alpha = options_iso_surf['fill_alpha'],
                        line_color=color, 
                        line_alpha=params["fig_params"]["alpha_cont"],
                        line_width=params["fig_params"]["line_width_surf"], 
                        source=source_simplified,
                        legend=name + " (simplified)"
                        )
                
                poly_simplified = p_shape.patches(
                    'xs', 
                    'ys', 
                    **options_iso_simplified,
                    name=name + " (simplified)"
                    )
                
                #EXPORT TO GEOJSON
                cds = dict_geojson(options_iso_simplified, colors_geo)
                write_geojson(cds, params_iso["id"], unique_id)
                
            # Buffered polygons
            if simplify == "buffered" and source_buffered is not None:
                options_iso_buffered = dict(
                        fill_color = 'color', 
                        fill_alpha = options_iso_surf['fill_alpha'],
                        line_color=color, 
                        line_alpha=params["fig_params"]["alpha_cont"],
                        line_width=params["fig_params"]["line_width_surf"], 
                        source=source_buffered,
                        legend=name + " (buffered)"
                        )
                
                poly_buffered = p_shape.patches(
                    'xs', 
                    'ys', 
                    **options_iso_buffered,
                    name=name + " (buffered)"
                    )
                
                #EXPORT TO GEOJSON
                cds = dict_geojson(options_iso_buffered, colors_geo)
                write_geojson(cds, params_iso["id"], unique_id)
                
            ###########################################################
            
        elif shape == "line":
            name = "lines"  + str(counter_lines)
            options_iso_contours = dict(
                    line_color=color, 
                    line_alpha = opacity_iso,
                    line_width=params["fig_params"]["line_width_cont"], 
                    source=source,
                    legend="Isochrone_lines" + str(counter_lines)
                    )
            
            p_shape.multi_line(
                'xs', 
                'ys', 
                **options_iso_contours,
                name=name
                )
            
            counter_lines += 1
            
            ###########################################################
            # SIMPLIFIED VERSIONS
            ###########################################################
            
            # Convex_hull polygons
            if simplify == "convex" and source_convex is not None:
                options_iso_convex = dict(
                        line_color = 'color', 
                        line_alpha = options_iso_surf['line_alpha'],
                        line_width=params["fig_params"]["line_width_cont"], 
                        source=source_convex,
                        legend="Iso_convex_" + str(counter_polys)
                        )
                
                poly_convex = p_shape.multi_line(
                    'xs', 
                    'ys', 
                    **options_iso_convex,
                    name=name + " (convex)"
                    )
            
            # Envelope polygons
            if simplify == "envelope" and source_envelope is not None:
                options_iso_envelope = dict(
                        line_color = 'color', 
                        line_alpha = options_iso_surf['line_alpha'],
                        line_width=params["fig_params"]["line_width_cont"],  
                        source=source_envelope,
                        legend=name + " (envelope)"
                        )
                
                poly_envelope = p_shape.multi_line(
                    'xs', 
                    'ys', 
                    **options_iso_envelope,
                    name=name + " (envelope)"
                    )
                
            
            # Simplified polygons
            if simplify == "simplify" and source_simplified is not None:
                options_iso_simplified = dict(
                        line_color = 'color', 
                        line_alpha = options_iso_surf['line_alpha'],
                        line_width=params["fig_params"]["line_width_cont"], 
                        source=source_simplified,
                        legend=name + " (simplified)"
                        )
                
                poly_simplified = p_shape.multi_line(
                    'xs', 
                    'ys', 
                    **options_iso_simplified,
                    name=name + " (simplified)"
                    )
                
            # Buffered polygons
            if simplify == "buffered" and source_buffered is not None:
                options_iso_buffered = dict(
                        line_color = 'color', 
                        line_alpha = options_iso_surf['line_alpha'],
                        line_width=params["fig_params"]["line_width_cont"], 
                        source=source_simplified,
                        legend=name + " (buffered)"
                        )
                
                poly_buffered = p_shape.multi_line(
                    'xs', 
                    'ys', 
                    **options_iso_buffered,
                    name=name + " (buffered)"
                    )
            ###########################################################
            
        elif shape == "point":
            name="points"  + str(counter_polys)
            options_iso_pts = dict(
                    color=color,
                    alpha = opacity_iso,
                    line_width=params["fig_params"]["line_width_surf"], 
                    size=3,
                    source=source,
                    legend="Isochrone_points" + str(counter_points),
                    name="intersection"
                    )
            
            p_shape.circle(
                'x', 
                'y', 
                **options_iso_pts,
                name="points"  + str(counter_polys)
                )
            
            counter_points += 1
        
        
#        if data_intersection is not None:
#    #        name = "Intersection" + str(counter_intersection)
#    #        source_intersection = data_intersection
#            name = "Overlay"
#            source_intersection.data.update(data_intersection.data)
#            options_intersect = dict(
#    #                fill_alpha= params["fig_params"]["alpha_surf"], 
#        #            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
#                    source=source_intersection,
#                    fill_color='color',
#                    fill_alpha=params_iso['opacity_intersection'],
#                    line_color='color', 
#                    line_alpha=params["fig_params"]["alpha_cont"],
#                    line_width=params["fig_params"]["line_width_surf"], 
#    #                fill_color="black", 
#    #                fill_alpha = 0.70,
#    #                line_color="black", 
#    #                line_width=params["fig_params"]["line_width_surf"], 
#                    legend=name
#                    )
#            
#            intersections = p_shape.patches(
#                                            'xs', 
#                                            'ys', 
#                                            **options_intersect
#                                            )
#            counter_intersection += 1
#            
#    else:
#        if data_intersection is not None:
#    #        name = "Intersection" + str(counter_intersection)
#    #        source_intersection = data_intersection
#            name = "Overlay"
#            source_intersection.data.update(data_intersection.data)
#            
#            if end_loop is True:
#                options_intersect = dict(
#        #                fill_alpha= params["fig_params"]["alpha_surf"], 
#            #            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
#                        source=source_intersection,
#                        fill_color='color',
#                        fill_alpha=params_iso['opacity_intersection'],
#                        line_color='color', 
#                        line_alpha=params["fig_params"]["alpha_cont"],
#                        line_width=params["fig_params"]["line_width_surf"], 
#        #                fill_color="black", 
#        #                fill_alpha = 0.70,
#        #                line_color="black", 
#        #                line_width=params["fig_params"]["line_width_surf"], 
#                        legend=name
#                        )
#                
#                intersections = p_shape.patches(
#                                                'xs', 
#                                                'ys', 
#                                                **options_intersect
#                                                )
        
    #Draw buffer radar
    if buffer_radar == 1:
        if source_buffer is not None:
            buffer_name = "Buffer_" + name
        #    source_intersection = data_intersection
            
            
            options_buffer = dict(
                    source=source_buffer,
                    fill_color="grey",
                    fill_alpha=0.0,
                    line_color='color',
                    line_width='width',
                    line_alpha=1.0, 
                    legend=buffer_name
                    )
            
            buffer = p_shape.patches(
                                    'xs', 
                                    'ys', 
                                    **options_buffer
                                    )
    #Draw only buffers
    
    p_shape.legend.location = "top_right"
    p_shape.legend.click_policy="hide"
    p_shape.legend.visible = False
    
    if data_intersection is None:
        return p_shape, dict_source, None
    else:
        return p_shape, dict_source, data_intersection.data

###################################################
###################################################
###################################################
###################################################
###################################################
###################################################

if __name__ == "__main__":
    
    unique_id = 0

    #Parameters
    try:
        env_path = Path('./') / '.env'
        load_dotenv(dotenv_path=env_path)
        TOKEN = os.getenv("NAVITIA_TOKEN")
    except:
        TOKEN = os.getenv("NAVITIA_TOKEN")
        
#    params = "./params/params.json"
#    params = json.load(open(params))

    fmt = 'Elapsed time: {0.minutes} minutes {0.seconds} seconds'
    
    #Default
    default = "./params/default.json"
    default = json.load(open(default))
    #output_png = "./output_png/tests/"
    from_place = default["from_place"]
    adress = default["adress"]
    time_ = default["time_"]
    step = default["step"]
    nb_iter = default["nb_iter"]
    year_min = default["year_min"]
    month_min = default["month_min"]
    day_min = default["day_min"]
    year_max = default["year_max"]
    month_max = default["month_max"]
    day_max = default["day_max"]
    counter_polys = 0 
    counter_lines = 0 
    counter_points = 0 
    counter_intersection = 0 
    alert = """<span style="color: red"><b>{}</b></span>"""
    selected = False
    old_selections = []
    list_gdf = []
    coeff_ampl = 0.8 # See Brinkhoff et al. paper
    coeff_conv = 0.2 # See Brinkhoff et al. paper
    
    export_auto = True
    anim = False
    
    #Set range date
    min_date = date(year_min, month_min, day_min)
    max_date = date(year_max, month_max, day_max)
    ####################
    
    #Set ColumnDataSource
    source_poly = {}
    ####################
    
    #Set intersections
    gdf_poly_mask = None
    ####################
    
    #JSON INPUT
    arguments = docopt(__doc__)
    infile = arguments["<infile_csv>"]
    outfile = arguments["<outfile_json>"]
    sep = arguments["<separator>"]
    json_file = csv_to_json(infile, outfile, sep, columns_with_array_of_str)
#    json_file = "./paracsv_to_jsonms/params_auto.json"
    params_auto = json.load(open(json_file, encoding='utf-8'))
    ####################

    source_iso = ColumnDataSource(
            data=dict(
                    xs=[], 
                    ys=[], 
                    adress=[],
                    time=[],
                    duration=[], 
                    color=[],
                    date=[],
                    shape=[],
                    area=[],
                    perimeter=[],
                    nb_componants=[],
                    amplitude=[],
                    convex=[],
                    norm_notches=[],
                    complexity=[]
                    )
            )
            
    TOOLS = ""
    
    #export_no_tiles = "./output_png/tests/no_tiles/"
    #export_with_tiles = "./output_png/tests/with_tiles/"
    #export_anim = "./output_png/tests/animation/"
    
    #Default params to start
    fig_params = {
            "width":800,
            "height":800,
            "alpha_tile":0.5
    }
    params = {
            "fig_params":fig_params
            }
    
    params_plot = {
                'params':params, 
                'tools':TOOLS,
    #            'buildings':buildings,
    #            'network':network,
                'tile_provider':None,
                'source_iso': source_iso,
                'title': ""
                }
    
    p_shape = make_plot(params_plot)
    
    #Delete logo and toolbar
    p_shape.toolbar.logo = None
    p_shape.toolbar_location = None
    
    #Add origin points
    source_origins = ColumnDataSource(
            data=dict(
                    x=[], 
                    y=[],
                    adress=[]
                    )
            )
    
    source_intersection = ColumnDataSource(
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
            
    #Buffers solo
#    source_buffers = ColumnDataSource(
#            data=dict(
#                    xs=[], 
#                    ys=[], 
#                    times=[],
#                    colors=[],
#                    width=[],
#                    fill_alpha=[],
#                    radius = []
#                    )
#            )

    
    #PROGRESS BAR##################
    widgets=[
        ' [',progressbar.ETA(), '] ',
        progressbar.Bar(),
        progressbar.Percentage(),
    ]
    
    bar = progressbar.ProgressBar(max_value=len(params_auto), redirect_stdout=True)
    ################################
    
    if export_auto is True:
        start_time = time.time()
        for i,param in enumerate(params_auto):
            
            #Recreate dict params
            proj = {
                		"inProj": param["inProj"],
                		"outProj": param["outProj"]
            }
            
            fig_params = {
                    		"width": param["width"],
                    		"height": param["height"],
                    		"alpha_tile": param["alpha_tile"],
                    		"alpha_surf": param["alpha_surf"],
                    		"alpha_cont": param["alpha_cont"],
                    		"alpha_building": param["alpha_building"],
                    		"alpha_network": param["alpha_network"],
                    		"color_network": param["color_network"],
                    		"line_width_surf": param["line_width_surf"],
                    		"line_width_cont": param["line_width_cont"],
                    		"line_width_building": param["line_width_building"]
            }
            
            params = {}
            params["proj"] = proj
            params["fig_params"] = fig_params
            ####################
            
            #Projections
            inProj = params["proj"]["inProj"]
            outProj = params["proj"]["outProj"]
            epsg_in = Proj(init=inProj)
            epsg_out = Proj(init=outProj)
            ####################
            
            #Range for figure
            points = []
            for element in param["adresses"]:
                coords = geocode(element, places_cache)
                coords = transform(epsg_in,epsg_out,coords[0],coords[1]) 
                points.append(coords)
                
            bounds = get_bbox(points, param["distance_bbox"])
            start_x, end_x = bounds.start_x, bounds.end_x
            start_y, end_y = bounds.start_y, bounds.end_y
            ####################
            
            how = param["how"]
            colors_iso = param["colors_iso"]
            color_switch = param["colors_intersection"]
            if color_switch == "None":
                color_switch = None
            region_id = param["region_id"]
            date_value = param["date"]
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
            adresses = param["adresses"]
            time_value = param["time"]
            try:
                jump = param["jump"].split(",")
                jump_mn, jump_nb = int(jump[0]), int(jump[1])
            except:
                jump_mn, jump_nb = 0,0
            duration = param["duration"]
            id_ = param["region_id"]
            step_value = int(param["duration"]) * 60
            opacity_iso = param["opacity_isos"]
            opacity_intersection = param["opacity_intersection"]
            shape = param["shape"]
            identity = str(param["id"])
            buffer_radar = param["buffer_radar"]
            step_mn = param["step"]
            simplify = param["simplify"]
            if simplify == "simplify":
                tolerance = param["tolerance"]
                topology = param["preserve_topology"]
                if topology == 1:
                    topology = True
                else:
                    topology = False
            else:
                tolerance = 10
                topology = False
            try:
                around = param["around"].split(',')
                around = [int(around[0]), int(around[1])]
            except:
                around = []
            origine_screen = param["origine_screen"]	
            only_overlay = param["only_overlay"]
            only_buffer = param["only_buffer"]	
            buffer_times = param["buffer_times"]	
            buffer_opacity = param["buffer_opacity"]	
            buffer_color = param["buffer_color"]	
            buffer_contour_size = param["buffer_contour_size"]
            excluded_modes = param["excluded_modes"]
            export_no_tiles = param["export_no_tiles"]
            export_with_tiles = param["export_with_tiles"]
            export_only_tiles = param["export_only_tiles"]
            export_anim = param["export_anim"]
            
            if excluded_modes != []:
                str_modes = list_excluded(excluded_modes)
            else:
                str_modes = ""
            
            l_dict_iso = []
            l_buffer = []
            
            gdf_poly_mask = None
            
            counter_polys = 0
            counter_lines = 0
            counter_points = 0
            counter_intersection = 0
            
            x = []
            y = []
            l_adress = []
            l_colors = colors_iso
            
            
            if jump_mn != 0:
                dict_time = {}
                dict_time["get_iso"] = 0
                
                for adress in adresses:
                    end_loop = False
                    index_list = adresses.index(adress)
                    color = colors_iso[index_list]
                    
                    from_place = geocode(adress, places_cache)
                    
                    x_, y_ = transform(epsg_in,epsg_out,from_place[0],from_place[1]) 
                    x.append(x_)
                    y.append(y_)
                    l_adress.append(adress)
                    from_place = str(from_place[0]) + ";" + str(from_place[1])
                    
                    for nb in range(0, jump_nb):
                        add_mn = timedelta(seconds=nb*jump_mn*60)
                        datetime_object = datetime.strptime(time_value, '%H:%M')
                        new_time = (datetime_object + add_mn).strftime("%H:%M")
                        
                        params_iso = {
                            'token': TOKEN,
                            'from_place': from_place,
                            'address': adress,
                            'time_in': new_time,
                            'min_date': date_value,
                            'step': step_value,
                            'step_mn': 0,
                            'nb_iter': 1,
                            'shape': shape,
                            'inProj': inProj,
                            'outProj': outProj,
                            'how': how,
                            'color':color,
                            'color_switch': color_switch,
                            'opacity_intersection':opacity_intersection,
                            'opacity_iso':opacity_iso,
                            'str_modes': str_modes,
                            'tolerance': tolerance,
                            'simplify': simplify,
                            'topology': topology,
                            'durations': param["durations"],
                            'id': param["id"]
                                }     
                        
                        if nb == jump_nb-1:
                            end_loop = True
                        
                        p_shape, dict_source, dict_intersection = run(params_iso, x,y,l_adress, color)
                        
                        
                        if step_mn == 0 and params_iso["durations"] == []:
                            del dict_source['xs']
                            del dict_source['ys']
                            del dict_intersection['xs']
                            del dict_intersection['ys']
                            l_dict_iso.append(dict_source)
            
            elif only_buffer == 1: #Do only buffers, no isochrones
                epsg_in = Proj(init=inProj)
                epsg_out = Proj(init=outProj)
                places = [geocode(adress, places_cache) for adress in adresses]
                colors = buffer_color
                opacities = buffer_opacity
                times = str_list_to_list(buffer_times)
                contours = str_list_to_list(buffer_contour_size)
                
                l_colors = colors
                
                for adress,place,opacity,time_,contour in zip(
                        adresses,
                        places,
                        opacities,
                        times,
                        contours
                        ):
                    index_color = adresses.index(adress)
                    color = colors[index_color]
                    fill_colors = [color for x in time_]
                    
                    x_, y_ = transform(epsg_in,epsg_out,place[0],place[1]) 
                    x.append(x_)
                    y.append(y_)
                    l_adress.append(adress)
                    
                    fill_colors = change_color(fill_colors, used_colors, value_max)

                    params_buffers = {
                            "inproj":epsg_in,
                            "outproj":epsg_out,
                            "colors":fill_colors,
                            "opacities":opacity,
                            "times":time_,
                            "contours":contour,
                            "from_place":place,
                            "address":adress
                            }
                    
                    start_time = time.time()
                    source_buffers = create_buffers(params_buffers)
                    dict_time = {}
                    dict_time["buffer"] = time_profile(start_time, option="ms")
                    del params_buffers["inproj"]
                    del params_buffers["outproj"]
                    del params_buffers["opacities"]
                    del params_buffers["from_place"]
                    params_buffers["colors"] = list(params_buffers["colors"])
                    
                    l_buffer.append(params_buffers)
                    
                    options_buffers = dict(
                            source=source_buffers,
                            fill_color='colors',
                            fill_alpha='fill_alpha',
                            line_color='colors',
                            line_width="width"
#                            line_alpha=1.0,
                            )
                    
                    p_shape.patches(
                                    xs='xs', 
                                    ys='ys', 
                                    **options_buffers
#                                    legend=adress
                                    )
                   
                p_shape.legend.location = "top_right"
                p_shape.legend.click_policy="hide"
                p_shape.legend.visible = False
                        
            else:
                if around != []:
                    dict_time = {}
                    dict_time["get_iso"] = 0
                    for adress in adresses:
                        index_list = adresses.index(adress)
                        color = colors_iso[index_list]
                        
                        from_place = geocode(adress, places_cache)
                        
                        places = buffer_point(from_place, epsg_in, epsg_out, around[0], around[1])
                        
                        for place in places:
                        
                            x_, y_ = transform(epsg_in,epsg_out,place[0],place[1]) 
                            x.append(x_)
                            y.append(y_)
                            l_adress.append(adress)
                            from_place = str(place[0]) + ";" + str(place[1])
                        
                            params_iso = {
                                'token': TOKEN,
                                'address': adress,
                                'from_place': from_place,
                                'time_in': time_value,
                                'min_date': date_value,
                                'step': step_value,
                                'step_mn': step_mn,
                                'nb_iter': 1,
                                'shape': shape,
                                'inProj': inProj,
                                'outProj': outProj,
                                'how': how,
                                'color':color,
                                'color_switch': color_switch,
                                'opacity_intersection':opacity_intersection,
                                'opacity_iso':opacity_iso,
                                'str_modes': str_modes,
                                'tolerance': tolerance,
                                'simplify': simplify,
                                'topology': topology,
                                'durations': param["durations"],
                                'id': param["id"]
                                    }     
                            
                            p_shape, dict_source, dict_intersection = run(params_iso, x,y,l_adress,color)
                            
                            if step_mn == 0 and params_iso["durations"] == []:
                                del dict_source['xs']
                                del dict_source['ys']
                                del dict_intersection['xs']
                                del dict_intersection['ys']
                                l_dict_iso.append(dict_source)
                            
                else:
                    dict_time = {}
                    dict_time["get_iso"] = 0
                    
                    #INTERSECTIONS, ONLY WORKS IF DURATIONS, STEP, JUMP AND AROUND ARE EMPTY
                    l_intersections = []
                    l_stats = ['amplitude', 'area', 'complexity', 'convex', 'nb_vertices', 'norm_notches', 'perimeter', 'area_sum']
                    
                    for intersection_index,adress in enumerate(adresses):
                        index_list = adresses.index(adress)
                        color = colors_iso[index_list]
                        
                        from_place = geocode(adress, places_cache)
                        
                        x_, y_ = transform(epsg_in,epsg_out,from_place[0],from_place[1]) 
                        x.append(x_)
                        y.append(y_)
                        l_adress.append(adress)
                        from_place = str(from_place[0]) + ";" + str(from_place[1])
                    
                        params_iso = {
                            'token': TOKEN,
                            'address': adress,
                            'from_place': from_place,
                            'time_in': time_value,
                            'min_date': date_value,
                            'step': step_value,
                            'step_mn': step_mn,
                            'nb_iter': 1,
                            'shape': shape,
                            'inProj': inProj,
                            'outProj': outProj,
                            'how': how,
                            'color':color,
                            'color_switch': color_switch,
                            'opacity_intersection':opacity_intersection,
                            'opacity_iso':opacity_iso,
                            'str_modes': str_modes,
                            'tolerance': tolerance,
                            'simplify': simplify,
                            'topology': topology,
                            'durations': param["durations"],
                            'id': param["id"]
                                }    

                        p_shape, dict_source, dict_intersection = run(params_iso, x,y,l_adress, color)
                        
                        #INTERSECTIONS, ONLY WORKS IF DURATIONS, STEP, JUMP AND AROUND ARE EMPTY
                        if intersection_index != 0 and dict_intersection is not None:
                            excluded = ["token", "shape", "inProj", "outProj", "address", "from_place", "min_date"]
                            nb = len(dict_intersection["xs"])
                            l_params = []
                            
                            dict_intersection["addresses"] = [adresses for x in range(0,nb)]
                            dict_intersection["intersection_index"] = [intersection_index for x in range(0,nb)]
                            
                            for k,v in params_iso.items():
                                if k not in excluded:
                                    dict_intersection[k] = [v for x in range(0,nb)]
                                    l_params.append(k)
                            
                            if step_mn == 0 and params_iso["durations"] == []:
                                del dict_source['xs']
                                del dict_source['ys']
                                del dict_intersection['xs']
                                del dict_intersection['ys']
                                l_dict_iso.append(dict_source)
    #                            print (pd.DataFrame.from_dict(dict_intersection))
                                l_intersections.append(pd.DataFrame.from_dict(dict_intersection))
                        
                
                    #INTERSECTIONS, ONLY WORKS IF DURATIONS, STEP, JUMP AND AROUND ARE EMPTY
                    if l_intersections != []:
                        df_all_intersections = pd.concat(l_intersections)
    #                    print (df_all_intersections.area)
    #                    print (df_all_intersections.area.where(df_all_intersections.area==0).dropna().size)

                        
                        #CHECK IF NULL VALUE FOR AREA
                        if df_all_intersections.area.where(df_all_intersections.area==0).dropna().size != 0:
#                            df_all_intersections = {}
                            nb_element = df_all_intersections["time_in"].count()
                            df_all_intersections["id"] = [param["id"] for i in range(0, nb_element)]
                            df_all_intersections["area_sum"] = [0 for i in range(0, nb_element)]
                            df_all_intersections["nb_poly"] = [0 for i in range(0, nb_element)]
                            df_all_intersections = df_all_intersections.reset_index()
#                            print (df_all_intersections)
#                            df_all_intersections = pd.DataFrame.from_dict(df_all_intersections)
#                            print (df_all_intersections)
                            
                        else:
                            df_all_intersections = df_all_intersections.loc[df_all_intersections["intersection_index"] == intersection_index]
                            df_all_intersections["area_sum"] = df_all_intersections["area"].sum()
                            df_all_intersections["nb_poly"] = len(df_all_intersections.index)
                        
#                        #Export to csv
#                        create_dir(export_no_tiles)
#                        name_csv = export_no_tiles + str(param["id"]) + "_intersections_details.csv"
#                        df_all_intersections.to_csv(name_csv, encoding="utf-8")
                        
                        #Make list of dict for future json export
                        l_intersections_json.append(df_stats_to_json(df_all_intersections, l_params, l_stats))
            
            #EXPORT NO_TILES PNG
            #Add origins points
            if origine_screen == 1:
                data = dict(
                            x=x,
                            y=y,
                            adress=l_adress,
                            color=l_colors
                            )
                source_origins.data.update(data)
                
                poly_circles = p_shape.circle(
                    'x', 
                    'y', 
                    source=source_origins,
                    fill_color='color', 
                    fill_alpha = 1.0,
                    size=10,
                    line_color='black',
                    line_alpha=1.0,
                    line_width=1.0, 
#                    legend="Origins"
                        )
                
            #Set range of figure
            if (start_x != end_x) and (start_y != end_y):
                p_shape.x_range = Range1d(start_x, end_x)
                p_shape.y_range = Range1d(start_y, end_y)
            
            p_shape.output_backend="webgl"
            p_shape.background_fill_color = None
            p_shape.border_fill_color = None
            p_shape.outline_line_color = None
            
#            p_shape.add_tile(
#                    tile_provider, 
#                    alpha=0.5, 
#                    name="no_tile",
#                    visible=False
#                    )
            
            create_dir(export_no_tiles)
            name = export_no_tiles + identity
            start_time = time.time()
            export_png(p_shape, filename="{}.png".format(name), webdriver=my_webdriver)
            dict_time["png_no_tiles"] = time_profile(start_time, option="ms")
#            export_png(p_shape, filename="{}.gif".format(name), webdriver=my_webdriver)
#            export_png(p_shape, filename="{}.bmp".format(name), webdriver=my_webdriver)
            p_shape.output_backend="svg"
            start_time = time.time()
            export_svgs(p_shape, filename="{}.svg".format(name), webdriver=my_webdriver)
            dict_time["svg"] = time_profile(start_time, option="ms")
            
            
            #EXPORT PARAMS TO JSON
            params_name = export_no_tiles + identity + "_params"
            json_name = filename="{}.json".format(params_name)
            with open(json_name, 'w', encoding='utf-8') as outfile:
                json.dump(param, outfile, sort_keys=True, indent=2)
                
            #EXPORT BUFFERS TO JSON
            if l_buffer != []:
                buffer_name = export_no_tiles + identity + "_buffer"
                json_name = filename="{}.json".format(buffer_name)
                with open(json_name, 'w', encoding='utf-8') as outfile:
                    json.dump(l_buffer, outfile, sort_keys=True, indent=2)
              
            #EXPORT ISOS TO JSON
            if l_dict_iso != []:
                iso_name = export_no_tiles + identity + "_iso"
                json_name = filename="{}.json".format(iso_name)
                with open(json_name, 'w', encoding='utf-8') as outfile:
                    json.dump(l_dict_iso, outfile, sort_keys=True, indent=2)
                
                #EXPORT OVERLAY TO JSON
#                overlay_name = export_no_tiles + identity + "_overlay"
#                json_name = filename="{}.json".format(overlay_name)
#                with open(json_name, 'w', encoding='utf-8') as outfile:
#                    json.dump(dict_intersection, outfile, sort_keys=True, indent=2)
                    
            #EXPORT TO HTLM
#            create_dir("./html/")
#            name = "./html/" + identity + ".html"
#            p_shape.add_tools(WheelZoomTool())
#            p_shape.add_tools(PanTool())
#            
#            html = file_html(p_shape, CDN, identity)
#            with open(name, "w") as f:
#                f.write(html)
            
            #EXPORT WITH_TILES PNG
            #Add origins points
            if origine_screen == 1:
                data = dict(
                            x=x,
                            y=y,
                            adress=l_adress,
                            color=l_colors
                            )
                source_origins.data.update(data)
                
                poly_circles = p_shape.circle(
                    'x', 
                    'y', 
                    source=source_origins,
                    fill_color='color', 
                    fill_alpha = 1.0,
                    size=10,
                    line_color='black',
                    line_alpha=1.0,
                    line_width=1.0, 
#                    legend="Origins"
                        )
            
            p_shape.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"], name="tile")
            
            #Set range of figure
            if (start_x != end_x) and (start_y != end_y):
                p_shape.x_range = Range1d(start_x, end_x)
                p_shape.y_range = Range1d(start_y, end_y)
                
#            else:
#                x_range_start, x_range_end = p_shape.x_range.start, p_shape.x_range.end
#                y_range_start, y_range_end = p_shape.y_range.start, p_shape.y_range.end
#                p_shape.x_range = Range1d(x_range_start, x_range_end)
#                p_shape.y_range = Range1d(y_range_start, y_range_end)
                
            p_shape.background_fill_color = None
            p_shape.border_fill_color = None
            p_shape.output_backend="webgl"
            
            create_dir(export_with_tiles)
            name = export_with_tiles + identity
            start_time = time.time()
            export_png(p_shape, filename="{}.png".format(name), webdriver=my_webdriver)
            dict_time["png_with_tiles"] = time_profile(start_time, option="ms")
#            export_png(p_shape, filename="{}.gif".format(name), webdriver=my_webdriver)
#            export_png(p_shape, filename="{}.bmp".format(name), webdriver=my_webdriver)
                
            #EXPORT PARAMS TO JSON
            params_name = export_with_tiles + identity + "_params"
            json_name = filename="{}.json".format(params_name)
            with open(json_name, 'w', encoding='utf-8') as outfile:
                json.dump(param, outfile, sort_keys=True, indent=2)
                
            #EXPORT ISOS TO JSON
            if l_dict_iso != []:
                iso_name = export_with_tiles + identity + "_iso"
                json_name = filename="{}.json".format(iso_name)
                with open(json_name, 'w', encoding='utf-8') as outfile:
                    json.dump(l_dict_iso, outfile, sort_keys=True, indent=2)
                
                #EXPORT OVERLAY TO JSON
#                overlay_name = export_with_tiles + identity + "_overlay"
#                json_name = filename="{}.json".format(overlay_name)
#                with open(json_name, 'w', encoding='utf-8') as outfile:
#                    json.dump(dict_intersection, outfile, sort_keys=True, indent=2)
            
            #EXPORT ONLY TILES
            x_range_start, x_range_end = p_shape.x_range.start, p_shape.x_range.end
            y_range_start, y_range_end = p_shape.y_range.start, p_shape.y_range.end
            
            p_shape = make_plot(params_plot)
            #Delete logo and toolbar
            p_shape.toolbar.logo = None
            p_shape.toolbar_location = None
            p_shape.x_range = Range1d(x_range_start, x_range_end)
            p_shape.y_range = Range1d(y_range_start, y_range_end)
            
            p_shape.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"], name="tile")
            
            create_dir(export_only_tiles)
            name = export_only_tiles + identity
            
            start_time = time.time()
            export_png(p_shape, filename="{}.png".format(name), webdriver=my_webdriver)
            dict_time["only_tiles"] = time_profile(start_time, option="ms")
            
            
            #RESET
            p_shape = make_plot(params_plot)
            #Delete logo and toolbar
            p_shape.toolbar.logo = None
            p_shape.toolbar_location = None
            
            #MEASURE ALL OVERLAYS AND COLORS
    #        zip_gdf = pairwise(list_gdf)
    #        for x in zip_gdf: 
    #            x[0]['time'] = None
    #            x[1]['time'] = None
    #            source_intersection, gdf_overlay = overlay(x[0], x[1], how, coeff_ampl, coeff_conv, color_switch)
    #            list_gdf.append(gdf_overlay)
                
    #        gdfs = pd.concat(list_gdf)
            
            exe_duration = time.time() - start_time
            dict_all_times[param["id"]] = dict_time
            
            
    #        gdfs.to_csv("test.csv")
            
            time.sleep(2) #sleep 5 seconds to avoid a Geocoder problem
    #        print (fmt.format(rd(seconds=exe_duration)))
            
            bar.update(i+1)
    
    #EXPORT LOGS
    df_times = pd.DataFrame.from_dict(dict_all_times, orient='index')
    dict_ = {}
    
    for col in df_times.columns:
        tmp = {}
        tmp["mean"] = df_times[col].mean()
        tmp["max"] = df_times[col].max()
        tmp["min"] = df_times[col].min()
        dict_[col] = tmp
        
    df_ = pd.DataFrame.from_dict(dict_, orient='columns')
    df = pd.concat([df_times, df_])
    
    for col in df.columns:
        new_col = col + "_format"
        df[new_col] = df[col].map(lambda x: seconds_to_time(x/1000, option="format"))
        
    df.to_csv("time_logs.csv")
    
    #WRITE PLACES_CACHE
    with open("./params/places_cache.json", 'w', encoding='utf-8') as outfile:
        json.dump(places_cache, outfile, sort_keys=True, indent=2)
        
    #EXPORT TO ONE JSON INTERSECTION FILE
    intersection_name = export_no_tiles + "intersections.json"
    if l_intersections_json != []:
        with open(intersection_name, 'w', encoding='utf-8') as outfile:
            json.dump(l_intersections_json, outfile, sort_keys=True, indent=2)
    
    if anim is True:
        adress = "20 hameau de la commanderie, 59840 LOMPRET"
        color = "#5BC862"
        date_value = "2018-06-28"
        date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        id_ = "fr-ne"
        step_value = 3600
        opacity_iso = 0.4
        shape = "poly"
        identity = "iso"
        step_mn = 1200
        how = "intersection"
        x_bounds = [305394,305394,382134,382134]
        y_bounds = [6521786, 6585394,6521786,6585394]
        duration = 0.5
        
        range_value = 86400//step_mn
        time_value = "08:00"
        
        start_time = time.time()
        
        epsg_in = Proj(init=inProj)
        epsg_out = Proj(init=outProj)
        
        from_place = geocode(adress, places_cache)
        l_adress = []
        x=[]
        y=[]
        ori = transform(epsg_in,epsg_out,from_place[0],from_place[1])
        from_place = str(from_place[0]) + ";" + str(from_place[1])
        
        params_iso = {
                'token': TOKEN,
                'address': adress,
                'from_place': from_place,
                'time_in': time_value,
                'min_date': date_value,
                'step': step_value,
                'nb_iter': 1,
                'shape': shape,
                'inProj': inProj,
                'outProj': outProj,
                'how': how,
                'color':color,
                'color_switch': "white",
                'opacity_intersection':0.0,
                'opacity_iso':opacity_iso,
                'id': param["id"]
                    }     
     
        for i in range(0,range_value):
            mn = step_mn*i
            time_value = timedelta(seconds=mn)
            params_iso["time_in"] = str(time_value)
        
            p_shape = run(params_iso, x,y,l_adress)
        
            #EXPORT NO_TILES PNG
            p_shape.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"], name="tile")
            
            #ADD TITLE
            title = "From: " + adress + ", Duration: " + str(step_value//60) + "mn at " + str(time_value)
            p_shape.title.text = title
            p_shape.title.align = "left"
            p_shape.title.text_color = "white"
            p_shape.title.text_font_size = "18px"
            p_shape.title.background_fill_color = "black"
    
            #Add circles as range
            #Add origins points
            source_bounds = ColumnDataSource(
                    data=dict(
                            x=x_bounds,
                            y=y_bounds
                    )
            ) 
            
            poly_circles = p_shape.circle(
                'x', 
                'y', 
                source=source_bounds,
                color='blue', 
                alpha = 0.0,
                size=10,
                    )
            
            source_ori = ColumnDataSource(
                    data=dict(
                            x=[ori[0]],
                            y=[ori[1]],
                    )
            ) 
            
            poly_circles = p_shape.circle(
                'x', 
                'y', 
                source=source_ori,
                color='blue', 
                alpha = 1.0,
                size=10,
                    )
            
            time_str = str(time_value).replace(":","_")
            iso_name = str(i) + identity + "_" + time_str
            iso_name = export_anim + iso_name
            
            #Set range of figure
            if (start_x != end_x) and (start_y != end_y):
                p_shape.x_range = Range1d(start_x, end_x)
                p_shape.y_range = Range1d(start_y, end_y)
            
            p_shape.background_fill_color = None
            p_shape.border_fill_color = None
            
            export_png(p_shape, filename="{}.png".format(iso_name), webdriver=my_webdriver)
            p_shape = make_plot(params_plot)
            
            #Delete logo and toolbar
            p_shape.toolbar.logo = None
            p_shape.toolbar_location = None
            
            time.sleep(2) #sleep 5 seconds to avoid a Geocoder problem
            
            exe_duration = time.time() - start_time
            
    #        print (fmt.format(rd(seconds=exe_duration)))
        
        images = []
        for file_name in os.listdir(export_anim):
            if file_name.endswith('.png'):
                file_path = os.path.join(export_anim, file_name)
                images.append(imageio.imread(file_path))
        iso_gif = export_anim + "anim_iso.gif"
        imageio.mimsave(iso_gif, images, duration=duration)
    