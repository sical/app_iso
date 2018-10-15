# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 12:38:20 2018

@author: thomas
"""

import osmnx as ox
import geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
import pandas as pd

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
        poly = self.geojson_bbox["geometry"].values[0]
        
        G = ox.graph_from_polygon(
                poly,
                timeout=self.timeout
                )
        
        gdf_graph = ox.graph_to_gdfs(G)
        self.lines = gdf_graph[1]
        self.points = gdf_graph[0]
        
#        return self.gdf_graph
    
    def get_value_by_intersect(self):
        """
        Sources: https://github.com/gboeing/urban-data-science/blob/master/19-Spatial-Analysis-and-Cartography/rtree-spatial-indexing.ipynb
                 https://geoffboeing.com/2016/10/r-tree-spatial-index-python/
        """
        #Build R-tree index
        sindex = self.lines.sindex
        dict_ = {}
        self.lines["duration"] = 0 
        
        for gdf in self.geojsons:
#            print (gdf)
#            print (self.gdf_graph[1])
            duration = gdf["time"][0]
            lines_within_geometry = pd.DataFrame()
            print (duration)
            
            for geometry in gdf["geometry"]:
                # make the geometry a multipolygon if it's not already
#                if isinstance(geometry, Polygon):
#                    geometry = MultiPolygon([geometry])
                
#                #Make sub polygons
                geometry_cut = ox.quadrat_cut_geometry(geometry, quadrat_width=0.1)
                
                #CHANGE NOW
                
                # find the points that intersect with each subpolygon and add them to points_within_geometry
                for poly in geometry_cut:
                    possible_matches_index = list(sindex.intersection(poly.bounds))
                    possible_matches = self.lines.iloc[possible_matches_index]
                    precise_matches = possible_matches[possible_matches.intersects(poly)]
                    # buffer by the <1 micron dist to account for any space lost in the quadrat cutting
                    # otherwise may miss point(s) that lay directly on quadrat line
    #                    poly = poly.buffer(1e-14).buffer(0)
    #                
    #                    # find approximate matches with r-tree, then precise matches from those approximate ones
    #                    possible_matches_index = list(sindex.intersection(poly.bounds))
    #                    possible_matches = self.lines.iloc[possible_matches_index]
    #                    precise_matches = possible_matches[possible_matches.intersects(poly)]
                    lines_within_geometry = lines_within_geometry.append(precise_matches)
                    
    #                    overlay_ids = gpd.overlay(self.lines, gdf, how="intersection")[self.id_field]
    #                    self.gdf_graph.loc[self.gdf_graph[self.id_field].isin(overlay_ids)]["duration"] = duration
#            print (len(lines_within_geometry))
#            print ("#################################################")
            
            # Add duration value in the new field duration in self.lines
            ## Get osmid of lines_within_geometry
            osmids = lines_within_geometry["osmid"].values
            print (osmids)
            self.lines.loc[self.lines["osmid"] == osmids]["duration"] = duration
        
#            if type(lines_within_geometry) == list  and lines_within_geometry != []:
#                dict_[duration] = pd.concat(lines_within_geometry)
#            else:
#                dict_[duration] = None
##            print (dict_)
#        
#        self.gdf_export = gpd.GeoDataFrame.from_dict(dict_, orient="index")

#        with open(self.network_output, "w") as f:
#            f.write(self.gdf_export.to_json())
        
        self.lines.to_file(self.network_output, driver="GeoJSON")
        
        return self.lines
    
    def run(self):
        self.get_network_from_poly()
        return self.get_value_by_intersect()
        