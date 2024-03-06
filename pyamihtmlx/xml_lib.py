import copy
import logging
import os
import re
from pathlib import Path
from urllib.request import urlopen

import chardet
import lxml
import lxml.etree
import requests
from lxml import etree as ET
from lxml.etree import _Element, _ElementTree
from lxml.html import HTMLParser

from pyamihtmlx.file_lib import FileLib

# from pyamihtmlx.util import EnhancedRegex

logging.debug("loading xml_lib")

# make leafnodes and copy remaning content as XML
TERMINAL_COPY = {
    "abstract",
    "aff",
    "article-id",
    "article-categories",
    "author-notes",
    "caption",
    "contrib-group",
    "fig",
    "history",
    "issue",
    "journal_id",
    "journal-title-group",
    "kwd-group",
    "name",
    "notes",
    "p",
    "permissions",
    "person-group",
    "pub-date",
    "publisher",
    "ref",
    "table",
    "title",
    "title-group",
    "volume",
}

TERMINALS = [
    "inline-formula",
]

TITLE = "title"

IGNORE_CHILDREN = {
    "disp-formula",
}

HTML_TAGS = {
    "italic": "i",
    "p": "p",
    "sub": "sub",
    "sup": "sup",
    "tr": "tr",
}

H_TD = "td"
H_TR = "tr"
H_TH = "th"
LINK = "link"
UTF_8 = "UTF-8"
SCRIPT = "script"
STYLESHEET = "stylesheet"
TEXT_CSS = "text/css"
TEXT_JAVASCRIPT = "text/javascript"

H_HTML = "html"
H_BODY = "body"
H_TBODY = "tbody"
H_DIV = "div"
H_TABLE = "table"
H_THEAD = "thead"
H_HEAD = "head"
H_TITLE = "title"

RESULTS = "results"

SEC_TAGS = {
    "sec",
}

LINK_TAGS = {
    "xref",
}

SECTIONS = "sections"

HTML_NS = "HTML_NS"
MATHML_NS = "MATHML_NS"
SVG_NS = "SVG_NS"
XMLNS_NS = "XMLNS_NS"
XML_NS = "XML_NS"
XLINK_NS = "XLINK_NS"

XML_LANG = "{" + XML_NS + "}" + 'lang'

NS_MAP = {
    HTML_NS: "http://www.w3.org/1999/xhtml",
    MATHML_NS: "http://www.w3.org/1998/Math/MathML",
    SVG_NS: "http://www.w3.org/2000/svg",
    XLINK_NS: "http://www.w3.org/1999/xlink",
    XML_NS: "http://www.w3.org/XML/1998/namespace",
    XMLNS_NS: "http://www.w3.org/2000/xmlns/",
}

DEFAULT_DECLUTTER = [
    ".//style",
    ".//script",
    ".//noscript",
    ".//meta",
    ".//link",
    ".//button",
    ".//picture",
    ".//svg",  # the IPCC logo swamps the first page
    # "//footer",
    ".//textarea",
    # ".//img"
]

DECLUTTER_BASIC = [
    ".//style",
    ".//script",
    ".//noscript",
    ".//meta",
    ".//link",
    ".//textarea",
]

# elemnts which cause display problems
BAD_DISPLAY = [
    "//i[not(node())]",
    "//a[@href and not(node())]",
    "//div[contains(@style, 'position:absolute')]"
]

logger = logging.getLogger("xml_lib")
logger.setLevel(logging.WARNING)
logging.debug(f"===========LOGGING {logger.level} .. {logging.DEBUG}")


