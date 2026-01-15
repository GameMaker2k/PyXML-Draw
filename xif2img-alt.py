#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Optimized PyXML-Draw renderer (xif2img optimized)
- Preserves original XML schema: root with width/height/fill; children with nested <coordinates .../>
- Python 2 + 3 compatible
- Fixes original bugs:
  * rgb() parsing incorrectly treated as hex
  * broken 'line' fill attribute key
  * safer URL/image loading (binary BytesIO)
  * more robust coordinate parsing + percent support
- Reduces redundancy via helpers and dispatch table
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import sys
import argparse
import platform

from PIL import Image, ImageDraw, ImageFont

import upcean.barcodes.shortcuts

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

# --- Py2/Py3 HTTP + BytesIO compatibility ---
PY2 = (sys.version_info[0] == 2)

if PY2:
    import urllib2
    import urlparse
    try:
        from cStringIO import StringIO as _Py2BytesIO  # bytes string container
    except ImportError:
        from StringIO import StringIO as _Py2BytesIO
else:
    import urllib.request as urllib2
    import urllib.parse as urlparse
    from io import BytesIO as _Py3BytesIO

def _bytes_io(data):
    # Return a file-like bytes buffer for Pillow
    if PY2:
        return _Py2BytesIO(data)
    return _Py3BytesIO(data)

# --- Metadata / UA ---
__version_info__ = (0, 0, 8, "RC optimized")
__version__ = "{}.{}.{} {}".format(__version_info__[0], __version_info__[1], __version_info__[2], __version_info__[3])
__project__ = "PyXML-Draw"
__project_url__ = "https://github.com/GameMaker2k/PyXML-Draw"

useragent_string = "Mozilla/5.0 (compatible; {proname}/{prover}; +{prourl})".format(
    proname=__project__, prover=__version__, prourl=__project_url__
)

# Pillow resampling (compat across versions)
_RESAMPLE = {
    "nearest": Image.NEAREST,
    "bilinear": Image.BILINEAR,
    "bicubic": Image.BICUBIC,
    "antialias": getattr(Image, "LANCZOS", Image.ANTIALIAS),  # LANCZOS preferred when available
}

_HEX_RE = re.compile(r"^\#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})$")
_RGB_RE = re.compile(
    r"^rgb\(\s*(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\s*,\s*"
    r"(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\s*,\s*"
    r"(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\s*\)\s*$"
)
_PCT_RE = re.compile(r"^(\d+)\%$")

_URL_RE = re.compile(r"^(http|https)\:\/\/", re.I)


# ---------------------------
# Helpers
# ---------------------------

def parse_color_rgb(color_str):
    """Parse '#RRGGBB' or 'rgb(r,g,b)' -> (r,g,b). Returns None if invalid."""
    if color_str is None:
        return None
    color_str = color_str.strip()
    m = _HEX_RE.match(color_str)
    if m:
        return (int(m.group(1), 16), int(m.group(2), 16), int(m.group(3), 16))
    m = _RGB_RE.match(color_str)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None

def parse_color_rgba(color_str, alpha):
    rgb = parse_color_rgb(color_str)
    if rgb is None:
        return None
    try:
        a = int(alpha)
    except Exception:
        a = 255
    if a < 0:
        a = 0
    if a > 255:
        a = 255
    return (rgb[0], rgb[1], rgb[2], a)

def coord_value(val, full_size):
    """Supports numeric strings and 'NN%' strings."""
    if val is None:
        return 0
    val = str(val).strip()
    m = _PCT_RE.match(val)
    if m:
        pct = int(m.group(1))
        if pct <= 0:
            return 0
        return int(float(full_size) * (float(pct) / 100.0))
    return int(float(val))

def fetch_url_bytes(url, headers=None):
    headers = headers or {}
    req = urllib2.Request(url)
    # Py2/3: request header API differs slightly; this works broadly:
    for k, v in headers.items():
        try:
            req.add_header(k, v)
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
    """Load XML from local file path or URL."""
    if _URL_RE.match(xif_source):
        data = fetch_url_bytes(xif_source, headers={"User-Agent": useragent_string})
        return ET.ElementTree(ET.fromstring(data))
    if os.path.isfile(xif_source):
        return ET.ElementTree(file=xif_source)
    # fallback: treat input as raw xml string
    return ET.ElementTree(ET.fromstring(xif_source))

