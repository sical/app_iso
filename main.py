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

import json

from functions import get_iso, make_plot

min_date = date(2018, 4, 4)
max_date = date(2018, 4, 29)

#WIDGETS
button = Button(label="C'est parti !", button_type="success")

adress_in = TextInput(value="", title="Entrez une adresse:")
time_in = TextInput(value="08:00", title="Entrez un horaire (HH:MM):")
date_ = DatePicker(max_date=max_date, min_date=min_date)
nb_iter_in = TextInput(value="3", title="Entrez un nombre d'etapes:")
step_in = TextInput(value="10", title="Entrez une duree en minutes:")


def get_value(attrname, old, new):
    
    print(date_.value)
    
    
date_.on_change('value', get_value)

chbx_modes = CheckboxGroup(
        labels=["Transports collectifs", "Voiture"], active=[0, 1])

l_widget = [
        [date_, time_in],
        [nb_iter_in, step_in],
        [chbx_modes, adress_in]
        [button, None]
        ]

#Parameters
params = "./app_iso/params.json"
params = json.load(open(params))

router = params["router"]

#Projections
#inProj = Proj(init=params["inProj"])
#outProj = Proj(init=params["outProj"])
inProj = params["proj"]["inProj"]
outProj = params["proj"]["outProj"]
 
from_place = 48.863043, 2.339759
time_ = "08:00" #HH:MM format
date = "04-05-2018" #MM-DD-YYYY format
modes = "TRANSIT,WALK"
max_dist = 800
step = 600
nb_iter = 3

#Set the dict_colors
dict_palette = {}
dict_palette["viridis"] = Viridis 
dict_palette["spectral"] = Spectral 
dict_palette["plasma"] = Plasma 

data = get_iso(router, from_place, time_, date, modes, max_dist, step, nb_iter, dict_palette, inProj, outProj)

#geo_source = GeoJSONDataSource(geojson=str(data[0]))
geo_source = data[0]
colors = data[1]
TOOLS = "pan,wheel_zoom,box_zoom,reset,hover,save"


l_viridis = make_plot(
        colors, 
        "viridis", 
        params, 
        TOOLS, 
        geo_source,
        STAMEN_TONER)

x_range = l_viridis[0].x_range
y_range = l_viridis[0].y_range

l_plasma = make_plot(
        colors, 
        "plasma", 
        params, 
        TOOLS, 
        geo_source,
        STAMEN_TONER,
        x_range=x_range,
        y_range=y_range
                      )

l_spectral = make_plot(
        colors, 
        "spectral", 
        params, 
        TOOLS, 
        geo_source,
        STAMEN_TONER,
        x_range=x_range,
        y_range=y_range
                      )


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