class XmlLib:

    def __init__(self, file=None, section_dir=SECTIONS):
        self.max_file_len = 30
        self.file = file
        self.parent_path = None
        self.root = None
        self.logger = logging.getLogger("xmllib")
        self.section_dir = section_dir
        self.section_path = None

    #         self.logger.setLevel(logging.INFO)

    def read(self, file):
        """reads XML file , saves file, and parses to self.root"""
        if file is not None:
            self.file = file
            self.parent_path = Path(file).parent.absolute()
            self.root = XmlLib.parse_xml_file_to_root(file)

    def make_sections(self, section_dir):
        """recursively traverse XML tree and write files for each terminal element"""
        self.section_dir = self.make_sections_path(section_dir)
        # indent = 0
        # filename = "1" + "_" + self.root.tag
        # self.logger.debug(" " * indent, filename)
        # subdir = os.path.join(self.section_dir, filename)
        # FileLib.force_mkdir(subdir)

        self.make_descendant_tree(self.root, self.section_dir)
        self.logger.info(
            f"wrote XML sections for {self.file} {self.section_dir}")

    @staticmethod
    def parse_xml_file_to_root(file):
        """read xml path and create root element"""
        file = str(file)  # if file is Path
        if not os.path.exists(file):
            raise IOError("path does not exist", file)
        xmlp = ET.XMLParser(encoding=UTF_8)
        element_tree = ET.parse(file, xmlp)
        root = element_tree.getroot()
        return root

    @staticmethod
    def parse_xml_string_to_root(xml):
        """read xml string and parse to root element"""
        from io import StringIO
        tree = ET.parse(StringIO(xml), ET.XMLParser(ns_clean=True))
        return tree.getroot()

    @classmethod
    def parse_url_to_tree(cls, url):
        """parses URL to lxml tree
        :param url: to parse
        :return: lxml tree"""
        with urlopen(url) as f:
            tree = lxml.etree.parse(f)
            """
    def get_html(url, retry_count=0):
    try:
        request = Request(url)
        response = urlopen(request)
        html = response.read()
    except ConectionResetError as e:
        if retry_count == MAX_RETRIES:
            raise e
        time.sleep(for_some_time)
        get_html(url, retry_count + 1)
        """
        return tree

    def make_sections_path(self, section_dir):
        self.section_path = os.path.join(self.parent_path, section_dir)
        if not os.path.exists(self.section_path):
            FileLib.force_mkdir(self.section_path)
        return self.section_path

    def make_descendant_tree(self, elem, outdir):

        self.logger.setLevel(logging.INFO)
        if elem.tag in TERMINALS:
            self.logger.debug("skipped ", elem.tag)
            return
        TERMINAL = "T_"
        IGNORE = "I_"
        children = list(elem)
        self.logger.debug(f"children> {len(children)} .. {self.logger.level}")
        isect = 0
        for child in children:
            if "ProcessingInstruction" in str(type(child)):
                # print("PI", child)
                continue
            if "Comment" in str(type(child)):
                continue
            flag = ""
            child_child_count = len(list(child))
            if child.tag in TERMINAL_COPY or child_child_count == 0:
                flag = TERMINAL
            elif child.tag in IGNORE_CHILDREN:
                flag = IGNORE

            title = child.tag
            if child.tag in SEC_TAGS:
                title = XmlLib.get_sec_title(child)

            if flag == IGNORE:
                title = flag + title
            filename = str(
                isect) + "_" + FileLib.punct2underscore(title).lower()[:self.max_file_len]

            if flag == TERMINAL:
                xml_string = ET.tostring(child)
                filename1 = os.path.join(outdir, filename + '.xml')
                self.logger.setLevel(logging.INFO)
                self.logger.debug(f"writing dbg {filename1}")
                try:
                    with open(filename1, "wb") as f:
                        f.write(xml_string)
                except Exception:
                    print(f"cannot write {filename1}")
            else:
                subdir = os.path.join(outdir, filename)
                # creates empty dirx, may be bad idea
                FileLib.force_mkdir(subdir)
                if flag == "":
                    self.logger.debug(f">> {title} {child}")
                    self.make_descendant_tree(child, subdir)
            isect += 1

    @staticmethod
    def get_sec_title(sec):
        """get title of JATS section

        :sec: section (normally sec element
        """
        title = None
        for elem in list(sec):
            if elem.tag == TITLE:
                title = elem.text
                break

        if title is None:
            # don't know where the 'xml_file' comes from...
            if not hasattr(sec, "xml_file"):
                title = "UNKNOWN"
            else:
                title = "?_" + str(sec["xml_file"][:20])
        title = FileLib.punct2underscore(title)
        return title

    @staticmethod
    def remove_all(elem, xpaths, debug=False):
        """removes all sub/elements in result of applying xpath
        :param elem: to remove sub/elements from
        :param xpaths: """
        xpaths = [xpaths] if type(xpaths) is str else xpaths
        if debug:
            print(f"xpaths for removal {xpaths}")
        for xpath in xpaths:
            elems = elem.xpath(xpath)
            if debug:
                print(f"elems to remove {elems}")
            for el in elems:
                if el.getparent() is not None:
                    el.getparent().remove(el)

    @staticmethod
    def get_or_create_child(parent, tag):
        child = None
        if parent is not None:
            child = parent.find(tag)
            if child is None:
                child = ET.SubElement(parent, tag)
        return child

    @classmethod
    def get_text(cls, node):
        """
        get text children as string
        """
        return ''.join(node.itertext())

    @staticmethod
    def add_UTF8(html_root):
        """adds UTF8 declaration to root

        """
        from lxml import etree as LXET
        root = html_root.get_or_create_child(html_root, "head")
        LXET.SubElement(root, "meta").attrib["charset"] = "UTF-8"

    # replace nodes with text
    @staticmethod
    def replace_nodes_with_text(data, xpath, replacement):
        """replace nodes with specific text

        """
        print(data, xpath, replacement)
        tree = ET.fromstring(data)
        for r in tree.xpath(xpath):
            XmlLib.replace_node_with_text(r, replacement)
        return tree

    @classmethod
    def replace_node_with_text(cls, r, replacement):
        print("r", r, replacement, r.tail)
        text = replacement
        if r.tail is not None:
            text += r.tail
        parent = r.getparent()
        if parent is not None:
            previous = r.getprevious()
            if previous is not None:
                previous.tail = (previous.tail or '') + text
            else:
                parent.text = (parent.text or '') + text
            parent.remove(r)

    @classmethod
    def remove_all_tags(cls, xml_string):
        """remove all tags from text

        :xml_string: string to be flattened
        :returns: flattened string
        """
        tree = ET.fromstring(xml_string.encode("utf-8"))
        strg = ET.tostring(tree, encoding='utf8',
                           method='text').decode("utf-8")
        return strg

    @classmethod
    def remove_elements(cls, elem, xpath, new_parent=None, debug=False):
        """remove all elems matching xpath
        :param elem: to remove elements from
        :param xpath: to select removable elemnts
        :param new_parent: new parent for removed nodes
        :param debug: output debug (def = False)
        """
        elems = elem.xpath(xpath, debug=True)
        if debug:
            print(f"{xpath} removes {len(elems)} elems")
        for elem in elems:
            XmlLib.remove_element(elem), debug
            if new_parent is not None:
                new_parent.append(elem)

    @classmethod
    def xslt_transform(cls, xmlstring, xslt_file):
        """transforms xmlstring using xslt
        :param xmlstring: xml string to transform
        :param xslt_file: stylesheet as xslt
        :return: transformed object"""
        xslt_root = ET.parse(xslt_file)
        root = cls.transform_xml_object(xmlstring, xslt_root)

        return root

    @classmethod
    def transform_xml_object(cls, xmlstring, xslt_root):
        """
        transforms html string using XSLT
        :param xmlstring: well-formed XML string
        :param xslt_root: xslt file (may include relative links)
        :return: transformed XML object
        """

        transform = ET.XSLT(xslt_root)
        if transform.error_log:
            print("bad xsl? XSLT log", transform.error_log)
        result_tree = transform(xmlstring)
        assert (result_tree is not None)
        html_root = result_tree.getroot()
        assert html_root is not None
        assert len(html_root.xpath("//*")) > 0
        return html_root

    @classmethod
    def xslt_transform_tostring(cls, data, xslt_file):
        root = cls.xslt_transform(data, xslt_file)
        return ET.tostring(root).decode("UTF-8") if root is not None else None

    @classmethod
    def validate_xpath(cls, xpath):
        """
        crude syntax validation of xpath string.
        tests xpath on a trivial element
        :param xpath:
        """
        tree = lxml.etree.fromstring("<foo/>")
        try:
            tree.xpath(xpath)
        except lxml.etree.XPathEvalError as e:
            logging.error(f"bad XPath {xpath}, {e}")
            raise e

    @classmethod
    def does_element_equal_serialized_string(cls, elem, string):
        try:
            elem1 = lxml.etree.fromstring(string)
            return cls.are_elements_equal(elem, elem1)
        except Exception:
            return False

    @classmethod
    def are_elements_equal(cls, e1, e2):
        """compares 2 elements
        :param e1:
        :param e2:
        :return: False if not equal
        """
        if type(e1) is not lxml.etree._Element or type(e2) is not lxml.etree._Element:
            raise ValueError(f" not a pair of XML elements {e1} {e2}")
        if e1.tag != e2.tag:
            return False
        if e1.text != e2.text:
            return False
        if e1.tail != e2.tail:
            return False
        if e1.attrib != e2.attrib:
            return False
        if len(e1) != len(e2):
            return False
        return all(cls.are_elements_equal(c1, c2) for c1, c2 in zip(e1, e2))

    @classmethod
    def write_xml(cls, elem, path, encoding="UTF-8", method="xml", debug=False, mkdir=True):
        """
        Writes XML to file
        :param elem: xml element to write
        :param path: path to write to
        :param method: xml default, could be html
        :except: bad encoding
        The use of encoding='UTF-8' is because lxml has a bug in some releases
        """
        if not path:
            return
        path = Path(path)
        if mkdir:
            path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            try:
                # this solves some problems but not unknown font encodings
                # xmlstr = lxml.etree.tostring(elem, encoding='UTF-8').decode(encoding)

                xmlstr = lxml.etree.tostring(elem).decode(encoding)
            except Exception as e:
                raise ValueError(f"****** cannot decode XML to {path}: {e} *******")
            try:
                if debug:
                    print(f"writing XML {path}")
                f.write(xmlstr)
            except Exception as ee:
                raise Exception(f"cannot write XMLString {ee}")

    @classmethod
    def remove_attribute(cls, elem, att):
        """
        removes at attribute (by name) if it exists
        :param elem: element with the attribute
        :param att: att_name to delete
        """
        if elem is not None and att in elem.attrib:
            del elem.attrib[att]

    @classmethod
    def delete_atts(cls, attnames, span):
        for att in attnames:
            attval = span.attrib.get(att)
            if attval:
                del (span.attrib[att])

    @classmethod
    def set_attname_value(cls, elem, attname, value):
        """
        set attribute, if value==None remove attribute
        :param elem: element with attribute
        :param attname: attribute name
        :param value: attribute value; if "" or None remove attribute
        """
        if value is None or value == "":
            XmlLib.remove_attribute(elem, attname)
        else:
            elem.attrib[attname] = value

    @classmethod
    def remove_element(cls, elem):
        """cnvenience method to remove element from tree
        :param elem: elem to be removed
        no-op if elem or its parent is None"""
        # does not remove tail (I don't think)
        if elem is not None:
            parent = elem.getparent()
            if parent is not None:
                parent.remove(elem)

    @classmethod
    def get_next_element(cls, elem):
        """
        get next element after elem
        convenience method to use following::
        :param elem: element in tree
        :return: next elemnt or None
        """
        nexts = elem.xpath("following::*")
        return None if len(nexts) == 0 else nexts[0]

    @classmethod
    def get_following_elements(cls, elem, predicate=None, count=9999):
        """
        get next elements after elem
        convenience method to use following::
        :param elem: element in tree
        :param predicate: condition (with the []), e.g "[@class='.s1010']"
        :return: next elemnts or empty list
        """
        pred_string = f"" if predicate is None else f"{predicate}"
        xp = f"following::*{pred_string}"
        xp = f"following::*"
        print(f"xp: {xp} {lxml.etree.tostring(elem)}")
        nexts = elem.xpath(xp)
        # next = None if len(nexts) == 0 else nexts[:count]
        print(f"nexts {len(nexts)}")
        return nexts

    @classmethod
    def getparent(cls, elem, debug=False):
        if elem is None:
            return None
        parent = elem.getparent()
        if parent is None and debug:
            print(f" parent of {elem} is None")
        return parent

    @classmethod
    def read_xml_element_from_github(cls, github_url=None, url_cache=None):
        """reads raw xml and parses to elem

        ent. Errors uncaught
        """
        if not github_url:
            return None
        # print(f"url: {github_url}")
        if url_cache:
            xml_elem = url_cache.read_xml_element_from_github(github_url)
        else:
            xml_elem = lxml.etree.fromstring(requests.get(github_url).text)
        return xml_elem

    @classmethod
    def is_integer(cls, elem):
        """test whether text content parses as an integer"""
        try:
            i = int(elem.text)
            return True
        except Exception as e:
            return False

    @classmethod
    def remove_common_clutter(cls, elem, declutter=None, bad_display=None):
        """
        :param elem: to declutter
        :param declutter: If None
        :param debug: print removed elements
        """
        if elem is None:
            print(f"remove clutter : element is None")
            return
        if declutter is None:
            declutter = DEFAULT_DECLUTTER

        cls.remove_all(elem, declutter)
        #  this causes display problems
        bad_display = BAD_DISPLAY if bad_display is None else bad_display
        cls.remove_all(elem, bad_display)

    @classmethod
    def replaceStrings(cls, text_elem, strings, debug=False):
        """edit text child of element

        :param text_elem: element with text child
        :param strings: list od tuples (oldstring, newstring)
        :return: 0 if no change, 1 if change
        """
        t1 = text_elem.text
        if t1:
            t2 = t1
            t2 = cls.iteratively_replace_strings(strings, t2)

            if t2 != t1:
                if debug:
                    print(f"replaced {t1} by {t2}")
                text_elem.text = t2
                return 1
        return 0

    @classmethod
    def iteratively_replace_strings(cls, strings, t2):
        """iterates over list of (old, new) pukles to replace substrings
        """
        for string in strings:
            t2 = t2.replace(string[0], string[1])
        return t2

    @classmethod
    def replace_substrings_in_all_child_texts(cls, html_elem, subs_list, debug=False):
        """
        edit all text children of elements, replacing oldstr with newstr
        :param html_elem: elements with texts to edit
        :param subs_list: list of (oldStr, newstr) pairs
        """
        text_elems = html_elem.xpath(".//*[text()]")
        for text_elem in text_elems:
            XmlLib.replaceStrings(text_elem, subs_list, debug=debug)

    @classmethod
    def split_span_by_regex(cls, span, regex, ids=None, href=None, clazz=None, markup_dict=None, repeat=0):
        """this is phased out in favour or templates
        """
        """split a span into 3 sections but matching substring
        <parent><span attribs>foo bar plugh</span></parent>
        if "bar" matches regex gives:
        <parent><span attribs>foo </span><span attribs id=id>bar</span><span attribs> plugh</span></parent>
        if count > 1, repeats the splitting on the new RH span , decrementing repeat until zero

        :param span: the span to split
        :param regex: finds (first) match in span.text and extracts matched text into middle span
        :param id: if string, adds id to new mid element; if array of len 3 gives id[0], id[1], id[2] to each new span
        :param href: adds <a href=href>matched-text</a> as child of mid span (1) if un.GENERATE generates HREF
        :param clazz: 3-element array to add class attributes to split sections
        :param repeat: repeats split on (new) rh span
        :return: None if no match, else first match in span
        """
        print(f"USE TEMPLATES INSTEAD for HREF or ID generation")
        type_span = type(span)
        parent = span.getparent()

        if span is None or regex is None or type_span is not lxml.etree._Element \
                or parent is None or span.tag != 'span' or repeat < 0:
            return None
        text = span.text
        if text is None:
            # print(f"text is None")
            return None
        if regex is None:
            print("regex is None")
            return None
        match = None
        try:
            match = re.search(regex, text)
        except Exception as e:
            print(f"bad match {regex} /{e} --> {text}")
            return
        idx = parent.index(span)
        dummy_templater = Templater()
        # enhanced_regex = EnhancedRegex(regex=regex)
        if match:
            anchor_text = match.group(0)
            print(f"matched: {regex} {anchor_text}")
            # href_new = enhanced_regex.get_href(href, text=anchor_text)
            # make 3 new spans
            # some may be empty
            offset = 1
            offset, span0 = cls.create_span(idx, match, offset, parent, span, text, "start")
            href_new = None
            mid = dummy_templater.create_new_span_with_optional_a_href_child(parent, idx + offset, span, anchor_text,
                                                                             href=href_new)
            offset += 1
            offset, span2 = cls.create_span(idx, match, offset, parent, span, text, "end")
            # span_last_text = text[match.span()[1]:]
            # if len(span_last_text) > 0 :
            #     span2 = cls.new_span(parent, idx + offset, span, span_last_text)
            # else:
            #     print(f"zero-length span2 in {span.text}")
            if ids and type(ids) is str:
                ids = [None, ids, None]
            if ids and len(ids) == 3:
                if span0 is not None:
                    span0.attrib["id"] = ids[0]
                mid.attrib["id"] = ids[1]
                if span2 is not None:
                    span2.attrib["id"] = ids[2]
            if clazz and len(clazz) == 3:
                if span0 is not None:
                    span0.attrib["class"] = clazz[0]
                mid.attrib["class"] = clazz[1]
                if span2 is not None:
                    span2.attrib["class"] = clazz[2]
            clazz = None if not markup_dict else markup_dict.get("class")
            if clazz is not None:
                mid.attrib["class"] = clazz
            if span2 is not None:
                print(f"style {span2.attrib.get('style')}")

            parent.remove(span)
            # recurse in RH split
            if regex is None:
                print("no regex")
                return
            if repeat > 0:
                repeat -= 1
                cls.split_span_by_regex(span2, regex, ids=ids, href=href, repeat=repeat)
        return match

    @classmethod
    def create_span(cls, idx, match, offset, parent, span, text, pos_str=None):
        """
        :param idx: index of new child span relative to old span
        :param match: result of regex search
        :param offset: number of new child, incremented when added
        :param parent: of span, to which new soan is attached
        :param span: old span
        :param text: text to add
        :param pos_str: "start" or "end"
        :return: tuple (offset, new_span)
        """
        # note: match has a span() attribute!
        if pos_str == "start":
            span_text = text[0:match.span()[0]]  # first string
        elif pos_str == "end":
            span_text = text[match.span()[1]:]  # last string
        new_span = None
        if len(span_text) > 0:
            dummy_templater = Templater()
            new_span = dummy_templater.create_new_span_with_optional_a_href_child(parent, idx + offset, span, span_text)
            # new_span = XmlLib.create_and_add_anchor(href, span, span_text)
            offset += 1
        else:
            print(f"zero-length span0 in {span.text}")
            pass
        return offset, new_span

    @classmethod
    def create_and_add_anchor(cls, href, span, atext):
        """makes a@href child of span
        :param href: href text
        :param soan: to add child to
        :param text: anchor text
        """
        a_elem = lxml.etree.SubElement(span, "a")
        a_elem.attrib["href"] = href
        a_elem.text = atext
        span.text = None


