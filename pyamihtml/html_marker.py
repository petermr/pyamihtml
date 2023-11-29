import csv
import re
from collections import Counter
from pathlib import Path

import lxml

from pyamihtml.ami_integrate import HtmlGenerator
from pyamihtml.util import EnhancedRegex
from pyamihtml.xml_lib import HtmlLib


class SpanMarker:
    """supports the UN FCCC documents (COP, etc.)
    """
    REGEX = "regex"
    BACKGROUND = "background"
    COMPONENTS = "components"
    SECTION_ID = "section_id"
    TARGET = "target"

    def __init__(self, markup_dict=None, regex=None):
        self.graph = True
        self.unmatched = Counter() # counter for sets
        self.indir = None
        self.outdir = None
        self.infile = None
        self.outfile = None
        self.inhtml = None
        self.outcsv = None
        self.enhanced_regex = None if not regex else EnhancedRegex(regex=regex)
        if markup_dict is None:
            print("WARNING no markup_dict given")
        self.markup_dict = markup_dict

    #    class SpanMarker:

    # this is a mess
    def read_and_process_pdfs(self, pdf_list):
        if len(pdf_list) == 0:
            print(f"no PDF files given")
            return None
        self.outdir.mkdir(exist_ok=True)
        self.outcsv = str(Path(self.outdir, self.outfile))
        self.analyze_pdfhtml_and_write_links(pdf_list)

    #    class SpanMarker:

    def analyze_pdfhtml_and_write_links(self, pdfs):
        if pdfs is None:
            print(f'no pdfs')
            return
        if self.outcsv is None:
            print(f"no outfile")
        pdf_list = [pdfs] if type(pdfs) is not list else pdfs
        Path(self.outcsv).parent.mkdir(exist_ok=True)
        with open(self.outcsv, "w") as f:
            self.csvwriter = csv.writer(f)
            self.csvwriter.writerow(["source", "link_type", self.TARGET, self.SECTION_ID, "para"])
            if self.get_regex() is None:
                print(f"no regex")
            else:
                for i, pdf in enumerate(sorted(pdf_list)):
                    self.create_html_from_pdf_and_markup_spans_with_options(pdf, options=[self.SECTION_ID])
        print(f"wrote {self.outcsv}")

# class SpanMarker:

    def create_html_from_pdf_and_markup_spans_with_options(self, pdf, options=None, write_files=False):
        from pyamihtml.ami_integrate import HtmlGenerator
        from pyamihtml.xml_lib import HtmlLib, XmlLib


        if not options:
            options = []
        self.stem = Path(pdf).stem

        html_elem = self.create_styled_html_sections(pdf)

        out_type = ""
        if self.SECTION_ID in options:
            self.outdir = outdir = str(Path(Path(pdf).parent, self.stem + "_section"))
            self.markup_spans(html_elem)
            out_type = self.SECTION_ID
        # if self.TARGET in options:
        #     regex = self.enhanced_regex.regex
        #     self.find_targets(regex, html_elem)
        #     out_type += " " + self.TARGET
        if out_type and write_files:
            html_out = Path(Path(pdf).parent, self.stem + "_" + out_type.strip( ) + ".html")
            HtmlLib.write_html_file(html_elem, html_out, debug=True)

    #    class SpanMarker:

    def create_styled_html_sections(self, pdf):
        html_elem = HtmlGenerator.create_sections(pdf, debug=False)
        outdir = self.outdir
        outdir = None
        SpanMarker.normalize_html_and_extract_styles(html_elem, outdir=outdir)

        return html_elem

    #    class SpanMarker:

    def markup_spans(self, html_elem):
        """finds numbered sections
        1) font-size: 14.04; font-family: DDBMKM+TimesNewRomanPS-BoldMT;  starts-with I|II...VI|VII|VIII
        """


        div_with_spans = html_elem.xpath(".//div[span]")
        for div_with_span in div_with_spans:
            self.markup_span(div_with_span)

    #    class SpanMarker:

    @classmethod
    def normalize_html_and_extract_styles(cls, html_elem, outdir=None):
        from pyamihtml.ami_html import HtmlStyle
        HtmlStyle.extract_all_style_attributes_to_head(html_elem)
        HtmlStyle.extract_styles_and_normalize_classrefs(html_elem, outdir=outdir)

    # class SpanMarker:

    def find_targets(self, target_regex, html_elem):
        raise NotImplemented("targets should be rewritten")
        text_parents = html_elem.xpath("//*[text()]")
        dec_end = DEC_END
#        texts = html_elem.xpath("//*/text()")
        """decisión 2/CMA.3, anexo, capítulo IV.B"""
        # doclink = re.compile(".*decisión (?P<decision>\d+)/CMA\.(?P<cma>\d+), (?P<anex>anexo), (?P<capit>capítulo) (?P<roman>[IVX]+)\.(?P<letter>5[A-F]).*")
        for text_parent in text_parents:
            text = text_parent.xpath("./text()")[0]
            if text is not None and len(text.strip()) > 0:
                row = self.extract_text(target_regex, text, dec_end=dec_end)
                if row:
                    self.csvwriter.writerow(row)
                    text_parent.attrib["style"] = "background : #bbbbf0"



# class SpanMarker:

    def extract_text(self, regex, text, dec_end=None):
        """rgeex"""
        # print (f"parent {type(text.parent)}")
        # priextract_textnt(f"{text}")
        match = re.match(regex, text)
        if not match:
            return None
        # print(f"{match.group('front'), match.group('dec_no'), match.group('body'), match.group('sess_no'), match.group('end')}")
        front = match.group("front")
        dec_no = match.group('dec_no')
        body = match.group('body')
        session = match.group('sess_no')
        end = match.group("end")
        target = f"{dec_no}_{body}_{session}"

        print(f"({front[:15]} || {front[-30:]} {target} || {end[:30]}")
        # match end
        match_end = re.match(dec_end, end)
        annex = ""
        para = ""
        if match_end:
            annex = match_end.group("annex")
            para = match_end.group("para")
            print(f">>>(annex || {para}")

        row = [self.stem, "refers", target, annex[:25], para]
        return row

