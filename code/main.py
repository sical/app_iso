# -*- coding: utf-8 -*-
"""

"""
from datetime import date
import os

from bokeh.palettes import Viridis, Spectral, Plasma, Set1
from bokeh.io import show, curdoc, export_png, export_svgs
from bokeh.plotting import figure
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import LinearColorMapper, Slider, ColumnDataSource
from bokeh.models.widgets import TextInput, Button, DatePicker, RadioButtonGroup,  Dropdown, Panel, Tabs, DataTable, DateFormatter, TableColumn, Div
from bokeh.layouts import row, column, gridplot, widgetbox
from dotenv import load_dotenv
from pathlib import Path
from copy import deepcopy
import json
from datetime import datetime
import pandas as pd

from get_iso import get_iso
from make_plot import make_plot
from functions import geocode
from bokeh_tools import colors_slider, colors_radio

#Parameters
try:
    env_path = Path('./code/') / '.env'
    load_dotenv(dotenv_path=env_path)
    TOKEN = os.getenv("NAVITIA_TOKEN")
except:
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
counter_polys = 0 
counter_lines = 0 
counter_points = 0 
color_choice = 0
names = []

#Set range date
min_date = date(year_min, month_min, day_min)
max_date = date(year_max, month_max, day_max)

#Set ColumnDataSource
source_poly = {}

#Set intersections
gdf_poly_mask = None

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

#OPACITY
opacity = Slider(start=0.1, end=1, value=0.5, step=.1,
                     title="Opacite")
opacity_tile = Slider(start=0.0, end=1, value=0.5, step=.1,
                     title="Tuiles opacite")
viridis = Slider(start=0.1, end=1, value=0.5, step=.1,
                     title="Viridis_opacite")

#COLORS
color_vis, red_slider, green_slider, blue_slider = colors_slider()
panel_slide = row(
                widgetbox(red_slider, green_slider, blue_slider, opacity),
                column(color_vis)
                )
tab_slide_colors = Panel(child=panel_slide, title="Sliders colors")
panel_viridis = colors_radio(Viridis[5])
tab_viridis = Panel(child=panel_viridis, title="Viridis colors")

#INPUT 
div_alert = Div(text="")

#EXPORT
menu = [("PNG", "png"), ("SVG", "svg")]
save_ = Dropdown(label="Exporter vers:", button_type="warning", menu=menu)


l_widget = [
        [date_, time_in],
        [adress_in, step_in],
        [radio_button_shapes, div_alert],
        [
                Tabs(tabs=[ tab_slide_colors, tab_viridis ])
        ],
        [opacity_tile],
        [button,clear],
        [save_]
        ]


#Run with defaults
TOOLS = "pan,wheel_zoom,reset"
#data = get_iso(params_iso)
    
#source_polys = data['poly']
#source_pts = data['points']
#colors = data['colors']
#buildings = data['buildings']
#network = data['network']

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

params_plot = {
            'params':params, 
            'tools':TOOLS, 
#            'buildings':buildings,
#            'network':network,
            'tile_provider':STAMEN_TONER,
            'source_iso': source_iso
            }

p_shape = make_plot(params_plot)

#x_range = p_shape.x_range
#y_range = p_shape.y_range

#DATASOURCE
#source = ColumnDataSource(data=dict(
#    x=[1, 2, 3, 4, 5],
#    y=[2, 5, 8, 2, 7],
#    color=["navy", "orange", "olive", "firebrick", "gold"]
#    ))

columns = ["date", "time", "adress", "duration", "shape", "colors"]
array_log = pd.DataFrame(columns=columns)

  
def run():
    global counter_polys
    global counter_lines
    global counter_points
    global names
    global p_shape
    global color_choice
    global gdf_poly_mask
    
    date_value = date_.value
    time_value = time_in.value
    
    if date_value is None:
        date_value = date.today()
    if time_value is None:
        time_value = datetime.datetime.now().time()
#    nb_iter_value = int(nb_iter_in.value)
    step_value = int(step_in.value) * 60
    adress = adress_in.value
    from_place = geocode(adress)
    from_place = str(from_place[0]) + ";" + str(from_place[1])
    
    if color_choice == 0:
        color_value = (red_slider.value, green_slider.value, blue_slider.value, opacity.value)
    else:
        color_value = Viridis[5][panel_viridis.children[0].children[0].active]
    
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
    
