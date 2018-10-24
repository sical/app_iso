# -*- coding: utf-8 -*-
"""
Created on Wed Oct 24 13:40:27 2018

@author: thomas
"""

import math
from shapely.geometry import Polygon, MultiPolygon

def get_thinness_ratio(poly):
    """
    Source: https://math.stackexchange.com/a/2914366
    """
    return (4*math.pi * poly.area)/(poly.length*poly.length)

def fill_holes_major_poly(multipoly):
    #Get major poly
    max_area = 0
    multis = [poly for poly in multipoly]
    
    #Check area and thinness ratio (https://math.stackexchange.com/a/2914366)
    for poly in multis:
        if list(poly.interiors) != []:            
            if poly.area > max_area:
                max_area = poly.area
                poly_to_fill = poly
                index_ = multis.index(poly)
            
    #Delete major hole in this poly
    if max_area != 0:
        poly_filled = delete_major_poly(poly_to_fill)
        multis[index_] = poly_filled
    
    #Check thinness ratio (https://math.stackexchange.com/a/2914366
    for poly in multis:
        if list(poly.interiors) != []:
            index_new_geom = multis.index(poly)
            multis[index_new_geom] = delete_inner_poly(poly)
    
    return MultiPolygon(multis)
            

def delete_major_poly(geom):
    max_area = 0 
    
    list_interiors = list(geom.interiors)
    for inner_ring in list_interiors:
        area = Polygon(inner_ring.coords).area
        if area > max_area:
            max_area = area
            index_ = list_interiors.index(inner_ring)
    
    del list_interiors[index_]
    
    return Polygon(shell=geom.exterior, holes=list_interiors)

def delete_inner_poly(geom):
    list_interiors = []

    for inner_ring in geom.interiors:
        if get_thinness_ratio(Polygon(inner_ring)) < 0.55:
            list_interiors.append(inner_ring)
    
    return Polygon(shell=geom.exterior, holes=list_interiors)