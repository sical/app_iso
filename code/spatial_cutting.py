# -*- coding: utf-8 -*-
"""
Created on Wed Oct 10 12:38:20 2018

@author: thomas
"""

import osmnx as ox
import geopandas as gpd
#from shapely.geometry import Polygon, MultiPolygon
import pandas as pd
import overpass
import time

def gdf_bool_to_int(gdf):
    """
    For a given GeoDataFrame, returns a copy that
    recasts all `bool`-type columns as `int`.

    GeoDataFrame -> GeoDataFrame
    
    Source: https://github.com/geopandas/geopandas/issues/437#issuecomment-341184104
    """
    df = gdf.copy()
    coltypes = gpd.io.file.infer_schema(df)['properties']
    to_drop = []
    for c in coltypes.items():
        if c[1] == 'bool':
            colname = c[0]
            df[colname] = df[colname].astype('int')
        elif c[1] == "str":
            colname = c[0]
            to_drop.append(colname)
    
    df = df.drop(columns=to_drop)
    
    return df

def get_transit_network(
        bbox="",
        endpoint="https://overpass-api.de/api/interpreter",
        timeout=40, 
        modes=["tram","subway","bus"],
        network=""
        ):
    
    """
    Get the transit networks (tramway, bus, subway, train, ...)
    and return GeoJSON of nodes and lines
    
    @bbox[tuple]: coordinates of bounding box: 
        EPSG: 4326, 
        format: south,west,north,east
        ex: 45.746312,4.840357,45.766805,4.865903,
        default: ""
    @endpoint[str]: endpoint overpass:
        see https://wiki.openstreetmap.org/wiki/Overpass_API#Public%20Overpass%20API%20instances
        default: "https://overpass-api.de/api/interpreter"
    @timeout[int]: timeout for overpass request:
        default: 40
    @modes[list of str]: each mode for network request:
        default: ["tram","subway","bus"]
    @network[str]: network name:
        default: ""
        ex: "TCL"
        
    Returns dict of modes/GeoJSON
    """
    
    dict_ = {}
    api = overpass.API(endpoint=endpoint, timeout=timeout)
    if network != "":
            network = "[network={}]".format(network)
    
    for mode in modes:
        requ = """
            (
              rel{}["type"="route"]["route"="{}"]{};
            );
            (._;>;);
            out geom;
            
        """.format(network, mode, bbox)
        
        dict_[mode] = api.get(requ)
        
    return dict_


class SpatialCut:
    def __init__(
            self, 
            bbox_file, 
            timeout, 
            spatial_cuts,
            epsg_in, 
            epsg_out=None
            ):
        
        self.bbox_file = gpd.read_file(bbox_file)
        self.bbox_file.crs = {"init":epsg_in}
        spatial_cuts = [gpd.read_file(x) for x in spatial_cuts]
        
        for geo in spatial_cuts:
            geo.crs = {"init":epsg_in}

        if epsg_out != None:
            self.bbox_file = self.bbox_file.to_crs(
                    {"init":epsg_out}
                    )
            
            self.spatial_cuts = []
            for geo in spatial_cuts:
                self.spatial_cuts.append(
                        geo.to_crs({"init":epsg_out})
                        )
        else:
            self.spatial_cuts = spatial_cuts
            
        self.timeout = timeout
    
    def _bbox(self):
        return self.bbox_file["geometry"].values[0]
    
    def get_network_from_poly(self):
        poly = self._bbox()
        
        G = ox.graph_from_polygon(
                poly,
                timeout=self.timeout
                )
        
        gdf_graph = ox.graph_to_gdfs(G)
        self.lines = gdf_graph[1]
        self.points = gdf_graph[0]
        
    def get_buildings_from_poly(self):
        poly = self._bbox()
        self.buildings = ox.buildings_from_polygon(poly)
        
    def get_network_duration(self):
        return self._get_value_by_intersect(self.lines)
    
    def get_buildings_duration(self):
        return self._get_value_by_intersect(self.buildings)
    
    def get_spatial_duration(self, spatial):
        return self._get_value_by_intersect(spatial)
    
    def _get_value_by_intersect(self, spatial_objects):
        """
        Sources: https://github.com/gboeing/urban-data-science/blob/master/19-Spatial-Analysis-and-Cartography/rtree-spatial-indexing.ipynb
                 https://geoffboeing.com/2016/10/r-tree-spatial-index-python/
        """
        #Build R-tree index
        sindex = spatial_objects.sindex
        spatial_objects["duration"] = 0 
        
        for gdf in self.spatial_cuts:
            duration = gdf["time"][0]
            lines_within_geometry = pd.DataFrame()
            
            for geometry in gdf["geometry"]:
                #Make sub polygons
                geometry_cut = ox.quadrat_cut_geometry(geometry, quadrat_width=0.1)
                
                # find the points that intersect with each subpolygon and add them to points_within_geometry
                for poly in geometry_cut:
                    possible_matches_index = list(sindex.intersection(poly.bounds))
                    possible_matches = spatial_objects.iloc[possible_matches_index]
                    precise_matches = possible_matches[possible_matches.intersects(poly)]

                    lines_within_geometry = lines_within_geometry.append(precise_matches)
            
            # Add duration value in the new field duration in spatial_objects
            ## Get osmid of lines_within_geometry
            ids = lines_within_geometry.index.tolist()
            spatial_objects.loc[spatial_objects.index.isin(ids), "duration"] = spatial_objects.loc[spatial_objects.index.isin(ids), "duration"].apply(lambda x: duration)
        
        return gdf_bool_to_int(spatial_objects)
    
    def apply_duration(self, network=True, buildings=True, spatial_inputs=[]):
        dict_ = {}
        if spatial_inputs == []:
            if network == True and buildings == True:
                self.get_network_from_poly()
                self.get_buildings_from_poly()
                
                dict_["network"] = self.get_network_duration()
                dict_["buildings"] = self.get_buildings_duration()
            
            elif network == False and buildings == True:
                self.get_buildings_from_poly()
                
                dict_["network"] = None
                dict_["buildings"] = self.get_buildings_duration()
            
            elif network == True and buildings == False:
                self.get_network_from_poly()
                
                dict_["network"] = self.get_network_duration()
                dict_["buildings"] = None
        else:
            for spatial in spatial_inputs:
                dict_[spatial] = self.get_spatial_duration(spatial)
            
        return dict_
            
        