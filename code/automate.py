# -*- coding: utf-8 -*-
"""Automate
Usage: automate.py  [<infile_csv>] [<outfile_json>] [<separator>]


Arguments:
  infile_csv        input file name (tsv or csv format) path, ex: ./params/params.tsv
  outfile_json      output json file name path, ex: ./params/params.json
  separator         separator used in the csv/tsv file
    
@author: thomas
"""
from datetime import date
import os
import itertools

from bokeh.io import export_png, export_svgs
from bokeh.tile_providers import STAMEN_TONER, STAMEN_TERRAIN_RETINA
from bokeh.models import ColumnDataSource
from dotenv import load_dotenv
from pathlib import Path
import json
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta as rd
from pyproj import transform, Proj
import imageio
import numpy as np
import progressbar
from docopt import docopt
import warnings

warnings.filterwarnings('ignore')

from get_iso import get_iso, overlay
from make_plot import make_plot
from functions import geocode, colors_blend, hex2rgb, buffer_point, create_buffers, str_list_to_list
from csv_to_json import csv_to_json

columns_with_array_of_str = ["colors_iso","adresses","buffer_times","buffer_opacity","buffer_color","buffer_contour_size"]


def change_color(source):
        #Give each polygon a unique color
        l_colors = []
        nb = len(source.data['color'])
        
        if nb != 0:
            r,g,b = hex2rgb(source.data['color'][0])
            
            if r + nb >= 255:
                for i in range(0, nb):
                    new_color = r - i, g, b
                    new_color = colors_blend(new_color, new_color)
                    l_colors.append(new_color)
                
            else:
                for i in range(0, nb):
                    new_color = r + i, g, b
                    new_color = colors_blend(new_color, new_color)
                    l_colors.append(new_color)
            
            source.data['color'] = np.array(l_colors)
        
        return source
    
    
