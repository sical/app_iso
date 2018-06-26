# -*- coding: utf-8 -*-
"""
@author: thomas
"""
from datetime import date
import os

from bokeh.io import export_png, export_svgs
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import ColumnDataSource
from dotenv import load_dotenv
from pathlib import Path
import json
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta as rd
from pyproj import transform, Proj

from get_iso import get_iso
from make_plot import make_plot
from functions import geocode

#Parameters
try:
    env_path = Path('./') / '.env'
    load_dotenv(dotenv_path=env_path)
    TOKEN = os.getenv("NAVITIA_TOKEN")
except:
    TOKEN = os.getenv("NAVITIA_TOKEN")
params = "./params/params.json"
params = json.load(open(params))

fmt = '{0.days} days {0.hours} hours {0.minutes} minutes {0.seconds} seconds'

#Projections
inProj = params["proj"]["inProj"]
outProj = params["proj"]["outProj"]

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
color_choice = 0
names = []
alert = """<span style="color: red"><b>{}</b></span>"""
selected = False
old_selections = []
color_value = (127,127,127)

#Set range date
min_date = date(year_min, month_min, day_min)
max_date = date(year_max, month_max, day_max)

#Set ColumnDataSource
source_poly = {}

#Set intersections
gdf_poly_mask = None


#JSON INPUT
json_file = "./params/params_auto.json"
params_auto = json.load(open(json_file))


#source_iso = ColumnDataSource(
#        data=dict(
#                xs=[], 
#                ys=[], 
#                adress=[],
#                time=[],
#                duration=[], 
#                color=[],
#                date=[],
#                shape=[],
#                area=[],
#                perimeter=[],
#                nb_componants=[],
#                amplitude=[],
#                convex=[],
#                norm_notches=[],
#                complexity=[]
#                )
#        )
        
TOOLS = ""

export_no_tiles = "./output_png/tests/no_tiles/"
export_with_tiles = "./output_png/tests/with_tiles/"

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

def run(x,y,adress):
    global counter_polys
    global counter_lines
    global counter_points
    global counter_intersection
    global names
    global p_shape
    global color_choice
    global gdf_poly_mask
    global alert
    global color_value
    global opacity_intersection
    global opacity_iso
    
    data = get_iso(params_iso, gdf_poly_mask, id_)
    gdf_poly_mask = data['gdf_poly_mask']

    source = data['source']
    shape = data['shape']
    data_intersection = data['intersection']
    status = data['status']
    
    if source is None:
        shape = ""
    
#        source_intersection.data.update(data_intersection.data)

    if shape == "poly":
        name = "polys" + str(counter_polys)
        options_iso_surf = dict(
                fill_color='color', 
                fill_alpha = opacity_iso,
                line_color='white', 
                line_alpha=0.0,
                line_width=params["fig_params"]["line_width_surf"], 
                source=source,
                legend="Isochrone_polys" + str(counter_polys)
                )
        
        poly_patches = p_shape.patches(
            'xs', 
            'ys', 
            **options_iso_surf,
            name=name
            )
        
        counter_polys += 1 
        
    elif shape == "line":
        name = "lines"  + str(counter_lines)
        options_iso_contours = dict(
                line_color='color', 
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
        
    elif shape == "point":
        name="points"  + str(counter_polys)
        options_iso_pts = dict(
                color='color',
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
        
        
    if data_intersection is not None:
#        name = "Intersection" + str(counter_intersection)
#        source_intersection = data_intersection
        name = "Overlay"
        source_intersection.data.update(data_intersection.data)
        options_intersect = dict(
#                fill_alpha= params["fig_params"]["alpha_surf"], 
    #            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
                source=source_intersection,
                fill_color='color',
                fill_alpha=opacity_intersection,
                line_color='white', 
                line_alpha=0.0,
                line_width=params["fig_params"]["line_width_surf"], 
#                fill_color="black", 
#                fill_alpha = 0.70,
#                line_color="black", 
#                line_width=params["fig_params"]["line_width_surf"], 
                legend=name
                )
        
        intersections = p_shape.patches(
                                        'xs', 
                                        'ys', 
                                        **options_intersect
                                        )
        counter_intersection += 1
        
    p_shape.legend.location = "top_right"
    p_shape.legend.click_policy="hide"
    p_shape.legend.visible = False
    
    return p_shape

for param in params_auto:
    how = param["how"]
    colors_iso = param["colors_iso"]
    color_switch = param["colors_intersection"]
    if color_switch == "None":
        color_switch = None
    opacity_isos = param["opacity_isos"]
    region_id = param["region_id"]
    date_value = param["date"]
    date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
    adresses = param["adresses"]
    time_value = param["time"]
    duration = param["duration"]
    id_ = param["region_id"]
    step_value = int(param["duration"]) * 60
    opacity_iso = param["opacity_isos"]
    opacity_intersection = param["opacity_intersection"]
    shape = param["shape"]
    
    gdf_poly_mask = None
    
    counter_polys = 0
    counter_lines = 0
    counter_points = 0
    counter_intersection = 0
    
    start_time = time.time()
    
    x = []
    y = []
    l_adress = []
    l_colors = colors_iso
    
    epsg_in = Proj(init=inProj)
    epsg_out = Proj(init=outProj)
    
    for adress in adresses:
        index_list = adresses.index(adress)
        color = colors_iso[index_list]
        
        from_place = geocode(adress)
        
        x_, y_ = transform(epsg_in,epsg_out,from_place[0],from_place[1]) 
        x.append(x_)
        y.append(y_)
        l_adress.append(adress)
        from_place = str(from_place[0]) + ";" + str(from_place[1])
        
        opacity_iso = opacity_iso
    
        params_iso = {
            'token': TOKEN,
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
            'color_switch': color_switch
                }     
        
        p_shape = run(x,y,l_adress)
        
#        if index_list == len(adresses) -1:
#            export_png(p_shape, filename="{}.png".format(name))
    
    #EXPORT NO_TILES PNG
    name = export_no_tiles + param["name"]
    export_png(p_shape, filename="{}.png".format(name))
    json_name = filename="{}.json".format(name)
    
    with open(json_name, 'w') as outfile:
        json.dump(param, outfile)
        
    
    #EXPORT WITH_TILES PNG
    #Add origins points
    data = dict(
                x=x,
                y=y,
                adress=l_adress,
                color=l_colors
                )
    source_origins.data.update(data)
    
    export_name = export_no_tiles 
    
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
        legend="Origins"
            )
    
    p_shape.add_tile(STAMEN_TERRAIN_RETINA, alpha=params["fig_params"]["alpha_tile"], name="tile")
    
    name = export_with_tiles + param["name"]
    export_png(p_shape, filename="{}.png".format(name))
    json_name = filename="{}.json".format(name)
    
    with open(json_name, 'w') as outfile:
        json.dump(param, outfile)
    
    p_shape = make_plot(params_plot)
    
    exe_duration = time.time() - start_time
    
    print (fmt.format(rd(seconds=exe_duration)))
        