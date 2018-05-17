# -*- coding: utf-8 -*-
"""

"""
from datetime import date
import os

from bokeh.palettes import Viridis, Spectral, Plasma, Set1
from bokeh.io import show, curdoc, export_png, export_svgs
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import LinearColorMapper, Slider, ColumnDataSource
from bokeh.models.widgets import TextInput, Button, DatePicker, RadioButtonGroup, Dropdown
from bokeh.layouts import row, column, gridplot, widgetbox
from dotenv import load_dotenv
from pathlib import Path
from copy import deepcopy
import json
from datetime import datetime

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
#############
button = Button(label="C'est parti !", button_type="success")
clear = Button(label="Reset", button_type="warning")

#API
adress_in = TextInput(value=adress, title="Entrez une adresse:")
time_in = TextInput(value=time_, title="Entrez un horaire (HH:MM):")
date_ = DatePicker(max_date=max_date, min_date=min_date)
#nb_iter_in = TextInput(value=nb_iter, title="Entrez un nombre d'etapes:")
step_in = TextInput(value=str(int(step/60)), title="Entrez une duree en minutes:")

#SHAPES
radio_button_shapes = RadioButtonGroup(
        labels=["Points", "Lines", "Polygons"], 
        active=2
        )

#COLORS
color_vis, red_slider, green_slider, blue_slider = colors_slider()

#OPACITY
opacity = Slider(start=0.1, end=1, value=0.5, step=.1,
                     title="Opacite")
opacity_tile = Slider(start=0.0, end=1, value=0.5, step=.1,
                     title="Tuiles opacite")

#EXPORT
menu = [("PNG", "png"), ("SVG", "svg")]
save_ = Dropdown(label="Exporter vers:", button_type="warning", menu=menu)

l_widget = [
        [date_, time_in],
        [adress_in, step_in],
        [radio_button_shapes],
        [row(
                widgetbox(red_slider, green_slider, blue_slider, opacity),
                column(color_vis)
                )
        ],
        [opacity_tile],
        [button,clear],
        [save_]
        ]

#Set the dict_colors
#dict_palette = {}
#dict_palette["viridis"] = Viridis 
#dict_palette["spectral"] = Spectral 
#dict_palette["plasma"] = Plasma 
#dict_palette["primary"] = Set1

#params_iso = {
#        'token': TOKEN,
#        'from_place': from_place,
#        'time_in': time_in.value,
#        'min_date': min_date.isoformat(),
#        'step': step,
#        'nb_iter': nb_iter,
#        'shape': dict_palette,
#        'inProj': inProj,
#        'outProj': outProj
#            }


#Run with defaults
TOOLS = "pan,wheel_zoom,reset,save, redo, undo"
#data = get_iso(params_iso)
    
#source_polys = data['poly']
#source_pts = data['points']
#colors = data['colors']
#buildings = data['buildings']
#network = data['network']



params_plot = {
#            'shape': shape,
#            'colors':colors, 
#            'palette_name':"viridis", 
            'params':params, 
            'tools':TOOLS, 
#            'source_polys':source_polys,
#            'source_pts':source_pts,
#            'buildings':buildings,
#            'network':network,
            'tile_provider':STAMEN_TONER,
#            'x_range':[243978, 276951],
#            'y_range':[6234235, 6265465]
            }

p_shape = make_plot(params_plot)

x_range = p_shape.x_range
y_range = p_shape.y_range
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
#    nb_iter_value = int(nb_iter_in.value)
    step_value = int(step_in.value) * 60
    adress = adress_in.value
    from_place = geocode(adress)
    from_place = str(from_place[0]) + ";" + str(from_place[1])
    
    color_value = (red_slider.value, green_slider.value, blue_slider.value, opacity.value)
    
    if radio_button_shapes.active == 0:
        shape = "point"
    elif radio_button_shapes.active == 1:
        shape = "line"
    elif radio_button_shapes.active == 2:
        shape = "poly"
    
    params_iso = {
        'token': TOKEN,
        'from_place': from_place,
        'time_in': time_value,
        'min_date': date_value,
        'step': step_value,
        'nb_iter': 1,
        'shape': shape,
        'inProj': inProj,
        'outProj': outProj
            }
    
    data = get_iso(params_iso)
    
    source = data['source']
    shape = data['shape']

