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
#    colors = params_plot['colors']
#    palette_name = params_plot['palette_name']
    params = params_plot['params']
    TOOLS = params_plot['tools'] 
#    source = params_plot['source']
#    source_pts = params_plot['source_pts']
#    buildings = params_plot['buildings']
#    network = params_plot['network']
    tile_provider = params_plot['tile_provider']
    source = params_plot['source_iso']
#    x_range = params_plot['x_range']
#    y_range = params_plot['y_range']
    
#    color_mapper = LinearColorMapper(palette=colors[palette_name])
    
#    xs_opacity = [[140750, 386600, 386600, 140750],]
#    ys_opacity = [[6138497, 6138497, 6369840, 6369840],]
#    
#    opacity_layer = ColumnDataSource(
#            {'xs':xs_opacity,
#             'ys':ys_opacity
#            }
#            )
    
#    options_buildings = dict(
#            fill_alpha= params["fig_params"]["alpha_building"],
#            fill_color= "black", 
#            line_color='white', 
#            line_width=params["fig_params"]["line_width_building"], 
#            source=buildings,
#            legend="batiments"
#            )
    
#    options_iso_surf = dict(
#            fill_alpha= params["fig_params"]["alpha_surf"], 
#            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
#            line_color='white', 
#            line_width=params["fig_params"]["line_width_surf"], 
#            source=source,
#            legend="isochrones"
#            )
#    
#    options_iso_contours = dict(
#            line_alpha= params["fig_params"]["alpha_cont"], 
#            line_color={'field': params["fig_params"]["field"], 'transform': color_mapper},
#            line_width=params["fig_params"]["line_width_cont"], 
#            source=source_polys,
#            legend="isochrones"
#            )
#    
#    options_iso_pts = dict(
#            line_alpha= params["fig_params"]["alpha_surf"], 
#            color={'field': 'time', 'transform': color_mapper},
#            line_width=params["fig_params"]["line_width_surf"], 
#            size=3,
#            source=source_pts,
#            legend="isopoints"
#            )
    
#    options_network = dict(
#                line_alpha= params["fig_params"]["alpha_network"], 
#                line_color=params["fig_params"]["color_network"],
#                line_width=params["fig_params"]["line_width_surf"], 
#                source=network,
#                legend="network"
#                )
    
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
    
    # TODO, fix edit tool
#    p1 = p_shape.patches([], [], fill_alpha=0.4)
#    c1 = p_shape.circle([], [], size=10, color='red')
#    edit_tool = PolyEditTool(renderers=[p1, p1], vertex_renderer=c1)
#
#    p_shape.add_tools(edit_tool)
#    p_shape.toolbar.active_drag = edit_tool
    
    data_table = DataTable(source=source, columns=columns, width=600, height=280)
    
#    p_shape.patches(
#            'xs',
#            'ys', 
#            fill_alpha= 0.5, 
#            fill_color= "black",
#            source=opacity_layer
#            )
    
#    p_surface_cat.patches('xs', 
#                          'ys', 
#                          **options_buildings)
    
    p_shape.grid.grid_line_color = None

#    p_shape.patches('xs',
#                    'ys', 
#                    **options_iso_surf)
    
#    p_surface_cat.multi_line('xs', 
#                             'ys', 
#                             **options_network)
    
    
    p_shape.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"], name="tile")
    
    return p_shape