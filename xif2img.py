#!/usr/bin/python

from __future__ import absolute_import, division, print_function, unicode_literals;
import re, os, sys, argparse, platform;
from PIL import Image, ImageColor, ImageDraw, ImageFont;
try:
 import xml.etree.cElementTree as cElementTree;
except ImportError:
 import xml.etree.ElementTree as cElementTree;
if(sys.version[0]=="2"):
 try:
  from cStringIO import StringIO;
 except ImportError:
  from StringIO import StringIO;
 import urllib2, urlparse;
if(sys.version[0]=="3"):
 from io import StringIO, BytesIO;
 import urllib.request as urllib2;
 import urllib.parse as urlparse;
from xml.sax.saxutils import XMLGenerator;

'''
http://pillow.readthedocs.org/en/latest/reference/ImageDraw.html
https://infohost.nmt.edu/tcc/help/pubs/pil/image-draw.html
https://github.com/GameMaker2k/PyUPC-EAN/blob/master/upcean/barcodes/files.py
https://github.com/GameMaker2k/PyPixel-Draw/blob/master/PyPixelDraw.py
'''

if(__name__ == "__main__"):
 sys.tracebacklimit = 0;
__version_info__ = (1, 0, 0, "RC 1");
if(__version_info__[3]!=None):
 __version__ = str(__version_info__[0])+"."+str(__version_info__[1])+"."+str(__version_info__[2])+" "+str(__version_info__[3]);
if(__version_info__[3]==None):
 __version__ = str(__version_info__[0])+"."+str(__version_info__[1])+"."+str(__version_info__[2]);

parser = argparse.ArgumentParser(conflict_handler = "resolve", add_help = True);
parser.add_argument("-i", "--input", default = None, help = "enter name of input file");
parser.add_argument("-t", "--outputtype", default = None, help = "enter file type of output image");
parser.add_argument("-o", "--output", default = None, help = "enter name of output image");
parser.add_argument("-s", "--resize", default = 1, help = "enter number to resize image");
parser.add_argument("-r", "--resizetype", default = "nearest", help = "enter resize type");
parser.add_argument("-v", "--version", action = "version", version = __version__);
getargs = parser.parse_args();

def colortolist(color):
 if(re.findall("^\#", color)):
  colorsplit = re.findall("^\#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", color)[0];
  return (int(colorsplit[0], 16), int(colorsplit[1], 16), int(colorsplit[2], 16));
 if(re.findall("^rgb", color)):
  colorsplit = re.findall("^rgb\(([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\)", color)[0];
  return (int(colorsplit[0], 16), int(colorsplit[1], 16), int(colorsplit[2], 16));
 return None;

def colortolistalpha(color, alpha):
 if(re.findall("^\#", color)):
  colorsplit = re.findall("^\#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", color)[0];
  return (int(colorsplit[0], 16), int(colorsplit[1], 16), int(colorsplit[2], 16), int(alpha));
 if(re.findall("^rgb", color)):
  colorsplit = re.findall("^rgb\(([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\)", color)[0];
  return (int(colorsplit[0], 16), int(colorsplit[1], 16), int(colorsplit[2], 16), int(alpha));
 return None;

tree = cElementTree.ElementTree(file=getargs.input);
root = tree.getroot();
root.attrib['fill'] = colortolist(root.attrib['fill']);
pre_xml_img = Image.new("RGBA", (int(root.attrib['width']), int(root.attrib['height'])));
xml_img = ImageDraw.Draw(pre_xml_img);
xml_img.rectangle([(0, 0), (int(root.attrib['width']), int(root.attrib['height']))], fill=root.attrib['fill']);

for child in root:
 sublist = ();
 tmp_img_paste = None;
 tmp_ttf_file = None;
 if(child.tag=="arc"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  xml_img.arc(sublist, int(child.attrib['start']), int(child.attrib['end']), fill=child.attrib['fill']);

 if(child.tag=="chord"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  if('outlinealpha' not in child.attrib):
   child.attrib['outlinealpha'] = 255;
  child.attrib['outline'] = colortolistalpha(child.attrib['outline'], child.attrib['outlinealpha']);
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  xml_img.chord(sublist, int(child.attrib['start']), int(child.attrib['end']), fill=child.attrib['fill'], outline=child.attrib['outline']);

 if(child.tag=="ellipse"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  if('outlinealpha' not in child.attrib):
   child.attrib['outlinealpha'] = 255;
  child.attrib['outline'] = colortolistalpha(child.attrib['outline'], child.attrib['outlinealpha']);
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  xml_img.ellipse(sublist, fill=child.attrib['fill'], outline=child.attrib['outline']);

 if(child.tag=="line"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  xml_img.line(sublist, fill=child.attrib['fill'], width=int(child.attrib['width']));

 if(child.tag=="multiline"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  tmp_ttf_file = ImageFont.truetype(child.attrib['font'], int(child.attrib['size']));
  xml_img.multiline_text(sublist, child.attrib['text'], fill=child.attrib['fill'], font=tmp_ttf_file, spacing=int(child.attrib['spacing']), align=child.attrib['align']);
  del(tmp_ttf_file);

 if(child.tag=="picture"):
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  tmp_img_paste = Image.open(child.attrib['file']).convert('RGBA');
  pre_xml_img.paste(tmp_img_paste, sublist, tmp_img_paste);
  del(tmp_img_paste);

 if(child.tag=="pieslice"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  if('outlinealpha' not in child.attrib):
   child.attrib['outlinealpha'] = 255;
  child.attrib['outline'] = colortolistalpha(child.attrib['outline'], child.attrib['outlinealpha']);
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  xml_img.pieslice(sublist, int(child.attrib['start']), int(child.attrib['end']), fill=child.attrib['fill'], outline=child.attrib['outline']);

 if(child.tag=="point"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  xml_img.point(sublist, fill=child.attrib['fill']);

 if(child.tag=="polygon"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  if('outlinealpha' not in child.attrib):
   child.attrib['outlinealpha'] = 255;
  child.attrib['outline'] = colortolistalpha(child.attrib['outline'], child.attrib['outlinealpha']);
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  xml_img.polygon(sublist, fill=child.attrib['fill'], outline=child.attrib['outline']);

 if(child.tag=="rectangle"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  if('outlinealpha' not in child.attrib):
   child.attrib['outlinealpha'] = 255;
  child.attrib['outline'] = colortolistalpha(child.attrib['outline'], child.attrib['outlinealpha']);
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  xml_img.rectangle(sublist, fill=child.attrib['fill'], outline=child.attrib['outline']);

 if(child.tag=="text"):
  if('alpha' not in child.attrib):
   child.attrib['alpha'] = 255;
  for coordinates in child.iter('coordinates'):
   if(sublist!=None):
    sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(sublist==None):
    sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
  child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
  tmp_ttf_file = ImageFont.truetype(child.attrib['font'], int(child.attrib['size']));
  xml_img.text(sublist, child.attrib['text'], fill=child.attrib['fill'], font=tmp_ttf_file);
  del(tmp_ttf_file);

pre_xml_img.save(getargs.output, getargs.outputtype);
