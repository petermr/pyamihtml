import os

import lxml.etree

from pyamihtmlx.ami_html import HtmlStyle
from pyamihtmlx.xml_lib import XmlLib, HtmlLib
from test.test_all import AmiAnyTest


class TestXml(AmiAnyTest):

    def test_is_integer(self):
        span = lxml.etree.Element("span")
        span.text = "12"
        assert XmlLib.is_integer(span), f"an integer {span}"

        span.text = "+12"
        assert XmlLib.is_integer(span), f"an integer {span}"

        span.text = "-12"
        assert XmlLib.is_integer(span), f"integer {span.text}"

        span.text = "b12"
        assert not XmlLib.is_integer(span), f"not an integer {span.text}"

        span.text = "-12.0"
        assert not XmlLib.is_integer(span), f"not an integer {span.text}"

    def test_split_span_by_regex(self):
        """
        takes simple HTML element:
        div
            span
        and splits the span with a regex, annotating the results
        adds classes
        tackles most of functionality

        """
        div = lxml.etree.Element("div")
        div.attrib["pos"] = "top"
        span = lxml.etree.SubElement(div, "span")
        span.attrib["biff"] = "boff"
        span.text = "This is foo and bar and more foo marked and plugh and foo not marked"
        regex = "fo+" # searches for strings of form fo, foo, for etc
        ids = ["id0", "id1", "id2"] # ids to give new spans
        clazz = ["class0", ":class1", "class2"] # classes for result
        XmlLib.split_span_by_regex(span, regex, ids=ids, clazz=clazz, href="https://google.com")

        file = os.path.expanduser('~') + "/junk.html"
        print(file)
        html = HtmlLib.create_html_with_empty_head_body()
        styles =  [
            (".class0", [("color", "red;")]),
            (".class1", [("background", "#ccccff;")]),
            (".class2", [("color", "#00cc00;")]),
        ]

        HtmlStyle.add_head_styles_orig(html, styles)
        HtmlLib.get_body(html).append(div)
        HtmlLib.write_html_file(html, file, debug=True)
