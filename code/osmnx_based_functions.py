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
import pandas as pd
import multiprocessing as mp
import threading

import time
from functions import time_profile
from constants import WALK_SPEED, DISTANCE, METERS_SECOND, DIST_BUFF
from graph_utils import graph_to_df

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

def graph_with_time(point, distance, edges_path, nodes_path, epsg=None):
    """
    
    """
    G = get_graph_from_point(point, distance, epsg=epsg)
    meters_per_minute = WALK_SPEED/60

    for u, v, k, data in G.edges(data=True, keys=True):
        data['time'] = data['length'] / meters_per_minute
    
#    nx.write_yaml(G,path)
    
    graph_to_df(G, edges_path, nodes_path)
    
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

def getLineCoords(row, geom, coord_type):
        """
        Returns a list of coordinates ('x' or 'y') of a LineString geometry
        Source: https://automating-gis-processes.github.io/2016/Lesson5-interactive-map-bokeh.html
        
        """
        if coord_type == 'x':
            return list( row[geom].coords.xy[0] )
        elif coord_type == 'y':
            return list( row[geom].coords.xy[1] )

def make_iso_lines(pts, trip_times, G=None, df=None, inproj=None, outproj=None):
    """
    Sources:
        https://github.com/gboeing/osmnx-examples/blob/master/notebooks/13-isolines-isochrones.ipynb
        http://kuanbutts.com/2017/12/16/osmnx-isochrones/
    
    """
    polys = []
    X = []
    Y = []
    l_gdf = []
    
#    if inproj is not None:
#        inProj = Proj(init="epsg:3857")
#        outProj = Proj(init="epsg:4326")
    
    if G is None:
        G = get_graph_from_point((pts[0].x, pts[0].y), DISTANCE, epsg={"init":"epsg:3857"})
        meters_per_minute = WALK_SPEED/60
        
        for u, v, k, data in G.edges(data=True, keys=True):
            data['time'] = data['length'] / meters_per_minute
            
    #Get center nodes
    for pt in pts:
        pt_proj = Point(transform(Proj(init="epsg:4326"), Proj(init="epsg:3857"), pt.x, pt.y))
        X.append(pt_proj.x)
        Y.append(pt_proj.y)
        
    
    center_nodes = ox.get_nearest_nodes(G, X, Y, method="kdtree")
        
    for center_node,pt in zip(center_nodes,pts):
        
        if df is not None:
            trip_time = df.loc[df["geometry"] == pt]["time_left"].values[0]
        
        subgraph = nx.ego_graph(G, center_node, radius=trip_time//60, distance='time')

        node_points = [
                Point(
                        (
                                data['x'],
                                data['y']
                                )
                        ) for node, data in subgraph.nodes(data=True)
                ]
        
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
            
            df_edges["line"] = df_edges.apply(
                    lambda x: LineString([x["from"], x["to"]]),
                    axis=1
                    )
            
            l_gdf.append(df_edges)
    
    gdf = gpd.pd.concat(l_gdf, sort=False)
    gdf_lines = gdf[["source", "target", "from", "to", "line", "time"]]
    gdf_lines.drop_duplicates(subset=["source","target"],inplace=True)
    gdf_lines['xs'] = gdf_lines.apply(getLineCoords, geom='line', coord_type='x', axis=1)
    gdf_lines['ys'] = gdf_lines.apply(getLineCoords, geom='line', coord_type='y', axis=1)

    start = time.time()
    
    gdf_polys = gdf_lines[["source", "target","line", "time"]]
    gdf_polys["polys"] = gdf_polys.apply(
                    lambda x: x["line"].buffer(DIST_BUFF),
                    axis=1
                    )
#    gdf_polys = gdf_polys.rename(columns={"polys":"geometry"}).set_geometry('geometry')
#    gdf_polys["aggregate"] = [1 for i in gdf_polys["geometry"]]
#    gdf_polys = gdf_polys.dissolve(by="aggregate")
    
    polys = cascaded_union(gdf_polys["polys"].values.tolist()) 
    gdf_polys_union = gpd.GeoDataFrame(geometry=[polys])
    gdf_polys_union.crs = {'init': "epsg:3857"}
    
    gdf_lines.drop(['line','from','to'], axis=1, inplace=True)
    
    print ("polys", time_profile(start, option="format"))
    
    gdf_polys = gdf_polys.rename(
                    columns={'polys': 'geometry'}
                    ).set_geometry('geometry')
    
    return {
            "gdf_lines":gdf_lines,
            "polys_union":gdf_polys_union,
            "polys":gdf_polys
            }
    
def buffering(point, distance):
    return point.buffer(distance, resolution=16)
    
def _get_overlays(polys, union, intersection, difference, cutted, sindex):
    """
    
    """
    
    for poly in polys:
        possible_matches_index = list(sindex.intersection(poly.bounds))
        possible_matches = cutted.iloc[possible_matches_index]
        precise_matches = possible_matches[possible_matches.intersects(poly)]
        
        gdf_poly = gpd.GeoDataFrame(crs={"init":"epsg:3857"}, geometry = [poly])

        union_overlay = gpd.overlay(
                gdf_poly, 
                precise_matches, 
                how="union"
                )
        intersection_overlay = gpd.overlay(
                precise_matches, 
                gdf_poly, 
                how="intersection"
                )
        difference_overlay = gpd.overlay(
                union_overlay, 
                intersection_overlay, 
                how="symmetric_difference"
                )
        
        
        union.append(union_overlay)
        intersection.append(intersection_overlay)
        difference.append(difference_overlay)
    
#    return union, intersection, difference
    

def chunks(l, n):
    """
    
    Sources:https://chrisalbon.com/python/data_wrangling/break_list_into_chunks_of_equal_size/
            https://stackoverflow.com/a/312464
            
    """
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n]
    
