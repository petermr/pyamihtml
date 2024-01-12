import copy
import csv
import glob
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import lxml.etree

from pyamihtmlx.ami_html import HtmlStyle
from pyamihtmlx.ami_integrate import HtmlGenerator
from pyamihtmlx.util import Util, EnhancedRegex, GENERATE
# from pyamihtmlx.util import EnhancedRegex, GENERATE, Util
from pyamihtmlx.xml_lib import HtmlLib, Templater, XmlLib


def replace_parent(current_parents, div):
    pass


def add__and_insert_parents(current_parents, div, level_index):
    pass


def create_dummy_div():
    dummy_div = lxml.etree.Element("div")
    dummy_div.attrib["name"] = "dummy"
    return dummy_div


def get_div_text(div):
    return div.xpath("span/text()[1]")[0][:100]


class SpanMarker:
    """supports the UN FCCC documents (COP, etc.)
    """
    """combines general markup with primitive pipeline
    needs refactopring"""
    REGEX = "regex"
    CLASS = "class"
    BACKGROUND = "background"
    COMPONENTS = "components"
    SECTION_ID = "section_id"
    SPAN_RANGE = "span_range"
    TARGET = "target"
    TARGET_BACKGROUND = "#bbbbf0"

    def __init__(self, markup_dict=None, regex=None, templater=None):
        self.graph = True
        self.unmatched = Counter()  # counter for sets
        self.indir = None
        self.outdir = None
        self.infile = None
        self.outfile = None
        self.inhtml = None
        self.outcsv = None
        self.templater = None
        self.enhanced_regex = None if not regex else EnhancedRegex(regex=regex)
        if markup_dict is None:
            print("WARNING no markup_dict given")
        self.markup_dict = markup_dict
        self.templater = templater

    #    class SpanMarker:

    # this is a mess
    def read_and_process_pdfs(self, pdf_list, debug=False):
        if len(pdf_list) == 0:
            print(f"no PDF files given")
            return None
        self.outdir.mkdir(exist_ok=True)
        self.outcsv = str(Path(self.outdir, self.outfile))
        self.analyze_pdfhtml_and_write_links(pdf_list, debug=debug)

    # Article 2, paragraph 2, of the Paris Agreement
    #    class SpanMarker:

    def analyze_pdfhtml_and_write_links(self, pdfs, debug=False):
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
            for i, pdf in enumerate(sorted(pdf_list)):
                self.create_html_from_pdf_and_markup_spans_with_options(pdf, debug=debug)
        print(f"wrote {self.outcsv}")

    # class SpanMarker:

    def create_html_from_pdf_and_markup_spans_with_options(self, pdf, write_files=True, debug=False):
        """This is MESSY"""

        self.stem = Path(pdf).stem

        html_elem = self.create_styled_html_sections(pdf)
        html_out = None
        if write_files:
            html_out = Path(Path(pdf).parent, self.stem + "pdf2html.html")

        self.markup_html_element_with_markup_dict(html_elem, html_out, debug=debug)

    def create_styled_html_sections(self, pdf):
        html_elem = HtmlGenerator.create_sections(pdf, debug=False)
        outdir = self.outdir
        outdir = None
        SpanMarker.normalize_html_and_extract_styles(html_elem, outdir=outdir)

        return html_elem

    #    class SpanMarker:

    def apply_markup_to_spans_in_divs(self, html_elem):
        """finds numbered sections
        1) font-size: 14.04; font-family: DDBMKM+TimesNewRomanPS-BoldMT;  starts-with I|II...VI|VII|VIII
        """
        div_with_spans = html_elem.xpath(".//div[span]")
        for div_with_span in div_with_spans:
            self.apply_markup_to_spans_in_single_div(div_with_span)
            # self.add_id_to_div(div_with_span)

    #    class SpanMarker:

    @classmethod
    def normalize_html_and_extract_styles(cls, html_elem, outdir=None):
        from pyamihtmlx.ami_html import HtmlStyle
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
                    text_parent.attrib["style"] = f"background : {self.TARGET_BACKGROUND}"

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

    def apply_markup_to_spans_in_single_div(self, div):
        """extract number/letter and annotate
        for each span iterate over markup instructions
        """
        spans = div.xpath("./span")
        if len(spans) == 0:
            return
        span_range = self.get_span_range_from_markup_dict(self.markup_dict)
        for i, span in enumerate(spans):
            if span_range[0] <= i < span_range[1]:
                texts = span.xpath("./text()")
                if texts:
                    text = texts[0]
                self.iterate_over_markup_dict_items(span, text)

    #    class SpanMarker:

    def iterate_over_markup_dict_items(self, span, text):
        match = None
        if self.markup_dict is None:
            print(f"need a markup dict in iterate_over_markup_dict_items")
            return match

        for markup_item in self.markup_dict.items():
            match = self.make_id_add_atributes_with_enhanced_regex(markup_item, span, text)
            if match:
                regex = markup_item[1].get(self.REGEX)
                XmlLib.split_span_by_regex(span, regex, markup_dict=self.markup_dict, href=GENERATE)
                print(f">>>span {span.text[0]}")
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

        regex_list = markup_dict.get(self.REGEX)
        if regex_list is None:
            print(f"no regex in {markup_dict}")
            return
        if type(regex_list) is not list:
            regex_list = [regex_list]
        for regex in regex_list:
            if regex is None:
                print(f"bad regex_list {regex_list}")
                return
            self.search_text_with_regex(regex, markup_dict, span0)

    #    class SpanMarker:

    def search_text_with_regex(self, regex, markup_dict, span0):
        enhanced_regex = EnhancedRegex(regex=regex)
        # print(f"regex {regex}")
        try:
            match = re.match(regex, span0.text)
        except Exception as e:
            print(f"*************** regex fails {regex} {e} \n******************")
            raise e
        if match:
            # components = ["", ("decision", "\d+"), "/", ("type", "CP|CMA|CMP"), "\.", ("session", "\d+"), ""]
            id = enhanced_regex.make_id(span0.text)
            # if id is None:
            # print(f">>ID {id}")
            clazz = span0.attrib["class"]
            if clazz:
                pass
                # print(f"clazz {clazz}")
            span0.attrib["class"] = f"{markup_dict.get(self.CLASS)}"
            span0.attrib["style"] = f"background : {markup_dict.get(self.BACKGROUND)}"
            if self.templater:
                id = self.templater.create_id_from_span(span0)
            span0.attrib["id"] = id
        return match

    #    class SpanMarker:

    def analyse_after_match_NOOP(self, outgraph="graph.html"):
        if self.unmatched:
            # print(f"UNMATCHED {self.unmatched}")
            pass
        # if self.graph:
        #     self.plot_graph(outgraph)

    #    class SpanMarker:

    def split_spans_in_html(self, html_infile=None, outfile=None, html_elem=None, regex_list=None, targets=None,
                            markup_dict=None,
                            templater_list=None, styles=None, debug=False):
        """Takes HTML file, extracts <span>s and splits/marks these using regex"""
        from pyamihtmlx.ami_html import HtmlLib
        """
        splits at regex match, makes 3 spans and adds href with ID to middle (captured) spane
        INPUT: <span>Parties that have not ... ... with decision 9/CMA.1 ahead of the fourth ... as to provide timely input to the global stocktake;
        OUTPUT:
        <span x0="179.61" y0="455.22" x1="484.27" style="x0: 179.61; x1: 185.15; y0: 455.22; y1: 465.18; width: 5.54;" class="class0" id="id0">Parties that have not yet done so to submit their adaptation communications in accordance with </span>
        <span x0="179.61" y0="455.22" x1="484.27" class=":class1" id="id1">
        <a href="9_CMA_1">decision 9/CMA.1</a></span>
        <span x0="179.61" y0="455.22" x1="484.27" class="class2" id="id2"> ahead of the fourth session ... ...timely input to the global stocktake; </span>
        """

        # regex = self.get_regex()
        if regex_list is None:
            print(f"no regex_list")
        if type(regex_list) is str:
            regex_list = [regex_list]
        if html_elem is None:
            if html_infile is not None:
                html_elem = lxml.etree.parse(str(html_infile))
        if html_elem is None:
            print(f"no file or html_elem given")
            return
        if not templater_list:
            if targets and markup_dict:
                templater_list = Templater.get_anchor_templaters(markup_dict, targets)

        if templater_list:
            span_range = markup_dict["decision"]["span_range"]
            repeat = span_range[1]
            print(f"span_range {span_range} repeat {repeat}")
            self.markup_with_templates(html_elem, templater_list, repeat=repeat)
        if outfile is None:
            outfile = Path(str(html_infile).replace(".html", ".marked.html"))
        if styles:
            HtmlStyle.add_head_styles(html_elem, styles)
        HtmlLib.write_html_file(html_elem, outfile, debug=debug)

    def markup_with_regexes(self, clazz, html_elem, ids, regex_list):
        for regex in regex_list:
            print(f">>regex {regex}")
            # recalculate as more spans may be generated
            spans = html_elem.xpath("//span")
            print(f"spans {len(spans)}")

            for i, span in enumerate(spans):
                match = XmlLib.split_span_by_regex(span, regex, ids=ids, clazz=clazz, href=GENERATE)
                if match:
                    print(f">match {match}")

    def markup_with_templates(self, html_elem, templater_list, repeat=0):
        for templater in templater_list:
            print(f">>templater {templater}")
            # recalculate as more spans may be generated
            spans = html_elem.xpath("//span")
            print(f"spans {len(spans)}")

            for i, span in enumerate(spans):
                match = templater.split_span_by_templater(span, repeat=repeat)
                if match:
                    print(f">>>match {match}")
                    pass

    """
    "Article 9, paragraph 4, of the Paris Agreement;"
    "paragraph 44 above "
    "paragraph 9 of decision 19/CMA.3;"
    "Article 6, paragraph 2, of the Paris Agreement (decision 2/CMA.3);"
    """

    def run_pipeline(self, input_dir=None, pdf_list=None, outcsv=None, regex=None, outdir=None, outhtml=None,
                     markup_dict=None, debug=False):
        self.indir = input_dir
        self.outdir = outdir
        self.outfile = outcsv
        self.markup_dict = markup_dict
        self.read_and_process_pdfs(pdf_list, debug=debug)
        self.analyse_after_match_NOOP(outhtml)

    #    class SpanMarker:

    def parse_html(self, splitter_re=None, idgen=None):
        """may be obsolete"""
        """
        :param splitter_re: to match divs for splitting
        parse self.infile
        create a divtop
        find divs matching splitter_re and add an implicit one at the start
        create create new div for each and add self+following as children
        the splits come before the matched div
        input:
        body
            div1
            div2
            div3 (matches re)
            div4
            div5 (matches re)
            div6
            div7

         gives

        body
            divtop (class='top')
                div_sect0 (implicit)
                    div1
                    div2
                div_sect1 (matched)
                    div3
                    div4
                div_sect2  (matched)
                    div5
                    div6
                    div7


        """
        if not self.infile:
            print(f"infile is null")
            return
        try:
            self.inhtml = lxml.etree.parse(str(self.infile))
        except FileNotFoundError as fnfe:
            print(f"file not found {fnfe}")
            return
        if not splitter_re:
            return self.inhtml
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
                    id = SpanMarker.create_id
                    # id = make_id_from_match_and_idgen()
                print(f"{match.group('decision')}:{match.group('type')}:{match.group('session')}")
            div0.append(div)
        return self.inhtml

    #    class SpanMarker:

    def add_new_section_div(self, divtop):
        div0 = lxml.etree.SubElement(divtop, "div")
        div0.attrib["class"] = "section"
        return div0

    def write_links(self, param):
        print(f"write_links NYI")

    #    class SpanMarker:

    def get_regex(self):
        return None if not self.enhanced_regex else self.enhanced_regex.regex

    def markup_html_element_with_markup_dict(
            self, html_elem, html_outdir=None, input_dir=None, html_out=None, dict_name=None, debug=False):
        self.apply_markup_to_spans_in_divs(html_elem)
        if html_out:
            HtmlLib.write_html_file(html_elem, html_out, debug=debug)
        return html_out

    #    class SpanMarker:

    @classmethod
    def make_new_html_body(cls):
        html_new = HtmlLib.create_html_with_empty_head_body()
        body_new = HtmlLib.get_body(html_new)
        return html_new, body_new

    #    class SpanMarker:

    @classmethod
    def split_at_sections_and_write_split_files(
            cls, infile, output_dir=None, subdirname=None, splitter=None, id_regex=None, id_template=None,
            id_xpath=None,
            filestem="split", debug=False):
        """adds split instruction sections into html file using splitter xpath"""

        def _write_output_file(html_new, output_dir, subdirname, filestem, debug=False):
            file = Path(output_dir, f"{subdirname}", f"{filestem}.html")
            HtmlLib.write_html_file(html_new, file, debug=debug)

        assert Path(infile).exists()
        parent_stem = Path(infile).parent.stem
        try:
            html_elem = lxml.etree.parse(str(infile))
        except Exception as e:
            print(f"cannot parse html {infile}")
            return

        """<div left="113.28" right="225.63" top="748.51">
                 <span x0="113.28" y0="748.51" x1="225.63" style="background : #ffaa00" class="Decision">
                   <a href="1_CMA_3">Decision 1/CMA.3</a>
                 </span>
                 <span x0="113.28" y0="748.51" x1="225.63" style="background : #ffaa00" class="Decision"> </span><
                 /div>
        """

        body = HtmlLib.get_body(html_elem)
        head = HtmlLib.get_head(html_elem)
        divs = body.xpath("./div")
        print(f"divs {len(divs)}")
        body_new, html_new = cls.make_new_html_with_copied_head(head)
        assert len(html_new.xpath("head/style")) > 0
        # href0 = f"{Path(infile).stem}_start"
        if not output_dir:
            print("no output_dir")
            return
        sub_dirs = []
        filestem = "split"
        for div in divs:
            splitdivs = div.xpath(splitter)
            splitdiv = None if len(splitdivs) == 0 else splitdivs[0]
            if splitdiv is not None:
                print(f"split before {splitdiv.text[:150]}")
                ndivs = len(body_new.xpath("div"))
                print(f"ndivs {ndivs}")
                if ndivs > 0:
                    id = cls.create_id_write_output_append_to_subdirs(_write_output_file, debug, filestem, html_new,
                                                                      id_regex, id_template, id_xpath, output_dir,
                                                                      parent_stem, sub_dirs)
                    # html_new, body_new = cls.make_new_html_body()
                    body_new, html_new = cls.make_new_html_with_copied_head(head)
            body_new.append(div)
        if len(body_new.xpath("div")) > 0:
            id = cls.create_id_write_output_append_to_subdirs(_write_output_file, debug, filestem, html_new,
                                                              id_regex, id_template, id_xpath, output_dir,
                                                              parent_stem, sub_dirs)
        return sub_dirs, filestem

    #    class SpanMarker:

    @classmethod
    def create_id_write_output_append_to_subdirs(cls, _write_output_file, debug, filestem, html_new, id_regex,
                                                 id_template, id_xpath, output_dir, parent_stem, sub_dirs):
        id = Templater.create_id_from_section(html_new, id_xpath, regex=id_regex, template=id_template)
        if id is None:
            id = parent_stem + "_LEAD"
        _write_output_file(html_new, output_dir, id, filestem, debug=debug)
        sub_dirs.append(Path(output_dir, id))
        return id

    #    class SpanMarker:

    @classmethod
    def make_new_html_with_copied_head(cls, head):
        html_new, body_new = cls.make_new_html_body()
        head_new = HtmlLib.get_head(html_new)
        old_head = copy.deepcopy(head)
        print(f">>styles {len(old_head.xpath('style'))}")
        html_new.replace(head_new, old_head)
        print(f">>styles new {len(html_new.xpath('head/style'))}")
        return body_new, html_new

    #    class SpanMarker:

    @classmethod
    def markup_file_with_markup_dict(
            cls, input_dir, html_infile=None, html_elem=None, html_outdir=None, dict_name=None,
            outfile=None, markup_dict=None, add_ids=None, debug=False):

        html_elem = lxml.etree.parse(str(html_infile))
        span_marker = SpanMarker(markup_dict=markup_dict)
        if not dict_name:
            dict_name = "missing_dict_name"
        parent = Path(input_dir).parent
        if outfile and outfile.exists():
            outfile.unlink()  # delete file
        assert not outfile.exists()
        # outfile contains markup
        span_marker.markup_html_element_with_markup_dict(html_elem, html_out=outfile, debug=debug)
        """creates 
        <pyamihtmlx>/test/resources/unfccc/unfcccdocuments/1_CMA_3_section/normalized.sections.html
        """
        assert outfile.exists()
        return html_elem

    #    class SpanMarker:

    def get_span_range_from_markup_dict(self, markup_dict):
        """looks for
        'span_range': [n, m]
        and returns a range. Defaults to [0,99999]
        """
        span_range_text = self.markup_dict.get(self.SPAN_RANGE)
        if span_range_text is None:
            span_range_text = [0, 99999]
        else:
            # oif form
            pass
        return span_range_text

    #    class SpanMarker:

    @classmethod
    def move_implicit_children_to_parents(cls, html_elem):
        """not yet working fully"""
        levels = ['material', 'Decision', 'chapter', 'subchapter', 'para', 'subpara', 'subsubpara']
        head = HtmlLib.get_head(html_elem)
        body_new, html_new = cls.make_new_html_with_copied_head(head)
        body = HtmlLib.get_body(html_elem)
        divs = body.xpath("div")
        # assert len(divs) > 1
        stack = []
        root_div = lxml.etree.SubElement(body, "div")
        root_div.attrib["class"] = levels[0]
        stack.append(root_div)
        for div in divs:
            clazz = cls.get_class_for_div(div)
            if clazz is None or clazz not in levels:
                print(f" lenstack {len(stack)} {stack[-1]}")
                stack[-1].append(div)
                continue
            stack_parent = cls.get_lowest_parent_in_stack_higher_than_div(stack, div, levels)
            if stack_parent is None:
                raise Exception(f"no paremt error {div}")
            stack_parent.append(div)
            cls.clear_stack_below(stack, div)

    #    class SpanMarker:

    def move_implicit_children_to_parents_old(self):

        """look for preceeding sibling with higher class and add to it
        """
        """
            "subpara": {
                "level": 3,
                "parent": ["para"],
                "example": ["(a)Common time frames"],
                "regex": "\\((?P<subpara>[a-z])\\)",
                "names": ["subpara"],
                "background": "#ffff77",
                "class": "subpara",
                "span_range": [0, 1],
            },        
        """

        #    class SpanMarker:

        def delete_parent_level(current_parents, child_index, levels):
            print(f"delete {child_index} from {current_parents}")
            current_parent_index = len(current_parents) - 1
            delta = current_parent_index - child_index
            del current_parents[delta:]
            print(f" >> {current_parents}")

        #    class SpanMarker:

        def add_parent_level(current_parents, child_index, levels):
            print(f"add {child_index} to {current_parents}")
            current_parent_index = len(current_parents) - 1
            delta = child_index - current_parent_index - 1
            for i in range(delta):
                current_parents.append(levels[current_parent_index + i + 1])
            print(f" >> {current_parents}")

        self.html_elem = lxml.etree.parse(str(self.infile))
        divs = self.html_elem.xpath(".//div")

        """
        <div left="141.72" right="484.28" top="143.22">
          <span x0="141.72" y0="143.22" x1="484.28" style="background : #ffff77" class="subpara">
            <a href="a">(a)</a>
          </span>
          <span x0="141.72" y0="143.22" x1="484.28" style="background : #ffff77" class="subpara">Common time frames for nationally determined contributions referred to in Article 4, paragraph 10, of the Paris Agreement (decision 6/CMA.3); </span>
        </div>
        """
        level_dict_elems = self.get_dict_elems_with_levels(self.markup_dict)
        level_dict = defaultdict(list)
        levels = ["material", "Decision", "chapter", "subchapter", "para", "subpara", "subsubpara"]
        current_parent_levels = []
        current_parent_stack = []
        html_new = HtmlLib.create_html_with_empty_head_body()

        html_body = HtmlLib.get_body(html_new)
        root = lxml.etree.SubElement(html_body, "div")
        current_parent = root
        index = 0
        root.attrib["class"] = levels[index]
        current_parent_stack.append(root)
        last_parent_level_index = index

        preamble = lxml.etree.SubElement(root, "div")
        preamble.attrib["class"] = "Decision"
        # self.add_span(preamble, "preamble")
        # current_parents.append(preamble)

        divs = self.html_elem.xpath("//div")
        last_div = None
        for div in divs:
            print(f"current_parent {current_parent_stack[-1].attrib.get('class')}")
            clazz = self.get_class_from_div(div)
            print(f"div.txt> {clazz} {get_div_text(div)}")
            if not clazz in levels:
                current_parent_stack[-1].append(div)  # ordinary paragraphs
                current_parent = current_parent  # to emphasize we aren't changing
                current_parent.append(div)
                delta_level = -1
            else:
                level_index = levels.index(clazz)
                delta_level = last_parent_level_index - level_index
                print(f"class>>> {clazz} {level_index} {delta_level}")

                last_parent_level_index = -1 if len(current_parent_levels) == 0 else levels.index(
                    current_parent_levels[-1])
                if delta_level == -1:  # consistent parent
                    print(f"consistent {clazz} ")
                    current_parent_stack[-1].append(div)  # add to html document
                elif delta_level < -1:  # make
                    print(f"lower index {delta_level}")
                    add_parent_level(current_parent_levels, level_index, levels)
                    delta = last_parent_level_index - level_index + 1
                    for i in range(delta):
                        current_parent_stack.pop()
                    current_parent = div
                    current_parent_stack[-1].append(div)
                elif delta_level >= 0:
                    print(f"higher index {delta}")
                    delete_parent_level(current_parent_levels, level_index, levels)
                    delta = level_index - last_parent_level_index
                    for i in range(delta):
                        dummy_div = create_dummy_div()
                        try:
                            current_parent_stack[-1].append(div)
                            current_parent_stack.append(div)
                        except Exception as e:
                            print(f"**** cannot add div {e}")
                            continue
                else:
                    raise Exception(">>>impossible")
            last_div = div

        print(f"div {len(self.html_elem.xpath('//div'))}")
        print(f"div/div {len(self.html_elem.xpath('//div/div'))}")
        print(f"div/div/div {len(self.html_elem.xpath('//div/div/div'))}")
        print(f"div/div/div/div {len(self.html_elem.xpath('//div/div/div/div'))}")
        print(f"div/div/div/div/div {len(self.html_elem.xpath('//div/div/div/div/div'))}")

    def add_span(self, preamble, text):
        span = lxml.etree.SubElement(preamble, "span")
        span.text = text

    def get_class_from_div(self, div):
        return str(div.xpath("span/@class")[0])

    #    class SpanMarker:

    def get_dict_elems_with_levels(self, markup_dict):
        """finds markup_dit elements with 'level'"""
        level_dict_elems = []
        if markup_dict:
            for (key, dict_elem) in markup_dict.items():
                if dict_elem.get("level") is not None:
                    print(f"elem {dict_elem}")
                    level_dict_elems.append(dict_elem)
        return level_dict_elems

    #    class SpanMarker:

    @classmethod
    def create_dir_and_file(cls, subdir=None, stem=None, suffix=None):
        """create output directory from filename"""
        print(f"create_dir_and_file NYI")

    #    class SpanMarker:

    @classmethod
    def split_presplit_into_files(cls, presplit_file, outdir, outstem="split"):
        """reads presplit_file which contains nested split divs and write a file for each div
        structure:
        body
            div[class='topdiv']
            div[class='section']
                div
                div
            div[class='section']
                div
                div

        """
        # .../htnl/1_4_CMA_3/presplit.html
        top_stem = Path(presplit_file).parent.stem
        print(f"top stem {top_stem}")
        html = lxml.etree.parse(str(presplit_file))
        section_divs = HtmlLib.get_body(html).xpath("div[@class='top']/div[@class='section']")
        assert len(section_divs) > 0, f"expected section divs in file"
        for section_div in section_divs:
            text = cls.get_text_of_first_div(section_div)
            print(f"text {text}")

    #    class SpanMarker:

    @classmethod
    def get_text_of_first_div(cls, section_div):
        first_child_div = section_div.xpath("div")[0]
        text = "".join(first_child_div.itertext())
        return text

    #    class SpanMarker:

    @classmethod
    def _check_splittable(cls, html):
        """checks this is the output of presplit
        """
        bodydivs = HtmlLib.get_body(html).xpath("div")
        if len(bodydivs) >= 1:
            print(f"NOT A splittable file {html}")
            return
        assert len(bodydivs) == 1, "exactly one div on body"
        bodydiv = bodydivs[0]
        assert bodydiv.get("class") == "top", "body/div must have class='top'"
        subdivs = bodydiv.xpath("div[class='sectiom']")
        assert len(subdivs) > 0, "must have some divs with class='section'"
        subsubdivs = bodydiv.xpath("div[class='sectiom']/div")
        assert len(subsubdivs) > 0, "must have some children under sections"

    #    class SpanMarker:

    @classmethod
    def split_presplit_and_write_files(cls, infile, outdir=None, debug=False):
        """Obsolete?"""
        """presplit should have hierachy in HTML
        html
            head
                style
                style
            body
                div class='top'
                    div class='sectiom'
                       div
                       div
                       ...
                    div class='sectiom'
                       div
                       div
                       ...
        """
        inhtml = lxml.etree.parse(str(infile))
        cls._check_splittable(inhtml)
        body = HtmlLib.get_body(inhtml)
        sections = body.xpath("div[@class='top']/div[@class='section']")
        for section_div in sections:
            cls.get_title_from_first_div(section_div)

    @classmethod
    def get_title_from_first_div(cls, section_div):

        pass

    @classmethod
    def get_level_index(cls, levels, span):
        clazz = span.get("class")
        if not clazz in levels:
            return None
        index = None if clazz is None else levels.index(clazz)
        return index

    #    class SpanMarker:

    @classmethod
    def get_lowest_parent_in_stack_higher_than_div(cls, stack, div, levels):
        div_clazz = cls.get_class_for_div(div)
        div_index = cls.get_index_for_element(div, levels)

        position = len(stack) - 1
        while position >= 0:
            stack_elem = stack[position]
            stack_clazz = cls.get_class_for_div(stack_elem)
            stack_index = cls.get_index_for_element(stack_elem, levels)
            if stack_index is None:
                break
            if stack_index < div_index:
                print("add new elem NYI")
            print(f"stack_class {stack_clazz}")
            position -= 1
            if div_clazz == stack_clazz:
                print(f"matched ")

    #    class SpanMarker:

    @classmethod
    def get_class_for_div(cls, div):
        if div is None:
            return None
        spans = div.xpath("span[@class]")
        return None if len(spans) == 0 else spans[0].get("class")

    @classmethod
    def get_index_for_element(cls, div, levels):
        clazz = cls.get_class_for_div(div)
        return None if (clazz == None or clazz not in levels) else levels.index(clazz)

    #    class SpanMarker:

    @classmethod
    def clear_stack_below(cls, stack, div):
        div_index = stack.index(div)
        stack = stack[:div_index + 1]

    def create_id_from_span(self, span0):
        """creates id from span content
        :param span0: span containing text from which id can be generated
        "return" id or None
        """
        # TODO
        print("ID calculation NYI")
        return None

    #    class SpanMarker:

    #    class SpanMarker:

    @classmethod
    def assert_sections(cls, decisions, nlower):
        assert len(decisions) >= nlower
        print(f"decisions {len(decisions)}")