class HtmlElement:
    """to provide fluent HTML builder and parser NYI"""
    pass


class HtmlLib:

    @classmethod
    def convert_character_entities_in_lxml_element_to_unicode_string(cls, element, encoding="UTF-8") -> str:
        """
        converts character entities in lxml element to Unicode
        1) extract string as bytes
        2) converts bytes to unicode with html.unescape()
        (NOTE: may be able to use tostring to do this)


        :param element: lxml element
        :return: unicode string representation of element
        """
        import html
        stringx = lxml.etree.tostring(element)
        string_unicode = html.unescape(stringx.decode(encoding))
        return string_unicode

    @classmethod
    def create_html_with_empty_head_body(cls):
        """
        creates
        <html>
          <head/>
          <body/>
        </html>
        """
        html_elem = lxml.etree.Element("html")
        html_elem.append(lxml.etree.Element("head"))
        html_elem.append(lxml.etree.Element("body"))
        return html_elem

    @classmethod
    def add_copies_to_head(cls, html_elem, elems):
        """copies elems and adds them to <head> of html_elem
        no checks made for duplicates
        :param html_elem: elemnt to copy into
        :param elems: list of elements to copy (or single elemnt
        """
        if html_elem is None or elems is None:
            raise ValueError("Null arguments in HtmlLib.add_copies_to_head")
        head = html_elem.xpath("./head")[0]
        if type(elems) is not list:
            elems = [elems]
        for elem in elems:
            head.append(copy.deepcopy(elem))

    @classmethod
    def get_body(cls, html_elem):
        """
        :oaram html_elem: if None, creates new Html element; if not must have a body
        :return: body element
        """
        if html_elem is None:
            html_elem = HtmlLib.create_html_with_empty_head_body()
        bodys = html_elem.xpath("./body")
        return bodys[0] if len(bodys) == 1 else None

    @classmethod
    def get_head(cls, html_elem=None):
        """
        :oaram html_elem: if None, creates new Html element; if not must have a head
        :return: the head element
        """
        if html_elem is None:
            html_elem = HtmlLib.create_html_with_empty_head_body()
        heads = html_elem.xpath("/html/head")
        return heads[0] if len(heads) == 1 else None

    @classmethod
    def add_base_url(cls, html_elem, base_url):
        head = cls.get_head(html_elem)
        base = head.xpath("base")
        if len(base) > 1:
            print(f"too many base_urls; probable error")
            return
        if len(base) == 0:
            base = lxml.etree.SubElement(head, "base")
            base.attrib["href"] = base_url

    @classmethod
    def create_new_html_with_old_styles(cls, html_elem):
        """
        creates new HTML element with empty body and copies styles from html_elem
        """
        new_html_elem = HtmlLib.create_html_with_empty_head_body()
        HtmlLib.add_copies_to_head(new_html_elem, html_elem.xpath(".//style"))
        return new_html_elem

    @classmethod
    def add_head_style(cls, html, target, css_value_pairs):
        """This might duplicate things in HtmlStyle
        """

        if html is None or not target or not css_value_pairs:
            raise ValueError(f"None params in add_head_style")
        head = HtmlLib.get_head(html)
        style = lxml.etree.Element("style")
        head.append(style)
        style.text = target + " {"
        for css_value_pair in css_value_pairs:
            if len(css_value_pair) != 2:
                raise ValueError(f"bad css_value_pair {css_value_pair}")
            style.text += css_value_pair[0] + " : " + css_value_pair[1] + ";"
        style.text += "}"

    @classmethod
    def add_explicit_head_style(cls, html_page, target, css_string):
        """
        :param html_page: element receiving styles in head
        :param target: the reference (e.g. 'div', '.foo')
        """

        if html_page is None or not target or not css_string:
            raise ValueError(f"None params in add_head_style")
        if not css_string.startswith("{") or not css_string.endswith("}"):
            raise ValueError(f"css string must include {...}")
        head = HtmlLib.get_head(html_page)
        style = lxml.etree.Element("style")
        head.append(style)
        style.text = target + " " + css_string

    @classmethod
    def write_html_file(self, html_elem, outfile, debug=False, mkdir=True, pretty_print=False, encoding="UTF-8"):
        """writes XML element (or tree) to file, making directory if needed .
        adds method=True to ensure end tags
        :param html_elem: element to write
        :param outfile: file to write
        :param mkdir: make directory if not exists (def True)
        :param debug: output debug (def False)
        :param pretty_print: pretty print output (def False)
        """
        if html_elem is None:
            if debug:
                print("null html elem to write")
            return
        if outfile is None:
            if debug:
                print("no outfile given")
            return
        if type(html_elem) is _ElementTree:
            html_elem = html_elem.getroot()
        if not (type(html_elem) is _Element or type(html_elem) is lxml.html.HtmlElement):
            raise ValueError(f"type(html_elem) should be _Element or lxml.html.HtmlElement not {type(html_elem)}")
        if encoding and encoding.lower() == "utf-8":
            head = HtmlLib.get_or_create_head(html_elem)
            if head is None:
                print(f"cannot create <head> on html elem; not written")
                return

        outdir = os.path.dirname(outfile)
        if mkdir:
            Path(outdir).mkdir(exist_ok=True, parents=True)

        # cannot get this to output pretty_printed, (nor the encoding)
        tobytes = lxml.etree.tostring(html_elem, method="html", pretty_print=pretty_print)
        tostring = tobytes.decode("UTF-8")

        with open(str(outfile), "w") as f:
            f.write(tostring)
        if debug:
            print(f"wrote: {Path(outfile).absolute()}")

    @classmethod
    def create_rawgithub_url(cls, site=None, username=None, repository=None, branch=None, filepath=None,
                             rawgithubuser="https://raw.githubusercontent.com"):
        """creates rawgithub url for programmatic HTTPS access to repository"""
        site = "https://raw.githubusercontent.com"
        url = f"{site}/{username}/{repository}/{branch}/{filepath}" if site and username and repository and branch and filepath else None
        return url

    @classmethod
    def get_or_create_head(cls, html_elem):
        """ensures html_elem is <html> and first child is <head>"""
        if html_elem is None:
            return None
        if html_elem.tag.lower() != "html":
            print(f"not a full html element")
            return None
        head = HtmlLib.get_head(html_elem)
        if head is None:
            head = lxml.etree.SubElement(html_elem, "head")
            html_elem.insert(0, head)
        return head

    @classmethod
    def add_charset(cls, html_elem, charset="utf-8"):
        """adds <meta charset=charset" to <head>"""
        head = HtmlLib.get_or_create_head(html_elem)
        if head is None:
            print(f"cannot create <head>")
            return
        cls.remove_charsets(head)
        meta = lxml.etree.SubElement(head, "meta")
        meta.attrib["charset"] = charset

    @classmethod
    def remove_charsets(cls, head):
        XmlLib.remove_elements(head, ".//meta[@charset]")

    @classmethod
    def extract_ids_from_html_page(cls, input_html_path, regex_str=None, debug=False):
        """
        finds possible IDs in PDF HTML pages
        must lead the text in a span
        """
        elem = lxml.etree.parse(str(input_html_path))
        div_with_spans = elem.xpath(".//div[span]")
        regex = re.compile(regex_str)
        sectionlist = []
        for div in div_with_spans:
            spans = div.xpath(".//span")
            for span in spans:
                matchstr = regex.match(span.text)
                if matchstr:
                    if debug:
                        print(f"matched {matchstr.group(1)} {span.text[:50]}")
                    sectionlist.append(span)
        return sectionlist

    @classmethod
    def parse_html(cls, infile):
        """
        parse html file as checks for file existence
        :param infile: file to parse
        :return: root element
        """
        if not infile:
            print(f"infile is None")
            return None
        path = Path(infile)
        if not path.exists():
            print(f"file does not exist {infile}")
            return None
        else:
            try:
                html_tree = lxml.etree.parse(str(infile))
                return html_tree.getroot()
            except Exception as e:
                print(f"cannot parse {infile} because {e}")
                return None

    @classmethod
    def find_paras_with_ids(cls, html, xpath=None):
        """
        find all p's with @id and return ordered list
        :param html: parsed html DOM
        """
        if not xpath:
            xpath = ".//p[@id]"
        paras = []
        if html is None:
            return paras
        body = HtmlLib.get_body(html)
        paras = body.xpath(xpath)
        return paras

    @classmethod
    def para_contains_phrase(cls, para, phrase, ignore_case=True):
        if ignore_case:
            phrase = phrase.lower()
        text = "".join(para.itertext())
        if ignore_case:
            text = text.lower()
        if re.search(r'\b' + phrase + r'\b', text):
            return True
        return False

    @classmethod
    def create_para_ohrase_dict(cls, paras, phrases):
        """search for phrases in paragraphs
        :param paras: list of HTML elems with text (normally <p>), must have @id else ignored
        :param phrases: list of strings to search for (word boundary honoured)
        :return: dict() keyed on para_ids values are dict of search hits by phrase
        """
        para_phrase_dict = dict()
        for para in paras:
            para_id = para.get("id")
            if para_id is None:
                continue
            phrase_dict = dict()
            for phrase in phrases:
                count = HtmlLib.para_contains_phrase(para, phrase, ignore_case=True)
                if count > 0:
                    phrase_dict[phrase] = count
                    para_phrase_dict[para_id] = phrase_dict
        return para_phrase_dict

    @classmethod
    def retrieve_with_useragent_parse_html(cls, url, user_agent='my-app/0.0.1', encoding="UTF-8", debug=False):

        """
        Some servers give an Error 403 unless they have a user_agent.
        This provides a dummy one and allows users to add the true one
        """
        content, encoding = FileLib.read_string_with_user_agent(url, user_agent=user_agent, encoding=encoding,
                                                                debug=debug)
        assert type(content) is str
        html = lxml.html.fromstring(content, base_url=url, parser=HTMLParser())

        return html


