# -*- coding: utf-8 -*-
"""

"""
from datetime import date

from bokeh.palettes import Viridis, Spectral, Plasma
from bokeh.io import show, output_notebook, output_file, curdoc
from bokeh.plotting import figure, show, output_file
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import ColumnDataSource, GeoJSONDataSource, HoverTool, LinearColorMapper
from bokeh.layouts import row, widgetbox, gridplot, column
from bokeh.models.widgets import TextInput, Button, CheckboxGroup, DatePicker

import osmnx as ox
import json

from functions import get_iso, make_plot, geocode

#Parameters
params = "./app_iso/params.json"
params = json.load(open(params))

router = params["router"]

#Projections
inProj = params["proj"]["inProj"]
outProj = params["proj"]["outProj"]

#Default
default = "./app_iso/default.json"
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
    
    
#def get_value(attrname, old, new):
#    
#    print(date_.value)
    

#date_.on_change('value', get_value)

#chbx_modes = CheckboxGroup(
#        labels=["Transports collectifs", "Voiture"], active=[0, 1])

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

#Run with defaults
TOOLS = "pan,wheel_zoom,box_zoom,reset,hover,save"
data = get_iso(router, 
               from_place, 
               time_in, 
               min_date.isoformat(), 
               modes, 
               max_dist, 
               step, 
               nb_iter, 
               dict_palette, 
               inProj, 
               outProj)
    
source_polys = data['poly']
source_pts = data['points']
colors = data['colors']
buildings = data['buildings']

l_viridis = make_plot(
    colors, 
    "viridis", 
    params, 
    TOOLS, 
    source_polys,
    source_pts,
    buildings,
    STAMEN_TONER)

x_range = l_viridis[0].x_range
y_range = l_viridis[0].y_range

l_plasma = make_plot(
        colors, 
        "plasma", 
        params, 
        TOOLS, 
        source_polys,
        source_pts,
        buildings,
        STAMEN_TONER,
        x_range=x_range,
        y_range=y_range
                      )

l_spectral = make_plot(
        colors, 
        "spectral", 
        params, 
        TOOLS, 
        source_polys,
        source_pts,
        buildings,
        STAMEN_TONER,
        x_range=x_range,
        y_range=y_range
                      )    

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
    source_buildings = data['buildings']
    colors = data['colors']
    
    
    for l in [("viridis",l_viridis), 
              ("plasma", l_plasma), 
              ("spectral", l_spectral)]:
            
        
        color_mapper = LinearColorMapper(palette=colors[l[0]])

        l[1][0].patches(
                'xs', 
                'ys', 
                fill_alpha= params["fig_params"]["alpha_surf"], 
                fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
                line_color='white', 
                line_width=params["fig_params"]["line_width_surf"], 
                source=source_polys
                )
        
        l[1][0].patches(
                'xs', 
                'ys', 
                fill_alpha= params["fig_params"]["alpha_building"], 
                fill_color= "black", 
                line_color='white', 
                line_width=params["fig_params"]["line_width_building"], 
                source=source_buildings,
                legend="batiments"
              )
         
        l[1][1].multi_line(
                'xs', 
                'ys', 
                line_alpha= params["fig_params"]["alpha_cont"], 
                color={'field': 'time', 'transform': color_mapper},
                line_width=params["fig_params"]["line_width_cont"], 
                source=source_polys)
        
        l[1][1].patches(
                'xs', 
                'ys', 
                fill_alpha= params["fig_params"]["alpha_building"], 
                fill_color= "black", 
                line_color='white', 
                line_width=params["fig_params"]["line_width_building"], 
                source=source_buildings,
                legend="batiments"
              )
        
#        print(len(source_pts.data["xs"]))

        l[1][2].circle(
                'x', 
                'y', 
                line_alpha= params["fig_params"]["alpha_surf"], 
                color={'field': 'time', 'transform': color_mapper},
                line_width=params["fig_params"]["line_width_surf"], 
                size=3,
                source=source_pts
                )
        
        l[1][2].patches(
                'xs', 
                'ys', 
                fill_alpha= params["fig_params"]["alpha_building"], 
                fill_color= "black", 
                line_color='white', 
                line_width=params["fig_params"]["line_width_building"], 
                source=source_buildings,
                legend="batiments"
              )
    
    
button.on_click(run)

#data = get_iso(router, from_place, time_, date, modes, max_dist, step, nb_iter, dict_palette, inProj, outProj)

#source_polys = GeoJSONDataSource(geojson=str(data[0]))
#source_polys = data[0]
#colors = data[1]





#hover = p.select_one(HoverTool)
#hover.point_policy = "follow_mouse"
#hover.tooltips = [("Provincia:", "@provincia")]

output_file("Iso_app.html", title="Testing isochrone")

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