class HtmlCleaner:
    XY_LIST = ["x0", "x1", "y0", "y1"]
    LRTB_LIST = ["left", "right", "top", "bottom"]
    STYLE_LIST = ["style"]

    def __init__(self, options=None):
        self.options = []
        if options:
            for option in options:
                if type(option) is list:
                    self.options.extend(option)
                else:
                    self.append(option)
            print(f"atts to remove {self.options}")

    def clean_elems(self, html_elem, xpath):
        if html_elem is None:
            raise ValueError(f" cannot clean None")
        if xpath is None:
            raise ValueError("must have xpath for clean")
        for option in self.options:
            for elem in html_elem.xpath(xpath):
                self.remove_att(elem, option)
        return html_elem

    @classmethod
    def create_cleaner(cls, options):
        html_cleaner = HtmlCleaner(options=options)
        return html_cleaner

    def remove_att(self, html_elem, att):
        """removes attributes
        :param html_elem: element to clean
        :param att: attribute to remove
        """
        if html_elem is None:
            raise ValueError(f"html_elem is None")
        attribs = html_elem.attrib
        if att in attribs:
            attribs.pop(att)


@dataclass
class HtmlPipelineData:
    """holds state and can be passed between steps"""
    """I'm not yet using this properly
    """
    file_splitter = None  # do we need this
    indir: str
    insubdir: str
    instem: str
    outsubdir: str
    top_outdir: str
    directory_maker: str
    markukp_dict: dict
    inline_dict: dict
    param_dict: dict
    targets: list
    styles: list
    force_make_pdf: bool
    svg_dir: str
    page_json_dir: str
    debug: bool

    def __init__(self,
        file_splitter = None,
        insubdir = None,
        instem = None,
        outsubdir = None,
        top_outdir = None,
        directory_maker = None,
        markukp_dict = None,
        inline_dict = None,
        param_dict = None,
        targets = None,
        styles = None,
        force_make_pdf = True,
        svg_dir = None,
        page_json_dir = None,
        debug = False
    ):
        self.file_splitter=file_splitter
        self.insubdir=insubdir
        self.instem=instem
        self.outsubdir=outsubdir
        self.top_outdir=top_outdir
        self.directory_maker=directory_maker
        self.markukp_dict=markukp_dict
        self.inline_dict=inline_dict
        self.param_dict=param_dict
        self.targets=targets
        self.styles=styles
        self.force_make_pdf=force_make_pdf
        self.svg_dir=svg_dir
        self.page_json_dir=page_json_dir
        self.debug=debug

    @classmethod
    def make_dataclass(cls):
        dc = HtmlPipelineData(
        file_splitter = None,
        insubdir = None,
        instem = None,
        outsubdir = None,
        top_outdir = None,
        directory_maker = None,
        markukp_dict = None,
        inline_dict = None,
        param_dict = None,
        targets = None,
        styles = None,
        force_make_pdf = True,
        svg_dir = None,
        page_json_dir = None,
        debug = False
        )
        """holds state and can be passed between steps"""
        return dc


