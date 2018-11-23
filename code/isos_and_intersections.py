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
from geojson import Feature, MultiPolygon, FeatureCollection, Polygon, Point, LineString
import geopandas as gpd
import pandas as pd
from datetime import datetime

import fill_poly_holes as fph
from schema import schema
from osmnx_based_functions import make_iso_lines, get_graph_from_envelope

geolocator = Nominatim(user_agent="app") #https://operations.osmfoundation.org/policies/nominatim/
#https://geopy.readthedocs.io/en/stable/#nominatim
#VALIDATOR = json.load(open("params_json_schema.json"))
VALIDATOR = schema
WALK_SPEED = 5000 #m/h
METERS_SECOND = WALK_SPEED/3600

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
            if self.option == "isochrones":
                url='https://api.navitia.io/v1/coverage/{}/{}?from={}&datetime={}{}{}'.format(
                            self.param_request["region_id"],
                            self.option,
                            self.param_request["from_place"],
                            self.param_request["date_time"],
                            self.param_request["cutoffs"],
                            self.param_request["str_modes"]
                    )
            elif self.option == "journeys":
                duration = "&max_duration=" + str(self.param_request["max_duration"])
                url='https://api.navitia.io/v1/coverage/{}/{}?from={}&datetime={}{}{}'.format(
                            self.param_request["region_id"],
                            self.option,
                            self.param_request["from_place"],
                            self.param_request["date_time"],
                            duration,
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
        multis = []
        
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
                
#                print ("PLACE", from_place)
#                print ("DATETIME", date_time)
#                print ("URL", url)
        
                json_response = json.dumps(r.json())
                geojson_ = geojson.loads(json_response)
                
#                print (geojson_)
    
            for iso,duration in zip(geojson_["isochrones"], list_time):
                multi = Feature(
                        geometry=iso["geojson"],
                        properties={
                            "duration":duration,
                            "address": param["address"],
                            "datetime": date_time #TODO: add style properties 
                            }
                        )
                multis.append(multi)
                
        collection = FeatureCollection(multis)
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
        
    def get_journeys(self, param, from_place, address):
        """
        
        """
        multis = []
        self.urls = []
        self.pts_properties = []
        self.lines_properties = []
        
        durations = [i*60 for i in param["durations"]]
        geojsons = []
        l_gdf_journeys = []
        
        if self.api == "navitia":
            str_modes = self.list_excluded(param["excluded_modes"])
            date_time = datetime.strptime(
                    param["date"], 
                    '%Y-%m-%d'
                    ).date().isoformat() + "T" + param["time"]
            
            for duration in durations:
                self.param_request = {
                        "region_id":param["region_id"],
                        "from_place":from_place,
                        "date_time":date_time,
                        "max_duration":duration,
                        "str_modes":str_modes
                        }
                
                url, headers = self.define_request()
                r = requests.get(url, headers=headers)
                code = r.status_code
        
                json_response = json.dumps(r.json())
                geojson_ = geojson.loads(json_response)
                geojsons.append(geojson_)
    
            for iso,duration in zip(geojsons, durations):
                for journey in iso["journeys"]:
                    lon_from = journey["from"]["address"]["coord"]["lon"]
                    lat_from = journey["from"]["address"]["coord"]["lat"]
                    lon_to = journey["to"]["stop_point"]["coord"]["lon"]
                    lat_to = journey["to"]["stop_point"]["coord"]["lat"]
                    to_id = journey["to"]["stop_point"]["id"]
                    to_name = journey["to"]["stop_point"]["name"]
                    nb_transfers = journey["nb_transfers"]
                    arrival_date_time = journey["arrival_date_time"]
                    requested_date_time = journey["requested_date_time"]
                    departure_date_time = journey["departure_date_time"]
                    duration_ = journey["duration"]
                    
                    if "\'" in to_name:
                        to_name = to_name.replace("\'", "")
                    
                    pt = Feature(
                            geometry=Point((float(lon_to), float(lat_to))),
                            properties={
                                    "address_from":address,
                                    "lon_from":lon_from,
                                    "lat_from":lat_from,
                                    "lon_to":lon_to,
                                    "lat_to":lat_to,
                                    "to_id":to_id,
                                    "to_name":to_name.replace("\'","'"),
                                    "nb_transfers":nb_transfers,
                                    "arrival_date_time":arrival_date_time,
                                    "requested_date_time":requested_date_time,
                                    "departure_date_time":departure_date_time,
                                    "duration":duration_,
                                    "time_left":duration - duration_,
                                    "walkable_distance":(
                                            duration - duration_
                                            )*METERS_SECOND
                                    
                                    #TODO: ajouter durée restante à pied => duration - duration_ Pour les isos, voir notebook geoff boeing https://github.com/gboeing/osmnx-examples/blob/master/notebooks/13-isolines-isochrones.ipynb
                                    }
                            )
                    multis.append(pt)
                    
                    #Get pathes (linestring and nodes, modes)
                    #TODO: TRIER POUR ELIMINER LES DOUBLONS OU NE PAS LES INTEGRER
                    url_details = url + "&to=" + lon_to + ";" + lat_to
                    if (
                            self.option_journey is True
                            ) and (
                                    url_details not in self.urls
                                    ):
                        gdf_journeys_details = self.get_journey_details(
                                url_details,
                                headers,
                                param["inProj"],
                                duration,
                                from_place,
                                address
                                )
                        if gdf_journeys_details is not None:
                            l_gdf_journeys.append(gdf_journeys_details)
                            
                        self.urls.append(url_details)
                        
        
        if l_gdf_journeys != []:             
            gdf_journeys = pd.concat(l_gdf_journeys)  
        else:
            gdf_journeys = None
                
        collection = FeatureCollection(multis)
        gdf_pts = gpd.GeoDataFrame.from_features(collection['features'])
        gdf_pts.crs = {'init': param["inProj"]}
        
        return {
                "nodes":gdf_pts,
                "details":gdf_journeys
                }
    
    def get_journey_details(
            self, 
            url, 
            headers, 
            inproj, 
            duration, 
            from_place,
            address
            ):
        """
        
        """
        r = requests.get(url, headers=headers)
        code = r.status_code
        
        try:
            json_response = json.dumps(r.json())
            journey_json = geojson.loads(json_response)
        except: 
            raise ValueError("Error on:\n" + url)
        
        features = []
        
        if "journeys" in journey_json:
            for journey in journey_json["journeys"]:
                for section in journey["sections"]:
                    if "from" in section:
                        if "stop_point" in section["from"]:
        #                    print (section)
            #                lon_from = section["from"]["address"]["coord"]["lon"]
            #                lat_from = section["from"]["address"]["coord"]["lat"]
            #                name = section["from"]["name"]
            #                try:
            #                    physical_modes = section["to"]["stop_point"]["physical_modes"][0]["name"]
            #                except:
            #                    physical_modes = section["mode"]
                            
                            #Build line
                            if "display_informations" in section:
                                infos = section["display_informations"]
                            else:
                                infos = {
                                        "commercial_mode": "NR",
                                        "direction": "NR",
                                        "name": "NR"
                                        }
                            properties={
                                        "id":url,
                                        "mode":infos["commercial_mode"],
                                        "direction":infos["direction"],
                                        "name":infos["name"],
                                        "address_from":address,
                                        "duration":duration,
                                        "type":"line"
                                        }
                            line = Feature(
                                geometry=LineString(section["geojson"]["coordinates"]),
                                properties=properties
                                )
                            
                            if properties not in self.lines_properties:
                                features.append(line)
                                self.lines_properties.append(properties)
                            
                            #Build point
                            try:
                                lon_to = section["to"]["stop_point"]["coord"]["lon"]
                                lat_to = section["to"]["stop_point"]["coord"]["lat"]
                                name = section["to"]["stop_point"]["name"]
                                #TODO: MANQUE INFO POUR TRIER !!!!
                                properties={
                                                "id":url,
                                                "mode":infos["commercial_mode"],
                                                "direction":infos["direction"],
                                                "address_from":address,
                                                "duration":duration,
                                                "name":name,
                                                "type":"point"
                                                }
                                pt = Feature(
                                        geometry=Point((float(lon_to), float(lat_to))),
                                        properties=properties
                                        )
                                if properties not in self.pts_properties:
                                    features.append(pt)
                                    self.pts_properties.append(properties)
                            except:
                                pt = None
                        
        
        if features != []:
            gdf_features = gpd.GeoDataFrame.from_features(FeatureCollection(features))
            gdf_features.crs = {'init': inproj}
            gdf_features["duration"] = [duration for i in gdf_features["id"]]
            gdf_features["from_place"] = [from_place for i in gdf_features["id"]]
            
        else:
            gdf_features = None
            
        return gdf_features
    
    def polys_no_holes(self, durations, gdf):
        """
        
        """
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
        iso_cut = []
        iso_no_cut = []
        points = []
        details_pts = []
        details_lines = []
        
        l_all = [
                ("isochrones_cut",iso_cut), 
                ("isochrones_no_cut",iso_no_cut), 
                ("journeys_points",points), 
                ("journeys_details_pts",details_pts),
                ("journeys_details_lines",details_lines)
                ]
        
        dict_global = {
                "isochrones_cut":None,
                "isochrones_no_cut":None,
                "journeys_points":None,
                "journeys_details_points":None,
                "journeys_details_lines":None,
                }
        
        for param in self.params:
            self.option = param["option"]
            self.option_journey = param["option_journey"]
            self.option_isolines = param["option_isolines"]
            
            if self.option == "isochrones":
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
                iso_cut.append(gdf_param)
                iso_no_cut.append(gdf_param_filled)
                
                #Write GeoJSON by addresses
    #            name_isos = param["id"] + "_isos_by_addresses.geojson"
    #            name_isos = os.path.join(param["path"], name_isos)
    #            gdf_param.to_file(name_isos, driver="GeoJSON")
    #            
    #            #Write GeoJSON by duration
    #            ## Sort by durations
    #            gdf_param_filled.sort_values(["duration"], axis=1, inplace=True)
    #            
    #            ## Write files
    #            name_isos_durations = param["id"] + "_isos_by_durations.geojson"
    #            name_isos_durations = os.path.join(
    #                    param["path"], 
    #                    name_isos_durations
    #                    )
    #            gdf_param_filled.to_file(
    #                    name_isos_durations, 
    #                    driver="GeoJSON"
    #                    )
                
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
                
            
            elif self.option == "journeys":
                l_points = []
                l_journeys_pts = []
                l_journeys_lines = []
                
                for address in param["addresses"]:
                    from_place = self.places_cache[address]
                    from_place = str(from_place[0]) +";"+str(from_place[1])
                    dict_journeys = self.get_journeys(param, from_place, address)
                    l_points.append(dict_journeys["nodes"])
                    
                    if dict_journeys["details"] is not None:
                        l_journeys_pts.append(
                                dict_journeys["details"].loc[
                                        dict_journeys["details"]["type"] == "point"
                                        ]
                                )
                        l_journeys_lines.append(
                                dict_journeys["details"].loc[
                                        dict_journeys["details"]["type"] == "line"
                                        ]
                                )
                             
                points.append(pd.concat(l_points))
                if l_journeys_pts != []:
                    details_pts.append(pd.concat(l_journeys_pts))
                if l_journeys_lines != []:
                    details_lines.append(pd.concat(l_journeys_lines))
                    
        
        for i in l_all:
            if i[1] != []:
                gdf = pd.concat(i[1])
                gdf = gdf.reset_index()
                gdf.crs = {'init': param["inProj"]}
                gdf = gdf.to_crs({'init': param["outProj"]})
                dict_global[i[0]] = gdf
            else:
                dict_global[i[0]] = None
        
        return dict_global