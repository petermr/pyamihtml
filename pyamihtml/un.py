import csv
import re
from collections import Counter
from pathlib import Path

import lxml

# decisión 2/CMA.3, anexo, capítulo IV.B
from pyamihtml.util import EnhancedRegex
from pyamihtml.xml_lib import HtmlLib

DECISION_SESS_RE = re.compile("(?P<front>.*\D)(?P<dec_no>\d+)/(?P<body>.*)\.(?P<sess_no>\d+)\,?(?P<end>.*)")
# annex, para. 5).
DEC_END = re.compile("\)?(?P<annex>.*)?\,?\s*(para(\.|graph)?\s+(?P<para>\d+))\)?")
DEC_FRONT = re.compile(".*(?P<decision>decision)")

RESERVED_WORDS = {
    'Recalling',
    'Also recalling',
    'Further recalling',
    'Recognizing',
    'Cognizant',
    'Annex',
    'Abbreviations and acronyms',
    'Noting',
    'Acknowledging',
}

CPTYPE = "CP|CMA|CMP"
TARGET_DICT = {
    "decision": {
        "example": "decision 12/CMP.23",
         "components": ["", ("decision", "\d+"), "/", ("type", CPTYPE), "\.", ("session", "\d+"), ""],
         "regex": "decision \d+/(CMP|CMA|CP)\.\d+",

    }
}
ROMAN = "I|II|III|IIII|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI*"
# section dict
MARKUP_DICT = {

    "Decision": {
        "level": "0",
        "parent": [],
        "example": ["Decision 1/CMA.1"],
        "regex": f"Decision (?P<Decision>\d+)/(?P<type>{CPTYPE})\.(?P<session>\d+)",
        "components": ["", ("Decision", "\d+"), "/", ("type", CPTYPE), "\.", ("session", "\d+"), ""],
        "names": ["roman", "title"],
        "background": "#ffaa00",
    },
    "decision": {
        "example": "decision 12/CMP.23",
         "components": ["", ("decision", "\d+"), "/", ("type", CPTYPE), "\.", ("session", "\d+"), ""],
         "regex": f"decision (?P<decision>\d+)/(?P<type>{CPTYPE})\.(?P<session>)\d+",
         "background": "#ffffaa", # light yellow
    },
    "major": {
        "level": "1",
        "parent": ["decision"],
        "example": ["VIII.Collaboration"],
        "regex": f"(?P<roman>{ROMAN})\.\s*(?P<title>[A-Z].*)",
        "components": ["", ("roman", f"{ROMAN}"), "/", ("type", CPTYPE), "\.", ("session", "\d+"), ""],
        "names": ["roman", "title"],
        "background": "#ffaa00",
    },
    "para": {
        "level": "2",
        "parent": ["major"],
        "example": ["26. Emphasizes the urgent"],
        "regex": "(?P<para>\d+\.(\s*))",
        "names": ["para"],
        "background": "#00ffaa",
    },
    "subpara": {
        "level": "3",
        "parent": ["para"],
        "example": ["(a)Common time frames"],
        "regex": "\((?P<subpara>[a-z])\)",
        "names": ["subpara"],
        "background": "#ffff77",
    },
    "subsubpara": {
        "level": "4",
        "parent": ["subpara"],
        "example": ["(i)Methods for establishing"],
        "regex": "\((?P<subsubpara>[ivx]+)\)",
        "names": ["subsubpara"],
        "background": "#aaffaa",
    },
    "capital": {
        "level": "C",
        "parent": [],
        "example": ["B.Annual information"],
        "regex": "(?P<capital>[A-Z])\.",
        "names": ["capital"],
        "background": "#00ffff",
    },

}
INLINE_DICT = {
    "decision": {
        "regex": "[Dd]ecision\s+\d+/(CMA|CP|CMP)",
        "split_span": True,
        "idgen": "NYI",
    }
}


def plot_test():
    from pyvis.network import Network
    import networkx as nx
    nx_graph = nx.cycle_graph(10)
    nx_graph.nodes[1]['title'] = 'Number 1'
    nx_graph.nodes[1]['group'] = 1
    nx_graph.nodes[3]['title'] = 'I belong to a different group!'
    nx_graph.nodes[3]['group'] = 10
    nx_graph.add_node(20, size=20, title='couple', group=2)
    nx_graph.add_node(21, size=15, title='couple', group=2)
    nx_graph.add_edge(20, 21, weight=5)
    nx_graph.add_node(25, size=25, label='lonely', title='lonely node', group=3)
    nt = Network('500px', '500px')
    # populates the nodes and edges data structures
    nt.from_nx(nx_graph)
    nt.show('nx.html', notebook=True)

