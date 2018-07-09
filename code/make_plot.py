# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 16:50:50 2018

@author: thomas
"""

from geopy.geocoders import Nominatim


from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, LinearColorMapper, PolyEditTool
from bokeh.models.widgets import DataTable, DateFormatter, TableColumn

geolocator = Nominatim()


def make_plot(params_plot):
    """
    Build Bokeh map figure for each palette colors and 
    surface iso / contour iso / points iso
    
    @param params_plot (dict): dict of parameters
        list of parameters:
            - colors (dict): dict of colors
            - palette-name (str): name of the palette color
            - params (dict): params from json parameters file
            - TOOLS (str): list of Bokeh tools
            - source_polys (ColumnDataSource object): source of polys
            - source_pts (ColumnDataSource object): source of points
            - buildings (GeoJSONDataSource object): source of buildings 
            - network (ColumnDataSource object): source of network
            - tile_provider (str): name of Bokeh tile provider
            - x_range (list): x range coordinates for map spatial limits
            - y_range (list): y range coordinates for map spatial limits
    
    Returns list of Bokeh figure
    """
    params = params_plot['params']
    TOOLS = params_plot['tools'] 
    tile_provider = params_plot['tile_provider']
    source = params_plot['source_iso']
    title = params_plot['title']
    
    p_shape = figure(
            title= title, 
            tools=TOOLS, 
            x_axis_location=None, 
            y_axis_location=None, 
            width=params["fig_params"]["width"], 
            height=params["fig_params"]["height"],
            match_aspect=True, 
            aspect_scale=1
            )
    
    columns = [
        TableColumn(field="adress", title="Adress"),
        TableColumn(field="time", title="Time"),
        TableColumn(field="duration", title="Duration"),
        TableColumn(field="color", title="Color"),
        TableColumn(field="date", title="Date"),
        TableColumn(field="shape", title="Shape"),
        TableColumn(field="area", title="Area"),
        TableColumn(field="perimeter", title="Perimeter"),
        TableColumn(field="nb", title="Number of componants"),
        TableColumn(field="amplitude", title="Amplitude"),
        TableColumn(field="convex", title="Deviation from convex hull"),
        TableColumn(field="norm_notches", title="Normalized notches"),
        TableColumn(field="complexity", title="Complexity")
    ]
    
    data_table = DataTable(source=source, columns=columns, width=600, height=280)
    
    p_shape.grid.grid_line_color = None
    
    if tile_provider is not None:
        p_shape.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"], name="tile")
    
    return p_shape