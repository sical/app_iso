# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 15:55:39 2018

@author: thomas
"""
from shapely.geometry import LineString, Polygon, MultiPolygon, Point, MultiPoint
from shapely.geometry.polygon import LinearRing
from shapely.ops import nearest_points, transform
from functools import partial
import pyproj


def _middle_ring(pts_within, pts_contains):
    """
    
    See also: https://automating-gis-processes.github.io/2017/lessons/L3/nearest-neighbour.html
    """
    coords = []
    pts_within = [Point(pt) for pt in pts_within]
    pts_contains = MultiPoint([Point(pt) for pt in pts_contains])
    
    for pt in pts_within:
        nearest_pt = nearest_points(pt, pts_contains)
        pt_to_add = LineString(
                        [nearest_pt[0], nearest_pt[1]]
                        ).interpolate(
                                0.5, 
                                normalized=True
                                )
        coords.append((pt_to_add.x, pt_to_add.y))
                
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
    list_interiors = []
    if list(poly_within.interiors) != [] and list(poly_contains.interiors) != []:
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
                  

def reproject(element, inproj, outproj):
    """
    Source: https://gis.stackexchange.com/a/127432
    """
    project = partial(
    pyproj.transform,
    pyproj.Proj(init=inproj),
    pyproj.Proj(init=outproj)) 

    return transform(project, element)

def delete_inner_holes(multi_polys):
    """
    
    """
    l_polys = []
    for poly in multi_polys:
        if list(poly.interiors) != []:
            l_polys.append(
                    Polygon(
                            poly.exterior,
                            []
                            )
                    )
    
    return MultiPolygon(l_polys)

def middle_multi_poly(multi_within, multi_contains, epsg):
    """
    
    """    
    multi_contains = delete_inner_holes(multi_contains)
    
    polys = []
    #Get the majors poly and manage them first
    major_within = get_major_poly(multi_within)
    major_contains = get_major_poly(multi_contains)
    
    
    if major_within.within(major_contains) is True:
        new_major_poly = middle_poly(major_within, major_contains)
        polys.append(new_major_poly)
        
        for poly_within in multi_within:
            for poly_contains in multi_contains:
                if poly_within.within(poly_contains) is True and (poly_contains != major_contains and poly_within != major_within):
                    polys.append(middle_poly(poly_within, poly_contains))
    
        middle_multi = MultiPolygon(polys)
    
    else:
        try:
            if get_offset(major_within).within(major_contains) is True:
                new_major_poly = middle_poly(major_within, major_contains)
                polys.append(new_major_poly)
        except ValueError:
            print ("Major polygon of greater multipolygon does not contain the major polygone of smaller multipolygon")
            middle_multi = MultiPolygon([])
    
    return middle_multi
    

def get_offset(poly):
    """
    
    """
    return Polygon(LinearRing(poly.exterior.coords).parallel_offset(0.00001))