#    buildings = data['buildings']
#    colors = data['colors']['viridis']
#    network = data['network']
            
        
#    color_mapper = LinearColorMapper(palette=colors)
    
#        options_buildings = dict(
#            fill_alpha= params["fig_params"]["alpha_building"],
#            fill_color= "black", 
#            line_color='white', 
#            line_width=params["fig_params"]["line_width_building"], 
#            source=buildings,
#            legend="batiments"
#            )

    if shape == "poly":
        options_iso_surf = dict(
#                fill_alpha= params["fig_params"]["alpha_surf"], 
    #            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
                fill_color=color_value, 
                fill_alpha = opacity.value,
                line_color='white', 
                line_width=params["fig_params"]["line_width_surf"], 
                source=source,
                legend="Isochrone_polys"
                )
        
        p_shape.patches(
            'xs', 
            'ys', 
            **options_iso_surf,
            name="polys"
            )
        
    elif shape == "line":
        options_iso_contours = dict(
#                line_alpha= params["fig_params"]["alpha_cont"],
    #            line_color={'field': params["fig_params"]["field"], 'transform': color_mapper},
                line_color=color_value, 
                line_alpha = opacity.value,
                line_width=params["fig_params"]["line_width_cont"], 
                source=source,
                legend="Isochrone_lines"
                )
        
        p_shape.multi_line(
            'xs', 
            'ys', 
            **options_iso_contours,
            name="lines"
            )
        
    else:
        options_iso_pts = dict(
#                line_alpha= params["fig_params"]["alpha_surf"], 
    #            color={'field': 'time', 'transform': color_mapper},
                color=color_value, 
                alpha = opacity.value,
                line_width=params["fig_params"]["line_width_surf"], 
                size=3,
                source=source,
                legend="Isochrone_points"
                )
        
        p_shape.circle(
            'x', 
            'y', 
            **options_iso_pts,
            name="points"
            )
        
    
#        options_network = dict(
#                line_alpha= params["fig_params"]["alpha_network"], 
#                line_color=params["fig_params"]["color_network"],
#                line_width=params["fig_params"]["line_width_surf"], 
#                source=network,
#                legend="network"
#                )

    
    
#        p_shape[1][0].patches(
#                'xs', 
#                'ys', 
#                **options_buildings
#              )
#        
#        p_shape[1][0].multi_line(
#                'xs', 
#                'ys', 
#                **options_network
#              )
     
    
    
#        p_shape[1][1].patches(
#                'xs', 
#                'ys', 
#                **options_buildings
#              )
#        
#        p_shape[1][1].multi_line(
#                'xs', 
#                'ys', 
#                **options_network
#              )
    
#        p_shape[1][2].patches(
#                'xs', 
#                'ys', 
#                **options_buildings
#              )
#        
#        p_shape[1][2].multi_line(
#                'xs', 
#                'ys', 
#                **options_network
#              )
        
    p_shape.legend.location = "top_right"
    p_shape.legend.click_policy="hide"

def clear_plots():
#    global params_plot
#    p_shape = make_plot(params_plot)
#    layout.children[0] = p_shape
    
    names = ["points", "polys", "lines"]

    for name in names:
        if p_shape.select(name=name):
            glyphs = p_shape.select(name=name)
            glyphs.visible = False
            
def save_handeler(attr, old, new):
#    title = p_shape.title.__dict__["_property_values"]["text"]
    name = datetime.now().strftime("%d_%b_%Y_%HH_%MM_%SS")
    title = "export_" + name
    if new == 'png':
        export_png(layout, filename="%s.png" % title)
    elif  new == 'svg':
        p_shape.output_backend = "svg"
        export_svgs(layout, filename="%s.svg" % title) 
        
def tile_opacity(attrname, old, new):
    p_shape.select(name="tile")[0].alpha=new


save_.on_change('value', save_handeler)            
button.on_click(run)
clear.on_click(clear_plots)
opacity_tile.on_change('value', tile_opacity)


layout = row(
        p_shape,
        gridplot(
                l_widget
                )
)


curdoc().add_root(layout)
curdoc().title = "Iso_app"