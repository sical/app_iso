# -*- coding: utf-8 -*-
"""
Created on Fri Nov 23 16:22:58 2018

@author: thomas
"""

import osmnx as ox
import networkx as nx
import numpy as np
import geopandas as gpd
from shapely.ops import cascaded_union
from shapely.geometry import Point, LineString
from pyproj import Proj, transform

import time
from functions import time_profile


def get_graph_from_envelope(gdf, crs_init='epsg:3857', to_latlong=True):
    """
    Return a NetworkX graph (walk) from a points GeoDataframe
    """
    #Get the unique buffer (union of all buffers from points)
    poly = _get_buffer(gdf)
    
    #Reprojection if necessary
    if crs_init != '':     
        poly, _ = ox.project_geometry(
                poly.envelope[0], 
                crs={'init':crs_init}, 
                to_latlong=to_latlong
                )
    else:
        poly = poly.envelope[0]
        
    #Get the graph
    G = ox.graph_from_polygon(poly, network_type="walk")

    return G

def _buffering(point, distance):
    """
    Buffering a Shapely point
    """
    return point.buffer(distance, resolution=16)

def _get_buffer(gdf):
    """
    Returns a GeoSerie buffer from a points GeoDataframe
    """
    gdf["buffer"] = np.vectorize(_buffering)(gdf["geometry"], gdf["walkable_distance"])
    gdf = gdf.rename(columns={'geometry': 'pts'})
    gdf = gdf.rename(columns={'buffer': 'geometry'}).set_geometry('geometry')
    poly = gpd.GeoSeries(cascaded_union(gdf["geometry"]))
    
    return poly

def get_graph_from_point(point, distance):
    """
    
    """
    inProj = Proj(init="epsg:4326")
    outProj = Proj(init="epsg:3857")
    x,y = transform(inProj,outProj,point[0],point[1])
    point = Point((x,y))
    buffer = _buffering(point, distance)
    
    poly, _ = ox.project_geometry(
                buffer.envelope, 
                crs={'init':"epsg:3857"}, 
                to_latlong=True
                )
    
    #Get the graph
    G = ox.graph_from_polygon(poly, network_type="walk")
    
    return G

def make_iso_lines(G, oris, trip_times, inproj="epsg:4326", outproj="epsg:3857"):
    """
    @G (NetworkX Graph): graph used to get isolines
    @trip_times (list): durations values
    @inproj (str): input projection, if reprojection necessary, default None
    @outproj (str): output projection, if reprojection necessary, default None
    
    Sources:
        https://github.com/gboeing/osmnx-examples/blob/master/notebooks/13-isolines-isochrones.ipynb
        http://kuanbutts.com/2017/12/16/osmnx-isochrones/
        
    Adaptation: thomas
        
    Returns dict of "xs", "ys" (for Bokeh ColumnDatasource), durations and LineStrings
    
    """
    xs = []
    ys = []
    durations = []
    if inproj is not None:
        inProj = Proj(init=inproj)
        outProj = Proj(init=outproj)
    
    for ori in oris:
        center_node = ox.get_nearest_node(G, (ori[0], ori[1]))
        
        for trip_time in sorted(trip_times, reverse=True):
            subgraph = nx.ego_graph(
                    G, center_node, 
                    radius=trip_time, 
                    distance='time'
                    )

            node_points = [
                    Point(
                            (data['x'], data['y'])
                            ) for node, data in subgraph.nodes(data=True)
                    ]
            nodes_gdf = gpd.GeoDataFrame(
                    {'id': subgraph.nodes()}, 
                    geometry=node_points
                    )
            nodes_gdf = nodes_gdf.set_index('id')

#            edge_lines = []
            for n_fr, n_to in subgraph.edges():
                f = nodes_gdf.loc[n_fr].geometry
                t = nodes_gdf.loc[n_to].geometry
#                edge_lines.append(LineString([f,t]))
                
                if inproj is not None:
                    fx,fy = transform(inProj,outProj,f.x,f.y)
                    tx,ty = transform(inProj,outProj,t.x,t.y)
                    xs.append([fx,tx])
                    ys.append([fy,ty])
                else:
                    xs.append([f.x,t.x])
                    ys.append([f.y,t.y])
                    
                durations.append(trip_time)

    data = {
#            "geometry":edge_lines,
            "durations":durations,
            "xs":xs,
            "ys":ys
        }   
        
    return data

def isolines_df(G, center_node, trip_time, inproj=None, outproj=None):
    """
    @G (NetworkX Graph): graph used to get isolines
    @ori (Point): Shapely Point
    @trip_time (int): durations
    @inproj (str): input projection, if reprojection necessary, default None
    @outproj (str): output projection, if reprojection necessary, default None
    
    Sources:
        https://github.com/gboeing/osmnx-examples/blob/master/notebooks/13-isolines-isochrones.ipynb
        http://kuanbutts.com/2017/12/16/osmnx-isochrones/
        
    Adaptation: thomas
        
    Returns dict of "xs", "ys" (for Bokeh ColumnDatasource), durations and LineStrings
    
    """
    start = time.time()
    
    xs = []
    ys = []
    durations = []
    if inproj is not None:
        inProj = Proj(init=inproj)
        outProj = Proj(init=outproj)
    
#    center_node = ox.get_nearest_node(G, (ori.x, ori.y))
    
    print ("1", time_profile(start, option="format"))
    start = time.time()
    
    subgraph = nx.ego_graph(
            G, center_node, 
            radius=trip_time, 
            distance='time'
            )
    
    print ("2", time_profile(start, option="format"))
    start = time.time()
    
    node_points = [
            Point(
                    (data['x'], data['y'])
                    ) for node, data in subgraph.nodes(data=True)
            ]
    
    print ("3", time_profile(start, option="format"))
    start = time.time()
    
    nodes_gdf = gpd.GeoDataFrame(
            {'id': subgraph.nodes()}, 
            geometry=node_points
            )
    
    print ("4", time_profile(start, option="format"))
    start = time.time()
    
    nodes_gdf = nodes_gdf.set_index('id')
    
    print ("5", time_profile(start, option="format"))
    start = time.time()
#            edge_lines = []
    for n_fr, n_to in subgraph.edges():
        f = nodes_gdf.loc[n_fr].geometry
        t = nodes_gdf.loc[n_to].geometry
#                edge_lines.append(LineString([f,t]))
        
        if inproj is not None:
            fx,fy = transform(inProj,outProj,f.x,f.y)
            tx,ty = transform(inProj,outProj,t.x,t.y)
            xs.append([fx,tx])
            ys.append([fy,ty])
        else:
            xs.append([f.x,t.x])
            ys.append([f.y,t.y])
            
        durations.append(trip_time)
    
    print ("6", time_profile(start, option="format"))
    print ("###################")

    data = {
#            "geometry":edge_lines,
            "durations":durations,
            "xs":xs,
            "ys":ys
        }   
        
    return data