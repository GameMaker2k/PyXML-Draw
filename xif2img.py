#!/usr/bin/python

'''
    This program is free software; you can redistribute it and/or modify
    it under the terms of the Revised BSD License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    Revised BSD License for more details.

    Copyright 2015 Game Maker 2k - https://github.com/GameMaker2k
    Copyright 2015 Kazuki Przyborowski - https://github.com/KazukiPrzyborowski

    $FileInfo: xif2img.py - Last Update: 7/6/2015 Ver. 0.0.7 RC 2 - Author: cooldude2k $
'''

from __future__ import absolute_import, division, print_function, unicode_literals;
import re, os, sys, argparse, platform;
from PIL import Image, ImageColor, ImageDraw, ImageFont;
import upcean.validate, upcean.support, upcean.barcodes.barcode, upcean.barcodes.shortcuts;
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
__version_info__ = (0, 0, 7, "RC 2");
if(__version_info__[3]!=None):
 __version__ = str(__version_info__[0])+"."+str(__version_info__[1])+"."+str(__version_info__[2])+" "+str(__version_info__[3]);
if(__version_info__[3]==None):
 __version__ = str(__version_info__[0])+"."+str(__version_info__[1])+"."+str(__version_info__[2]);
__project__ = "PyXML-Draw";
__project_url__ = "https://github.com/GameMaker2k/PyXML-Draw";
useragent_string = "Mozilla/5.0 (compatible; {proname}/{prover}; +{prourl})".format(proname=__project__, prover=__version__, prourl=__project_url__);
if(platform.python_implementation()!=""):
 useragent_string_alt = "Mozilla/5.0 ({osver}; {archtype}; +{prourl}) {pyimp}/{pyver} (KHTML, like Gecko) {proname}/{prover}".format(osver=platform.system()+" "+platform.release(), archtype=platform.machine(), prourl=__project_url__, pyimp=platform.python_implementation(), pyver=platform.python_version(), proname=__project__, prover=__version__);
if(platform.python_implementation()==""):
 useragent_string_alt = "Mozilla/5.0 ({osver}; {archtype}; +{prourl}) {pyimp}/{pyver} (KHTML, like Gecko) {proname}/{prover}".format(osver=platform.system()+" "+platform.release(), archtype=platform.machine(), prourl=__project_url__, pyimp="Python", pyver=platform.python_version(), proname=__project__, prover=__version__);

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

def check_if_string(strtext):
 if(sys.version[0]=="2"):
  if(isinstance(strtext, basestring)):
   return True;
 if(sys.version[0]=="3"):
  if(isinstance(strtext, str)):
   return True;
 return False;

def coordinate_calc(calc_num, calc_size):
 if(re.findall("([0-9]+)%", calc_num)):
  if(int(re.findall("([0-9]+)%", calc_num)[0])==0):
   return int(0);
  per_num = int(re.findall("([0-9]+)%", calc_num)[0]);
  return int(float(calc_size) * (float(per_num) / float(100)));
 return int(calc_num);

