#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import sys
import argparse

from PIL import Image, ImageDraw, ImageFont

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import upcean.barcodes.shortcuts

PY2 = (sys.version_info[0] == 2)

if PY2:
    import urllib2
    try:
        from cStringIO import StringIO as _Py2BytesIO
    except ImportError:
        from StringIO import StringIO as _Py2BytesIO
else:
    import urllib.request as urllib2
    from io import BytesIO as _Py3BytesIO

def _bytes_io(data):
    return _Py2BytesIO(data) if PY2 else _Py3BytesIO(data)

_URL_RE = re.compile(r"^(http|https)\:\/\/", re.I)
_HEX_RE = re.compile(r"^\#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$")
_RGB_RE = re.compile(
    r"^rgb\(\s*(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\s*,\s*"
    r"(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\s*,\s*"
    r"(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\s*\)\s*$"
)
_PCT_RE = re.compile(r"^(\d+)\%$")

# Pillow resampling
_RESAMPLE = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "bicubic": Image.BICUBIC,
    "antialias": getattr(Image, "LANCZOS", Image.ANTIALIAS),
}

__project__ = "PyXML-Draw"
__version__ = "0.0.9 hybrid"
__project_url__ = "https://github.com/GameMaker2k/PyXML-Draw"
useragent_string = "Mozilla/5.0 (compatible; {}/{}; +{})".format(__project__, __version__, __project_url__)


def safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default


def parse_color_rgb(s):
    if s is None:
        return None
    s = s.strip()
    m = _HEX_RE.match(s)
    if m:
        return (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16))
    m = _RGB_RE.match(s)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def parse_color_rgba(s, alpha):
    rgb = parse_color_rgb(s)
    if rgb is None:
        return None
    a = safe_int(alpha, 255)
    if a < 0:
        a = 0
    if a > 255:
        a = 255
    return (rgb[0], rgb[1], rgb[2], a)


def coord_value(val, full_size):
    """Supports 'NN' and 'NN%'."""
    if val is None:
        return 0
    v = str(val).strip()
    m = _PCT_RE.match(v)
    if m:
        pct = int(m.group(1))
        return int(float(full_size) * (float(pct) / 100.0))
    return int(float(v))


def fetch_url_bytes(url):
    req = urllib2.Request(url)
    try:
        req.add_header("User-Agent", useragent_string)
    except Exception:
        pass
    resp = urllib2.urlopen(req)
    try:
        return resp.read()
    finally:
        try:
            resp.close()
        except Exception:
            pass


def load_xml_tree(xif_source):
    """Load XML from file path, URL, or raw XML string."""
    if _URL_RE.match(xif_source):
        data = fetch_url_bytes(xif_source)
        return ET.ElementTree(ET.fromstring(data))
    if os.path.isfile(xif_source):
        return ET.ElementTree(file=xif_source)
    return ET.ElementTree(ET.fromstring(xif_source))


def load_image_rgba(path_or_url):
    if _URL_RE.match(path_or_url):
        data = fetch_url_bytes(path_or_url)
        return Image.open(_bytes_io(data)).convert("RGBA")
    return Image.open(path_or_url).convert("RGBA")


def resize_if_needed(img, w, h, resizetype):
    if img.size == (w, h):
        return img
    resample = _RESAMPLE.get((resizetype or "nearest").lower(), Image.NEAREST)
    return img.resize((w, h), resample)


def nested_points(child, root_w, root_h):
    """Flatten nested <coordinates x="" y=""/> nodes into (x1,y1,x2,y2,...)"""
    pts = []
    for c in child.iter("coordinates"):
        x = coord_value(c.attrib.get("x", "0"), root_w)
        y = coord_value(c.attrib.get("y", "0"), root_h)
        pts.extend([x, y])
    return tuple(pts)


