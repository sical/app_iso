# -*- coding: utf-8 -*-
"""
Created on Thu May 31 15:28:44 2018

@author: thomas
"""

import math
import os
import pandas as pd
import geopandas as gpd
from tabulate import tabulate as tb
import numpy as np
    

def get_notches(poly):
    """
    Determine the number of notches in a polygon object and calculate 
    normalized notches of polygon
    
    Based on: 
        "Measuring the Complexity of Polygonal Objects" 
        (Thomas Brinkhoff, Hans-Peter Kriegel, Ralf Schneider, Alexander Braun)
        http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
        
        https://github.com/pondrejk/PolygonComplexity/blob/master/PolygonComplexity.py
        
    @poly (Shapely Polygon object)
    
    Returns normalized notches
    """
    notches = 0 
    coords = poly.exterior.coords
    for i, pt in enumerate(coords[:-1]):
#        x_diff = coords[i+1][0] - pt[0]
#        y_diff = coords[i+1][1] - pt[1]
#        angle = math.atan2(y_diff, x_diff)
#        angle = np.arctan2(x_diff, y_diff)
        
        x1,x2,y1,y2 = pt[0], coords[i+1][0], pt[1], coords[i+1][1] 
        
        dX = x2 - x1
        dY = y2 - y1
        
        angle = math.atan2(-dY, dX)
        
        print (angle, math.degrees(angle))
        
#        dot = x1*x2 + y1*y2
#        det = x1*y2 - y1*x2
#        
#        angle = math.atan2(det,dot)
#        print (dot, det, angle)
#        print (y_diff, x_diff, angle, math.pi, notches)
        
        if (angle > math.pi) or (angle < -math.pi): #PB ICI: COMPRENDRE CE QUE VALENT LES VALEURS NEGATIVES
            print ("YOUPI\n===========================")
            notches += 1
            
    if notches != 0:
        notches_norm = notches / (len(coords)-3)
    else:
        notches_norm = 0 
        
#    print (notches, notches_norm)
        
    return notches_norm

def get_stats(gdf, coeff_ampl, coeff_conv):
    """
    Get polygon's amplitude of vibration:
    
    ampl(pol) = (boundary(pol) - boundary(convexhull(pol))) / boundary(pol)
    
    Get deviation from convex hull:
    conv(pol) = (area(convexhull(pol)) - area(pol)) / area(convexhull(pol))
    
    Measure complexity
    
     Based on: 
        "Measuring the Complexity of Polygonal Objects" 
        (Thomas Brinkhoff, Hans-Peter Kriegel, Ralf Schneider, Alexander Braun)
        http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
        
        https://github.com/pondrejk/PolygonComplexity/blob/master/PolygonComplexity.py
    
    Get area, centroid, distance from each others, boudary, convex hull, 
    perimeter, number of vertices
    
    @param gdf(GeoDataframe): geodataframe with polygons
    @param coeff_ampl(float): coefficient for amplitude's calculation
    @param coeff_conv(float): coefficient for deviation from convex hull calculation
    
    Returns tuple with dict of stats values and GeoDataframe with stats
    
    """
    nb = gdf['geometry'].count()
    gdf['area'] = gdf['geometry'].area
    tot_area = gdf['area'].sum()
    gdf['centroid'] = gdf['geometry'].centroid
#    gdf['distance'] = gdf['geometry'].distance()
    gdf['boundary'] = gdf['geometry'].boundary
    gdf['convex_hull'] = gdf['geometry'].convex_hull
    gdf['convex_boundary'] = gdf['geometry'].convex_hull.boundary
    gdf['convex_area'] = gdf['geometry'].convex_hull.area
    gdf['nbvertices'] = gdf['geometry'].apply(lambda x: len(list(x.exterior.coords)))
    gdf['notches'] = gdf['geometry'].apply(lambda x: get_notches(x))
    
    gdf['amplitude'] = gdf.apply(
            lambda x:(
                    x['boundary'].length - x['convex_boundary'].length
                    ) / x['boundary'].length, 
                    axis=1)
            
    gdf['convex'] = gdf.apply(
            lambda x: (
                    x['convex_area'] - x['area']
                    ) / x['convex_area'],
                    axis=1)
            
    gdf['freq'] = gdf.apply(
            lambda x: 16*(x['notches'] - 0.5)**4 - 8*(x['notches'] - 0.5)**2 + 1,
            axis=1
            )
    
    #OLD VERSION
