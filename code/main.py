# -*- coding: utf-8 -*-
"""

"""
from datetime import date

from bokeh.palettes import Viridis, Spectral, Plasma
from bokeh.io import show, curdoc
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import LinearColorMapper
from bokeh.layouts import row, gridplot
from bokeh.models.widgets import TextInput, Button, DatePicker

import json

from get_iso import get_iso
from make_plot import make_plot
from functions import geocode

#Parameters
params = "./code/params/params.json"
params = json.load(open(params))

router = params["router"]

#Projections
inProj = params["proj"]["inProj"]
outProj = params["proj"]["outProj"]

#Default
default = "./code/params/default.json"
default = json.load(open(default))
from_place = default["from_place"]
adress = default["adress"]
time_ = default["time_"]
modes = default["modes"]
max_dist = default["max_dist"]
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

#WIDGETS
button = Button(label="C'est parti !", button_type="success")

adress_in = TextInput(value=adress, title="Entrez une adresse:")
time_in = TextInput(value=time_, title="Entrez un horaire (HH:MM):")
date_ = DatePicker(max_date=max_date, min_date=min_date)
nb_iter_in = TextInput(value=nb_iter, title="Entrez un nombre d'etapes:")
step_in = TextInput(value=str(int(step/60)), title="Entrez une duree en minutes:")
modes_in = TextInput(value=modes, title="Entrez des modes:")
max_dist_in = TextInput(value=max_dist, title="Entrez une distance maximum de marche (en mètres)")
    

l_widget = [
        [date_, time_in],
        [nb_iter_in, step_in],
        [adress_in, button]
        ]

#Set the dict_colors
dict_palette = {}
dict_palette["viridis"] = Viridis 
dict_palette["spectral"] = Spectral 
dict_palette["plasma"] = Plasma 

params_iso = {
        'router': router,
        'from_place': from_place,
        'time_in': time_in,
        'min_date': min_date,
        'modes': modes,
        'max_dist': max_dist,
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
buildings = data['buildings']
network = data['network']


params_plot = {
            'colors':colors, 
            'palette_name':"viridis", 
            'params':params, 
            'tools':TOOLS, 
            'source_polys':source_polys,
            'source_pts':source_pts,
            'buildings':buildings,
            'network':network,
            'tile_provider':STAMEN_TONER,
            'x_range':[243978, 276951],
            'y_range':[6234235, 6265465]
            }

l_viridis = make_plot(params_plot)

x_range = l_viridis[0].x_range
y_range = l_viridis[0].y_range
params_plot['palette_name'] = "plasma"
params_plot['x_range'] = x_range
params_plot['y_range'] = y_range

l_plasma = make_plot(params_plot)

params_plot['palette_name'] = "spectral"
l_spectral = make_plot(params_plot)    

def run():
    date_value = date_.value
    if date_value is None:
        date_value = date_.min_date.isoformat()
    time_value = time_in.value
    nb_iter_value = int(nb_iter_in.value)
    step_value = int(step_in.value) * 60
    adress = adress_in.value
    from_place = geocode(adress)
    modes = modes_in.value
    max_dist = max_dist_in.value    
    
    data = get_iso(router, 
                   from_place, 
                   time_value,
                   date_value, 
                   modes, 
                   max_dist, 
                   step_value, 
                   nb_iter_value, 
                   dict_palette, 
                   inProj, 
                   outProj)
    
    source_polys = data['poly']
    source_pts = data['points']
    buildings = data['buildings']
    colors = data['colors']
    network = data['network']
    
    
    for l in [("viridis",l_viridis), 
              ("plasma", l_plasma), 
              ("spectral", l_spectral)]:
            
        
        color_mapper = LinearColorMapper(palette=colors[l[0]])
        
        options_buildings = dict(
            fill_alpha= params["fig_params"]["alpha_building"],
            fill_color= "black", 
            line_color='white', 
            line_width=params["fig_params"]["line_width_building"], 
            source=buildings,
            legend="batiments"
            )
    
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
        
        options_network = dict(
                line_alpha= params["fig_params"]["alpha_network"], 
                line_color=params["fig_params"]["color_network"],
                line_width=params["fig_params"]["line_width_surf"], 
                source=network,
                legend="network"
                )

        l[1][0].patches(
                'xs', 
                'ys', 
                **options_iso_surf
                )
        
        l[1][0].patches(
                'xs', 
                'ys', 
                **options_buildings
              )
        
        l[1][0].multi_line(
                'xs', 
                'ys', 
                **options_network
              )
         
        l[1][1].multi_line(
                'xs', 
                'ys', 
                **options_iso_contours)
        
        l[1][1].patches(
                'xs', 
                'ys', 
                **options_buildings
              )
        
        l[1][1].multi_line(
                'xs', 
                'ys', 
                **options_network
              )

        l[1][2].circle(
                'x', 
                'y', 
                **options_iso_pts
                )
        
        l[1][2].patches(
                'xs', 
                'ys', 
                **options_buildings
              )
        
        l[1][2].multi_line(
                'xs', 
                'ys', 
                **options_network
              )
    
    
button.on_click(run)


layout = row(
            gridplot(
                [l_viridis,
                 l_plasma,
                 l_spectral]
                ),
             gridplot(
                 l_widget
                ),
    
#    widgetbox(min_schedule,button)
)


show(layout)

curdoc().add_root(layout)
curdoc().title = "Iso_app"