class HtmlPipeline:
    """pipeline for HTML conversioms"""

    @classmethod
    def stateless_pipeline(
            cls, file_splitter=None, in_dir=None, in_sub_dir=None, instem=None, out_sub_dir=None, top_out_dir=None,
            directory_maker=None, markup_dict=None, inline_dict=None, param_dict=None, targets=None,
            styles=None, force_make_pdf=False, svg_dir=None, page_json_dir=None, pipeline_data=None,
            debug=True):
        """original, being converted to instances with stateful dataclass"""
        """file_splitter, in_dir, in_sub_dir, instem, out_sub_dir, skip_assert, top_out_dir,
                    directories=UNFCCC, markup_dict=MARKUP_DICT"""
        # runs about 10 steps , nearly production quality
        if pipeline_data is None:
            pipeline_data = HtmlPipelineData.make_dataclass()
        if targets == "*" and markup_dict:
            targets = markup_dict.keys()
        if debug:
            print(f"targets {targets}")

        print(f"=================\nparsing {instem}\n===============")
        if directory_maker is None:
            print(f" cannot create directories using {directory_maker}")
            return
        if not markup_dict:
            print(f"no markup_dict given, abort")
            return

        # STEP 1
        # in "/Users/pm286/workspace/pyamihtml_top/test/resources/unfccc/unfcccdocuments1/CMA_3/1_4_CMA_3.pdf
        # out "/Users/pm286/workspace/pyamihtml_top/temp/unfcccOUT/CMA_3/1_4_CMA_3/raw.html"
        outfile = cls.convert_pdf_to_html(directory_maker=directory_maker, in_sub_dir=in_sub_dir, instem=instem,
                                          top_out_dir=top_out_dir, param_dict=param_dict,
                                          force_make_pdf=force_make_pdf, svg_dir=svg_dir, page_json_dir=page_json_dir,
                                          pipeline_data=pipeline_data, debug=debug)
        assert outfile.exists(), f"{outfile} should exist"
        # STEP 2/3
        html_outdir, outfile_normalized = cls.run_step2_3(outfile)
        # STEP 4
        sectiontag_file = cls.run_step_4_tag_sections(html_outdir, in_dir, markup_dict, outfile_normalized)
        """types of tag (not exhaustive"""
        """ Decision
                    <div left="113.28" right="225.63" top="754.51">
                      <span x0="113.28" y0="754.51" x1="225.63" style="background : #ffaa00" class="Decision">Decision 2/CMA.3 </span>
                    </div>

                    5 ) split major sections into separate HTML files (CMA1_4 -> CMA1, CMA2 ...)
                    """
        # STEP 5 splitting
        filestem, subdirs = cls.run_step5_split_to_files(file_splitter, markup_dict, out_sub_dir, sectiontag_file)
        print(f"subdirs {subdirs}")
        """
                    7 ) assemble nested hierarchical documents
                    """
        outstem = "nested"
        outstem1 = "marked"
        outstem2 = "cleaned"
        for subdir in subdirs:
            cls.make_nested_and_inline_markup_and_clean(filestem, inline_dict, outstem, outstem1, styles, subdir,
                                                        subdirs, targets)

    #    class SpanMarker:

    @classmethod
    def make_nested_and_inline_markup_and_clean(cls, filestem, inline_dict, outstem, outstem1, styles, subdir, subdirs,
                                                targets, outstem2="cleaned", outstem_final="final"):
        infile = Path(subdir, f"{filestem}.html")
        if not infile.exists():
            print(f"cannot find {infile}")
        else:
            outfile = Path(subdir, f"{outstem}.html")
            cls.run_step7_make_nested_noop(filestem, outfile)
            """
            8 ) search for substrings in spans and link to dictionaries
            """
            # partially written
            infile = Path(infile)  # we don't have nested yet
            # infile = Path(outfile)
            outfile = Path(infile.parent, f"{outstem1}.html")
            cls.run_step8_inline_markup(infile, outfile, targets=targets, markup_dict=inline_dict, styles=styles)
            infile = outfile
            outfile = Path(infile.parent, f"{outstem2}.html")
            cleaner = HtmlCleaner.create_cleaner(
                options=[HtmlCleaner.XY_LIST, HtmlCleaner.LRTB_LIST, HtmlCleaner.STYLE_LIST])
            cls.run_step_9_clean(infile, cleaner, outfile=outfile)

            # final step - copy of files to ensure last file is "final"
            infile = outfile
            outfile = Path(infile.parent, f"{outstem_final}.html")
            cls.run_final_step_999(infile, outfile)

    #    class SpanMarker:

    @classmethod
    def convert_pdf_to_html(cls, directory_maker=None, in_sub_dir=None, instem=None, top_out_dir=None,
                            force_make_pdf=True,
                            param_dict=None, svg_dir=None, page_json_dir=None, pipeline_data=None, debug=False):
        pdf_in = Path(in_sub_dir, f"{instem}.pdf")
        print(f"parsing {pdf_in}")
        outsubsubdir, outfile = directory_maker.create_initial_directories(
            in_sub_dir, pdf_in, top_out_dir, out_stem="raw", out_suffix="html")
        # skip PDF conversion if already performed
        if Util.need_to_make(outfile, pdf_in, debug=True) or force_make_pdf:
            html_elem = HtmlGenerator.read_pdf_convert_to_html(
                input_pdf=pdf_in, param_dict=param_dict, svg_dir=svg_dir, page_json_dir=page_json_dir, debug=debug)
            HtmlLib.write_html_file(html_elem, outfile=outfile, debug=debug)
        assert Path(outfile).exists()
        return outfile

    #    class SpanMarker:

    @classmethod
    def run_step2_3(cls, outfile):
        # STEP2
        # STEP3
        cls.print_step(f"STEP2, STEP3 reading {outfile}")
        html_elem = HtmlLib.parse_html(outfile)
        html_outdir = outfile.parent
        print(f"html_outdir {html_outdir}")
        HtmlStyle.extract_styles_and_normalize_classrefs(html_elem,
                                                         font_styles=True)  # TODO has minor bugs in joinig spans
        outfile_normalized = Path(html_outdir, "normalized.html")
        HtmlLib.write_html_file(html_elem, outfile_normalized, debug=True)
        assert outfile_normalized.exists()
        return html_outdir, outfile_normalized

    #    class SpanMarker:

    @classmethod
    def run_step_4_tag_sections(cls, html_outdir, in_dir, markup_dict, outfile_normalized):
        # STEP4 tag sections by style and content
        # marks all potential sections with tags
        # (Decision, Chapter, subchapter, para (numbered) , ascii_list, roman_list,
        cls.print_step("STEP4")
        infile = outfile_normalized
        dict_name = "sectiontag"
        print(f"html_outdir {html_outdir}")
        sectiontag_file = Path(html_outdir, f"{dict_name}.html")
        # tags are defined in markup_dict
        html_elem_out = SpanMarker.markup_file_with_markup_dict(
            in_dir, infile, html_outdir=html_outdir, dict_name=dict_name, outfile=sectiontag_file,
            markup_dict=markup_dict, add_ids=True, debug=True)
        assert sectiontag_file.exists()
        return sectiontag_file

    #    class SpanMarker:

    @classmethod
    def run_step5_split_to_files(cls, file_splitter, markup_dict, out_sub_dir, sectiontag_file):
        cls.print_step("STEP5")
        infile = sectiontag_file
        filestem = "split"
        # # splitter = "span"
        output_dir = out_sub_dir
        # later this will be read from markup_dict, where it can ve generated with f-strings
        # regex = "(?P<DecRes>Decision|Resolution)\\s(?P<decision>\\d+)/(?P<type>CMA|CMP|CP)\\.(?P<session>\\d+)"
        decision_regex = markup_dict["Decision"]["regex"]
        # template = "{DecRes}_{decision}_{type}_{session}"
        decision_template = markup_dict["Decision"]["template"]
        id_xpath = ".//div[span[@class='Decision']]"
        subdirs, filestem = SpanMarker.split_at_sections_and_write_split_files(
            infile, output_dir=output_dir, splitter=file_splitter, id_template=decision_template, id_xpath=id_xpath,
            id_regex=decision_regex, debug=True)
        return filestem, subdirs

    #    class SpanMarker:

    @classmethod
    def run_step7_make_nested_noop(cls, infile, outfile):
        print(f"nesting not yet written")
        return
        html_elem = HtmlLib.parse_html(infile)
        SpanMarker.move_implicit_children_to_parents(html_elem)
        HtmlLib.write_html_file(html_elem, outfile)

    #    class SpanMarker:

    @classmethod
    def run_step8_inline_markup(cls, infile, outfile, targets=None, markup_dict=None, styles=None):
        cls.print_step("STEP8 split spans, add annotation and hyperlinks")
        span_marker = SpanMarker()
        if not targets:
            targets = ["decision", "paris"]  # remove this
        span_marker.split_spans_in_html(
            html_infile=infile, outfile=outfile, targets=targets, markup_dict=markup_dict, debug=True, styles=styles)

    @classmethod
    def run_step_9_clean(cls, infile, html_cleaner, outfile):
        """applies a cleaner to HTML and writes it
        :param infile: input html
        :param outfile: output
        :param cleaner: HtmlCleaner"""
        html_root = HtmlLib.parse_html(infile)

        xpath = ".//span|.//div"
        new_html = html_cleaner.clean_elems(html_root, xpath)
        if new_html is None:
            raise ValueError(f"not new_html")

        HtmlLib.write_html_file(new_html, outfile=outfile, debug=True)
        return new_html

    @classmethod
    def run_final_step_999(cls, infile, outfile):
        """copies file to 'final.html'"""
        html_elem = HtmlLib.parse_html(infile)
        HtmlLib.write_html_file(html_elem, outfile=outfile)

    @classmethod
    def print_step(cls, step):
        print(f"==========\nrunning {step}\n============")

class HearstPattern:
    """extracts Hearst paaterns using regexes
    NYI
    """

    def __init__(self, regex=None):
        self.regex = regex

    def extract_group0(self, string):
        pass