def plot_test1():
    from pyvis import network as net
    import networkx as nx

    g = net.Network(
        # notebook=True
    )
    nxg = nx.complete_graph(5)
    g.from_nx(nxg)

    # html = str(Path("example.html    g.show(html, notebook=True)


def make_id_from_match_and_idgen(match, idgen):
    """idgen is of the form <grouo>some text<group>
    where groups correspond to named capture groups in regex

    """
    diamond = "<[^>]*>"
    match = re.split(diamond, idgen)


class UNFCCC:
    """supports the UN FCCC documents (COP, etc.)
    """
    REGEX = "regex"
    BACKGROUND = "background"
    COMPONENTS = "components"
    SECTION = "section"
    TARGET = "target"

    def __init__(self):
        self.graph = True
        self.unmatched = Counter() # counter for sets
        self.indir = None
        self.outdir = None
        self.infile = None
        self.outfile = None
        self.inhtml = None
        self.outcsv = None

#    class UNFCCC:

    # this is a mess
    def read_and_process_pdfs(self, pdf_list):
        if len(pdf_list) == 0:
            print(f"no PDF files given")
            return None
        self.outdir.mkdir(exist_ok=True)
        self.outcsv = str(Path(self.outdir, self.outfile))
        self.anayze_pdfhtml_and_write_links(pdf_list)

    def anayze_pdfhtml_and_write_links(self, pdfs):
        if pdfs is None:
            print(f'no pdfs')
            return
        if self.outcsv is None:
            print(f"no outfile")
        pdf_list = [pdfs] if type(pdfs) is not list else pdfs
        Path(self.outcsv).parent.mkdir(exist_ok=True)
        with open(self.outcsv, "w") as f:
            self.csvwriter = csv.writer(f)
            self.csvwriter.writerow(["source", "link_type", self.TARGET, self.SECTION, "para"])

            for i, pdf in enumerate(sorted(pdf_list)):
                self.analyze_pdf(DECISION_SESS_RE, pdf, options=[self.TARGET, self.SECTION])
        print(f"wrote {self.outcsv}")

# class UNFCCC:

    def analyze_pdf(self, decision_sess_re, pdf, options=None):
        from pyamihtml.ami_integrate import HtmlGenerator
        from pyamihtml.xml_lib import HtmlLib, XmlLib

        if not options:
            options = []
        self.stem = Path(pdf).stem
        html_elem = HtmlGenerator.create_sections(pdf, debug=False)
        out_type = ""
        if self.SECTION in options:
            self.outdir = outdir = str(Path(Path(pdf).parent, self.stem + "_section"))
            self.markup_spans(html_elem)
            out_type = self.SECTION
        if self.TARGET in options:
            self.find_targets(decision_sess_re, html_elem)
            out_type += " " + self.TARGET
        if out_type:
            html_out = Path(Path(pdf).parent, self.stem + "_" + out_type.strip( ) + ".html")
            HtmlLib.write_html_file(html_elem, html_out)
    #    class UNFCCC:

    def markup_spans(self, html_elem):
        """finds numbered sections
        1) font-size: 14.04; font-family: DDBMKM+TimesNewRomanPS-BoldMT;  starts-with I|II...VI|VII|VIII
        """
        from pyamihtml.ami_html import HtmlStyle

        HtmlStyle.extract_all_style_attributes_to_head(html_elem)
        HtmlStyle.extract_styles_and_normalize_classrefs(html_elem, outdir=self.outdir)
        div_with_spans = html_elem.xpath(".//div[span]")
        for div_with_span in div_with_spans:
            self.markup_span(div_with_span)

# class UNFCCC:

    def find_targets(self, target_regex, html_elem):
        text_parents = html_elem.xpath("//*[text()]")
