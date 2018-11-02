# -*- coding: utf-8 -*-
"""
Created on Mon Oct 29 15:55:39 2018

@author: thomas
"""
from shapely.geometry import LineString, Polygon, MultiPolygon, Point, MultiPoint, MultiLineString
from shapely.geometry.polygon import LinearRing
from shapely.ops import nearest_points, transform
from functools import partial
import pyproj

    

class GetMiddleMultiPoly:
    def __init__(self, multis, ratio_diff):
        """
        @multis (list): list of Polygons or MultiPolygons
        @ratio_diff (float): Minimum ratio for "middle" calculation between
        all "secondary" polygons. If intersection(poly_A, poly_B).area/poly_A.area
        is inferior to or equal to this ratio, "middle" calculation is considered 
        possible. See self.get_diff_area
        """
        self.multis = multis
        self.ratio_diff = ratio_diff
        
    def iterate_for_middle(self):
        """
        
        """
        new_middle = self.middle_multi_poly(self.multis[0], self.multis[1])
        
        if len(self.multis) > 2:
            self.multis.remove(self.multis[0])
            self.multis.remove(self.multis[1])
            
            for i in self.multis:
                new_middle = self.middle_multi_poly(new_middle, i)
        
        return new_middle
    
    
    def get_multi_poly(self, spatial_object):
        """
        Transforms a polygon to multipolygon or raise an error if object is not
        either a Shapely Polygon or Shapely MultiPolygon
        """
        if isinstance(spatial_object, Polygon) is True:
            multi_poly = MultiPolygon([spatial_object])
        elif isinstance(spatial_object, MultiPolygon) is True:
            multi_poly = spatial_object
        else:
            raise ValueError(str(spatial_object) + " is not either Shapely Polygon or Shapely MultiPolygon instance")
        
        return multi_poly
        
    def _middle_ring(self, pts_within, pts_contains):
        """
        Get the middle ring of a polygon (or holes)
        
        @pts_within(list of tuples): list of coordinates
        @pts_contains(list of tuples): list of coordinates
        
        Returns coordinates of new "middle" object
        
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
    
    def middle_poly(self, poly_within, poly_contains):
        """
        Return the "middle" polygon from 2 input polygons
        
        @poly_within (Shapely Polygon): input Polygon
        @poly_contains (Shapely Polygon): input Polygon
        
        """
        #Get "middle" poly of outer ring
        new_outer_ring = self._middle_ring(
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
                                self._middle_ring(
                                        inner_within, 
                                        inner_contains
                                        )
                                )
                        list_interiors.append(coords)
        
        return Polygon(shell=new_outer_ring, holes=list_interiors).buffer(0) #add buffer(0) to avoid invalid geometry
    
    def get_major_poly(self, multi_poly):
        """
        Return the polygon (major) with the greatest area from a multipolygon
        
        @muli_poly (Shapely Multipoligon)
        
        """
        max_area=0
        
        for poly in multi_poly:
            if poly.area > max_area:
                max_area = poly.area
                major_poly = poly
        
        return major_poly.buffer(0) #add buffer(0) to avoid invalid geometry
                      
    
    def reproject(self, element, inproj, outproj):
        """
        Change the projection of a Shapely geometry
        
        @element (Shapely Geometry instance)
        @inproj (str): input projection, ex: "epsg:4326"
        @outproj (str): output projection, ex: "epsg:3857"
        
        Source: https://gis.stackexchange.com/a/127432
        """
        project = partial(
        pyproj.transform,
        pyproj.Proj(init=inproj),
        pyproj.Proj(init=outproj)) 
    
        return transform(project, element)
    
    def delete_inner_holes(self, multi_poly):
        """
        Delete inner holes of a multipolygon in order to make spatial operations
        (contains, within, intersects) possible
        
        Returns new Shapely MultiPolygon
        """
        l_polys = []
        for poly in multi_poly:
            l_polys.append(
                    Polygon(
                            poly.exterior,
                            []
                            )
                    )
        
        return MultiPolygon(l_polys)
    
    def middle_multi_poly(self, spatial_object_1, spatial_object_2):
        """
        @spatial_object_1 (Shapely MultiPolygon or Shapely Polygon)
        @spatial_object_2 (Shapely MultiPolygon or Shapely Polygon)
        
        Returns "middle" Shapely MultiPolygon
        """    
        self.multi_within = self.get_multi_poly(spatial_object_1)
        multi_contains = self.get_multi_poly(spatial_object_2)
        self.multi_contains = self.delete_inner_holes(multi_contains)
        
        self.polys = []
        
        #Get the majors poly and manage them first
        if len(list(self.multi_within)) > 1:
            self.major_within = self.get_major_poly(self.multi_within)
        else:
            self.major_within = self.multi_within[0]
            
        if len(list(self.multi_contains)) > 1:
            self.major_contains = self.get_major_poly(self.multi_contains) 
        else:
            self.major_contains = self.multi_contains[0]
        
        
        if (
                self.major_within.within(self.major_contains) is True
                ) or (
                        self.get_offset(self.major_within).within(self.major_contains) is True
                        ) :
            
            new_major_poly = self.middle_poly(self.major_within, self.major_contains)
            self.polys.append(new_major_poly)
        
            middle_multi = self.middle_secondary()
        
        else:
            if self.major_contains.intersects(self.major_within) is True:
                self.polys.append(self.middle_poly(self.major_within, self.major_contains))
                middle_multi = self.middle_secondary()
            else:
                middle_multi = MultiPolygon([])
                raise ValueError("No intersections, middle multipolygon can't be measured, returns empty MultiPolygon")
        
        return middle_multi
    
    def middle_secondary(self):
        for poly_within in self.multi_within:
            for poly_contains in self.multi_contains:
                if (
                        poly_within.within(poly_contains) is True 
                        or self.get_diff_area(poly_within, poly_contains) is True
                        )  and (
                                poly_contains != self.major_contains and poly_within != self.major_within
                                ):
                    self.polys.append(self.middle_poly(poly_within, poly_contains))
        
            middle_multi = MultiPolygon(self.polys)
            
        return middle_multi
        
    
    def get_offset(self, poly):
        """
        Get an offset polygon
        
        @poly (Shapely Polygon)
        
        Returns an offset Shapely Polygon
        """
        new_linear = LinearRing(poly.exterior.coords).parallel_offset(0.00001)
        
        if isinstance(new_linear, MultiLineString):
            new_poly = new_linear.convex_hull
        else:
            new_poly = Polygon(new_linear)
            
        return new_poly
    
    def get_diff_area(self, poly_A, poly_B):
        """
        Returns a boolean
        If difference between 2 polygons is inferior or equal to ratio, we 
        consider that we can make a "middle" polygon from them
        """
        middle_possible = False
        
        if poly_A.is_valid is False:
            poly_A = poly_A.buffer(0)
        elif poly_B.is_valid is False:
            poly_B = poly_B.buffer(0)
        else:
            if poly_A.difference(poly_B).area <= int(poly_A.area*self.ratio_diff):
                middle_possible = True
            
        return middle_possible