# class SpanMarker

    def markup_span(self, div):
        """extract number/letter and annotate
        for each span iterate over markup instructions
        """
        span = div.xpath("./span")
        if not span:
            return
        span0 = span[0]
        text = span0.xpath("./text()")
        if text:
            text = text[0]
        self.iterate_over_markup_dict_items(span0, text)

    #    class SpanMarker:

    def iterate_over_markup_dict_items(self, span0, text):
        match = None
        if self.markup_dict is None:
            print(f"need a markup dict")
            return match
        for markup in self.markup_dict.items():
            match = self.make_id_add_atributes_with_enhanced_regex(markup, span0, text)
            if match:
                break
        if not match:
            self.unmatched[text] += 1
        return match
            # print(f"cannot match: {text}")

    #    class SpanMarker:

    def make_id_add_atributes_with_enhanced_regex(self, markup, span0, text):
        if not markup:
            if self.get_regex():
                markup_dict = {
                    self.REGEX: self.get_regex()
                }
                markup = ("markup_key", markup_dict)
        if not markup:
            print("NO markup given")
            return

        markup_key = markup[0]
        markup_dict = markup[1]
        # print(f"markup_key {markup_key}, markup_dict {markup_dict}")
        return self.create_enhanced_regex_and_create_id(markup_dict, span0)

    #    class SpanMarker:

    def create_enhanced_regex_and_create_id(self, markup_dict, span0):
        regex = markup_dict.get(self.REGEX)
        enhanced_regex = EnhancedRegex(regex=regex)
        # print(f"regex {regex}")
        match = re.match(regex, span0.text)
        if match:
            # components = ["", ("decision", "\d+"), "/", ("type", "CP|CMA|CMP"), "\.", ("session", "\d+"), ""]
            id = enhanced_regex.make_id(span0.text)
            print(f"ID {id}")
            clazz = span0.attrib["class"]
            if clazz:
                pass
                # print(f"clazz {clazz}")
            span0.attrib["class"] = self.SECTION_ID
            span0.attrib["style"] = f"background : {markup_dict.get(self.BACKGROUND)}"
        return match

    #    class SpanMarker:

    def analyse_after_match_NOOP(self, outgraph="graph.html"):
        if self.unmatched:
            # print(f"UNMATCHED {self.unmatched}")
            pass
        # if self.graph:
        #     self.plot_graph(outgraph)

    #    class SpanMarker:

    @classmethod
    def parse_unfccc_html_split_spans(cls, html_infile, regex=None, debug=False):
        from pyamihtml.xml_lib import XmlLib
        from pyamihtml.ami_html import HtmlLib
        from pyamihtml.util import GENERATE

        html_elem = lxml.etree.parse(str(html_infile))
        spans = html_elem.xpath("//span")
        print(f"spans {len(spans)}")
        ids = ["id0", "id1", "id2"]  # ids to give new spans
        clazz = ["class0", ":class1", "class2"]  # classes for result
        print(f"regex {regex}")
        for i, span in enumerate(spans):
            match = XmlLib.split_span_by_regex(span, regex, id=ids, clazz=clazz, href=GENERATE)
            if match:
                print(f"match {match}")
        outfile = Path(str(html_infile).replace(".html", ".marked.html"))

        HtmlLib.write_html_file(html_elem, outfile, debug=debug)

    """
    "Article 9, paragraph 4, of the Paris Agreement;"
    "paragraph 44 above "
    "paragraph 9 of decision 19/CMA.3;"
    "Article 6, paragraph 2, of the Paris Agreement (decision 2/CMA.3);"
    """

    def run_pipeline(self, input_dir=None, pdf_list=None, outcsv=None, regex=None, outdir=None, outhtml=None, markup_dict=None):
        self.indir = input_dir
        self.outdir = outdir
        self.outfile = outcsv
        self.markup_dict = markup_dict
        self.read_and_process_pdfs(pdf_list)
        self.analyse_after_match_NOOP(outhtml)


    #    class SpanMarker:

    def parse_html(self, splitter_re, idgen=None):
        if not self.infile:
            print(f"infile is null")
            return
        try:
            self.inhtml = lxml.etree.parse(str(self.infile))
        except FileNotFoundError as fnfe:
            print(f"file not found {fnfe}")
            return
        body = HtmlLib.get_body(self.inhtml)
        divs = body.xpath("./div")
        divtop = lxml.etree.SubElement(body, "div")
        divtop.attrib["class"] = "top"
        regex = re.compile(splitter_re)
        div0 = self.add_new_section_div(divtop)
        enhanced_regex = EnhancedRegex(regex=regex)
        for i, div in enumerate(divs):
            texts = div.xpath("span/text()")
            text = None if len(texts) == 0 else texts[0]
            match = None if text is None else regex.match(text)
            if match:
                div0 = self.add_new_section_div(divtop)
                if idgen:
                    id = enhanced_regex.make_id(text)
                    # id = make_id_from_match_and_idgen()
                print(f"{match.group('decision')}:{match.group('type')}:{match.group('session')}")
            div0.append(div)

    def add_new_section_div(self, divtop):
        div0 = lxml.etree.SubElement(divtop, "div")
        div0.attrib["class"] = "section"
        return div0

    def write_links(self, param):
        print(f"write_links NYI")

    def get_regex(self):
        return None if not self.enhanced_regex else self.enhanced_regex.regex