#    gdf['complexity'] = gdf.apply(
#            lambda x: coeff_ampl*x['amplitude'] * x['notches'] + coeff_conv * x['convex'],
#            axis=1
#            )
    
    gdf['complexity'] = gdf.apply(
            lambda x: coeff_ampl*x['amplitude'] * x['freq'] + coeff_conv * x['convex'],
            axis=1
            )
    
    mean_amplitude = gdf['amplitude'].mean()
    mean_convex = gdf['convex'].mean()
    mean_norm_notches = gdf['notches'].mean()
    mean_complexity = gdf['complexity'].mean()
    
    gdf['perimeter'] = gdf['geometry'].length
    tot_perimeter = gdf['perimeter'].sum()
    
    if ("lat" in gdf.columns) or ("lon" in gdf.columns):
        columns_drop = ["boundary", "convex_hull", "convex_boundary", "convex_area", "centroid", "lat", "lon"]
    else:
        columns_drop = ["boundary", "convex_hull", "convex_boundary", "convex_area", "centroid"]
    gdf = gdf.drop(columns_drop, axis=1)
    
    gdf = gdf.reset_index()
    
#    print ("###########################")
##    print (gdf)
##    print ("=========================")
##    if nb > 1:
##        gdf = gdf.sort_values(by='perimeter', ascending=False)
##        gdf = gdf.iloc[[0]]s
#    
#    print (gdf)
#    print ("###########################")
    
    return {
            'area':tot_area,
            'perimeter':tot_perimeter,
#            'distance':mean_distance,
            'nb':nb,
            'amplitude': mean_amplitude,
            'convex': mean_convex,
            'notches': mean_norm_notches,
            'complexity': mean_complexity
            }, gdf
            
def complexity(shapes, coeff_ampl, coeff_conv, images=None, str_img=None):
    """
    @param shapes(): glob directory with shapefiles
    @param images(): glob directory with image files
    @param coeff_ampl(float): coefficient for amplitude's calculation
    @param coeff_conv(float): coefficient for deviation from convex hull calculation 
    @param str_img(str): string of image filepath
    
    Returns all Polygons with stats in a GeoDatafame
    """
    l_gdf = []
    pd.options.display.float_format = '{:,.2f}'.format
    dico = {}
    
    for shape in shapes:
        shape_name = os.path.basename(shape).split(".")[0]
        print ("SHAPE", shape_name)
        gdf = gpd.GeoDataFrame.from_file(shape)
        dict_complexity, gdf = get_stats(gdf, coeff_ampl, coeff_conv)
        name = os.path.basename(shape)
        name = name.replace(".shp","")
        gdf['name'] = name
        gdf['img'] = ''
#        gdf = img_str(gdf, images, name, str_img)
        
        gdf = gdf.drop('geometry', axis=1)
        l_gdf.append(gdf)
        
        dico[shape_name] = dict_complexity 
        
        print ("####################################")
    
    gdf_tot = pd.concat(l_gdf)
    
    return gdf_tot, dico

def img_str(x, str_img):
    x["img"] = str_img.format(x["name"])
    
    return x
                
def to_table(df, tablefmt, filename, str_img):
    """
    Export dataframe to a table file with a specific format
    (see tabulate doc for more information: 
        https://pypi.org/project/tabulate/):
        - "plain"
        - "simple"
        - "grid"
        - "fancy_grid"
        - "pipe"
        - "orgtbl"
        - "jira"
        - "presto"
        - "psql"
        - "rst"
        - "mediawiki"
        - "moinmoin"
        - "youtrack"
        - "html"
        - "latex"
        - "latex_raw"
        - "latex_booktabs"
        - "textile"
        
    @param df(dataframe): dataframe with stats and img
    @tablefmt(str): format of the table
    @filename(str): path and name to file
    """
    df = df.apply(lambda x: img_str(x, str_img), axis=1)
    
    f = open(filename, 'w')
    f.write(tb(
            df, 
            headers="keys", 
            showindex=False, 
            tablefmt=tablefmt
            ))
    f.close()