def load_image_rgba(path_or_url):
    """Load image (file or URL) and return RGBA Image."""
    if _URL_RE.match(path_or_url):
        data = fetch_url_bytes(path_or_url, headers={"User-Agent": useragent_string})
        return Image.open(_bytes_io(data)).convert("RGBA")
    return Image.open(path_or_url).convert("RGBA")

def resize_if_needed(img, target_w, target_h, resizetype):
    if img.size == (target_w, target_h):
        return img
    resample = _RESAMPLE.get((resizetype or "nearest").lower(), Image.NEAREST)
    return img.resize((target_w, target_h), resample)

def parse_points_from_coordinates(child, root_w, root_h):
    """
    Read nested <coordinates .../> elements into a flat tuple of ints: (x1,y1,x2,y2,...)
    Supports x/y percent.
    """
    pts = []
    for c in child.iter("coordinates"):
        x = coord_value(c.attrib.get("x", "0"), root_w)
        y = coord_value(c.attrib.get("y", "0"), root_h)
        pts.extend([x, y])
    return tuple(pts)

def parse_bbox_from_coordinates(child, root_w, root_h):
    """
    For bbox-based primitives (arc/chord/ellipse/pieslice/rectangle): expects either:
      A) two <coordinates x y/> nodes (top-left and bottom-right)
      or
      B) a single <coordinates x y width height/> node
    Returns (x1,y1,x2,y2).
    """
    coords = list(child.iter("coordinates"))
    if not coords:
        return (0, 0, 0, 0)

    # Case B: one node with width/height
    if len(coords) == 1 and ("width" in coords[0].attrib or "height" in coords[0].attrib):
        c = coords[0]
        x = coord_value(c.attrib.get("x", "0"), root_w)
        y = coord_value(c.attrib.get("y", "0"), root_h)
        w = coord_value(c.attrib.get("width", "0"), root_w)
        h = coord_value(c.attrib.get("height", "0"), root_h)
        return (x, y, x + w, y + h)

    # Case A: first two nodes define corners
    c1 = coords[0]
    c2 = coords[1] if len(coords) > 1 else coords[0]
    x1 = coord_value(c1.attrib.get("x", "0"), root_w)
    y1 = coord_value(c1.attrib.get("y", "0"), root_h)
    x2 = coord_value(c2.attrib.get("x", "0"), root_w)
    y2 = coord_value(c2.attrib.get("y", "0"), root_h)
    return (x1, y1, x2, y2)

def safe_int(val, default=0):
    try:
        return int(val)
    except Exception:
        return default


# ---------------------------
# Tag handlers
# ---------------------------

def handle_arc(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)
    bbox = parse_bbox_from_coordinates(child, root_w, root_h)
    draw.arc(bbox, safe_int(child.attrib.get("start", 0)), safe_int(child.attrib.get("end", 0)), fill=fill)

