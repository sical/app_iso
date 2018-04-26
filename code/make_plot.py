# -*- coding: utf-8 -*-
"""
Created on Thu Apr 26 16:50:50 2018

@author: thomas
"""

from geopy.geocoders import Nominatim


from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, LinearColorMapper

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
    colors = params_plot['colors']
    palette_name = params_plot['palette_name']
    params = params_plot['params']
    TOOLS = params_plot['tools'] 
    source_polys = params_plot['source_polys']
    source_pts = params_plot['source_pts']
    buildings = params_plot['buildings']
    network = params_plot['network']
    tile_provider = params_plot['tile_provider']
    x_range = params_plot['x_range']
    y_range = params_plot['y_range']
    
    color_mapper = LinearColorMapper(palette=colors[palette_name])
    
    xs_opacity = [[140750, 386600, 386600, 140750],]
    ys_opacity = [[6138497, 6138497, 6369840, 6369840],]
    
    opacity_layer = ColumnDataSource(
            {'xs':xs_opacity,
             'ys':ys_opacity
            }
            )
    
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
    
    # SURFACE
    if x_range is None and y_range is None:
        p_surface_cat = figure(
                title= palette_name.upper() + " categorized surface", 
                tools=TOOLS, 
                x_axis_location=None, 
                y_axis_location=None, 
                width=params["fig_params"]["width"], 
                height=params["fig_params"]["height"],
                match_aspect=True, 
                aspect_scale=1
                )
                
    else:
        p_surface_cat = figure(
                title= palette_name.upper() + " categorized surface", 
                tools=TOOLS, 
                x_axis_location=None, 
                y_axis_location=None, 
                width=params["fig_params"]["width"], 
                height=params["fig_params"]["height"],
                x_range=x_range,
                y_range=y_range,
                match_aspect=True, 
                aspect_scale=1
                )
    
    p_surface_cat.patches('xs', 
                          'ys', 
                          fill_alpha= 0.5, 
                          fill_color= "black",
                          source=opacity_layer)
    
    p_surface_cat.patches('xs', 
                          'ys', 
                          **options_buildings)
    
    p_surface_cat.grid.grid_line_color = None

    p_surface_cat.patches('xs', 
                          'ys', 
                          **options_iso_surf)
    
    p_surface_cat.multi_line('xs', 
                             'ys', 
                             **options_network)
    
    
    p_surface_cat.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"])
    p_surface_cat.legend.location = "top_left"
    p_surface_cat.legend.click_policy="hide"
    
    ########
    
    x_range = p_surface_cat.x_range
    y_range = p_surface_cat.y_range
    
    # CONTOUR 
    p_contour_cat = figure(
            title=palette_name.upper() + " categorized contour",  
            tools=TOOLS, 
            x_axis_location=None, 
            y_axis_location=None, 
            width=params["fig_params"]["width"], 
            height=params["fig_params"]["height"],
            x_range=x_range,
            y_range=y_range,
            match_aspect=True, 
            aspect_scale=1
            )
    
    p_contour_cat.patches('xs', 
                          'ys', 
                          fill_alpha= 0.5, 
                          fill_color= "black",
                          source=opacity_layer)
    
    p_contour_cat.patches('xs', 
                          'ys', 
                          **options_buildings)
    
    p_contour_cat.grid.grid_line_color = None
    p_contour_cat.multi_line('xs', 
                             'ys', 
                             **options_iso_contours)
    
    p_contour_cat.multi_line('xs', 
                          'ys', 
                          **options_network)
    
    p_contour_cat.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"])
    p_contour_cat.legend.location = "top_left"
    p_contour_cat.legend.click_policy="hide"
    
    
    # POINTS 
    p_points_cat = figure(
            title=palette_name.upper() + " categorized points",  
            tools=TOOLS, 
            x_axis_location=None, 
            y_axis_location=None, 
            width=params["fig_params"]["width"], 
            height=params["fig_params"]["height"],
            x_range=x_range,
            y_range=y_range,
            match_aspect=True, 
            aspect_scale=1
            )
    
    p_points_cat.patches('xs', 
                          'ys', 
                          fill_alpha= 0.5, 
                          fill_color= "black",
                          source=opacity_layer)
    
    p_points_cat.patches('xs', 
                          'ys', 
                          **options_buildings)
    
    p_points_cat.multi_line('xs', 
                          'ys', 
                          **options_network)
    
    p_points_cat.grid.grid_line_color = None
    p_points_cat.circle(
            'x', 
            'y', 
            **options_iso_pts
            )

    
    p_points_cat.add_tile(tile_provider, alpha=params["fig_params"]["alpha_tile"])
    p_points_cat.legend.location = "top_left"
    p_points_cat.legend.click_policy="hide"
    
    list_plot = [p_surface_cat, p_contour_cat, p_points_cat]
    
    return list_plot