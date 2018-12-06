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
import networkx as nx

import time
from functions import time_profile
from constants import WALK_SPEED, DISTANCE, METERS_SECOND, DIST_BUFF

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

def graph_with_time(point, distance, path, epsg=None):
    """
    
    """
    G = get_graph_from_point(point, distance, epsg=epsg)
    meters_per_minute = WALK_SPEED/60

    for u, v, k, data in G.edges(data=True, keys=True):
        data['time'] = data['length'] / meters_per_minute
    
    nx.write_yaml(G,path)
    
    return G
    

def get_graph_from_point(point, distance, epsg=None):
    """
    
    """
    inProj = Proj(init="epsg:4326")
    outProj = Proj(init="epsg:3857")
    x,y = transform(inProj,outProj,point[0],point[1])
    point = Point((x,y))
    buffer = _buffering(point, distance)
    
    poly, _ = ox.project_geometry(
                buffer, 
                crs={'init':"epsg:3857"}, 
                to_latlong=True
                )
    #Get the graph
    G = ox.graph_from_polygon(poly, network_type="walk")
    
    if epsg is not None:
#        print (epsg)
        G = ox.project_graph(G, to_crs=epsg)
    
    return G

def _get_geom_df(gdf, node):
    """
    @node(str): source or target
    
    """

    return gdf.at[(node, "geometry")]

def make_iso_lines(pts, trip_times, G=None, df=None, inproj=None, outproj=None):
    """
    Sources:
        https://github.com/gboeing/osmnx-examples/blob/master/notebooks/13-isolines-isochrones.ipynb
        http://kuanbutts.com/2017/12/16/osmnx-isochrones/
    
    """
    xs = []
    ys = []
    durations = []
    polys = []
    edge_lines = []
    X = []
    Y = []
    l_gdf = []
    
    if inproj is not None:
        inProj = Proj(init="epsg:3857")
        outProj = Proj(init="epsg:4326")
    
#    X = [ori[0] for ori in oris]
#    Y = [ori[1] for ori in oris]
    
    start = time.time()
    
    print ("NUMBER", G.number_of_edges())
    
    if G is None:
        G = get_graph_from_point((pts[0].x, pts[0].y), DISTANCE, epsg={"init":"epsg:3857"})
        meters_per_minute = WALK_SPEED/60
        
        print ("Get G", time_profile(start, option="format"))
        start = time.time()
        
        for u, v, k, data in G.edges(data=True, keys=True):
            data['time'] = data['length'] / meters_per_minute
            
        print ("Add data", time_profile(start, option="format"))
        start = time.time()
    
    
    #Get center nodes
    for pt in pts:
        pt_proj = Point(transform(Proj(init="epsg:4326"), Proj(init="epsg:3857"), pt.x, pt.y))
        X.append(pt_proj.x)
        Y.append(pt_proj.y)
        
    
    center_nodes = ox.get_nearest_nodes(G, X, Y, method="kdtree")
    
#    print ("1", time_profile(start, option="format"))
#    start = time.time()
    
#    print (X)
    
#    if df is not None:
#        df["center_nodes"] = center_nodes
        
    for center_node in center_nodes:
#        start = time.time()
#        G = get_graph_from_point((pt.x, pt.y), DISTANCE, epsg={"init":"epsg:3857"})
#        meters_per_minute = WALK_SPEED/60
#        
#        print ("Get G", time_profile(start, option="format"))
#        start = time.time()
#        
#        for u, v, k, data in G.edges(data=True, keys=True):
#            data['time'] = data['length'] / meters_per_minute
#            
#        print ("Add data", time_profile(start, option="format"))
#        start = time.time()
        
#        pt_proj = Point(transform(Proj(init="epsg:4326"), Proj(init="epsg:3857"), pt.x, pt.y))
#        center_node = ox.get_nearest_node(G, (pt_proj.x, pt_proj.y), method="euclidean")
        