class DataTable:
    """
<html xmlns="http://www.w3.org/1999/xhtml">
 <head charset="UTF-8">
  <title>ffml</title>
  <link rel="stylesheet" type="text/css" href="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/css/jquery.dataTables.css"/>
  <script src="http://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.8.2.min.js" charset="UTF-8" type="text/javascript"> </script>
  <script src="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min.js" charset="UTF-8" type="text/javascript"> </script>
  <script charset="UTF-8" type="text/javascript">$(function() { $("#results").dataTable(); }) </script>
 </head>
    """

    def __init__(self, title, colheads=None, rowdata=None):
        """create dataTables
        optionally add column headings (list) and rows (list of conformant lists)

        :param title: of data_title (required)
        :param colheads:
        :param rowdata:

        """
        self.html = ET.Element(H_HTML)
        self.head = None
        self.body = None
        self.create_head(title)
        self.create_table_thead_tbody()
        self.add_column_heads(colheads)
        self.add_rows(rowdata)
        self.head = None
        self.title = None
        self.title.text = None

    def create_head(self, title):
        """
          <title>ffml</title>
          <link rel="stylesheet" type="text/css" href="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/css/jquery.dataTables.css"/>
          <script src="http://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.8.2.min.js" charset="UTF-8" type="text/javascript"> </script>
          <script src="http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min.js" charset="UTF-8" type="text/javascript"> </script>
          <script charset="UTF-8" type="text/javascript">$(function() { $("#results").dataTable(); }) </script>
        """

        self.head = ET.SubElement(self.html, H_HEAD)
        self.title = ET.SubElement(self.head, H_TITLE)
        self.title.text = title

        link = ET.SubElement(self.head, LINK)
        link.attrib["rel"] = STYLESHEET
        link.attrib["type"] = TEXT_CSS
        link.attrib["href"] = "http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/css/jquery.dataTables.css"
        link.text = '.'  # messy, to stop formatter using "/>" which dataTables doesn't like

        script = ET.SubElement(self.head, SCRIPT)
        script.attrib["src"] = "http://ajax.aspnetcdn.com/ajax/jQuery/jquery-1.8.2.min.js"
        script.attrib["charset"] = UTF_8
        script.attrib["type"] = TEXT_JAVASCRIPT
        script.text = '.'  # messy, to stop formatter using "/>" which dataTables doesn't like

        script = ET.SubElement(self.head, SCRIPT)
        script.attrib["src"] = "http://ajax.aspnetcdn.com/ajax/jquery.dataTables/1.9.4/jquery.dataTables.min.js"
        script.attrib["charset"] = UTF_8
        script.attrib["type"] = TEXT_JAVASCRIPT
        script.text = "."  # messy, to stop formatter using "/>" which dataTables doesn't like

        script = ET.SubElement(self.head, SCRIPT)
        script.attrib["charset"] = UTF_8
        script.attrib["type"] = TEXT_JAVASCRIPT
        script.text = "$(function() { $(\"#results\").dataTable(); }) "

    def create_table_thead_tbody(self):
        """
     <body>
      <div class="bs-example table-responsive">
       <table class="table table-striped table-bordered table-hover" id="results">
        <thead>
         <tr>
          <th>articles</th>
          <th>bibliography</th>
          <th>dic:country</th>
          <th>word:frequencies</th>
         </tr>
        </thead>
        """

        self.body = ET.SubElement(self.html, H_BODY)
        self.div = ET.SubElement(self.body, H_DIV)
        self.div.attrib["class"] = "bs-example table-responsive"
        self.table = ET.SubElement(self.div, H_TABLE)
        self.table.attrib["class"] = "table table-striped table-bordered table-hover"
        self.table.attrib["id"] = RESULTS
        self.thead = ET.SubElement(self.table, H_THEAD)
        self.tbody = ET.SubElement(self.table, H_TBODY)

    def add_column_heads(self, colheads):
        if colheads is not None:
            self.thead_tr = ET.SubElement(self.thead, H_TR)
            for colhead in colheads:
                th = ET.SubElement(self.thead_tr, H_TH)
                th.text = str(colhead)

    def add_rows(self, rowdata):
        if rowdata is not None:
            for row in rowdata:
                self.add_row_old(row)

    def add_row_old(self, row: [str]):
        """ creates new <tr> in <tbody>
        creates <td> child elements of row containing string values

        :param row: list of str
        :rtype: object
        """
        if row is not None:
            tr = ET.SubElement(self.tbody, H_TR)
            for val in row:
                td = ET.SubElement(tr, H_TD)
                td.text = val
                # print("td", td.text)

    def make_row(self):
        """

        :return: row element
        """
        return ET.SubElement(self.tbody, H_TR)

    def append_contained_text(self, parent, tag, text):
        """create element <tag> and add text child
        :rtype: element

        """
        subelem = ET.SubElement(parent, tag)
        subelem.text = text
        return subelem

    def write_full_data_tables(self, output_dir: str) -> None:
        """

        :rtype: object
        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        data_table_file = os.path.join(output_dir, "full_data_table.html")
        with open(data_table_file, "w") as f:
            text = bytes.decode(ET.tostring(self.html))
            f.write(text)
            print("WROTE", data_table_file)

    def __str__(self):
        # s = self.html.text
        # print("s", s)
        # return s
        # ic("ichtml", self.html)
        htmltext = ET.tostring(self.html)
        print("SELF", htmltext)
        return htmltext


HREF_TEMPLATE = "href_template"
ID_TEMPLATE = "id_template"


class Templater:
    """
    inserts strings into templates
    uses format, not f-strings
    """

    def __init__(self, template=None, regex=None, href_template=None, id_template=None, repeat=0):
        self.template = template
        self.regex = regex
        self.href_template = href_template
        self.id_template = id_template
        self.repeat = repeat

    def __str__(self):
        return f"{str(self.template)}\n{str(self.regex)}\nhref: {str(self.href_template)}\nid: {str(self.id_template)}"

    def match_template(self, strng, template_type=None):
        if template_type is None:
            template = self.template
        if template_type == HREF_TEMPLATE:
            template = self.href_template
        elif template_type == ID_TEMPLATE:
            template = self.id_template
        else:
            print(f"***Bad template type** {template_type}")
            return None
        return Templater.get_matched_template(self.regex, strng, self.template)

    def match_href_template(self, strng):
        href = Templater.get_matched_template(self.regex, strng, self.href_template)
        return href

    @classmethod
    def get_matched_templates(cls, regex, strings, template):
        matched_templates = []
        for strng in strings:
            matched_template = cls.get_matched_template(regex, strng, template)
            matched_templates.append(matched_template)
        return matched_templates

    # class Templater

    @classmethod
    def get_matched_template(cls, regex, strng, template):
        """
        matches strng with regex-named-capture-groups and extracts matches into template
        :parem regex: with named captures
        :param strng: to match
        :param template: final string with named groups in {} to substitute
        :return substituted strng

        Simple Examaple
        template = "{DecRes}_{decision}_{type}_{session}"
        regex = "(?P<DecRes>Decision|Resolution)\\s(?P<decision>\\d+)/(?P<type>CMA|CMP|CP)\\.(?P<session>\\d+)"
        strng = "Decision 12/CMP.5"
        returns 'Decision_12_CMP_5'

        but more complex templates can include repeats. However these are NOT f-strings and do not use eval()
        """
        if regex is None:
            print(f"**************regex is None")
            return None
        if template is None:
            raise ValueError("template shuuld not be None")
        match = re.search(regex, strng)
        if not match:
            matched_template = None
        else:
            template_values = match.groupdict()
            matched_template = template.format(**template_values)
        return matched_template

    # class Templater

    @classmethod
    def create_template(cls, template=None, regex=None, href_template=None, id_template=None):
        templater = Templater()
        if not regex:
            print(f"no regex in templater")
            return None
        templater.regex = regex
        templater.template = template
        templater.href_template = href_template
        templater.id_template = id_template
        return templater

    def split_span_by_templater(self, span, repeat=0, debug=False):
        """split a span into 3 sections but matching substring
        <parent><span attribs>foo bar plugh</span></parent>
        if "bar" matches regex gives:
        <parent><span attribs>foo </span><span attribs id=id>bar</span><span attribs> plugh</span></parent>
        if count > 1, repeats the splitting on the new RH span , decrementing repeat until zero

        :param span: the span to split
        :param regex: finds (first) match in span.text and extracts matched text into middle span
        :param id: if string, adds id to new mid element; if array of len 3 gives id[0], id[1], id[2] to each new span
        :param href: adds <a href=href>matched-text</a> as child of mid span (1) if un.GENERATE generates HREF
        :param clazz: 3-element array to add class attributes to split sections
        :param repeat: repeats split on (new) rh span
        :return: None if no match, else first match in span
        """
        if span is None:
            print(f"span is None")
            return None
        type_span = type(span)
        parent = span.getparent()

        if span is None or type_span is not lxml.etree._Element \
                or parent is None or span.tag != 'span' or repeat < 0:
            return None
        text = span.text
        if text is None:
            return None
        match = None
        regex = self.regex
        if regex is None:
            print(f"************no regex in templater")
            return
        try:
            match = re.search(regex, text)
        except Exception as e:
            print(f"bad match {regex} /{e} => {text}")
            return
        idx = parent.index(span)
        # enhanced_regex = EnhancedRegex(regex=regex)
        if match:
            anchor_text = match.group(0)
            if debug:
                print(f"matched: {regex} {anchor_text}")
            # href_new = enhanced_regex.get_href(href, text=anchor_text)
            # make 3 new spans
            # some may be empty
            offset = 1
            offset, span0 = XmlLib.create_span(idx, match, offset, parent, span, text, "start")
            mid = self.create_new_span_with_optional_a_href_child(parent, idx + offset, span, anchor_text)
            offset += 1
            offset, span2 = XmlLib.create_span(idx, match, offset, parent, span, text, "end")
            id_markup = False
            ids = None

            parent.remove(span)
            # recurse in RH split
            if repeat > 0 and span2 is not None:
                repeat -= 1
                self.split_span_by_templater(span2, repeat=repeat, debug=debug)
        return match

    # class Templater

    def create_new_span_with_optional_a_href_child(self, parent, idx, span, textx, href=None):
        """
        :param parent: of span, to which new soan is attached
        :param idx: index of new child span relative to old span
        :param span: old span
        :param textx: text to add
        :param href: optional href (address) to add
        :return: new span
        """
        new_span = lxml.etree.Element("span")

        if self.href_template:
            href = self.match_href_template(textx)
            # print(f">>>>  {href}..{self}")
            XmlLib.create_and_add_anchor(href, new_span, textx)
        elif href:
            XmlLib.create_and_add_anchor(href, new_span, textx)
        else:
            new_span.text = textx

        new_span.attrib.update(span.attrib)
        parent.insert(idx, new_span)
        return new_span

    # class Templater

    @classmethod
    def get_anchor_templaters(cls, markup_dict, template_ref_list):
        """
        templates are of the form
            "paris" : {
                "regex": "([Tt]he )?Paris Agreement",
                "target_template": "https://unfccc.int/process-and-meetings/the-paris-agreement",

            more complex:

            "decision": {
                "example": ["decision 1/CMA.2", "noting decision 1/CMA.2, paragraph 10 and ", ],
                "regex": [f"decision{WS}(?P<decision>{INT})/(?P<type>{CPTYPE}){DOT}(?P<session>{INT})",
                          f"decision{WS}(?P<decision>{INT})/(?P<type>{CPTYPE}){DOT}(?P<session>{INT})(,{WS}paragraph(?P<paragraph>{WS}{INT}))?",
                          ],
                "href": "FOO_BAR",
                "split_span": True,
                "idgen": "NYI",
                "_parent_dir": f"{PARENT_DIR}", # this is given from environment
                "target_template": "{_parent_dir}/{type}_{session}/Decision_{decision}_{type}_{session}",
    },


        """
        templater_list = []

        for template_ref in template_ref_list:
            sub_markup_dict = markup_dict.get(template_ref)
            if not sub_markup_dict:
                print(f"cannot find template {template_ref}")
                continue
            regex = sub_markup_dict.get("regex")
            target_template = sub_markup_dict.get("target_template")
            id_template = sub_markup_dict.get("id_template")
            href_template = sub_markup_dict.get("href_template")
            if not regex:
                raise Exception(f"missing key regex in {template_ref} {markup_dict} ")
                continue
            templater = Templater.create_template(
                regex=regex, template=target_template, href_template=href_template, id_template=id_template)
            templater_list.append(templater)
        return templater_list

    # class Templater

    @classmethod
    def create_id_from_section(cls, html_elem, id_xpath, template=None, regex=None, maxchar=100):
        from pyamihtmlx.xml_lib import ID_TEMPLATE
        """create id from html content
        id_xpath is where to find the content
        template is how to transform it
        """
        divs = html_elem.xpath(id_xpath)
        if len(divs) == 0:
            print(f"cannot find id {id_xpath}")
            return
        div = divs[0]
        div_content = ''.join(html_elem.itertext())
        # print(f" div_content {div_content[:maxchar]}")
        templater = Templater.create_template(template, regex)
        id = templater.match_template(div_content, template_type=ID_TEMPLATE)
        print(f">>id {id}")
        return id


class Web:
    def __init__(self):
        import tkinter as tk
        root = tk.Tk()
        site = "http://google.com"
        self.display_html(root, site)
        root.mainloop()

    @classmethod
    def display_html(cls, master, site):
        import tkinterweb
        frame = tkinterweb.HtmlFrame(master)
        frame.load_website(site)
        frame.pack(fill="both", expand=True)

    @classmethod
    def tkinterweb_demo(cls):
        from tkinterweb import Demo
        Demo()


def main():
    XmlLib().test_recurse_sections()  # recursively list sections


#    test_data_table()
#    test_xml()

#    web = Web()
#    Web.tkinterweb_demo()


def test_xml():
    xml_string = "<a>foo <b>and</b> with <d/> bar</a>"
    print(XmlLib.remove_all_tags(xml_string))


def test_data_table():
    import pprint
    data_table = DataTable("test")
    data_table.add_column_heads(["a", "b", "c"])
    data_table.add_row_old(["a1", "b1", "c1"])
    data_table.add_row_old(["a2", "b2", "c2"])
    data_table.add_row_old(["a3", "b3", "c3"])
    data_table.add_row_old(["a4", "b4", "c4"])
    html = ET.tostring(data_table.html).decode("UTF-8")
    HOME = os.path.expanduser("~")
    with open(os.path.join(HOME, "junk_html.html"), "w") as f:
        f.write(html)
    pprint.pprint(html)


def test_replace_strings_with_unknown_encodings():
    s = """
    form to mean âaerosol particlesâ. Aerosols 
    """
    tuple_list = [
        ("â", "‘"),
        ("â", "’"),
    ]
    target = "âaerosol particlesâ."
    assert len(tuple_list[0][0]) == 3
    sout = XmlLib.iteratively_replace_strings(tuple_list, target)
    print(sout)
    assert sout == "‘aerosol particles’."


def test_replace_element_child_text_with_unknown_encodings():
    tuple_list = [
        ("â", "‘"),
        ("â", "’"),
    ]
    target = "âaerosol particlesâ."
    elem = lxml.etree.Element("foo")
    elem.text = target
    assert elem.text == "â\x80\x98aerosol particlesâ\x80\x99."
    XmlLib.replaceStrings(elem, tuple_list)
    assert elem.text == "‘aerosol particles’."


if __name__ == "__main__":
    print("running file_lib main")
    main()
else:
    #    print("running file_lib main anyway")
    #    main()
    pass
