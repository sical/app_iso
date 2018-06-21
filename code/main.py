# -*- coding: utf-8 -*-
"""
@author: thomas
"""
from datetime import date
import os

import requests

from bokeh.palettes import Viridis, Spectral, Plasma, Set1
from bokeh.io import show, curdoc, export_png, export_svgs
from bokeh.plotting import figure
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import LinearColorMapper, Slider, ColumnDataSource, PointDrawTool, DataTable
from bokeh.models.widgets import TextInput, Button, DatePicker, RadioButtonGroup,  Dropdown, Panel, Tabs, DataTable, DateFormatter, TableColumn, Div, Select, CheckboxButtonGroup
from bokeh.models.glyphs import Patches
from bokeh.layouts import row, column, gridplot, widgetbox
from dotenv import load_dotenv
from pathlib import Path
from copy import deepcopy
import json
from datetime import datetime
import pandas as pd
from shapely.wkt import loads as sh_loads
from pyproj import transform, Proj

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

#Get dict of coverage regions by Navitia
url='https://api.navitia.io/v1/coverage/'
headers = {
        'accept': 'application/json',
        'Authorization': TOKEN
        }
r = requests.get(url, headers=headers)
code = r.status_code


if code == 200:
    coverage = r.json()['regions']
else:
    print ('ERROR:', code)

dict_region = {}    

for region in coverage:
    status = region["status"]
    if status == "running":
        name = region["name"]
        id_ = region["id"]
        shape = sh_loads(region["shape"])
        if name is not None:
            dict_region[name] = {
                    "id":id_,
                    "shape":shape
                    }

for region, data in dict_region.items():
    if data["id"] == "fr-idf":
        default_region = region

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

#POINT/ADRESS
radio_button_loc = RadioButtonGroup(
        labels=["Point", "Adresse"], 
        active=0
        )

#INTERSECTION MODE
radio_button_intersection = RadioButtonGroup(
        labels=["Intersection","Union", "Difference"], 
        active=0
        )

#OPACITY
opacity = Slider(start=0.0, end=1.0, value=0.5, step=.1,
                     title="Opacite")
opacity_tile = Slider(start=0.0, end=1.0, value=0.5, step=.1,
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

#INTERSECTION TYPE AND COLOR
intersection_color = CheckboxButtonGroup(
        labels=["Intersection_contour", "Intersection_fond"], 
        active=[])
panel_intersection_color = Panel(child=intersection_color, title="Intersection colors")
slider_contour = Slider(start=0, end=30, value=1, step=1,
                     title="Taille contour")
panel_contour = Panel(child=slider_contour, title="Taille contour")

#INPUT 
div_alert = Div(text="")

#EXPORT
menu = [("PNG", "png"), ("SVG", "svg")]
save_ = Dropdown(label="Exporter vers:", button_type="warning", menu=menu)

#SELECT REGION
select = Select(title="Region:", value=default_region, options=list(dict_region.keys()))

l_widget = [
        [select, div_alert],
        [date_, time_in],
        [adress_in, step_in],
        [radio_button_shapes, radio_button_loc],
        [
                Tabs(tabs=[ tab_slide_colors, tab_viridis ])
        ],
        [opacity_tile],
        [radio_button_intersection, Tabs(tabs=[ panel_intersection_color, panel_contour ])],
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
            'tile_provider':STAMEN_TERRAIN_RETINA,
            'source_iso': source_iso
            }

p_shape = make_plot(params_plot)


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
        
source_goto = ColumnDataSource(
        data=dict(
                x=[], 
                y=[],
                )
        )

options_goto = dict(
                color="white",
                alpha=0.0,
#                fill_alpha = 1.0,
#                line_color="white", 
#                line_alpha = 0.0,
                source = source_goto
                )

x, y = dict_region[select.value]["shape"][0].exterior.xy
p_4326 = Proj(init='epsg:4326')
p_3857 = Proj(init='epsg:3857')
coords= [transform(p_4326, p_3857, lat, lon) for lat,lon in zip(list(x),list(y))]
x = [coord[0] for coord in coords]
y = [coord[1] for coord in coords]

source_goto.data = dict(
        x=x,
        y=y
        )

p_shape.circle(
    'x', 
    'y', 
    **options_goto
    )



options_intersect = dict(
#                fill_alpha= params["fig_params"]["alpha_surf"], 
    #            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
                source=source_intersection,
                color='color',
                alpha=0.70,
#                fill_color="black", 
#                fill_alpha = 0.70,
#                line_color="black", 
#                line_width=params["fig_params"]["line_width_surf"], 
                legend="Intersection"
                )
        
intersections = p_shape.patches(
                                'xs', 
                                'ys', 
                                **options_intersect
                                )

#DRAW POINT (add origine)
source_point = ColumnDataSource({
    'x': [], 
    'y': []
})

renderer = p_shape.circle(
        x='x', 
        y='y', 
        source=source_point, 
        size=10,
        fill_color='#5BC862',
        fill_alpha=0.5,
        line_color='black'
        )
draw_tool = PointDrawTool(renderers=[renderer], empty_value='black')
p_shape.add_tools(draw_tool)

columns = [TableColumn(field="x", title="x"),
           TableColumn(field="y", title="y")]
table = DataTable(source=source_point, columns=columns, editable=True, height=200)
#l_widget.append(table)

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
    global alert
    global color_value
    
    alert.format("")
    
    date_value = date_.value
    time_value = time_in.value
    
    id_ = dict_region[select.value]["id"]
    
    if date_value is None:
        date_value = date.today()
    if time_value is None:
        time_value = datetime.datetime.now().time()
#    nb_iter_value = int(nb_iter_in.value)
    step_value = int(step_in.value) * 60
    adress = adress_in.value
            
    
    if radio_button_loc.active == 1:
        from_place = geocode(adress)
        from_place = str(from_place[0]) + ";" + str(from_place[1])
    else:
        lat = source_point.data["x"][-1]
        lon = source_point.data["y"][-1]
        coords = transform(p_3857, p_4326, lat, lon)
        from_place = str(coords[0]) + ";" + str(coords[1])
    
#    if color_choice == 0:
#        color_value = (red_slider.value, green_slider.value, blue_slider.value, opacity.value)
#    else:
#        color_value = Viridis[5][panel_viridis.children[0].children[0].active]
        
        
#    source_intersection.data['color'] = [color_value,]
    
    if radio_button_intersection.active == 0:
        how="intersection"
    elif radio_button_intersection.active == 1:
        how="union"
    else:
        how="symmetric_difference"
    
    if radio_button_shapes.active == 0:
        shape = "point"
    elif radio_button_shapes.active == 1:
        shape = "line"
    elif radio_button_shapes.active == 2:
        shape = "poly"
    
    color = color_value
    
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
        'color':color
            }
    
