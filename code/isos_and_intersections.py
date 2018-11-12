# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 17:28:25 2018

@author: thomas
"""
import os
import json
import time
import copy
import requests
import geojson
from geopy.geocoders import Nominatim
from jsonschema import validate
from geojson import Feature, MultiPolygon, FeatureCollection, Polygon
import geopandas as gpd
import pandas as pd
from datetime import datetime

import fill_poly_holes as fph
from schema import schema

geolocator = Nominatim(user_agent="app") #https://operations.osmfoundation.org/policies/nominatim/
#https://geopy.readthedocs.io/en/stable/#nominatim
#VALIDATOR = json.load(open("params_json_schema.json"))
VALIDATOR = schema

class GetIso:
    def __init__(self, params, places_cache, api="navitia", token=None):
        """
        @params (str): filepath of parameters [json]
        @places_cache (str): filepath of places cache [json]
        """
        self.params = json.load(open(params, encoding="utf-8"))
        for param in self.params:
            validate(param, VALIDATOR)
        try:
            self.places_cache = json.load(open(places_cache))
        except:
            self.places_cache = {} # dict to keep lat/lon if adress already been geocoded 
        
        self.api = api
        
        if self.api == "navitia":
            self.TOKEN = token
    
    def geocode(self, address):
        """
        Use geopy.geolocator (Nominatim) to get latitude and longitude (EPSG 4326) 
        of an adress
        
        @param adress (str): postal adress
        
        Returns latitude and longitude
        
        """
        if address not in self.places_cache:
            location = geolocator.geocode(address)
            if location is None:
                print ('Error on : ' + address)
            else:
                self.places_cache[address] = location.longitude, location.latitude
                time.sleep(5)
                return location.longitude, location.latitude 
        else:
            location = self.places_cache[address]
            return location[0], location[1]
        
    def get_coords_of_addresses(self):
        """
        Get coords of all addresses
        """
        self.dict_addresses = {}
        
        for param in self.params:
            for address in param["addresses"]:
                self.dict_addresses[address] = self.geocode(address)
    
    def define_request(self):
        """
        
        """
        #TODO: OPTIONS => Iso, journeys, ...
        if self.api == "navitia":
            url='https://api.navitia.io/v1/coverage/{}/{}?from={}&datetime={}{}{}'.format(
                        self.param_request["region_id"],
                        self.param_request["option"],
                        self.param_request["from_place"],
                        self.param_request["date_time"],
                        self.param_request["cutoffs"],
                        self.param_request["str_modes"]
                )
                
            headers = {
                    'accept': 'application/json',
                    'Authorization': self.TOKEN
                    }
            
        return url, headers
    
    def list_excluded(self, modes):
        """
        
        """
        forbidden = "&forbidden_uris[]=physical_mode:"
        str_modes = ""
        for mode in modes:
            str_modes += forbidden + mode
        
        return str_modes
    
    def _cutoffs(self, durations=[1200]):
        """
        Returns a string for Navitia API for step and seconds by step
        Returns a list of time values
        
        @param nb_iter (number): numer of iterations
        @param step (number): number of steps
        """
        list_time = []
        cutoffs = ""
        cuts = []
        
        for i in durations:
            cut = "&boundary_duration[]=" + str(i)
            cutoffs += cut
            cuts.append(cut)
            list_time.append(i)
        
        return cutoffs, list_time, cuts
    
    def get_iso(self, param, from_place):
        """
        
        """
        multipolys = []
        
        durations = [i*60 for i in param["durations"]]
        if len(durations) > 10:
            cutoffs, list_time, cuts = self._cutoffs(durations=durations)
            l_cuts = [cuts[x:x+10] for x in range(0, len(cuts),10)]
        else:
            cutoffs, list_time, cuts = self._cutoffs(durations=durations)
            l_cuts = cuts
        
        if self.api == "navitia":
            str_modes = self.list_excluded(param["excluded_modes"])
            date_time = datetime.strptime(
                    param["date"], 
                    '%Y-%m-%d'
                    ).date().isoformat() + "T" + param["time"]
            
            for element in l_cuts:
                self.param_request = {
                        "region_id":param["region_id"],
                        "option":param["option"],
                        "from_place":from_place,
                        "date_time":date_time,
                        "cutoffs":element,
                        "str_modes":str_modes
                        }
                
                url, headers = self.define_request()
                r = requests.get(url, headers=headers)
                code = r.status_code
                
                print ("PLACE", from_place)
                print ("DATETIME", date_time)
                print ("URL", url)
        
                json_response = json.dumps(r.json())
                geojson_ = geojson.loads(json_response)
                
                print (geojson_)
    
            for iso,duration in zip(geojson_[param["option"]], list_time):
                if param["option"] == "journeys":
                    iso["geojson"] = None #TODO TRANSFORMER COORDS EN PTS GEOJSON
                multi = Feature(
                        geometry=iso["geojson"],
                        properties={
                            "duration":duration,
                            "address": param["address"],
                            "datetime": date_time #TODO: add style properties 
                            }
                        )
                multipolys.append(multi)
                
        collection = FeatureCollection(multipolys)
        gdf_poly = gpd.GeoDataFrame.from_features(collection['features'])
        
        gdf_poly.crs = {'init': param["inProj"]}
        
        #Simplify
        if param["tolerance"] != 0:
            simplified = gdf_poly.geometry.simplify(
                    param["tolerance"],  
                    preserve_topology=param["preserve_topology"]
                    )
            simplified_gdf = copy.deepcopy(gdf_poly)
            simplified_gdf.geometry = simplified
            
            return simplified_gdf
        
        else:
            return gdf_poly
    
    def polys_no_holes(self, durations, gdf):
        for dur in durations:
            if durations.index(dur) != 0:
                gdf.loc[
                        gdf["duration"] == dur, "geometry"
                        ] = gdf.loc[
                                gdf["duration"] == dur, "geometry"
                                ].apply(
                        lambda x: fph.fill_holes_major_poly(x)
                        )
        return gdf
    
    def get_all_isos(self):
        """
        
        """
        l_all_gdf = []
        l_all_gdf_filled = []
        
        for param in self.params:
            l_param_gdf = []
            l_param_gdf_filled = []
            for address in param["addresses"]:
                from_place = self.places_cache[address]
                from_place = str(from_place[0]) +";"+str(from_place[1])
                gdf_poly = self.get_iso(param, from_place)
                l_param_gdf.append(gdf_poly)
                
                ## Rebuild isos (fill holes) for gdf sorted by durations
                gdf_poly_durations = self.polys_no_holes(
                        param["durations"], 
                        gdf_poly
                        )
                
                l_param_gdf_filled.append(gdf_poly_durations)
                
            gdf_param = pd.concat(l_param_gdf)
            gdf_param_filled = pd.concat(l_param_gdf_filled)
            l_all_gdf.append(gdf_param)
            l_all_gdf_filled.append(gdf_param_filled)
            
            #Write GeoJSON by addresses
            name_isos = param["id"] + "_isos_by_addresses.geojson"
            name_isos = os.path.join(param["path"], name_isos)
            gdf_param.to_file(name_isos, driver="GeoJSON")
            
            #Write GeoJSON by duration
            ## Sort by durations
            gdf_param_filled.sort_values(["duration"], axis=1, inplace=True)
            
            ## Write files
            name_isos_durations = param["id"] + "_isos_by_durations.geojson"
            name_isos_durations = os.path.join(
                    param["path"], 
                    name_isos_durations
                    )
            gdf_param_filled.to_file(
                    name_isos_durations, 
                    driver="GeoJSON"
                    )
            
            #TODO GET STATS
            #TODO GET COMPLEXITY
            #TODO INTERSECTIONS GDF AND GEOJSONS 
            #Intersections by addresses/durations
            how = param["how"]
#            if how is not None:
#                for dur in param["durations"]:
#                    
#                #TODO INTERSECTIONS BETWEEN ISO ADDRESS FOR A SAME DURATION => DO IT WITH SHAPELY
#                intersection = gpd.overlay(
#                        gdf_poly, 
#                        gdf_overlay, 
#                        how=param["how"]
#                        )
            #TODO EMPTINESS ISO => See automate.py, 1213
            
        
        gdf_global = pd.concat(l_all_gdf)
        
        return gdf_global
                
            
            
            