def nested_bbox(child, root_w, root_h):
    """BBox from nested coordinates: (x1,y1,x2,y2). Supports single node with width/height."""
    coords = list(child.iter("coordinates"))
    if not coords:
        return None

    if len(coords) == 1 and ("width" in coords[0].attrib or "height" in coords[0].attrib):
        c = coords[0]
        x = coord_value(c.attrib.get("x", "0"), root_w)
        y = coord_value(c.attrib.get("y", "0"), root_h)
        w = coord_value(c.attrib.get("width", "0"), root_w)
        h = coord_value(c.attrib.get("height", "0"), root_h)
        return (x, y, x + w, y + h)

    c1 = coords[0]
    c2 = coords[1] if len(coords) > 1 else coords[0]
    x1 = coord_value(c1.attrib.get("x", "0"), root_w)
    y1 = coord_value(c1.attrib.get("y", "0"), root_h)
    x2 = coord_value(c2.attrib.get("x", "0"), root_w)
    y2 = coord_value(c2.attrib.get("y", "0"), root_h)
    return (x1, y1, x2, y2)


def inline_xy(child, root_w, root_h):
    """Get (x,y) from inline attributes, with % support."""
    if "x" not in child.attrib or "y" not in child.attrib:
        return None
    x = coord_value(child.attrib.get("x", "0"), root_w)
    y = coord_value(child.attrib.get("y", "0"), root_h)
    return (x, y)


def inline_rect_bbox(child, root_w, root_h):
    """Rectangle bbox from inline x,y,width,height."""
    needed = ("x", "y", "width", "height")
    if not all(k in child.attrib for k in needed):
        return None
    x = coord_value(child.attrib["x"], root_w)
    y = coord_value(child.attrib["y"], root_h)
    w = coord_value(child.attrib["width"], root_w)
    h = coord_value(child.attrib["height"], root_h)
    return (x, y, x + w, y + h)


def inline_ellipse_bbox(child, root_w, root_h):
    """
    Ellipse bbox:
    - supports sample format: center x,y with rx,ry
    """
    if all(k in child.attrib for k in ("x", "y", "rx", "ry")):
        cx = coord_value(child.attrib["x"], root_w)
        cy = coord_value(child.attrib["y"], root_h)
        rx = coord_value(child.attrib["rx"], root_w)
        ry = coord_value(child.attrib["ry"], root_h)
        return (cx - rx, cy - ry, cx + rx, cy + ry)
    return None


def get_fill_outline(child, default_fill="#000000"):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    outlinealpha = safe_int(child.attrib.get("outlinealpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", default_fill), alpha)
    outline = None
    if "outline" in child.attrib:
        outline = parse_color_rgba(child.attrib.get("outline", "#000000"), outlinealpha)
    return fill, outline


def handle_polygon(draw, base, child, root_w, root_h, resizetype):
    pts = nested_points(child, root_w, root_h)
    if not pts:
        return
    fill, outline = get_fill_outline(child, default_fill="#000000")
    draw.polygon(pts, fill=fill, outline=outline)


def handle_rectangle(draw, base, child, root_w, root_h, resizetype):
    bbox = inline_rect_bbox(child, root_w, root_h) or nested_bbox(child, root_w, root_h)
    if not bbox:
        return
    fill, outline = get_fill_outline(child, default_fill="#000000")
    draw.rectangle(bbox, fill=fill, outline=outline)


def handle_ellipse(draw, base, child, root_w, root_h, resizetype):
    bbox = inline_ellipse_bbox(child, root_w, root_h) or nested_bbox(child, root_w, root_h)
    if not bbox:
        return
    fill, outline = get_fill_outline(child, default_fill="#000000")
    draw.ellipse(bbox, fill=fill, outline=outline)


