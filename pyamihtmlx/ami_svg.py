import lxml.etree

from pyamihtmlx.util import AmiLogger, Util
from pyamihtmlx.xml_lib import NS_MAP, XML_NS, SVG_NS

SVG_SVG = "svg"
SVG_G = "g"
SVG_CIRCLE = "circle"
SVG_LINE = "line"
SVG_POLYLINE = "polyline"
SVG_RECT = "rect"
SVG_PATH = "path"

# path attrs
SVG_d = "d"
SVG_H = "H"
SVG_h = "h"
SVG_C = "C"
SVG_c = "c"
SVG_L = "L"
SVG_l = "l"
SVG_M = "M"
SVG_m = "m"
SVG_Q = "Q"
SVG_q = "q"
SVG_V = "V"
SVG_v = "v"

# coord attrs
X1 = "x1"
X2 = "x2"
Y1 = "y1"
Y2 = "y2"

POINTS = "points"
FILL = "fill"
STROKE = "stroke"
STROKE_WIDTH = "stroke-width"

logger = AmiLogger.create_named_logger(__file__)

class AmiSVG:
    """for actually rendering SVG?"""

    def __init__(self):
        pass

    @classmethod
    def create_SVGElement(cls, tag):
        svg_ns = NS_MAP[SVG_NS]
        return lxml.etree.Element(f"{{{svg_ns}}}{tag}")

    @classmethod
    def create_svg(cls):
        svg_elem = cls.create_SVGElement(SVG_SVG)
        return svg_elem

    @classmethod
    def create_circle(cls, xy, r, parent=None,  fill="yellow", stroke="red", stroke_width=1):
        circle_elem = None
        if xy and r:
            circle_elem = cls.create_SVGElement(SVG_CIRCLE)
            circle_elem.attrib["cx"] = str(xy[0])
            circle_elem.attrib["cy"] = str(xy[1])
            circle_elem.attrib["r"] = str(r)
            circle_elem.attrib["fill"] = fill
            circle_elem.attrib["stroke"] = stroke
            circle_elem.attrib["stroke-width"] = str(stroke_width)
        if parent is not None:
            parent.append(circle_elem)
        return circle_elem

    @classmethod
    def create_polyline(cls, xy_array, parent=None, fill="yellow", stroke="red", stroke_width=1, ndec=2):
        """
        creates svg:polyline
        :param xy_array: N*2 array of row-wies x,y coords
        :param parent: if not none, use ase parent element
        :param fill: default 'yellow'
        :param stroke: default red
        :param stroke_width: default 1
        :return: lxml namespaced svg:polyline
        """
        polyline_elem = None
        if xy_array:
            polyline_elem = cls.create_SVGElement(SVG_POLYLINE)
            points = ""
            for i, xy in enumerate(xy_array):
                if i > 0:
                    points += " "
                points += str(round(xy[0], ndec))+","+str(round(xy[1], ndec))
            polyline_elem.attrib[POINTS] = points
            polyline_elem.attrib[FILL] = fill
            polyline_elem.attrib[STROKE] = stroke
            polyline_elem.attrib[STROKE_WIDTH] = str(stroke_width)

        if parent is not None:
            parent.append(polyline_elem)
        return polyline_elem

    @classmethod
    def create_rect(cls, x0y0x1y1, parent=None, fill="gray", stroke="blue", stroke_width=0.3):
        """
        requires coords in  form [x1, y1, x2, y2]
        :param x0y0x1y1: coords in  form [x1, y1, x2, y2]
        :param parent: if not None, appends to this
        """
        logger.debug(f"box {x0y0x1y1}")
        svg_rect = AmiSVG.create_SVGElement(SVG_RECT)
        svg_rect.attrib["fill"] = fill
        svg_rect.attrib["stroke"] = stroke
        svg_rect.attrib["stroke-width"] = str(stroke_width)
        try:
            width = x0y0x1y1[2] - x0y0x1y1[0]
            height = x0y0x1y1[3] - x0y0x1y1[1]
        except Exception as e:
            raise ValueError(f"bbox must be four floats [x0, y0, x1, y1], got {x0y0x1y1}")
        svg_rect.attrib["x"] = str(x0y0x1y1[0])
        svg_rect.attrib["y"] = str(x0y0x1y1[1])
        svg_rect.attrib["width"] = str(width)
        svg_rect.attrib["height"] = str(height)
        if parent is not None:
            parent.append(svg_rect)
        return svg_rect

    @classmethod
    def get_x_y_width_height(cls, svg_rect):
        """requires svg_rect to have canonical form x,y,w,h
        """

        x = Util.get_float(svg_rect.attrib.get("x"))
        y = Util.get_float(svg_rect.attrib.get("y"))
        width = Util.get_float(svg_rect.attrib.get("width"))
        height = Util.get_float(svg_rect.attrib.get("height"))
        return (x, y, width, height)

    @classmethod
    def create_canonical_rect(cls, params):
        """doesn't yet do attributes
        params can be [x0, y0, x1, y1] or [[x0, x1], [y0, y1]]"""
        if type(params) is list:
            if len(list) == 4:
                rect = AmiSVG.create_rect()

    @classmethod
    def create_hline(cls, x0, y0, width):
        svg_line = AmiSVG.create_SVGElement(SVG_LINE)
        svg_line.attrib[X1] = str(x0)
        svg_line.attrib[X2] = str(x0 + width)
        svg_line.attrib[Y1] = str(y0)
        svg_line.attrib[Y2] = str(y0)
        return svg_line

    @classmethod
    def create_vline(cls, x0, y0, height):
        svg_line = AmiSVG.create_SVGElement(SVG_LINE)
        svg_line.attrib[X1] = str(x0)
        svg_line.attrib[X2] = str(x0)
        svg_line.attrib[Y1] = str(y0)
        svg_line.attrib[Y2] = str(y0 + height)
        return svg_line

