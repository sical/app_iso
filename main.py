# -*- coding: utf-8 -*-
"""

"""
from bokeh.palettes import Viridis, Spectral, Plasma
from bokeh.io import show, output_notebook, output_file
from bokeh.plotting import figure, show, output_file
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import ColumnDataSource, GeoJSONDataSource, HoverTool, LinearColorMapper
from bokeh.layouts import row, widgetbox, gridplot

import json

from functions import get_iso, make_plot

params = "params.json"
params = json.load(open(params))

router = params["router"]

#Projections
#inProj = Proj(init=params["inProj"])
#outProj = Proj(init=params["outProj"])
inProj = params["proj"]["inProj"]
outProj = params["proj"]["outProj"]
 

router = "Paris"
from_place = 48.863043, 2.339759
time = "08:00" #HH:MM format
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



data = get_iso(router, from_place, time, date, modes, max_dist, step, nb_iter, dict_palette, inProj, outProj)

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

layout = gridplot(
    [l_viridis,
     l_plasma,
     l_spectral]
    
#    widgetbox(min_schedule,button)
)


show(layout)