def pairwise(iterable):
    """
    source: https://stackoverflow.com/questions/5434891/iterate-a-list-as-pair-current-next-in-python
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    
    return zip(a, b)  

def run(params_iso,x,y,adress, color):
    global counter_polys
    global counter_lines
    global counter_points
    global counter_intersection
    global p_shape
    global gdf_poly_mask
    global alert
    
    data = get_iso(params_iso, gdf_poly_mask, id_)
    gdf_poly_mask = data['gdf_poly_mask']

    source = data['source']
    shape = data['shape']
    data_intersection = data['intersection']
    status = data['status']
    gdf_poly = data['gdf_poly']
    source_buffer = data['source_buffer']
    source_convex = data['source_convex']
    source_envelope = data['source_envelope']
    source_simplified = data['source_simplified']
    
    list_gdf.append(gdf_poly)
    
    #Give each polygon a unique color
    if step_mn == 0:
        source = change_color(source)
        data_intersection = change_color(data_intersection)
        
        #DataSource to dict
        dict_source = {}
        for key,value in source.data.items():
            if type(value) is np.ndarray:
                new_value = value.tolist()
                dict_source[key] = new_value
            else:
                dict_source[key] = value
                
        dict_intersection = {}
        for key,value in source_intersection.data.items():
            if type(value) is np.ndarray:
                new_value = value.tolist()
                dict_intersection[key] = new_value
            else:
                dict_intersection[key] = value
    
    else:
        dict_source = {}
        dict_intersection = {}
        
    
    if source is None:
        shape = ""
    
#        source_intersection.data.update(data_intersection.data)
        
    if step_mn == 0:
        color = 'color' 
        

    if shape == "poly":
        name = "polys" + str(counter_polys)
        options_iso_surf = dict(
                fill_color=color, 
                fill_alpha = params_iso['opacity_iso'],
                line_color='white', 
                line_alpha=0.0,
                line_width=params["fig_params"]["line_width_surf"], 
                source=source,
                legend="Isochrone_polys" + str(counter_polys)
                )
        
        poly_patches = p_shape.patches(
            'xs', 
            'ys', 
            **options_iso_surf,
            name=name
            )
        
        counter_polys += 1 
        
        ###########################################################
        # SIMPLIFIED VERSIONS
        ###########################################################
        # Convex_hull polygons
        if simplify == "convex" and source_convex is not None:
            options_iso_convex = dict(
                    fill_color = options_iso_surf['fill_color'], 
                    fill_alpha = options_iso_surf['fill_alpha'],
                    line_color='white', 
                    line_alpha = 0.0,
                    line_width=params["fig_params"]["line_width_surf"], 
                    source=source_convex,
                    legend=name + " (convex)"
                    )
            
            poly_convex = p_shape.patches(
                'xs', 
                'ys', 
                **options_iso_convex,
                name=name + " (convex)"
                )
        
        # Envelope polygons
        if simplify == "envelope" and source_envelope is not None:
            options_iso_envelope = dict(
                    fill_color = options_iso_surf['fill_color'], 
                    fill_alpha = options_iso_surf['fill_alpha'],
                    line_color='white', 
                    line_alpha = 0.0,
                    line_width=params["fig_params"]["line_width_surf"], 
                    source=source_envelope,
                    legend=name + " (envelope)"
                    )
        
            poly_envelope = p_shape.patches(
                'xs', 
                'ys', 
                **options_iso_envelope,
                name=name + " (envelope)"
                )
            
        # Simplified polygons
        if simplify == "simplify" and source_simplified is not None:
            options_iso_simplified = dict(
                    fill_color = options_iso_surf['fill_color'], 
                    fill_alpha = options_iso_surf['fill_alpha'],
                    line_color='white', 
                    line_alpha = 0.0,
                    line_width=params["fig_params"]["line_width_surf"], 
                    source=source_simplified,
                    legend=name + " (simplified)"
                    )
            
            poly_simplified = p_shape.patches(
                'xs', 
                'ys', 
                **options_iso_simplified,
                name=name + " (simplified)"
                )
        ###########################################################
        
    elif shape == "line":
        name = "lines"  + str(counter_lines)
        options_iso_contours = dict(
                line_color=color, 
                line_alpha = opacity_iso,
                line_width=params["fig_params"]["line_width_cont"], 
                source=source,
                legend="Isochrone_lines" + str(counter_lines)
                )
        
        p_shape.multi_line(
            'xs', 
            'ys', 
            **options_iso_contours,
            name=name
            )
        
        counter_lines += 1
        
        ###########################################################
        # SIMPLIFIED VERSIONS
        ###########################################################
        
        # Convex_hull polygons
        if simplify == "convex" and source_convex is not None:
            options_iso_convex = dict(
                    line_color = options_iso_surf['line_color'], 
                    line_alpha = options_iso_surf['line_alpha'],
                    line_width=params["fig_params"]["line_width_cont"], 
                    source=source_convex,
                    legend="Iso_convex_" + str(counter_polys)
                    )
            
            poly_convex = p_shape.multi_line(
                'xs', 
                'ys', 
                **options_iso_convex,
                name=name + " (convex)"
                )
        
        # Envelope polygons
        if simplify == "envelope" and source_envelope is not None:
            options_iso_envelope = dict(
                    line_color = options_iso_surf['line_color'], 
                    line_alpha = options_iso_surf['line_alpha'],
                    line_width=params["fig_params"]["line_width_cont"],  
                    source=source_envelope,
                    legend=name + " (envelope)"
                    )
            
            poly_envelope = p_shape.multi_line(
                'xs', 
                'ys', 
                **options_iso_envelope,
                name=name + " (envelope)"
                )
            
        
        # Simplified polygons
        if simplify == "simplify" and source_simplified is not None:
            options_iso_simplified = dict(
                    line_color = options_iso_surf['line_color'], 
                    line_alpha = options_iso_surf['line_alpha'],
                    line_width=params["fig_params"]["line_width_cont"], 
                    source=source_simplified,
                    legend=name + " (simplified)"
                    )
            
            poly_simplified = p_shape.multi_line(
                'xs', 
                'ys', 
                **options_iso_simplified,
                name=name + " (simplified)"
                )
        ###########################################################
        
    elif shape == "point":
        name="points"  + str(counter_polys)
        options_iso_pts = dict(
                color=color,
                alpha = opacity_iso,
                line_width=params["fig_params"]["line_width_surf"], 
                size=3,
                source=source,
                legend="Isochrone_points" + str(counter_points),
                name="intersection"
                )
        
        p_shape.circle(
            'x', 
            'y', 
            **options_iso_pts,
            name="points"  + str(counter_polys)
            )
        
        counter_points += 1
        
        
    if data_intersection is not None:
#        name = "Intersection" + str(counter_intersection)
#        source_intersection = data_intersection
        name = "Overlay"
        source_intersection.data.update(data_intersection.data)
        options_intersect = dict(
#                fill_alpha= params["fig_params"]["alpha_surf"], 
    #            fill_color={'field': params["fig_params"]["field"], 'transform': color_mapper}, 
                source=source_intersection,
                fill_color='color',
                fill_alpha=params_iso['opacity_intersection'],
                line_color='white', 
                line_alpha=0.0,
                line_width=params["fig_params"]["line_width_surf"], 
#                fill_color="black", 
#                fill_alpha = 0.70,
#                line_color="black", 
#                line_width=params["fig_params"]["line_width_surf"], 
                legend=name
                )
        
        intersections = p_shape.patches(
                                        'xs', 
                                        'ys', 
                                        **options_intersect
                                        )
        counter_intersection += 1
        
    #Draw buffer radar
    if buffer_radar == 1:    
        if source_buffer is not None:
            buffer_name = "Buffer_" + name
        #    source_intersection = data_intersection
            
            
            options_buffer = dict(
                    source=source_buffer,
                    fill_color="grey",
                    fill_alpha=0.0,
                    line_color='color',
                    line_width='width',
                    line_alpha=1.0, 
                    legend=buffer_name
                    )
            
            buffer = p_shape.patches(
                                    'xs', 
                                    'ys', 
                                    **options_buffer
                                    )
    #Draw only buffers
    
    
    p_shape.legend.location = "top_right"
    p_shape.legend.click_policy="hide"
    p_shape.legend.visible = False
    
    return p_shape, dict_source, dict_intersection

###################################################
###################################################
###################################################
###################################################
###################################################
###################################################

if __name__ == "__main__":

    #Parameters
    try:
        env_path = Path('./') / '.env'
        load_dotenv(dotenv_path=env_path)
        TOKEN = os.getenv("NAVITIA_TOKEN")
    except:
        TOKEN = os.getenv("NAVITIA_TOKEN")
        
    params = "./params/params.json"
    params = json.load(open(params))

    fmt = 'Elapsed time: {0.minutes} minutes {0.seconds} seconds'
    
    #Projections
    inProj = params["proj"]["inProj"]
    outProj = params["proj"]["outProj"]
    
    #Default
    default = "./params/default.json"
    default = json.load(open(default))
    #output_png = "./output_png/tests/"
    from_place = default["from_place"]
    adress = default["adress"]
    time_ = default["time_"]
    step = default["step"]
    nb_iter = default["nb_iter"]
    year_min = default["year_min"]
    month_min = default["month_min"]
    day_min = default["day_min"]
    year_max = default["year_max"]
    month_max = default["month_max"]
    day_max = default["day_max"]
    counter_polys = 0 
    counter_lines = 0 
    counter_points = 0 
    counter_intersection = 0 
    alert = """<span style="color: red"><b>{}</b></span>"""
    selected = False
    old_selections = []
    list_gdf = []
    coeff_ampl = 0.8 # See Brinkhoff et al. paper
    coeff_conv = 0.2 # See Brinkhoff et al. paper
    
    export_auto = True
    anim = False
    
    #Set range date
    min_date = date(year_min, month_min, day_min)
    max_date = date(year_max, month_max, day_max)
    
    #Set ColumnDataSource
    source_poly = {}
    
    #Set intersections
    gdf_poly_mask = None
    
    
    #JSON INPUT
    arguments = docopt(__doc__)
    infile = arguments["<infile_csv>"]
    outfile = arguments["<outfile_json>"]
    sep = arguments["<separator>"]
    json_file = csv_to_json(infile, outfile, sep, columns_with_array_of_str)
#    json_file = "./params/params_auto.json"
    params_auto = json.load(open(json_file, encoding='utf-8'))

    source_iso = ColumnDataSource(
            data=dict(
                    xs=[], 
                    ys=[], 
                    adress=[],
                    time=[],
                    duration=[], 
                    color=[],
                    date=[],
                    shape=[],
                    area=[],
                    perimeter=[],
                    nb_componants=[],
                    amplitude=[],
                    convex=[],
                    norm_notches=[],
                    complexity=[]
                    )
            )
            
    TOOLS = ""
    
    #export_no_tiles = "./output_png/tests/no_tiles/"
    #export_with_tiles = "./output_png/tests/with_tiles/"
    #export_anim = "./output_png/tests/animation/"
    
    params_plot = {
                'params':params, 
                'tools':TOOLS,
    #            'buildings':buildings,
    #            'network':network,
                'tile_provider':None,
                'source_iso': source_iso,
                'title': ""
                }
    
    p_shape = make_plot(params_plot)
    
    #Add origin points
    source_origins = ColumnDataSource(
            data=dict(
                    x=[], 
                    y=[],
                    adress=[]
                    )
            )
    
    source_intersection = ColumnDataSource(
            data=dict(
                    xs=[], 
                    ys=[], 
                    time=[],
                    color=[],
                    area=[],
                    perimeter=[],
                    amplitude=[],
                    convex=[],
                    norm_notches=[],
                    complexity=[]
                    )
            )
            
    #Buffers solo
#    source_buffers = ColumnDataSource(
#            data=dict(
#                    xs=[], 
#                    ys=[], 
#                    times=[],
#                    colors=[],
#                    width=[],
#                    fill_alpha=[],
#                    radius = []
#                    )
#            )

    
    #PROGRESS BAR##################
    widgets=[
        ' [',progressbar.ETA(), '] ',
        progressbar.Bar(),
        progressbar.Percentage(),
    ]
    
    bar = progressbar.ProgressBar(max_value=len(params_auto), redirect_stdout=True)
    ################################
    
    if export_auto is True:
        start_time = time.time()
        for i,param in enumerate(params_auto):
            how = param["how"]
            colors_iso = param["colors_iso"]
            color_switch = param["colors_intersection"]
            if color_switch == "None":
                color_switch = None
            region_id = param["region_id"]
            date_value = param["date"]
            date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
            adresses = param["adresses"]
            time_value = param["time"]
            duration = param["duration"]
            id_ = param["region_id"]
            step_value = int(param["duration"]) * 60
            opacity_iso = param["opacity_isos"]
            opacity_intersection = param["opacity_intersection"]
            shape = param["shape"]
            identity = param["id"]
            buffer_radar = param["buffer_radar"]
            step_mn = param["step"]
            simplify = param["simplify"]
            try:
                around = param["around"].split(',')
                around = [int(around[0]), int(around[1])]
            except:
                around = []
            origine_screen = param["origine_screen"]	
            only_buffer = param["only_buffer"]	
            buffer_times = param["buffer_times"]	
            buffer_opacity = param["buffer_opacity"]	
            buffer_color = param["buffer_color"]	
            buffer_contour_size = param["buffer_contour_size"]
            export_no_tiles = param["export_no_tiles"]
            export_with_tiles = param["export_with_tiles"]
            export_anim = param["export_anim"]
            
            
            l_dict_iso = []
            
            gdf_poly_mask = None
            
            counter_polys = 0
            counter_lines = 0
            counter_points = 0
            counter_intersection = 0
            
            x = []
            y = []
            l_adress = []
            l_colors = colors_iso
            
            epsg_in = Proj(init=inProj)
            epsg_out = Proj(init=outProj)
            
            if only_buffer == 1: #Do only buffers, no isochrones
                epsg_in = Proj(init=inProj)
                epsg_out = Proj(init=outProj)
                places = [geocode(adress) for adress in adresses]
                colors = buffer_color
                opacities = buffer_opacity
                times = str_list_to_list(buffer_times)
                contours = str_list_to_list(buffer_contour_size)
                
                l_colors = colors
                
                for adress,place,opacity,time_,contour in zip(
                        adresses,
                        places,
                        opacities,
                        times,
                        contours
                        ):
                    index_color = adresses.index(adress)
                    color = colors[index_color]
                    fill_colors = [color for x in time_]
                    
                    x_, y_ = transform(epsg_in,epsg_out,place[0],place[1]) 
                    x.append(x_)
                    y.append(y_)
                    l_adress.append(adress)

                    params_buffers = {
                            "inproj":epsg_in,
                            "outproj":epsg_out,
                            "colors":fill_colors,
                            "opacities":opacity,
                            "times":time_,
                            "contours":contour,
                            "from_place":place
                            }

                    source_buffers = create_buffers(params_buffers)
                    
                    options_buffers = dict(
                            source=source_buffers,
                            fill_color='colors',
                            fill_alpha='fill_alpha',
                            line_color='colors',
                            line_width="width"
#                            line_alpha=1.0,
                            )
                    
                    p_shape.patches(
                                    xs='xs', 
                                    ys='ys', 
                                    **options_buffers
#                                    legend=adress
                                    )
                    
                p_shape.legend.location = "top_right"
                p_shape.legend.click_policy="hide"
                p_shape.legend.visible = False
                        
            else:
                if around != []:
                    for adress in adresses:
                        index_list = adresses.index(adress)
                        color = colors_iso[index_list]
                        
                        from_place = geocode(adress)
                        
                        places = buffer_point(from_place, epsg_in, epsg_out, around[0], around[1])
                        
                        for place in places:
                        
                            x_, y_ = transform(epsg_in,epsg_out,place[0],place[1]) 
                            x.append(x_)
                            y.append(y_)
                            l_adress.append(adress)
                            from_place = str(place[0]) + ";" + str(place[1])
                        
                            params_iso = {
                                'token': TOKEN,
                                'from_place': from_place,
                                'time_in': time_value,
                                'min_date': date_value,
                                'step': step_value,
                                'step_mn': step_mn,
                                'nb_iter': 1,
                                'shape': shape,
                                'inProj': inProj,
                                'outProj': outProj,
                                'how': how,
                                'color':color,
                                'color_switch': color_switch,
                                'opacity_intersection':opacity_intersection,
                                'opacity_iso':opacity_iso,
                                'tolerance': None
                                
                                    }     
                            
                            p_shape, dict_source, dict_intersection = run(params_iso, x,y,l_adress,color)
                            
                            if step_mn == 0:
                                del dict_source['xs']
                                del dict_source['ys']
                                del dict_intersection['xs']
                                del dict_intersection['ys']
                                l_dict_iso.append(dict_source)
                            
                else:
                    for adress in adresses:
                        index_list = adresses.index(adress)
                        color = colors_iso[index_list]
                        
                        from_place = geocode(adress)
                        
                        x_, y_ = transform(epsg_in,epsg_out,from_place[0],from_place[1]) 
                        x.append(x_)
                        y.append(y_)
                        l_adress.append(adress)
                        from_place = str(from_place[0]) + ";" + str(from_place[1])
                    
                        params_iso = {
                            'token': TOKEN,
                            'from_place': from_place,
                            'time_in': time_value,
                            'min_date': date_value,
                            'step': step_value,
                            'step_mn': step_mn,
                            'nb_iter': 1,
                            'shape': shape,
                            'inProj': inProj,
                            'outProj': outProj,
                            'how': how,
                            'color':color,
                            'color_switch': color_switch,
                            'opacity_intersection':opacity_intersection,
                            'opacity_iso':opacity_iso,
                            'tolerance': None
                            
                                }     
                        
                        p_shape, dict_source, dict_intersection = run(params_iso, x,y,l_adress, color)
                        
                        if step_mn == 0:
                            del dict_source['xs']
                            del dict_source['ys']
                            del dict_intersection['xs']
                            del dict_intersection['ys']
                            l_dict_iso.append(dict_source)
        
            #EXPORT NO_TILES PNG
            name = export_no_tiles + identity
            export_png(p_shape, filename="{}.png".format(name))
            
            #EXPORT PARAMS TO JSON
            params_name = export_no_tiles + identity + "_params"
            json_name = filename="{}.json".format(params_name)
            with open(json_name, 'w', encoding='utf-8') as outfile:
                json.dump(param, outfile, sort_keys=True, indent=2)
              
            #EXPORT ISOS TO JSON
            if l_dict_iso != []:
                iso_name = export_no_tiles + identity + "_iso"
                json_name = filename="{}.json".format(iso_name)
                with open(json_name, 'w', encoding='utf-8') as outfile:
                    json.dump(l_dict_iso, outfile, sort_keys=True, indent=2)
                
                #EXPORT OVERLAY TO JSON
                overlay_name = export_no_tiles + identity + "_overlay"
                json_name = filename="{}.json".format(overlay_name)
                with open(json_name, 'w', encoding='utf-8') as outfile:
                    json.dump(dict_intersection, outfile, sort_keys=True, indent=2)
            
            #EXPORT WITH_TILES PNG
            #Add origins points
            if origine_screen == 1:
                data = dict(
                            x=x,
                            y=y,
                            adress=l_adress,
                            color=l_colors
                            )
                source_origins.data.update(data)
                
                poly_circles = p_shape.circle(
                    'x', 
                    'y', 
                    source=source_origins,
                    fill_color='color', 
                    fill_alpha = 1.0,
                    size=10,
                    line_color='black',
                    line_alpha=1.0,
                    line_width=1.0, 
                    legend="Origins"
                        )
            
            p_shape.add_tile(STAMEN_TERRAIN_RETINA, alpha=params["fig_params"]["alpha_tile"], name="tile")
            
            name = export_with_tiles + identity
            export_png(p_shape, filename="{}.png".format(name))
                
            #EXPORT PARAMS TO JSON
            params_name = export_with_tiles + identity + "_params"
            json_name = filename="{}.json".format(params_name)
            with open(json_name, 'w', encoding='utf-8') as outfile:
                json.dump(param, outfile, sort_keys=True, indent=2)
                
            #EXPORT ISOS TO JSON
            if l_dict_iso != []:
                iso_name = export_with_tiles + identity + "_iso"
                json_name = filename="{}.json".format(iso_name)
                with open(json_name, 'w', encoding='utf-8') as outfile:
                    json.dump(l_dict_iso, outfile, sort_keys=True, indent=2)
                
                #EXPORT OVERLAY TO JSON
                overlay_name = export_with_tiles + identity + "_overlay"
                json_name = filename="{}.json".format(overlay_name)
                with open(json_name, 'w', encoding='utf-8') as outfile:
                    json.dump(dict_intersection, outfile, sort_keys=True, indent=2)
            
            p_shape = make_plot(params_plot)
            
            #MEASURE ALL OVERLAYS AND COLORS
    #        zip_gdf = pairwise(list_gdf)
    #        for x in zip_gdf: 
    #            x[0]['time'] = None
    #            x[1]['time'] = None
    #            source_intersection, gdf_overlay = overlay(x[0], x[1], how, coeff_ampl, coeff_conv, color_switch)
    #            list_gdf.append(gdf_overlay)
                
    #        gdfs = pd.concat(list_gdf)
            
            exe_duration = time.time() - start_time
            
    #        gdfs.to_csv("test.csv")
            
            time.sleep(5) #sleep 5 seconds to avoid a Geocoder problem
    #        print (fmt.format(rd(seconds=exe_duration)))
            
            bar.update(i+1)
    
    if anim is True:
        adress = "20 hameau de la commanderie, 59840 LOMPRET"
        color = "#5BC862"
        date_value = "2018-06-28"
        date_value = datetime.strptime(date_value, '%Y-%m-%d').date()
        id_ = "fr-ne"
        step_value = 3600
        opacity_iso = 0.4
        shape = "poly"
        identity = "iso"
        step_mn = 1200
        how = "intersection"
        x_bounds = [305394,305394,382134,382134]
        y_bounds = [6521786, 6585394,6521786,6585394]
        duration = 0.5
        
        range_value = 86400//step_mn
        time_value = "08:00"
        
        start_time = time.time()
        
        epsg_in = Proj(init=inProj)
        epsg_out = Proj(init=outProj)
        
        from_place = geocode(adress)
        l_adress = []
        x=[]
        y=[]
        ori = transform(epsg_in,epsg_out,from_place[0],from_place[1])
        from_place = str(from_place[0]) + ";" + str(from_place[1])
        
        params_iso = {
                'token': TOKEN,
                'from_place': from_place,
                'time_in': time_value,
                'min_date': date_value,
                'step': step_value,
                'nb_iter': 1,
                'shape': shape,
                'inProj': inProj,
                'outProj': outProj,
                'how': how,
                'color':color,
                'color_switch': "white",
                'opacity_intersection':0.0,
                'opacity_iso':opacity_iso
                    }     
     
        for i in range(0,range_value):
            mn = step_mn*i
            time_value = timedelta(seconds=mn)
            params_iso["time_in"] = str(time_value)
        
            p_shape = run(params_iso, x,y,l_adress)
        
            #EXPORT NO_TILES PNG
            p_shape.add_tile(STAMEN_TERRAIN_RETINA, alpha=params["fig_params"]["alpha_tile"], name="tile")
            
            #ADD TITLE
            title = "From: " + adress + ", Duration: " + str(step_value//60) + "mn at " + str(time_value)
            p_shape.title.text = title
            p_shape.title.align = "left"
            p_shape.title.text_color = "white"
            p_shape.title.text_font_size = "18px"
            p_shape.title.background_fill_color = "black"
    
            #Add circles as range
            #Add origins points
            source_bounds = ColumnDataSource(
                    data=dict(
                            x=x_bounds,
                            y=y_bounds
                    )
            ) 
            
            poly_circles = p_shape.circle(
                'x', 
                'y', 
                source=source_bounds,
                color='blue', 
                alpha = 0.0,
                size=10,
                    )
            
            source_ori = ColumnDataSource(
                    data=dict(
                            x=[ori[0]],
                            y=[ori[1]],
                    )
            ) 
            
            poly_circles = p_shape.circle(
                'x', 
                'y', 
                source=source_ori,
                color='blue', 
                alpha = 1.0,
                size=10,
                    )
            
            time_str = str(time_value).replace(":","_")
            iso_name = str(i) + identity + "_" + time_str
            iso_name = export_anim + iso_name
            export_png(p_shape, filename="{}.png".format(iso_name))
            p_shape = make_plot(params_plot)
            
            time.sleep(2) #sleep 5 seconds to avoid a Geocoder problem
            
            exe_duration = time.time() - start_time
            
    #        print (fmt.format(rd(seconds=exe_duration)))
        
        images = []
        for file_name in os.listdir(export_anim):
            if file_name.endswith('.png'):
                file_path = os.path.join(export_anim, file_name)
                images.append(imageio.imread(file_path))
        iso_gif = export_anim + "anim_iso.gif"
        imageio.mimsave(iso_gif, images, duration=duration)
    