def handle_text(draw, base, child, root_w, root_h, resizetype):
    # Position: inline x,y OR nested coordinates
    pos = inline_xy(child, root_w, root_h)
    if pos is None:
        pts = nested_points(child, root_w, root_h)
        pos = (pts[0], pts[1]) if len(pts) >= 2 else (0, 0)

    fill, _ = get_fill_outline(child, default_fill="#000000")

    # Text content: element text OR attribute 'text'
    txt = child.text if child.text is not None else ""
    txt = txt.strip()
    if not txt:
        txt = child.attrib.get("text", "")

    # Font: in your sample it's "Verdana" (not a path). truetype usually wants a path.
    # We'll try truetype; if it fails, fall back to default font.
    size_raw = child.attrib.get("size", "12")
    # allow percent size (relative to height)
    if _PCT_RE.match(str(size_raw).strip()):
        size = coord_value(size_raw, root_h)
    else:
        size = safe_int(size_raw, 12)
    if size < 1:
        size = 1

    font_spec = child.attrib.get("font", "")
    try:
        font = ImageFont.truetype(font_spec, size) if font_spec else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    draw.text(pos, txt, fill=fill, font=font)


def handle_barcode(draw, base, child, root_w, root_h, resizetype):
    # Support BOTH:
    # - nested coordinates (original)
    # - inline x,y (optional)
    pos = inline_xy(child, root_w, root_h)
    if pos is None:
        pts = nested_points(child, root_w, root_h)
        pos = (pts[0], pts[1]) if len(pts) >= 2 else (0, 0)

    bctype = child.attrib.get("type", "")
    code = child.attrib.get("code", "")
    if not bctype or not code:
        return

    kw = {"bctype": bctype, "upc": code}
    if "size" in child.attrib:
        kw["resize"] = safe_int(child.attrib["size"], 1)

    bc = upcean.barcodes.shortcuts.validate_draw_barcode(**kw).convert("RGBA")
    base.paste(bc, pos, bc)


HANDLERS = {
    "polygon": handle_polygon,
    "rectangle": handle_rectangle,
    "rect": handle_rectangle,
    "square": handle_rectangle,
    "ellipse": handle_ellipse,
    "text": handle_text,
    "barcode": handle_barcode,
    # you can add the rest (arc/line/pieslice/picture/photo/bitmap/...) the same way
}


def xml_draw_image(xif_source, imgtype="png", resize=1, resizetype="nearest", outfile="output.png"):
    tree = load_xml_tree(xif_source)
    root = tree.getroot()

    root_w = safe_int(root.attrib.get("width", 0), 0)
    root_h = safe_int(root.attrib.get("height", 0), 0)
    if root_w <= 0 or root_h <= 0:
        raise ValueError("Root <image> must include positive width and height.")

    bg = parse_color_rgb(root.attrib.get("fill", "#FFFFFF")) or (255, 255, 255)
    base = Image.new("RGB", (root_w, root_h), color=bg)
    draw = ImageDraw.Draw(base, "RGBA")

    for child in list(root):
        tag = (child.tag or "").lower().strip()
        handler = HANDLERS.get(tag)
        if handler:
            handler(draw, base, child, root_w, root_h, resizetype)

    # Final integer scale
    try:
        resize = int(resize)
    except Exception:
        resize = 1
    if resize < 1:
        resize = 1

    if resize > 1:
        base = resize_if_needed(base, root_w * resize, root_h * resize, resizetype)

    base.save(outfile, imgtype)
    return True


def main():
    p = argparse.ArgumentParser(add_help=True)
    p.add_argument("-i", "--input", required=True, help="Input XML file path, URL, or raw XML string")
    p.add_argument("-t", "--outputtype", default="png", help="Output image format")
    p.add_argument("-o", "--output", default="output.png", help="Output image filename")
    p.add_argument("-s", "--resize", default=1, help="Integer scale factor")
    p.add_argument("-r", "--resizetype", default="nearest", help="nearest|bilinear|bicubic|antialias")
    args = p.parse_args()

    xml_draw_image(args.input, args.outputtype, args.resize, args.resizetype, args.output)


if __name__ == "__main__":
    sys.tracebacklimit = 0
    main()