def spatial_cut(cutter, cutted):
    """
    Sources: https://github.com/gboeing/urban-data-science/blob/master/19-Spatial-Analysis-and-Cartography/rtree-spatial-indexing.ipynb
             https://geoffboeing.com/2016/10/r-tree-spatial-index-python/
    """
    #Build R-tree index
    sindex = cutted.sindex
    
    union = pd.DataFrame()
    intersection = pd.DataFrame()
    difference = pd.DataFrame()
    
    for geometry in cutter["geometry"]:
        #Make sub polygons
        geometry_cut = ox.quadrat_cut_geometry(geometry, quadrat_width=1000)
        
        # find the points that intersect with each subpolygon and add them to points_within_geometry
        for poly in geometry_cut:
            possible_matches_index = list(sindex.intersection(poly.bounds))
            possible_matches = cutted.iloc[possible_matches_index]
            precise_matches = possible_matches[possible_matches.intersects(poly)]
            
            if "geometry" in precise_matches.columns:
            
                gdf_poly = gpd.GeoDataFrame(crs={"init":"epsg:3857"}, geometry = [poly])
                    
                union_overlay = gpd.overlay(
                        gdf_poly, 
                        precise_matches, 
                        how="union"
                        )
                intersection_overlay = gpd.overlay(
                        precise_matches, 
                        gdf_poly, 
                        how="intersection"
                        )
                difference_overlay = gpd.overlay(
                        union_overlay, 
                        intersection_overlay, 
                        how="symmetric_difference"
                        )
                
                union.append(union_overlay)
                intersection.append(intersection_overlay)
                difference.append(difference_overlay)
            
    return {
            "symmetric_difference":difference,
            "union":union,
            "intersection":intersection
            }

def _overlay(list_, poly, matches, how="union"):
    """
    
    """
    if how == "union":
        spatial = poly.union(matches)
        if spatial.is_valid:
            list_.append(spatial.buffer(1))
    elif how == "intersection":
        spatial = poly.intersection(matches)
        if spatial.is_valid:
            list_.append(spatial.buffer(1))
    elif how == "difference":
        spatial = poly.difference(matches)
        if spatial.is_valid:
            list_.append(spatial.buffer(1))
    elif how == "symmetric_difference":
        spatial = poly.symmetric_difference(matches)
        if spatial.is_valid:
            list_.append(spatial.buffer(1))
    