#        print ("Get center node", time_profile(start, option="format"))
        start = time.time()
        
        if df is not None:
            trip_time = df.loc[df["geometry"] == pt]["time_left"].values[0]
            
            print ("TRIP:", trip_time, trip_time//60)
        
        subgraph = nx.ego_graph(G, center_node, radius=trip_time//60, distance='time')
        
        print ("Subgraph", time_profile(start, option="format"))
        start = time.time()

        node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
        
        print ("Nodes points", time_profile(start, option="format"))
        start = time.time()

        
        if len(node_points) > 1: 
            nodes_gdf = gpd.GeoDataFrame({'id': subgraph.nodes()}, geometry=node_points)
            nodes_gdf = nodes_gdf.set_index('id')
            
            df_edges = nx.to_pandas_edgelist(subgraph)
            df_edges["from"] = df_edges.apply(
                    lambda x: _get_geom_df(
                            nodes_gdf,
                            x["source"]
                            ),
                    axis=1
                    )

            df_edges["to"] = df_edges.apply(
                    lambda x: _get_geom_df(
                            nodes_gdf,
                            x["target"]
                            ),
                    axis=1
                    )
                                
#            df_edges["xs"] = df_edges.apply(
#                    lambda x: (x["from"].y, x["to"].y),
#                    axis=1
#                    )
#            
#            df_edges["ys"] = df_edges.apply(
#                    lambda x: (x["from"].y, x["to"].y),
#                    axis=1
#                    )
            
            df_edges["line"] = df_edges.apply(
                    lambda x: LineString([x["from"], x["to"]]),
                    axis=1
                    )
            
            l_gdf.append(df_edges)
            
            
#            for n_fr, n_to, data in subgraph.edges(data=True):
#                f = nodes_gdf.at[(n_fr,'geometry')]
#                t = nodes_gdf.at[(n_to,'geometry')]
#                edge_lines.append(LineString([f,t]))
#                
#                if inproj is not None:
#                    fx,fy = transform(inProj,outProj,f.x,f.y)
#                    tx,ty = transform(inProj,outProj,t.x,t.y)
#                    xs.append([fx,tx])
#                    ys.append([fy,ty])
#                else:
#                    xs.append([f.x,t.x])
#                    ys.append([f.y,t.y])
#                    
#                durations.append(data["time"])
#        
#        print ("TOTAL",len(edge_lines))
#        print ("Edges lines", time_profile(start, option="format"))
#        start = time.time()
#    
#    
##        edges_gdf = gpd.GeoDataFrame(geometry=edge_lines)
##        l_polys = edges_gdf.buffer(DIST_BUFF).values.tolist()
##        polys.append(edges_gdf.buffer(DIST_BUFF).unary_union)   
##        polys.append(cascaded_union(l_polys))
#        
#        print ("Edges gdf and polys", time_profile(start, option="format"))
#        start = time.time()
        
#        print ("5", time_profile(start, option="format"))
#        start = time.time()
    
    
#    data = {
#            "geometry":edge_lines,
#            "durations":durations,
#            "xs":xs,
#            "ys":ys,
#            "buffer":polys
#        }   
    
#    gdf = gpd.pd.concat(l_gdf).drop_duplicates(inplace=True)
    gdf = gpd.pd.concat(l_gdf, sort=False)
    return gdf


#def make_iso_lines(point, trip_time, inproj=None, outproj=None):
#    """
#    Sources:
#        https://github.com/gboeing/osmnx-examples/blob/master/notebooks/13-isolines-isochrones.ipynb
#        http://kuanbutts.com/2017/12/16/osmnx-isochrones/
#    
#    """
#    xs = []
#    ys = []
#    durations = []
#    polys = []
#    if inproj is not None:
#        inProj = Proj(init="epsg:3857")
#        outProj = Proj(init="epsg:4326")
#    
##    start = time.time()
#    
#    G = get_graph_from_point((point.x, point.y), DISTANCE, epsg={"init":"epsg:3857"})
#    
##    print ("1", time_profile(start, option="format"))
##    start = time.time()
##                            self.G = ox.project_graph(self.G)
#    meters_per_minute = WALK_SPEED/60
#    for u, v, k, data in G.edges(data=True, keys=True):
#        data['time'] = data['length'] / meters_per_minute
#        
##    print ("2", time_profile(start, option="format"))
##    start = time.time()
#    
#    center_node = ox.get_nearest_node(G, (point.x, point.y))
#    
##    print ("3", time_profile(start, option="format"))
##    start = time.time()
#    
##    print ("1", time_profile(start, option="format"))
##    start = time.time()
#    
#    subgraph = nx.ego_graph(G, center_node, radius=trip_time//60, distance='time')
#    
##    print ("2", time_profile(start, option="format"))
##    start = time.time()
#
#    node_points = [Point((data['x'], data['y'])) for node, data in subgraph.nodes(data=True)]
#    
##    print ("3", time_profile(start, option="format"))
##    start = time.time()
#
#    
#    if len(node_points) > 1:
#        nodes_gdf = gpd.GeoDataFrame({'id': subgraph.nodes()}, geometry=node_points)
#        nodes_gdf = nodes_gdf.set_index('id')
#        edge_lines = []
#        for n_fr, n_to, data in subgraph.edges(data=True):
#            f = nodes_gdf.loc[n_fr].geometry
#            t = nodes_gdf.loc[n_to].geometry
#            edge_lines.append(LineString([f,t]))
#            
#            
#            if inproj is not None:
#                fx,fy = transform(inProj,outProj,f.x,f.y)
#                tx,ty = transform(inProj,outProj,t.x,t.y)
#                xs.append([fx,tx])
#                ys.append([fy,ty])
#            else:
#                xs.append([f.x,t.x])
#                ys.append([f.y,t.y])
#                
#            durations.append(data["time"])
#            
##    print ("4", time_profile(start, option="format"))
##    start = time.time()
#
#
#    edges_gdf = gpd.GeoDataFrame(geometry=edge_lines)
#    polys.append(edges_gdf.buffer(20).unary_union)     
#    
##    print ("5", time_profile(start, option="format"))
##    start = time.time()
#    
#    
#    data = {
#            "geometry":edge_lines,
#            "durations":durations,
#            "xs":xs,
#            "ys":ys,
#            "buffer":polys
#        }   
#        
#    return data

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