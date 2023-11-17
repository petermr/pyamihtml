import os

import lxml.etree
from pyamihtml.xml_lib import XmlLib, HtmlLib
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
        div = lxml.etree.Element("div")
        div.attrib["pos"] = "top"
        span = lxml.etree.SubElement(div, "span")
        span.attrib["biff"] = "boff"
        span.text = "This is foo and bar and more foo and plugh"
        regex = "fo*"
        XmlLib.split_span_by_regex(span, regex, id="foo_bar", href="https://google.com")

        file = os.path.expanduser('~') + "/junk.html"
        print(file)
        html = HtmlLib.create_html_with_empty_head_body()
        HtmlLib.get_body(html).append(div)
        HtmlLib.write_html_file(html, file)