def xml_draw_image(xiffile, imgtype="png", outputimage=True, resize=1, resizetype="nearest", outfile=None):
 if(not str(resize).isdigit() or resize<1):
  resize = 1;
 resizetype = resizetype.lower();
 if(resizetype!="antialias" and resizetype!="bilinear" and resizetype!="bicubic" and resizetype!="nearest"):
  resizetype = "nearest";
 if(not os.path.isfile(xiffile) and re.findall("^(http|https)\:\/\/", xiffile)):
  xmlheaders = {'User-Agent': useragent_string};
  tree = cElementTree.ElementTree(file=urllib2.urlopen(urllib2.Request(xiffile, None, xmlheaders)));
 if(os.path.isfile(xiffile) and not re.findall("^(http|https)\:\/\/", xiffile)):
  tree = cElementTree.ElementTree(file=xiffile);
 if(not os.path.isfile(xiffile) and not re.findall("^(http|https)\:\/\/", xiffile)):
  tree = cElementTree.ElementTree(cElementTree.fromstring(text));
 root = tree.getroot();
 root.attrib['fill'] = colortolist(root.attrib['fill']);
 pre_xml_img = Image.new("RGB", (int(root.attrib['width']), int(root.attrib['height'])), color=root.attrib['fill']);
 xml_img = ImageDraw.Draw(pre_xml_img, "RGBA");
 for child in root:
  sublist = ();
  tmp_img_paste = None;
  new_img_paste = None;
  tmp_ttf_file = None;
  if(child.tag=="arc"):
   if('alpha' not in child.attrib):
    child.attrib['alpha'] = 255;
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
   xml_img.arc(sublist, int(child.attrib['start']), int(child.attrib['end']), fill=child.attrib['fill']);
  if(child.tag=="barcode"):
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   xmlbarcode = {"bctype": child.attrib['type'], "upc": child.attrib['code']};
   if('size' in child.attrib):
    xmlbarcode.update({"resize": int(child.attrib['size'])});
   if('hideinfo' in child.attrib):
    hidebcinfo = child.attrib['hideinfo'].split();
    hidebcinfoval = [];
    if(hidebcinfo[0]=="0"):
     hidebcinfoval.append(False);
    if(hidebcinfo[0]=="1"):
     hidebcinfoval.append(True);
    if(hidebcinfo[1]=="0"):
     hidebcinfoval.append(False);
    if(hidebcinfo[1]=="1"):
     hidebcinfoval.append(True);
    if(hidebcinfo[2]=="0"):
     hidebcinfoval.append(False);
    if(hidebcinfo[2]=="1"):
     hidebcinfoval.append(True);
    xmlbarcode.update({"hideinfo": tuple(hidebcinfoval)});
   if('height' in child.attrib):
    xmlbarcode.update({"barheight": tuple(map(int, child.attrib['height'].split()))});
   if('textxy' in child.attrib):
    xmlbarcode.update({"textxy": tuple(map(int, child.attrib['textxy'].split()))});
   if('color' in child.attrib):
    colorsplit = child.attrib['color'].split();
    colorsplit[0] = re.sub(r"\s+", "", colorsplit[0]);
    if(re.findall("^\#", colorsplit[0])):
     colorsplit1 = re.findall("^\#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", colorsplit[0]);
    if(re.findall("^rgb", colorsplit[0])):
     colorsplit1 = re.findall("^rgb\(([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\)", colorsplit[0]);
    colorsplit1 = colorsplit1[0];
    colorlist1 = (int(colorsplit1[0], 16), int(colorsplit1[1], 16), int(colorsplit1[2], 16));
    colorsplit[1] = re.sub(r"\s+", "", colorsplit[1]);
    if(re.findall("^\#", colorsplit[1])):
     colorsplit2 = re.findall("^\#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", colorsplit[1]);
    if(re.findall("^rgb", colorsplit[1])):
     colorsplit2 = re.findall("^rgb\(([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\)", colorsplit[1]);
    colorsplit2 = colorsplit2[0];
    colorlist2 = (int(colorsplit2[0], 16), int(colorsplit2[1], 16), int(colorsplit2[2], 16));
    colorsplit[2] = re.sub(r"\s+", "", colorsplit[2]);
    if(re.findall("^\#", colorsplit[2])):
     colorsplit3 = re.findall("^\#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})", colorsplit[2]);
    if(re.findall("^rgb", colorsplit[2])):
     colorsplit3 = re.findall("^rgb\(([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5]),([0-9]|[1-9][0-9]|1[0-9][0-9]|2[0-4][0-9]|25[0-5])\)", colorsplit[2]);
    colorsplit3 = colorsplit3[0];
    colorlist3 = (int(colorsplit3[0], 16), int(colorsplit3[1], 16), int(colorsplit3[2], 16));
    colorlist = (colorlist1, colorlist2, colorlist3);
    xmlbarcode.update({"barcolor": colorlist});
   tmp_img_paste = upcean.barcodes.shortcuts.validate_draw_barcode(**xmlbarcode).convert('RGBA');
   pre_xml_img.paste(tmp_img_paste, sublist, tmp_img_paste);
   del(tmp_img_paste);
  if(child.tag=="bitmap"):
   if('alpha' not in child.attrib):
    child.attrib['alpha'] = 255;
   child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(not os.path.isfile(child.attrib['file']) and re.findall("^(http|https)\:\/\/", child.attrib['file'])):
    xmlheaders = {'User-Agent': useragent_string};
    tmp_img_paste = Image.open(StringIO(urllib2.urlopen(urllib2.Request(child.attrib['file'], None, xmlheaders)).read())).convert('RGBA');
   if(os.path.isfile(child.attrib['file']) and not re.findall("^(http|https)\:\/\/", child.attrib['file'])):
    tmp_img_paste = Image.open(child.attrib['file']).convert('RGBA');
   if(re.findall("([0-9]+)%", child.attrib['width'])):
    child.attrib['width'] = coordinate_calc(child.attrib['width'], int(root.attrib['width']));
   if(re.findall("([0-9]+)%", child.attrib['height'])):
    child.attrib['height'] = coordinate_calc(child.attrib['height'], int(root.attrib['height']));
   if((tmp_img_paste.size[0]<int(child.attrib['width']) or tmp_img_paste.size[0]>int(child.attrib['width'])) or (tmp_img_paste.size[1]<int(child.attrib['height']) or tmp_img_paste.size[1]>int(child.attrib['height']))):
    if(resizetype=="antialias"):
     new_img_paste = tmp_img_paste.resize((int(child.attrib['width']), int(child.attrib['height'])), Image.ANTIALIAS);
    if(resizetype=="bilinear"):
     new_img_paste = tmp_img_paste.resize((int(child.attrib['width']), int(child.attrib['height'])), Image.BILINEAR);
    if(resizetype=="bicubic"):
     new_img_paste = tmp_img_paste.resize((int(child.attrib['width']), int(child.attrib['height'])), Image.BICUBIC);
    if(resizetype=="nearest"):
     new_img_paste = tmp_img_paste.resize((int(child.attrib['width']), int(child.attrib['height'])), Image.NEAREST);
    xml_img.bitmap(sublist, new_img_paste, fill=child.attrib['fill']);
    del(new_img_paste);
   if(tmp_img_paste.size[0]==int(child.attrib['width']) and tmp_img_paste.size[1]==int(child.attrib['height'])):
    xml_img.bitmap(sublist, tmp_img_paste, fill=child.attrib['fill']);
    del(tmp_img_paste);
  if(child.tag=="chord"):
   if('alpha' not in child.attrib):
    child.attrib['alpha'] = 255;
   child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
   if('outlinealpha' not in child.attrib):
    child.attrib['outlinealpha'] = 255;
   child.attrib['outline'] = colortolistalpha(child.attrib['outline'], child.attrib['outlinealpha']);
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
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
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   xml_img.ellipse(sublist, fill=child.attrib['fill'], outline=child.attrib['outline']);
  if(child.tag=="line"):
   if('alpha' not in child.attrib):
    child.attrib['alpha'] = 255;
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   child.attrib['fill'] = colortolistalpha(child.attrib['f/usr/share/pixmaps/acidrip.pngill'], child.attrib['alpha']);
   xml_img.line(sublist, fill=child.attrib['fill'], width=int(child.attrib['width']));
  if(child.tag=="multilinetext"):
   if('alpha' not in child.attrib):
    child.attrib['alpha'] = 255;
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   mltext = None;
   for string in child.iter('string'):
    mltextstrg = string.text;
   child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
   if(re.findall("([0-9]+)%", child.attrib['size'])):
    child.attrib['size'] = coordinate_calc(child.attrib['size'], int(root.attrib['height']));
   tmp_ttf_file = ImageFont.truetype(child.attrib['font'], int(child.attrib['size']));
   xml_img.multiline_text(sublist, mltextstrg, fill=child.attrib['fill'], font=tmp_ttf_file, spacing=int(child.attrib['spacing']), align=child.attrib['align']);
   del(tmp_ttf_file);
  if(child.tag=="picture" or child.tag=="photo"):
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   if(not os.path.isfile(child.attrib['file']) and re.findall("^(http|https)\:\/\/", child.attrib['file'])):
    xmlheaders = {'User-Agent': useragent_string};
    tmp_img_paste = Image.open(StringIO(urllib2.urlopen(urllib2.Request(child.attrib['file'], None, xmlheaders)).read())).convert('RGBA');
   if(os.path.isfile(child.attrib['file']) and not re.findall("^(http|https)\:\/\/", child.attrib['file'])):
    tmp_img_paste = Image.open(child.attrib['file']).convert('RGBA');
   if(re.findall("([0-9]+)%", child.attrib['width'])):
    child.attrib['width'] = coordinate_calc(child.attrib['width'], int(root.attrib['width']));
   if(re.findall("([0-9]+)%", child.attrib['height'])):
    child.attrib['height'] = coordinate_calc(child.attrib['height'], int(root.attrib['height']));
   if((tmp_img_paste.size[0]<int(child.attrib['width']) or tmp_img_paste.size[0]>int(child.attrib['width'])) or (tmp_img_paste.size[1]<int(child.attrib['height']) or tmp_img_paste.size[1]>int(child.attrib['height']))):
    if(resizetype=="antialias"):
     new_img_paste = tmp_img_paste.resize((int(child.attrib['width']), int(child.attrib['height'])), Image.ANTIALIAS);
    if(resizetype=="bilinear"):
     new_img_paste = tmp_img_paste.resize((int(child.attrib['width']), int(child.attrib['height'])), Image.BILINEAR);
    if(resizetype=="bicubic"):
     new_img_paste = tmp_img_paste.resize((int(child.attrib['width']), int(child.attrib['height'])), Image.BICUBIC);
    if(resizetype=="nearest"):
     new_img_paste = tmp_img_paste.resize((int(child.attrib['width']), int(child.attrib['height'])), Image.NEAREST);
    pre_xml_img.paste(new_img_paste, sublist, new_img_paste);
    del(new_img_paste);
   if(tmp_img_paste.size[0]==int(child.attrib['width']) and tmp_img_paste.size[1]==int(child.attrib['height'])):
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
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   xml_img.pieslice(sublist, int(child.attrib['start']), int(child.attrib['end']), fill=child.attrib['fill'], outline=child.attrib['outline']);
  if(child.tag=="point" or child.tag=="dot"):
   if('alpha' not in child.attrib):
    child.attrib['alpha'] = 255;
   child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
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
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   xml_img.polygon(sublist, fill=child.attrib['fill'], outline=child.attrib['outline']);
  if(child.tag=="rectangle" or child.tag=="square"):
   if('alpha' not in child.attrib):
    child.attrib['alpha'] = 255;
   child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
   if('outlinealpha' not in child.attrib):
    child.attrib['outlinealpha'] = 255;
   child.attrib['outline'] = colortolistalpha(child.attrib['outline'], child.attrib['outlinealpha']);
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   xml_img.rectangle(sublist, fill=child.attrib['fill'], outline=child.attrib['outline']);
  if(child.tag=="text"):
   if('alpha' not in child.attrib):
    child.attrib['alpha'] = 255;
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     if(re.findall("([0-9]+)%", coordinates.attrib['x'])):
      coordinates.attrib['x'] = coordinate_calc(coordinates.attrib['x'], int(root.attrib['width']));
     if(re.findall("([0-9]+)%", coordinates.attrib['y'])):
      coordinates.attrib['y'] = coordinate_calc(coordinates.attrib['y'], int(root.attrib['height']));
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
   if(re.findall("([0-9]+)%", child.attrib['size'])):
    child.attrib['size'] = coordinate_calc(child.attrib['size'], int(root.attrib['height']));
   tmp_ttf_file = ImageFont.truetype(child.attrib['font'], int(child.attrib['size']));
   xml_img.text(sublist, child.attrib['text'], fill=child.attrib['fill'], font=tmp_ttf_file);
   del(tmp_ttf_file);
 if(resize>1):
  if(resizetype=="antialias"):
   new_xml_img = pre_xml_img.resize((int(root.attrib['width']) * int(resize), int(root.attrib['height']) * int(resize)), Image.ANTIALIAS);
  if(resizetype=="bilinear"):
   new_xml_img = pre_xml_img.resize((int(root.attrib['width']) * int(resize), int(root.attrib['height']) * int(resize)), Image.BILINEAR);
  if(resizetype=="bicubic"):
   new_xml_img = pre_xml_img.resize((int(root.attrib['width']) * int(resize), int(root.attrib['height']) * int(resize)), Image.BICUBIC);
  if(resizetype=="nearest"):
   new_xml_img = pre_xml_img.resize((int(root.attrib['width']) * int(resize), int(root.attrib['height']) * int(resize)), Image.NEAREST);
  del(xml_img);
  del(pre_xml_img);
  xml_img = ImageDraw.Draw(new_xml_img, "RGBA");
 if(outputimage==True):
  if(resize>1):
   new_xml_img.save(outfile, imgtype);
  if(resize==1):
   pre_xml_img.save(outfile, imgtype);
  return True;
 if(outputimage==False):
  if(resize>1):
   return new_xml_img;
  if(resize==1):
   return pre_xml_img;
 return False;

xml_draw_image(getargs.input, getargs.outputtype, True, getargs.resize, getargs.resizetype, getargs.output);