#    try:
    data = get_iso(params_iso, gdf_poly_mask)
    gdf_poly_mask = data['gdf_poly_mask']
    
    print ("MASK", gdf_poly_mask)

    source = data['source']
    shape = data['shape']
    source_intersection = data['intersection']
    
    if source_intersection is not None:
        options_intersect = dict(
#                fill_alpha= params["fig_params"]["alpha_surf"], 
    #            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
                fill_color="blue", 
                fill_alpha = 0.75,
                line_color="black", 
                line_width=params["fig_params"]["line_width_surf"], 
                source=source_intersection,
                legend="Intersection"
                )
        
        intersections_patches = p_shape.patches(
            'xs', 
            'ys', 
            **options_intersect
            )
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
        name = "polys" + str(counter_polys)
        options_iso_surf = dict(
#                fill_alpha= params["fig_params"]["alpha_surf"], 
    #            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
                fill_color=color_value, 
                fill_alpha = opacity.value,
                line_color='white', 
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
        
#        p1 = p_shape.patches([], [], fill_alpha=0.4)
#
#        c1 = p_shape.circle([], [], size=10, color='red')
#        edit_tool = PolyEditTool(renderers=[p1, test], vertex_renderer=c1)
##        poly_renderer.append(test)
##        tool = PolyEditTool(renderers=poly_renderer)
#        p_shape.add_tools(edit_tool)
#        p_shape.toolbar.active_drag = edit_tool
        
        
    elif shape == "line":
        name = "lines"  + str(counter_lines)
        options_iso_contours = dict(
#                line_alpha= params["fig_params"]["alpha_cont"],
    #            line_color={'field': params["fig_params"]["field"], 'transform': color_mapper},
                line_color=color_value, 
                line_alpha = opacity.value,
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
        
    else:
        name="points"  + str(counter_polys)
        options_iso_pts = dict(
#                line_alpha= params["fig_params"]["alpha_surf"], 
    #            color={'field': 'time', 'transform': color_mapper},
                color=color_value, 
                alpha = opacity.value,
                line_width=params["fig_params"]["line_width_surf"], 
                size=3,
                source=source,
                legend="Isochrone_points" + str(counter_points)
                )
        
        p_shape.circle(
            'x', 
            'y', 
            **options_iso_pts,
            name="points"  + str(counter_polys)
            )
        
        counter_points += 1
        
    
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
    
    names.append(name)
    div_alert.text = ""
        
#    except:
#        div_alert.text =  """<span style="color: red"><b>ALERTE: Verifiez vos parametres</b></span>"""
        
    

def clear_plots():
    global counter_polys
    global counter_lines
    global counter_points
    global names
    global p_shape
    global params_plot
    
    params = params_plot['params']
    TOOLS = params_plot['tools'] 
    tile_provider = params_plot['tile_provider']
    p_shape = figure(
            title= "Isochrone", 
            tools=TOOLS, 
            x_axis_location=None, 
            y_axis_location=None, 
            width=params["fig_params"]["width"], 
            height=params["fig_params"]["height"],
            match_aspect=True, 
            aspect_scale=1
            )
    
    p_shape.grid.grid_line_color = None
    
    p_shape.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"], name="tile")
    layout.children[0] = p_shape
    
    counter_polys = 0
    counter_lines = 0
    counter_points = 0
    names = []
    p_shape.legend.location = "top_right"
    p_shape.legend.click_policy="hide"
    
            
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

def color_sliders(attrname, old, new):
    global color_choice
    color_choice = 0
    
def color_hex(attrname, old, new):
    global color_choice
    color_choice = 1
    
    

save_.on_change('value', save_handeler)            
button.on_click(run)
clear.on_click(clear_plots)
opacity_tile.on_change('value', tile_opacity)
red_slider.on_change('value',color_sliders)
blue_slider.on_change('value',color_sliders)
green_slider.on_change('value',color_sliders)
opacity.on_change('value', color_sliders)
panel_viridis.children[0].children[0].on_change('active',color_hex)

layout = row(
        p_shape,
        gridplot(
                l_widget
                )
)


curdoc().add_root(layout)
curdoc().title = "Iso_app"