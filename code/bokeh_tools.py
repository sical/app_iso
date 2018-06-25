# -*- coding: utf-8 -*-
"""
Created on Mon May 14 15:58:54 2018

@author: thomas
"""
import colorsys

from bokeh.models import ColumnDataSource, HoverTool, TapTool, Slider, CustomJS
from bokeh.models.widgets import Tabs, Div, RadioGroup
from bokeh.plotting import figure, curdoc
from bokeh.layouts import row, widgetbox

def generate_color_range(N, I):
    '''
    Source: https://bokeh.pydata.org/en/latest/docs/gallery/color_sliders.html
    '''
    HSV_tuples = [ (x*1.0/N, 0.5, I) for x in range(N) ]
    RGB_tuples = map(lambda x: colorsys.hsv_to_rgb(*x), HSV_tuples)
    for_conversion = []
    for RGB_tuple in RGB_tuples:
        for_conversion.append((int(RGB_tuple[0]*255), int(RGB_tuple[1]*255), int(RGB_tuple[2]*255)))
    hex_colors = [ rgb_to_hex(RGB_tuple) for RGB_tuple in for_conversion ]
    return hex_colors, for_conversion

# convert RGB tuple to hexadecimal code
def rgb_to_hex(rgb):
    '''
    Source: https://bokeh.pydata.org/en/latest/docs/gallery/color_sliders.html
    '''
    return '#%02x%02x%02x' % rgb

# convert hexadecimal to RGB tuple
def hex_to_dec(hex):
    '''
    Source: https://bokeh.pydata.org/en/latest/docs/gallery/color_sliders.html
    '''
    red = ''.join(hex.strip('#')[0:2])
    green = ''.join(hex.strip('#')[2:4])
    blue = ''.join(hex.strip('#')[4:6])
    return (int(red, 16), int(green, 16), int(blue,16))

def make_color_gradient():
    brightness = 0.8 # change to have brighter/darker colors
    crx = list(range(1,1001)) # the resolution is 1000 colors
    cry = [ 5 for i in range(len(crx)) ]
    crcolor, crRGBs = generate_color_range(1000,brightness) # produce spectrum
    
    # make data source object to allow information to be displayed by hover tool
    crsource = ColumnDataSource(data=dict(x=crx, y=cry, crcolor=crcolor, RGBs=crRGBs))
    
    # create second plot
    color_gradient = figure(x_range=(0,1000), y_range=(0,10),
                plot_width=600, plot_height=150,
                tools='hover, tap', title='Choose your color by clicking/taping')
    
    color_range1 = color_gradient.rect(x='x', y='y', width=1, height=10,
                           color='crcolor', source=crsource)
    
    # set up hover tool to show color hex code and sample swatch
    color_gradient.select_one(HoverTool).tooltips = [
        ('color', '$color[hex, rgb, swatch]:crcolor'),
        ('RGB levels', '@RGBs')
    ]
    
    return color_gradient

    
def colors_slider():
    '''
    Source: https://bokeh.pydata.org/en/latest/docs/gallery/color_sliders.html
    '''
    # initialise a white block for the first plot
    hex_color = rgb_to_hex((127, 127, 127))
    
    # initialise the text color as black. This will be switched to white if the block color gets dark enough
    text_color = '#000000'
    
    # create a data source to enable refreshing of fill & text color
    source = ColumnDataSource(data=dict(color=[hex_color], text_color=[text_color]))
    
    # create first plot, as a rect() glyph and centered text label, with fill and text color taken from source
    p1 = figure(x_range=(-8, 8), y_range=(-4, 4),
                plot_width=210, plot_height=170,
                title='Color generated with sliders', tools='')
    
    p1.rect(0, 0, width=18, height=10, fill_color='color',
            line_color = 'black', source=source)
    
    p1.text(0, 0, text='color', text_color='text_color',
            alpha=0.6667, text_font_size='8pt', text_baseline='middle',
            text_align='center', source=source)
    
    p1.axis.visible = False
    
    # the callback function to update the color of the block and associated label text
    # NOTE: the JS functions for converting RGB to hex are taken from the excellent answer
    # by Tim Down at http://stackoverflow.com/questions/5623838/rgb-to-hex-and-hex-to-rgb
    callback = CustomJS(args=dict(source=source), code="""
        function componentToHex(c) {
            var hex = c.toString(16);
            return hex.length == 1 ? "0" + hex : hex;
        }
        function rgbToHex(r, g, b) {
            return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
        }
        function toInt(v) {
           return v | 0;
        }
        var data = source.data;
        color = data['color'];
        text_color = data['text_color'];
        var R = toInt(red_slider.value);
        var G = toInt(green_slider.value);
        var B = toInt(blue_slider.value);
        color[0] = rgbToHex(R, G, B);
        text_color[0] = '#ffffff';
        if ((R > 127) || (G > 127) || (B > 127)) {
            text_color[0] = '#000000';
        }
        source.change.emit();
    """)
    
    # create slider tool objects with a callback to control the RGB levels for first plot
    SLIDER_ARGS = dict(start=0, end=255, value=127, step=1, callback=callback)
    
    red_slider = Slider(title="Rouge", **SLIDER_ARGS)
    callback.args['red_slider'] = red_slider
    
    green_slider = Slider(title="Vert", **SLIDER_ARGS)
    callback.args['green_slider'] = green_slider
    
    blue_slider = Slider(title="Bleu", **SLIDER_ARGS)
    callback.args['blue_slider'] = blue_slider
    
    return p1, red_slider, green_slider, blue_slider

def colors_radio(colors):
    divs = []
    labels = []
    for color in colors:
        text = """{}""".format(color)
        div = Div(text="",
                style={
                        'background-color':color,
                        'color':"white"
                        },
                width=60, 
                height=12)
        divs.append(div)
        labels.append(text)
        
    viridis_group = RadioGroup(
            labels=labels, 
            active=0,
            width=100)
    
    panel = row(
                    [viridis_group, widgetbox(divs)]
                    )
    return panel