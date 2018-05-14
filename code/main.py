# -*- coding: utf-8 -*-
"""

"""
from datetime import date
import os

from bokeh.palettes import Viridis, Spectral, Plasma, Set1
from bokeh.io import show, curdoc
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import LinearColorMapper, Slider
from bokeh.models.widgets import TextInput, Button, DatePicker, RadioButtonGroup
from bokeh.layouts import row, gridplot
from dotenv import load_dotenv
from pathlib import Path

import json

from get_iso import get_iso
from make_plot import make_plot
from functions import geocode
from bokeh_tools import colors_slider

#Parameters
env_path = Path('./code/') / '.env'
load_dotenv(dotenv_path=env_path)

TOKEN = os.getenv("NAVITIA_TOKEN")

params = "./code/params/params.json"
params = json.load(open(params))

#Projections
inProj = params["proj"]["inProj"]
outProj = params["proj"]["outProj"]

#Default
default = "./code/params/default.json"
default = json.load(open(default))
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


#Set range date
min_date = date(year_min, month_min, day_min)
max_date = date(year_max, month_max, day_max)

#############
#  WIDGETS  #
#############.
button = Button(label="C'est parti !", button_type="success")

#API
adress_in = TextInput(value=adress, title="Entrez une adresse:")
time_in = TextInput(value=time_, title="Entrez un horaire (HH:MM):")
date_ = DatePicker(max_date=max_date, min_date=min_date)
nb_iter_in = TextInput(value=nb_iter, title="Entrez un nombre d'etapes:")
step_in = TextInput(value=str(int(step/60)), title="Entrez une duree en minutes:")

#SHAPES
radio_button_shapes = RadioButtonGroup(
        labels=["Points", "Lines", "Polygons"], 
        active=0
        )

#COLORS
#color_gradient = make_color_gradient()
#taptool = color_gradient.select(type=TapTool)
#url = "http://www.colors.commutercreative.com/@color/"
#test = taptool.callback = OpenURL(url=url)
color_vis, red_slider, green_slider, blue_slider = colors_slider()
opacity = Slider(start=0.1, end=1, value=0.5, step=.1,
                     title="Opacite")

#OPACITY
    

l_widget = [
        [date_, time_in],
        [nb_iter_in, step_in],
        [adress_in, button],
        [radio_button_shapes],
        [red_slider, green_slider, blue_slider],
        [color_vis]
        ]

#Set the dict_colors
dict_palette = {}
dict_palette["viridis"] = Viridis 
dict_palette["spectral"] = Spectral 
dict_palette["plasma"] = Plasma 
dict_palette["primary"] = Set1

params_iso = {
        'token': TOKEN,
        'from_place': from_place,
        'time_in': time_in.value,
        'min_date': min_date.isoformat(),
        'step': step,
        'nb_iter': nb_iter,
        'dict_palette': dict_palette,
        'inProj': inProj,
        'outProj': outProj
            }


#Run with defaults
TOOLS = "pan,wheel_zoom,reset,hover,save"
data = get_iso(params_iso)
    
source_polys = data['poly']
source_pts = data['points']
colors = data['colors']
#buildings = data['buildings']
#network = data['network']



params_plot = {
#            'shape': shape,
            'colors':colors, 
            'palette_name':"viridis", 
            'params':params, 
            'tools':TOOLS, 
            'source_polys':source_polys,
            'source_pts':source_pts,
#            'buildings':buildings,
#            'network':network,
            'tile_provider':STAMEN_TONER,
            'x_range':[243978, 276951],
            'y_range':[6234235, 6265465]
            }

l_viridis = make_plot(params_plot)

x_range = l_viridis[0].x_range
y_range = l_viridis[0].y_range
#params_plot['palette_name'] = "plasma"
#params_plot['x_range'] = x_range
#params_plot['y_range'] = y_range
#
#l_plasma = make_plot(params_plot)
#
#params_plot['palette_name'] = "spectral"
#l_spectral = make_plot(params_plot)    

def run():
    date_value = date_.value
    if date_value is None:
        date_value = date_.min_date.isoformat()
    time_value = time_in.value
    nb_iter_value = int(nb_iter_in.value)
    step_value = int(step_in.value) * 60
    adress = adress_in.value
    from_place = geocode(adress)
    from_place = str(from_place[0]) + ";" + str(from_place[1])
    
    col = (red_slider.value, green_slider.value, blue_slider.value, opacity.value)
    
    params_iso = {
        'token': TOKEN,
        'from_place': from_place,
        'time_in': time_value,
        'min_date': date_value,
        'step': step_value,
        'nb_iter': nb_iter_value,
        'dict_palette': dict_palette,
        'inProj': inProj,
        'outProj': outProj
            }
    
    data = get_iso(params_iso)
    
    source_polys = data['poly']
    source_pts = data['points']
#    buildings = data['buildings']
    colors = data['colors']['viridis']
#    network = data['network']
            
        
    color_mapper = LinearColorMapper(palette=colors)
    
#        options_buildings = dict(
#            fill_alpha= params["fig_params"]["alpha_building"],
#            fill_color= "black", 
#            line_color='white', 
#            line_width=params["fig_params"]["line_width_building"], 
#            source=buildings,
#            legend="batiments"
#            )

    options_iso_surf = dict(
            fill_alpha= params["fig_params"]["alpha_surf"], 
            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
            line_color='white', 
            line_width=params["fig_params"]["line_width_surf"], 
            source=source_polys,
            legend="isochrones"
            )
    
    options_iso_contours = dict(
            line_alpha= params["fig_params"]["alpha_cont"],
            line_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
            line_width=params["fig_params"]["line_width_cont"], 
            source=source_polys,
            legend="isochrones"
            )
    
    options_iso_pts = dict(
            line_alpha= params["fig_params"]["alpha_surf"], 
            color={'field': 'time', 'transform': color_mapper},
            line_width=params["fig_params"]["line_width_surf"], 
            size=3,
            source=source_pts,
            legend="isopoints"
            )
    
#        options_network = dict(
#                line_alpha= params["fig_params"]["alpha_network"], 
#                line_color=params["fig_params"]["color_network"],
#                line_width=params["fig_params"]["line_width_surf"], 
#                source=network,
#                legend="network"
#                )

    l_viridis[0].patches(
            'xs', 
            'ys', 
            **options_iso_surf
            )
    
#        l_viridis[1][0].patches(
#                'xs', 
#                'ys', 
#                **options_buildings
#              )
#        
#        l_viridis[1][0].multi_line(
#                'xs', 
#                'ys', 
#                **options_network
#              )
     
    l_viridis[1].multi_line(
            'xs', 
            'ys', 
            **options_iso_contours)
    
#        l_viridis[1][1].patches(
#                'xs', 
#                'ys', 
#                **options_buildings
#              )
#        
#        l_viridis[1][1].multi_line(
#                'xs', 
#                'ys', 
#                **options_network
#              )

    l_viridis[2].circle(
            'x', 
            'y', 
            **options_iso_pts
            )
    
#        l_viridis[1][2].patches(
#                'xs', 
#                'ys', 
#                **options_buildings
#              )
#        
#        l_viridis[1][2].multi_line(
#                'xs', 
#                'ys', 
#                **options_network
#              )
    
    
button.on_click(run)


layout = row(
            gridplot(
                [l_viridis]
                ),
             gridplot(
                 l_widget
                ),
    
#    widgetbox(min_schedule,button)
)


show(layout)

curdoc().add_root(layout)
curdoc().title = "Iso_app"