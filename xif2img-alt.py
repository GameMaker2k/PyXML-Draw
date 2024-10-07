#!/usr/bin/python

'''
    Optimized version of xif2img.py based on the original script.
    Optimizations include reducing redundant code and improving readability.

    Copyright 2015 Game Maker 2k - https://github.com/GameMaker2k
    Optimized by ChatGPT - 2024.
'''

from __future__ import absolute_import, division, print_function, unicode_literals
import re
import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont
import upcean.barcodes.shortcuts
from xml.etree import ElementTree as ET
from io import BytesIO
import urllib.request as urllib2
import platform

# Metadata
__version_info__ = (0, 0, 8, "Optimized")
__version__ = '.'.join(map(str, __version_info__))
__project__ = "PyXML-Draw"
__project_url__ = "https://github.com/GameMaker2k/PyXML-Draw"
useragent_string = f"Mozilla/5.0 (compatible; {__project__}/{__version__}; +{__project_url__})"

# Argument parsing
parser = argparse.ArgumentParser(add_help=True)
parser.add_argument("-i", "--input", required=True, help="Input XML file")
parser.add_argument("-t", "--outputtype", default="png", help="Output image format (e.g. png, jpg)")
parser.add_argument("-o", "--output", default="output.png", help="Output image file name")
parser.add_argument("-s", "--resize", type=int, default=1, help="Resize factor")
parser.add_argument("-r", "--resizetype", default="nearest", help="Resize algorithm (nearest, bilinear, bicubic, antialias)")
parser.add_argument("-v", "--version", action="version", version=__version__)
args = parser.parse_args()

def colortolist(color):
    """Converts hex or RGB color strings to a tuple"""
    if color.startswith("#"):
        return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    if color.startswith("rgb"):
        return tuple(map(int, re.findall(r'\d+', color)))
    return None

def colortolistalpha(color, alpha):
    """Converts hex or RGB color strings to a tuple with alpha"""
    return (*colortolist(color), alpha)

def coordinate_calc(calc_num, calc_size):
    """Calculates coordinates based on percentage or fixed values"""
    if "%" in calc_num:
        return int(float(calc_size) * (float(calc_num.strip('%')) / 100))
    return int(calc_num)

def get_image_from_url(url):
    """Fetches image from a URL"""
    headers = {'User-Agent': useragent_string}
    req = urllib2.Request(url, headers=headers)
    with urllib2.urlopen(req) as response:
        return Image.open(BytesIO(response.read())).convert('RGBA')

def resize_image(image, size, method):
    """Resizes the image based on the method specified"""
    methods = {
        "nearest": Image.NEAREST,
        "bilinear": Image.BILINEAR,
        "bicubic": Image.BICUBIC,
        "antialias": Image.ANTIALIAS
    }
    method = methods.get(method, Image.NEAREST)
    return image.resize(size, method)

def process_shape(xml_img, shape_data, shape_type):
    """Handles drawing shapes on the image"""
    coordinates = tuple(map(int, shape_data['coordinates'].split(',')))
    fill = colortolistalpha(shape_data['fill'], int(shape_data.get('alpha', 255)))
    outline = colortolistalpha(shape_data.get('outline', '#000000'), int(shape_data.get('outlinealpha', 255)))

    draw_funcs = {
        'ellipse': xml_img.ellipse,
        'rectangle': xml_img.rectangle,
        'polygon': xml_img.polygon
    }

    draw_func = draw_funcs.get(shape_type, None)
    if draw_func:
        draw_func(coordinates, fill=fill, outline=outline)

def xml_draw_image(xiffile, imgtype="png", resize_factor=1, resizetype="nearest", outfile="output.png"):
    """Main function to draw the image based on the XML input"""
    # Parse XML
    tree = ET.ElementTree(file=xiffile) if os.path.isfile(xiffile) else ET.ElementTree(ET.fromstring(xiffile))
    root = tree.getroot()

    # Initialize base image
    bg_color = colortolist(root.attrib.get('fill', "#FFFFFF"))
    width, height = int(root.attrib['width']), int(root.attrib['height'])
    pre_xml_img = Image.new("RGB", (width, height), color=bg_color)
    xml_img = ImageDraw.Draw(pre_xml_img, "RGBA")

    # Process each child element
    for child in root:
        shape_type = child.tag
        shape_data = child.attrib
        if shape_type in ['rectangle', 'ellipse', 'polygon']:
            process_shape(xml_img, shape_data, shape_type)
        elif shape_type == 'text':
            font = ImageFont.truetype(shape_data['font'], int(shape_data['size']))
            xml_img.text((int(shape_data['x']), int(shape_data['y'])), shape_data['text'], font=font, fill=colortolistalpha(shape_data['fill'], int(shape_data['alpha'])))
        elif shape_type == 'barcode':
            barcode_image = upcean.barcodes.shortcuts.validate_draw_barcode(type=shape_data['type'], upc=shape_data['code']).convert('RGBA')
            pre_xml_img.paste(barcode_image, (int(shape_data['x']), int(shape_data['y'])), barcode_image)

    # Resize if required
    if resize_factor > 1:
        pre_xml_img = resize_image(pre_xml_img, (width * resize_factor, height * resize_factor), resizetype)

    # Save image
    pre_xml_img.save(outfile, imgtype)

# Run the image drawing process
xml_draw_image(args.input, args.outputtype, args.resize, args.resizetype, args.output)
