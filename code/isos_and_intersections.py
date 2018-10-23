# -*- coding: utf-8 -*-
"""
Created on Fri Oct 19 17:28:25 2018

@author: thomas
"""

import json
import time
import requests
import geojson
from geopy.geocoders import Nominatim
from jsonschema import validate
from geojson import Feature, MultiPolygon, FeatureCollection, Polygon
import geopandas as gpd
import pandas as pd

geolocator = Nominatim(user_agent="app") #https://operations.osmfoundation.org/policies/nominatim/
#https://geopy.readthedocs.io/en/stable/#nominatim
VALIDATOR = json.load(open("params_json_schema.json"))

class GetIso:
    def __init__(self, params, places_cache, api="navitia"):
        """
        @params (str): filepath of parameters [json]
        @places_cache (str): filepath of places cache [json]
        """
        self.params = json.loads(params)
        for param in self.params:
            validate(param, VALIDATOR)
        try:
            self.places_cache = json.load(open(places_cache))
        except:
            self.places_cache = {} # dict to keep lat/lon if adress already been geocoded 
        
        self.api = api
    
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
        if self.api == "navitia":
            url='https://api.navitia.io/v1/coverage/{}/isochrones?from={}&datetime={}{}{}'.format(
                        self.param_request["region_id"],
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
            l_cuts = [cuts,]
        
        if self.api == "navitia":
            str_modes = self.list_excluded(param["modes"])
            date_time = param["date"].isoformat() + "T" + param["time"]
            
            for element in l_cuts:
                self.param_request = {
                        "from_place":from_place,
                        "date_time":date_time,
                        "cutoffs":element,
                        "str_modes":str_modes
                        }
                
                url, headers = self.define_request()
                r = requests.get(url, headers=headers)
                code = r.status_code
        
                json_response = json.dumps(r.json())
                geojson_ = geojson.loads(json_response)
    
            for iso,duration in zip(geojson_['isochrones'], list_time):
                multi = Feature(
                        geometry=iso["geojson"],
                        properties={
                            "time":duration,
                            "address": param["address"],
                            "datetime": date_time #TODO: add style properties 
                            }
                        )
                multipolys.append(multi)
                
        collection = FeatureCollection(multipolys)
        gdf_poly = gpd.GeoDataFrame.from_features(collection['features'])
        
        gdf_poly.crs = {'init': param["inProj"]}
        
        return gdf_poly
    
    def get_all_isos(self, params):
        """
        
        """
        l_all_gdf = []
        for param in self.params:
            l_param_gdf = []
            for address in param["addresses"]:
                from_place = self.places_cache[param["address"]]
                gdf_poly = self.get_iso(param, from_place)
                l_param_gdf.append(gdf_poly)
            gdf_param = pd.concat(l_param_gdf)
            l_all_gdf.append(gdf_param)
            #TODO WRITE GEOJSON BY ADDRESSES AND BY DURATIONS
            #TODO INTERSECTIONS GDF AND GEOJSONS
            
        
        gdf_global = pd.concat(l_all_gdf)
        
        return gdf_global
                
                
            
            
            