def handle_chord(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    outlinealpha = safe_int(child.attrib.get("outlinealpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)
    outline = parse_color_rgba(child.attrib.get("outline", "#000000"), outlinealpha)
    bbox = parse_bbox_from_coordinates(child, root_w, root_h)
    draw.chord(bbox, safe_int(child.attrib.get("start", 0)), safe_int(child.attrib.get("end", 0)), fill=fill, outline=outline)

def handle_ellipse(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    outlinealpha = safe_int(child.attrib.get("outlinealpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)
    outline = parse_color_rgba(child.attrib.get("outline", "#000000"), outlinealpha)
    bbox = parse_bbox_from_coordinates(child, root_w, root_h)
    draw.ellipse(bbox, fill=fill, outline=outline)

def handle_pieslice(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    outlinealpha = safe_int(child.attrib.get("outlinealpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)
    outline = parse_color_rgba(child.attrib.get("outline", "#000000"), outlinealpha)
    bbox = parse_bbox_from_coordinates(child, root_w, root_h)
    draw.pieslice(bbox, safe_int(child.attrib.get("start", 0)), safe_int(child.attrib.get("end", 0)), fill=fill, outline=outline)

def handle_line(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)  # fixed original bug
    pts = parse_points_from_coordinates(child, root_w, root_h)
    width = max(1, safe_int(child.attrib.get("width", 1), 1))
    draw.line(pts, fill=fill, width=width)

def handle_point(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)
    pts = parse_points_from_coordinates(child, root_w, root_h)
    draw.point(pts, fill=fill)

def handle_polygon(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    outlinealpha = safe_int(child.attrib.get("outlinealpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)
    outline = parse_color_rgba(child.attrib.get("outline", "#000000"), outlinealpha)
    pts = parse_points_from_coordinates(child, root_w, root_h)
    draw.polygon(pts, fill=fill, outline=outline)

def handle_rectangle(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    outlinealpha = safe_int(child.attrib.get("outlinealpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)
    outline = parse_color_rgba(child.attrib.get("outline", "#000000"), outlinealpha)
    bbox = parse_bbox_from_coordinates(child, root_w, root_h)
    draw.rectangle(bbox, fill=fill, outline=outline)

def handle_text(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)
    pts = parse_points_from_coordinates(child, root_w, root_h)
    x, y = (pts[0], pts[1]) if len(pts) >= 2 else (0, 0)

    size = child.attrib.get("size", "12")
    if _PCT_RE.match(str(size).strip()):
        size = coord_value(size, root_h)
    size = max(1, safe_int(size, 12))

    font_path = child.attrib.get("font", "")
    text_value = child.attrib.get("text", "")

    # Load font (fallback to default)
    try:
        font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    draw.text((x, y), text_value, fill=fill, font=font)

def handle_multiline_text(draw, base_img, child, root_w, root_h, resizetype):
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)
    pts = parse_points_from_coordinates(child, root_w, root_h)
    x, y = (pts[0], pts[1]) if len(pts) >= 2 else (0, 0)

    # text is in <string> node in original
    text_value = ""
    for s in child.iter("string"):
        if s.text:
            text_value = s.text
            break

    size = child.attrib.get("size", "12")
    if _PCT_RE.match(str(size).strip()):
        size = coord_value(size, root_h)
    size = max(1, safe_int(size, 12))

    spacing = safe_int(child.attrib.get("spacing", 0), 0)
    align = child.attrib.get("align", "left")
    font_path = child.attrib.get("font", "")

    try:
        font = ImageFont.truetype(font_path, size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    draw.multiline_text((x, y), text_value, fill=fill, font=font, spacing=spacing, align=align)

def handle_picture(draw, base_img, child, root_w, root_h, resizetype):
    # picture/photo: paste RGBA image
    pts = parse_points_from_coordinates(child, root_w, root_h)
    x, y = (pts[0], pts[1]) if len(pts) >= 2 else (0, 0)

    img_path = child.attrib.get("file", "")
    if not img_path:
        return

    tmp = load_image_rgba(img_path)

    w = child.attrib.get("width", str(tmp.size[0]))
    h = child.attrib.get("height", str(tmp.size[1]))
    if _PCT_RE.match(str(w).strip()):
        w = coord_value(w, root_w)
    if _PCT_RE.match(str(h).strip()):
        h = coord_value(h, root_h)
    w = max(1, safe_int(w, tmp.size[0]))
    h = max(1, safe_int(h, tmp.size[1]))

    tmp = resize_if_needed(tmp, w, h, resizetype)
    base_img.paste(tmp, (x, y), tmp)

def handle_bitmap(draw, base_img, child, root_w, root_h, resizetype):
    # Keep behavior close to original: draw.bitmap with optional fill
    alpha = safe_int(child.attrib.get("alpha", 255), 255)
    fill = parse_color_rgba(child.attrib.get("fill", "#000000"), alpha)

    pts = parse_points_from_coordinates(child, root_w, root_h)
    x, y = (pts[0], pts[1]) if len(pts) >= 2 else (0, 0)

    img_path = child.attrib.get("file", "")
    if not img_path:
        return

    tmp = load_image_rgba(img_path)

    w = child.attrib.get("width", str(tmp.size[0]))
    h = child.attrib.get("height", str(tmp.size[1]))
    if _PCT_RE.match(str(w).strip()):
        w = coord_value(w, root_w)
    if _PCT_RE.match(str(h).strip()):
        h = coord_value(h, root_h)
    w = max(1, safe_int(w, tmp.size[0]))
    h = max(1, safe_int(h, tmp.size[1]))

    tmp = resize_if_needed(tmp, w, h, resizetype)

    # draw.bitmap expects a mask-like image in some modes; original used it anyway.
    # We'll keep it but fall back to paste if bitmap fails.
    try:
        draw.bitmap((x, y), tmp, fill=fill)
    except Exception:
        base_img.paste(tmp, (x, y), tmp)

def handle_barcode(draw, base_img, child, root_w, root_h, resizetype):
    pts = parse_points_from_coordinates(child, root_w, root_h)
    x, y = (pts[0], pts[1]) if len(pts) >= 2 else (0, 0)

    bctype = child.attrib.get("type", "")
    code = child.attrib.get("code", "")

    if not bctype or not code:
        return

    # Build kwargs similarly to original
    kw = {"bctype": bctype, "upc": code}

    if "size" in child.attrib:
        kw["resize"] = safe_int(child.attrib["size"], 1)

    if "hideinfo" in child.attrib:
        parts = child.attrib["hideinfo"].split()
        if len(parts) >= 3:
            kw["hideinfo"] = (parts[0] == "1", parts[1] == "1", parts[2] == "1")

    if "height" in child.attrib:
        try:
            kw["barheight"] = tuple(map(int, child.attrib["height"].split()))
        except Exception:
            pass

    if "textxy" in child.attrib:
        try:
            kw["textxy"] = tuple(map(int, child.attrib["textxy"].split()))
        except Exception:
            pass

    if "color" in child.attrib:
        # expects 3 colors separated by spaces
        cols = child.attrib["color"].split()
        if len(cols) >= 3:
            c1 = parse_color_rgb(cols[0].strip())
            c2 = parse_color_rgb(cols[1].strip())
            c3 = parse_color_rgb(cols[2].strip())
            if c1 and c2 and c3:
                kw["barcolor"] = (c1, c2, c3)

    bc_img = upcean.barcodes.shortcuts.validate_draw_barcode(**kw).convert("RGBA")
    base_img.paste(bc_img, (x, y), bc_img)

# Dispatch table (aliases included)
HANDLERS = {
    "arc": handle_arc,
    "barcode": handle_barcode,
    "bitmap": handle_bitmap,
    "chord": handle_chord,
    "ellipse": handle_ellipse,
    "line": handle_line,
    "multilinetext": handle_multiline_text,
    "picture": handle_picture,
    "photo": handle_picture,
    "pieslice": handle_pieslice,
    "point": handle_point,
    "dot": handle_point,
    "polygon": handle_polygon,
    "rect": handle_rectangle,        # original used rect in places
    "rectangle": handle_rectangle,
    "square": handle_rectangle,
    "text": handle_text,
}


# ---------------------------
# Main renderer
# ---------------------------

def xml_draw_image(xif_source, imgtype="png", outputimage=True, resize=1, resizetype="nearest", outfile=None):
    if not outfile and outputimage:
        raise ValueError("outfile is required when outputimage=True")

    if not isinstance(resize, int):
        try:
            resize = int(resize)
        except Exception:
            resize = 1
    if resize < 1:
        resize = 1

    resizetype = (resizetype or "nearest").lower()
    if resizetype not in _RESAMPLE:
        resizetype = "nearest"

    tree = load_xml_tree(xif_source)
    root = tree.getroot()

    root_w = safe_int(root.attrib.get("width", 0), 0)
    root_h = safe_int(root.attrib.get("height", 0), 0)
    if root_w <= 0 or root_h <= 0:
        raise ValueError("Root element must have valid width and height attributes.")

    bg = parse_color_rgb(root.attrib.get("fill", "#FFFFFF")) or (255, 255, 255)

    base = Image.new("RGB", (root_w, root_h), color=bg)
    draw = ImageDraw.Draw(base, "RGBA")

    for child in list(root):
        tag = (child.tag or "").lower().strip()
        handler = HANDLERS.get(tag)
        if handler:
            handler(draw, base, child, root_w, root_h, resizetype)

    # Final resize (integer scale)
    if resize > 1:
        new_w, new_h = root_w * resize, root_h * resize
        base = resize_if_needed(base, new_w, new_h, resizetype)

    if outputimage:
        base.save(outfile, imgtype)
        return True

    return base


def main():
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("-i", "--input", required=True, help="Input XML file path or URL")
    parser.add_argument("-t", "--outputtype", default="png", help="Output image format (png, jpg, etc.)")
    parser.add_argument("-o", "--output", required=True, help="Output image filename")
    parser.add_argument("-s", "--resize", default=1, help="Integer scale factor (>=1)")
    parser.add_argument("-r", "--resizetype", default="nearest", help="nearest|bilinear|bicubic|antialias")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    args = parser.parse_args()

    xml_draw_image(
        xif_source=args.input,
        imgtype=args.outputtype,
        outputimage=True,
        resize=int(args.resize) if str(args.resize).isdigit() else 1,
        resizetype=args.resizetype,
        outfile=args.output
    )

if __name__ == "__main__":
    # cleaner tracebacks like original did
    sys.tracebacklimit = 0
    main()
