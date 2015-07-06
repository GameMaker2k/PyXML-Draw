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

    $FileInfo: xif2img.py - Last Update: 7/06/2015 Ver. 0.0.2 RC 1 - Author: cooldude2k $
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
__version_info__ = (0, 0, 2, "RC 1");
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

def xml_draw_image(text, imgtype="png", outputimage=True, resize=1, resizetype="nearest", outfile=None):
 if(not str(resize).isdigit() or resize<1):
  resize = 1;
 resizetype = resizetype.lower();
 if(resizetype!="antialias" and resizetype!="bilinear" and resizetype!="bicubic" and resizetype!="nearest"):
  resizetype = "nearest";
 tree = cElementTree.ElementTree(cElementTree.fromstring(text));
 root = tree.getroot();
 root.attrib['fill'] = colortolist(root.attrib['fill']);
 pre_xml_img = Image.new("RGB", (int(root.attrib['width']), int(root.attrib['height'])));
 xml_img = ImageDraw.Draw(pre_xml_img, "RGBA");
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
  if(child.tag=="barcode"):
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
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
  if(child.tag=="multilinetext"):
   if('alpha' not in child.attrib):
    child.attrib['alpha'] = 255;
   for coordinates in child.iter('coordinates'):
    if(sublist!=None):
     sublist = sublist+(int(coordinates.attrib['x']), int(coordinates.attrib['y']));
    if(sublist==None):
     sublist = (int(coordinates.attrib['x']), int(coordinates.attrib['y']));
   mltext = None;
   for string in child.iter('string'):
    mltextstrg = string.text;
   child.attrib['fill'] = colortolistalpha(child.attrib['fill'], child.attrib['alpha']);
   tmp_ttf_file = ImageFont.truetype(child.attrib['font'], int(child.attrib['size']));
   xml_img.multiline_text(sublist, mltextstrg, fill=child.attrib['fill'], font=tmp_ttf_file, spacing=int(child.attrib['spacing']), align=child.attrib['align']);
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
 if(resizetype!="antialias"):
  new_xml_img = pre_xml_img.resize((int(root.attrib['width']) * int(resize), int(root.attrib['height']) * int(resize)), Image.ANTIALIAS);
 if(resizetype!="bilinear"):
  new_xml_img = pre_xml_img.resize((int(root.attrib['width']) * int(resize), int(root.attrib['height']) * int(resize)), Image.BILINEAR);
 if(resizetype!="bicubic"):
  new_xml_img = pre_xml_img.resize((int(root.attrib['width']) * int(resize), int(root.attrib['height']) * int(resize)), Image.BICUBIC);
 if(resizetype!="nearest"):
  new_xml_img = pre_xml_img.resize((int(root.attrib['width']) * int(resize), int(root.attrib['height']) * int(resize)), Image.NEAREST);
 del(xml_img);
 del(pre_xml_img);
 xml_img = ImageDraw.Draw(new_xml_img, "RGBA");
 new_xml_img.save(outfile, imgtype);
 return True;

ftest=open(getargs.input, "r");
xml_draw_image(ftest.read(), getargs.outputtype, True, getargs.resize, getargs.resizetype, getargs.output);
ftest.close();