#    try:
    data = get_iso(params_iso, gdf_poly_mask, id_)
    gdf_poly_mask = data['gdf_poly_mask']

    source = data['source']
    shape = data['shape']
    data_intersection = data['intersection']
    status = data['status']
    
    if source is None:
        shape = ""
    
    if data_intersection is not None:
        source_intersection.data.update(data_intersection.data)
#        count = source_intersection.data['xs'].size
#        source_intersection.data['color'] = ["red" for i in range(0,count)]
#        for x,y in source_intersection.data.items():
#            print (x,y)
#        print (source_intersection.data['color'])
        
#        options_intersect = dict(
##                fill_alpha= params["fig_params"]["alpha_surf"], 
#    #            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
#                fill_color="blue", 
#                fill_alpha = 0.70,
#                line_color="black", 
#                line_width=params["fig_params"]["line_width_surf"], 
#                source=source_intersection,
#                legend="Intersection"
#                )
#        
#        p_shape.patches(
#            'xs', 
#            'ys', 
#            **options_intersect
#            )
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
        
    elif shape == "point":
        name="points"  + str(counter_polys)
        options_iso_pts = dict(
#                line_alpha= params["fig_params"]["alpha_surf"], 
    #            color={'field': 'time', 'transform': color_mapper},
                color=color_value, 
                alpha = opacity.value,
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
    
#    names.append(name)
    div_alert.text = alert.format(status)
        
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
    
#    p_shape.grid.grid_line_color = None
    
    p_shape.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"], name="tile")
    draw_tool = PointDrawTool(renderers=[renderer], empty_value='black')
    p_shape.add_tools(draw_tool)
    
    layout.children[0].children[0] = p_shape
    
    source_goto.data = dict(
        x=x,
        y=y
        )
    
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
        export_png(p_shape, filename="{}.png".format(title))
    elif  new == 'svg':
        export = deepcopy(p_shape)
        export.output_backend = "svg"
        export_svgs(export, filename="{}.svg".format(title))
        
def tile_opacity(attrname, old, new):
    p_shape.select(name="tile")[0].alpha=new

def color_sliders(attrname, old, new):
    global color_choice
    global color_value
#    color_choice = 0
    color_value = (red_slider.value, green_slider.value, blue_slider.value, opacity.value)
    color_select()
    
def color_hex(attrname, old, new):
    global color_choice
    global color_value
#    color_choice = 1
    color_value = Viridis[5][panel_viridis.children[0].children[0].active]
    color_select()

def color_select():
    glyph = intersections.glyph

    if intersection_color.active == [0]:
        glyph.line_color = color_value
    elif intersection_color.active == [1]:
        glyph.fill_color = color_value
    elif intersection_color.active == [0,1]:
        glyph.line_color = color_value
        glyph.fill_color = color_value

def goto(attrname, old, new):
    x, y = dict_region[select.value]["shape"][0].exterior.xy
    p_4326 = Proj(init='epsg:4326')
    p_3857 = Proj(init='epsg:3857')
    coords= [transform(p_4326, p_3857, lat, lon) for lat,lon in zip(list(x),list(y))]
    x = [coord[0] for coord in coords]
    y = [coord[1] for coord in coords]
    
    source_goto.data = dict(
            x=x,
            y=y
            )
def contour_update(attrname, old, new):
    glyph = intersections.glyph
    glyph.line_width = slider_contour.value
    
#def selection(attrname, old, new):
##    global selected
##    print ("YES")
##    if selected is False:
##        selected = True
##    else:
##        selected = False
#    selections = new['1d']['indices']
#    
#    if selections == old_selections:
#        selected = False

save_.on_change('value', save_handeler)            
button.on_click(run)
clear.on_click(clear_plots)
opacity_tile.on_change('value', tile_opacity)
red_slider.on_change('value',color_sliders)
blue_slider.on_change('value',color_sliders)
green_slider.on_change('value',color_sliders)
opacity.on_change('value', color_sliders)
panel_viridis.children[0].children[0].on_change('active',color_hex)
select.on_change('value',goto)
slider_contour.on_change('value', contour_update)

#intersections.data_source.on_change('selected',selection)

layout = column(
        row(
            p_shape,
            gridplot(
                    l_widget
            ),
        ),
        table
)


curdoc().add_root(layout)
curdoc().title = "Iso_app"