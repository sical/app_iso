# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 12:38:20 2018

@author: thomas
"""

import osmnx as ox
import geopandas as gpd
#import pandas as pd

class SpatialCut:
    def __init__(
            self, 
            geojson_bbox, 
            timeout, geojsons, 
            id_field, 
            network_output, 
            epsg_in, 
            epsg_out
            ):
        
        self.geojson_bbox = gpd.read_file(geojson_bbox)
        self.geojson_bbox.crs = {"init":epsg_in}
        geojsons = [gpd.read_file(x) for x in geojsons]
        
        for geo in geojsons:
            geo.crs = {"init":epsg_in}

        if epsg_out != None:
            self.geojson_bbox = self.geojson_bbox.to_crs(
                    {"init":epsg_out}
                    )
            
            self.geojsons = []
            for geo in geojsons:
                self.geojsons.append(
                        geo.to_crs({"init":epsg_out})
                        )
        else:
            self.geojsons = geojsons
            
        self.timeout = timeout
        self.id_field = id_field
        self.network_output = network_output
        

    def get_network_from_poly(self):
        poly = self.geojson_bbox["geometry"][0]
        G = ox.graph_from_polygon(
                poly,
                timeout=self.timeout
                )
        
        gdf_graph = ox.graph_to_gdfs(G)
        self.lines = gdf_graph[1]
        self.points = gdf_graph[0]
        
#        return self.gdf_graph
    
    def get_value_by_intersect(self):
        
        for gdf in self.geojsons:
#            print (gdf)
#            print (self.gdf_graph[1])
            duration = gdf["time"][0]
            overlay_ids = gpd.overlay(self.lines, gdf, how="intersection")[self.id_field]
            self.gdf_graph.loc[self.gdf_graph[self.id_field].isin(overlay_ids)]["duration"] = duration

        with open(self.network_output, "w") as f:
            f.write(self.gdf_graph.to_json())
            
        return self.gdf_graph
    
    def run(self):
        self.get_network_from_poly()
        self.get_value_by_intersect()