#        texts = html_elem.xpath("//*/text()")
        """decisión 2/CMA.3, anexo, capítulo IV.B"""
        # doclink = re.compile(".*decisión (?P<decision>\d+)/CMA\.(?P<cma>\d+), (?P<anex>anexo), (?P<capit>capítulo) (?P<roman>[IVX]+)\.(?P<letter>5[A-F]).*")
        for text_parent in text_parents:
            text = text_parent.xpath("./text()")[0]
            if text is not None and len(text.strip()) > 0:
                row = self.extract_text(target_regex, text)
                if row:
                    self.csvwriter.writerow(row)
                    text_parent.attrib["style"] = "background : #bbbbf0"



# class UNFCCC:

    def extract_text(self, regex, text):
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
        match_end = re.match(DEC_END, end)
        annex = ""
        para = ""
        if match_end:
            annex = match_end.group("annex")
            para = match_end.group("para")
            print(f">>>(annex || {para}")

        row = [self.stem, "refers", target, annex[:25], para]
        return row

# class UNFCCC

    def markup_span(self, div):
        """extract number/letter and annotate """
        span = div.xpath("./span")
        if not span:
            return
        span0 = span[0]
        text = span0.xpath("./text()")
        if text:
            text = text[0]
        match = None
        for markup in MARKUP_DICT.items():
            match = self.apply_markup(markup, span0, text)
            if match:
                break
        if not match:
            self.unmatched[text] += 1
            print(f"cannot match: {text}")

    def apply_markup(self, markup, span0, text):
        markup_key = markup[0]
        markup_dict = markup[1]
        # print(f"markup_key {markup_key}, markup_dict {markup_dict}")
        regex = markup_dict.get(self.REGEX)
        # print(f"regex {regex}")
        match = re.match(regex, text)
        if match:
            components = markup_dict.get(self.COMPONENTS)
            if components:
                # components = ["", ("decision", "\d+"), "/", ("type", "CP|CMA|CMP"), "\.", ("session", "\d+"), ""]
                enhanced_regex = EnhancedRegex(components=components)
                id = enhanced_regex.make_id(text)
                print(f"ID {id}")
            clazz = span0.attrib["class"]
            if clazz:
                pass
                # print(f"clazz {clazz}")
            span0.attrib["class"] = self.SECTION
            span0.attrib["style"] = f"background : {markup_dict.get(self.BACKGROUND)}"
        return match

    def analyse_after_match(self, outgraph="graph.html"):
        if self.unmatched:
            # print(f"UNMATCHED {self.unmatched}")
            pass
        if self.graph:
            self.plot_graph(outgraph)

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

    def plot_graph(self, outhtml):
        from pyvis.network import Network
        import pandas as pd

        plot_test1()
        return
        if not self.outcsv:
            print(f"no CSV")
            return

        height = "750px"
        width = "100%"
        bgcolor = "#222222"
        font_color = "white"
        network = Network(height=height, width=(width), bgcolor=bgcolor, font_color=font_color)

        # set the physics layout of the network
        network.barnes_hut()
        got_data = pd.read_csv(self.outcsv)

# source,link_type,target,section,para
        sources = got_data['source']
        targets = got_data['target']
        # weights = got_data['Weight']

        # edge_data = zip(sources, targets, weights)
        edge_data = zip(sources, targets)

        for e in edge_data:
            src = e[0]
            dst = e[1]
            # w = e[2]
            w = 1

            network.add_node(src, src, title=src)
            network.add_node(dst, dst, title=dst)
            network.add_edge(src, dst, value=w)

        neighbor_map = network.get_adj_list()

        # add neighbor data to node hover data
        for node in network.nodes:
            node["title"] += " Neighbors:<br>" + "<br>".join(neighbor_map[node["id"]])
            node["value"] = len(neighbor_map[node["id"]])
        network.show(outhtml)

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
        for i, div in enumerate(divs):
            texts = div.xpath("span/text()")
            text = None if len(texts) == 0 else texts[0]
            match = None if text is None else regex.match(text)
            if match:
                div0 = self.add_new_section_div(divtop)
                if idgen:
                    id = make_id_from_match_and_idgen()
                print(f"{match.group('decision')}:{match.group('type')}:{match.group('session')}")
            div0.append(div)

    def add_new_section_div(self, divtop):
        div0 = lxml.etree.SubElement(divtop, "div")
        div0.attrib["class"] = "section"
        return div0

    def write_links(self, param):
        print(f"write_links NYI")




