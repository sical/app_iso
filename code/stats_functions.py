# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 15:55:39 2018

@author: thomas
"""
from shapely.geometry import LineString, Polygon
from shapely.ops import nearest_points

def _middle_ring(pts_within, pts_contains):
    """
    
    """
    coords = []
    
    for pt in pts_within:
        nearest_pt = nearest_points(pt, pts_contains)
        coords.append(
                LineString(
                        [pt, nearest_pt]
                        ).interpolate(
                                0.5, 
                                normalized=True
                                )
                )
                
    return coords

def middle_poly(poly_within, poly_contains):
    """
    
    
    """
    #Get "middle" poly of outer ring
    new_outer_ring = _middle_ring(
            poly_within.exterior.coords,
            poly_contains.exterior.coords
            )
    
    #Check if inner rings and get "middle" holes
    if list(poly_within.interiors) != [] and list(poly_contains.interiors) != []:
        list_interiors = []
        for inner_within in poly_within:
            for inner_contains in poly_contains:
                if Polygon(inner_within).within(Polygon(poly_contains)) is True:
                    coords = Polygon(
                            _middle_ring(
                                    inner_within, 
                                    inner_contains
                                    )
                            )
                    list_interiors.append(coords)
    
    return Polygon(shell=new_outer_ring, holes=list_interiors)

def get_major_poly(multi_poly):
    """
    
    """
    max_area=0
    
    for poly in multi_poly:
        if poly.area > max_area:
            max_area = poly.area
            major_poly = poly
    
    return major_poly
                  

def middle_multi_poly(multi_within, multi_contains):
    """
    
    """
    #Get the majors poly and manage them first
    major_within = get_major_poly(multi_within)
    major_contains = get_major_poly(multi_contains)
    
    
    
    for poly_within in multi_within:
        for poly_contains in multi_contains:
            if poly_within.within(poly_contains) is True and 
    