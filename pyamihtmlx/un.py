import argparse
import ast
import csv
import glob
import logging
import re

# decisión 2/CMA.3, anexo, capítulo IV.B
import textwrap
from collections import Counter
from datetime import date
from pathlib import Path

import json

import lxml
import pandas as pd
import sys

from lxml.html import HTMLParser

from pyamihtmlx.ami_html import HtmlUtil
from pyamihtmlx.html_marker import HtmlPipeline
from pyamihtmlx.util import AbstractArgs
from pyamihtmlx.xml_lib import HtmlLib
from test.resources import Resources

ROMAN = "I|II|III|IIII|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI*"
L_ROMAN = "i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xiv|xv|xvi|xvii|xviii|xix|xx"
INT = "\\d+"  # integer of any length
DIGIT = "\\d"  # single digit
DOT = f"\\."  # dot
MINUS = "-"
FLOAT = f"{MINUS}?{INT}({DOT}{INT})?"
SP = "\\s"  # single space
WS = "\\s+"  # spaces
ANY = ".*"
SL = "/"  # slash
LP = "\\("  # left parenthesis
RP = "\\)"  # right parenthesis
LC = "[a-z]"  # single uppercase
UC = "[A-Z]"  # single uppercase
#
DECISION_SESS_RE = re.compile(
    f"(?P<front>{ANY}\\D)(?P<dec_no>{INT})/(?P<body>{ANY}){DOT}(?P<sess_no>{INT}){DOT}?(?P<end>{ANY})")
# annex, para. 5).
DEC_END = re.compile(f"{RP}?(?P<annex>{ANY})?{DOT}?{WS}(para({DOT}|graph)?{WS}(?P<para>{INT})){RP}?")
DEC_FRONT = re.compile(f"{ANY}(?P<decision>decision)")

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

RESERVED_WORDS1 = "(Also|[Ff]urther )?([Rr]ecalling|[Rr]ecogniz(es|ing)|Welcomes|[Cc]ognizant|[Nn]ot(ing|es)" \
                  "|Invit(es|ing)|Acknowledging|[Ex]pressing appreciation]|Recalls|Stresses|Urges|Requests|Expresses alarm)"
DOC_STRUCT = {
    'Annex',
    'Abbreviations and acronyms',
}

STYLES = [
    #  <style classref="div">div {border: red solid 0.5px;}</style>
    "span.temperature {border: purple solid 0.5px;}",
    ".chapter {border: blue solid 0.8px; font-weight: bold; background: red;}",
    ".subchapter {background: pink;}",
    ".para {border: blue dotted 0.6px; margin: 0.3px;}",
    ".subpara {border: blue solid 0.4px; margin: 0.2px; background: #eeeeee; opacity: 0.7}",
    ".subsubpara {border: blue dashed 0.2px; margin: 2px; background: #dddddd; opacity: 0.3}",
    "a[href] {background: #ffeecc;}",
    "* {font-size: 7; font-family: helvetica;}",
]

CPTYPE = "CP|CMA|CMP"

TARGET_DICT = {
    "decision": {
        "example": "decision 12/CMP.23",
        "components": ["", ("decision", f"{INT}"), "/", ("type", CPTYPE), f"{DOT}", ("session", f"{INT}"), ""],
        "regex": f"decision {INT}/({CPTYPE}){DOT}{INT}",

    }
}

# section dict
MARKUP_DICT = {
    "Decision": {
        "level": 0,
        "parent": [],
        "example": ["Decision 1/CMA.1", "Decision 1/CMA.3"],
        "regex": f"Decision (?P<Decision>{INT})/(?P<type>{CPTYPE})\\.(?P<session>{INT})",
        "components": ["", ("Decision", f"{INT}"), "/", ("type", {CPTYPE}), f"{DOT}", ("session", f"{INT}"), ""],
        "names": ["roman", "title"],
        "class": "Decision",
        "span_range": [0, 1],
        "template": "Decision_{Decision}_{type}_{session}",
    },
    "Resolution": {
        "level": 0,
        "parent": [],
        "example": ["Resolution 1/CMA.1", "Resolution 1/CMA.3"],
        "regex": f"Resolution (?P<Resolution>{INT})/(?P<type>{CPTYPE})\\.(?P<session>{INT})",
        "components": ["", ("Resolution", f"{INT}"), "/", ("type", {CPTYPE}), f"{DOT}", ("session", f"{INT}"), ""],
        "names": ["roman", "title"],
        "class": "Resolution",
        "span_range": [0, 1],
        "template": "Resolution{Resolution}_{type}_{session}",
    },
    "chapter": {
        "level": 1,
        "parent": ["Decision"],
        "example": ["VIII.Collaboration", "I.Science and urgency"],
        "regex": f"(?P<dummy>)(?P<roman>{ROMAN}){DOT}\\s*(?P<title>{UC}.*)",
        "components": [("dummy", ""), ("roman", f"{ROMAN}"), f"{DOT}{WS}", ("title", f"{UC}{ANY}")],
        "names": ["roman", "title"],
        "class": "chapter",
        "span_range": [0, 1],
        "template": "chapter_{roman}",
    },
    "subchapter": {
        "level": "C",
        "parent": ["chapter"],
        "example": ["B.Annual information"],
        "regex": f"(?P<capital>{UC}){DOT}",
        "names": ["subchapter"],
        "class": "subchapter",
        "span_range": [0, 1],
        "template": "subchapter_{capital}",
    },

    "para": {
        "level": 2,
        "parent": ["chapter", "subchapter"],
        "example": ["26. "],
        "regex": f"(?P<para>{INT}){DOT}{SP}*",
        "names": ["para"],
        "class": "para",
        "parent": "preceeding::div[@class='roman'][1]",
        "idgen": {
            "parent": "Decision",
            "separator": ["_", "__"],
        },
        "span_range": [0, 1],
        "template": "para_{para}",
    },
    "subpara": {
        "level": 3,
        "parent": ["para"],
        "example": ["(a)Common time frames"],
        "regex": f"{LP}(?P<subpara>{LC}){RP}",
        "names": ["subpara"],
        "class": "subpara",
        "span_range": [0, 1],
        "template": "subpara_{subpara}",

    },
    "subsubpara": {
        "level": 4,
        "parent": ["subpara"],
        "example": ["(i)Methods for establishing"],
        "regex": f"{LP}(?P<subsubpara>{L_ROMAN}){RP}",
        "names": ["subsubpara"],
        "class": "subsubpara",
        "span_range": [0, 1],
    },

}
SUBPARA = f"({LP}?P<subpara>{LC}){RP}"
SUBSUBPARA = f"({LP}?P<subsubpara>{L_ROMAN}){RP}"
PARENT_DIR = "unfccc/unfcccdocuments1"  # probably temporary
TARGET_DIR = "../../../../../temp/unfccc/unfcccdocuments1/"

REPO_TOP = "https://raw.githubusercontent.com/petermr/pyamihtml/main"
TEST_REPO = f"{REPO_TOP}/test/resources/unfccc/unfcccdocuments1"
TEMP_REPO = f"{REPO_TOP}/temp/unfccc/unfcccdocuments1"
print(f"TEMP_REPO: {TEMP_REPO}")

# markup against terms in spans
TARGET_STEM = "marked"  # was "split"
INLINE_DICT = {
    "decision": {
        "example": ["decision 1/CMA.2", "noting decision 1/CMA.2, paragraph 10 and ", ],
        "regex":
        # f"decision{WS}(?P<decision>{INT})/(?P<type>{CPTYPE}){DOT}(?P<session>{INT})",
        # f"decision{WS}(?P<decision>{INT})/(?P<type>{CPTYPE}){DOT}(?P<session>{INT})(,{WS}paragraph(?P<paragraph>{WS}{INT}))?",
            f"(?P<decision>{INT})/(?P<type>{CPTYPE}){DOT}(?P<session>{INT})",
        "href": "FOO_BAR",
        "split_span": True,
        "idgen": "NYI",
        "_parent_dir": f"{TARGET_DIR}",
        "span_range": [0, 99],

        # "href_template": f"{PARENT_DIR}/{{type}}_{{session}}/Decision_{{decision}}_{{type}}_{{session}}",
        # "href_template": f"../../{{type}}_{{session}}/Decision_{{decision}}_{{type}}_{{session}}",
        "href_template": f"{TARGET_DIR}/{{type}}_{{session}}/Decision_{{decision}}_{{type}}_{{session}}/{TARGET_STEM}.html",
    },
    "paragraph": {
        "example": [
            "paragraph 32 above",
            "paragraph 23 below",
            "paragraph 9 of decision 19/CMA.3",
            "paragraph 77(d)(iii)",
            "paragraph 37 of chapter VII of the annex",
        ],
        "regex": [f"paragraph (?P<paragraph>{INT} (above|below))",
                  f"paragraph (?P<paragraph>{INT}{LP}{LC}{RP}{LP}{L_ROMAN}{RP})"
                  ],
    },
    "exhort": {
        "regex": f"{RESERVED_WORDS1}",
        "href": "None",
    },
    "article": {
        "example": ["Article 4, paragraph 19, of the (Paris Agreement)",
                    "tenth preambular paragraph of the Paris Agreement",
                    "Article 6, paragraph 3"],
        "regex": f"Article (?P<article>{INT}), paragraph (?P<paragraph>{INT}), (of the (?P<agreement>Paris Agreement))?",
    },
    "trust_fund": {
        "regex": "Trust Fund for Supplementary Activities",
        "href_template": "https://unfccc.int/documents/472648",
    },
    "adaptation_fund": {
        "regex": "([Tt]he )?Adaptation Fund",
        "href_template": "https://unfccc.int/Adaptation-Fund",
    },
    "paris": {
        "regex": "([Tt]he )?Paris Agreement",
        "href_template": "https://unfccc.int/process-and-meetings/the-paris-agreement",
    },
    "cop": {
        "regex": "([Tt]he )?Conference of the Parties",
        "href_template": "https://unfccc.int/process/bodies/supreme-bodies/conference-of-the-parties-cop",
    },
    "sbi": {
        "regex": "([Tt]he )?Subsidiary Body for Implementation",
        "acronym": "SBI",
        "wiki": "https://en.wikipedia.org/wiki/Subsidiary_Body_for_Implementation",
        "href": "https://unfccc.int/process/bodies/subsidiary-bodies/sbi"
    },
    # data
    "temperature": {
        "example": "1.5 °C",
        "regex": f"{FLOAT}{WS}°C",
        "class": "temperature",
    },
    # date
    "date": {
        "example": "2019",
        "regex": f"20\\d\\d",
        "class": "date",
    }
}

TITLE = "UNFCCC Publication Experiment"
AUTHOR = "UNFCCC"
FRONT_SUBTITLE = "#semanticClimate Research Demo"
GITHUB_SOURCE = "https://github.com/semanticClimate/unfccc/"

logger = logging.getLogger(__file__)


def read_dict():
    # reading the data from the file
    # doesn't easily work with f-strings
    # probably not usable
    pyamihtml = Path(__file__).parent
    print(f"path **************** {pyamihtml}")
    dict_file = Path(pyamihtml, 'markup_dict.txt')
    print(f"dict_file **************** {dict_file}")
    with open(str(dict_file)) as f:
        markup_dict_txt = f.read()
    markup_dict = str(markup_dict_txt)
    MARKUP_DICT = json.loads(markup_dict)


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


class UNFCCCArgs(AbstractArgs):

    SESSION_DIR = "session"
    SESSION_HELP = "UNFCCC session name (e.g. 'CMA_3')"
    VAR = "var"

    def __init__(self):
        """arg_dict is set to default"""
        super().__init__()
        self.subparser_arg = "UNFCCC"

    def parse_kwargs_to_string(self, kwargs, keys=None):
        kwargs_dict = {}
        logger.info(f"args: {kwargs}")
        if not kwargs:
            if keys:
                logger.warning(f"possible keys: {keys}")
        else:
            for arg in kwargs:
                logger.debug(f"pair {arg}")
                argz = arg.split(':')
                key = argz[0]
                value = argz[1]
                kwargs_dict[key] = value
            logger.warning(f"kwargs_dict {kwargs_dict}")
        return kwargs_dict

    def add_arguments(self):
        """creates adds the arguments for pyami commandline

        """
        if self.parser is None:
            self.parser = argparse.ArgumentParser()
        self.parser.description = textwrap.dedent(
            'Manage and search UNFCCC resources and other climate stuff. \n'
            '----------------------------------------------------------\n'
            'see pyamihtmlx/UNFCCC.md'
            '\nExamples:\n'
            'help'
            ''
            'parse foo.pdf and create default HTML'
            f'  pyamihtmlx UNFCCC --input foo.pdf\n'
            f''

        )
        self.parser.formatter_class = argparse.RawDescriptionHelpFormatter

        super().add_argumants()

        self.parser.add_argument(f"--{self.SESSION_DIR}", nargs="+",
                                 help=self.SESSION_HELP)



        return self.parser

    # class ProjectArgs:
    def process_args(self):
        """runs parsed args
        :return:

        """
        MAXPDF = 3
        if self.arg_dict:
            logger.info(f"argdict: {self.arg_dict}")
            # paths = self.get_paths()
            operation = self.get_operation()
            outdir = self.get_outdir()
            indir = self.get_indir()
            session_dir = self.get_session_dir()
            top_out_dir = self.get_outdir()
            otherargs = self.get_kwargs(save_global=True)  # not saved??

            if operation == UNFCCCArgs.PIPELINE:
                UNFCCC.run_pipeline_on_unfccc_session(
                    indir,
                    session_dir,
                    top_out_dir=top_out_dir
                )
            else:
                logger.warning(f"Unknown operation {operation}")

    def get_kwargs(self, save_global=False):
        kwargs = self.arg_dict.get(UNFCCCArgs.KWARGS)
        if not kwargs:
            print(f"no keywords given\nThey would be added to kwargs_dict\n or to global args")
            # system_args = get_system_args()
            return

        kwargs_dict = self.parse_kwargs_to_string(kwargs)
        print(f"saving kywords to kwargs_dict {kwargs_dict} ; not fully working")
        logger.info(f"kwargs {kwargs_dict}")
        if save_global:
            save_args_to_global(kwargs_dict, overwrite=True)
        return kwargs_dict

    @classmethod
    def create_default_arg_dict(cls):
        """returns a new COPY of the default dictionary"""
        arg_dict = dict()
        # arg_dict[UNFCCCArgs.INFORMAT] = ['PDF']
        return arg_dict

    def get_session_dir(self):
        return self.arg_dict.get(UNFCCCArgs.SESSION_DIR)


class UNFCCC:

    @classmethod
    def create_initial_directories(cls, in_sub_dir, in_file, top_out_dir, out_stem=None, out_suffix="html"):
        """creates initial directory structure from PDF files
        in:
        test/resources/unfccc/unfcccdocuments1/CMA_3/1_4_CMA_3.pdf
        ............................top_in_dir| (implicit filename.parent.parent)
        ....................................._in_file............|
        ..................................in_sub_dir|
                                                    |.........| = in_subdir_stem
        out:
        temp/unfccc/unfcccdocuments1/CMA_3/1_4_CMA_3/raw.html
        .................top_outdir|
        ........................out_subdir|
        ...............................out_subsubdir|
                                                    |...|= out_stem
                                                         |....| = out_suffix

        Create outsubdir with same stem as in in_subdir
        create out_subsubdir from in_file stem
        create any directories with mkdir()
        :param in_sub_dir: subdirectory of corpus (session)
        :param in_file: file has implict subsub in stem
        :param top_out_dir: top of output directory (analogous to top_in_dir)
        :param out_stem: no default
        :param out_suffix: defaults to "html"
        :return: out_subsubdir, outfile (None if out_stem not given)

        thus
        """
        in_subdir_stem = Path(in_sub_dir).stem
        out_subdir_stem = in_subdir_stem
        out_subdir = Path(top_out_dir, out_subdir_stem)
        out_subdir.mkdir(parents=True, exist_ok=True)
        out_subsubdir = Path(out_subdir, in_file.stem)
        out_subsubdir.mkdir(parents=True, exist_ok=True)
        outfile = Path(out_subsubdir, out_stem + "." + out_suffix) if out_stem else None
        return out_subsubdir, outfile

    @classmethod
    def extract_decision_files(cls, in_dir, stem="marked"):
        """extracts all files with "Decision" in file name
        :param in_dir: top directory of corpus (immediate children are session directories e.g. CMP_3
        :param stem: file stem, e.g. 'split', 'marked'"""
        files = glob.glob(str(in_dir) + f"/*/Decision*/{stem}.html")
        return files

    @classmethod
    def extract_hyperlinks_to_decisions(self, marked_file):
        """Currently hyperlinks are
        file:///Users/pm286/workspace/pyamihtml_top/temp/unfccc/unfcccdocuments1//CP_21/Decision_1_CP_21/marked.html
        <a href="../../../../../temp/unfccc/unfcccdocuments1//CMA_3/Decision_1_CMA_3/marked.html">1/CMA.3</a>
        """

        html_elem = lxml.etree.parse(str(marked_file))
        a_elems = html_elem.xpath(".//a[@href[contains(.,'ecision')]]")
        return a_elems

    @classmethod
    def create_decision_table(cls, in_dir, outcsv, outcsv_wt=None):
        """create table of links, rather ad hoc"""
        decision_files = UNFCCC.extract_decision_files(in_dir)
        weight_dict = Counter()
        typex = "type"
        for decision_file in decision_files:
            decision_path = Path(decision_file)
            a_els = UNFCCC.extract_hyperlinks_to_decisions(decision_file)
            source_id = str(decision_path.parent.stem).replace("ecision", "")
            for a_elem in a_els:
                text = a_elem.text
                splits = text.split(",")
                # this should use idgen
                target_id = splits[0].replace("d", "D").replace(" ", "_").replace("/", "_").replace(".", "_") \
                    .replace("ecision", "")
                para = splits[1] if len(splits) == 2 else ""
                edge = (source_id, target_id, para)
                weight_dict[edge] += 1
        with open(outcsv, "w") as fw:
            csvwriter = csv.writer(fw)
            csvwriter.writerow(["source", "link_type", "target", "para", "weight"])
            for (edge, wt) in weight_dict.items():
                csvwriter.writerow([edge[0], typex, edge[1], edge[2], wt])
        print(f"wrote {outcsv}")

    @classmethod
    def get_title_from_decision_file(cls, decision_html, font_class="timesnewromanpsmt_14_0_b"):
        """reads a title from UNFCCC Decision, relies on font class characterstics
        :param decision_html: HTML file with decision
        :param font_class: defaults to timesnewromanpsmt_14_0_b
        :return: title of decision based on font family, size, and weight
        """
        if decision_html is None:
            return "No title"
        title_spans = decision_html.xpath(f".//div/span[@class='{font_class}']")
        title_span = title_spans[0] if len(title_spans) > 0 else None
        title = title_span.xpath("text()")[0] if title_span is not None else None
        return title

    @classmethod
    def run_pipeline_on_unfccc_session(
            cls,
            in_dir,
            session_dir,
            in_sub_dir=None,
            top_out_dir=None,
            file_splitter=None,
            targets=None,
            directory_maker=None,
            markup_dict=None,
            inline_dict=None,
            param_dict=None,
            styles=None
    ):
        """
        directory structure is messy
        """

        session = Path(session_dir).stem
        if in_sub_dir is None:
            in_sub_dir = Path(in_dir, session)
        pdf_list = glob.glob(str(in_sub_dir) + "/*.pdf")
        print(f"pdfs in session {session} => {pdf_list}")
        if not pdf_list:
            print(f"****no PDFs in {in_sub_dir}")
        subsession_list = [Path(pdf).stem for pdf in pdf_list]
        print(f"subsession_list {subsession_list}")
        if not top_out_dir:
            print(f"must give top_out_dir")
            return
        out_sub_dir = Path(top_out_dir, session)
        skip_assert = True
        if not file_splitter:
            file_splitter = "span[@class='Decision']"  # TODO move to dictionary
        if not targets:
            targets = ["decision", "paris", "wmo", "temperature"]
        if not directory_maker:
            directory_maker = UNFCCC
        if not markup_dict:
            markup_dict = MARKUP_DICT
        if not inline_dict:
            inline_dict = INLINE_DICT
        if not param_dict:
            param_dict = Resources.UNFCCC_DICT
        if not styles:
            styles = STYLES
        for subsession in subsession_list:
            HtmlPipeline.stateless_pipeline(

                file_splitter=file_splitter, in_dir=in_dir, in_sub_dir=in_sub_dir, instem=subsession,
                out_sub_dir=out_sub_dir,
                top_out_dir=top_out_dir,
                page_json_dir=Path(top_out_dir, "json"),
                directory_maker=directory_maker,
                markup_dict=markup_dict,
                inline_dict=inline_dict,
                param_dict=param_dict,
                targets=targets,
                styles=styles,
                force_make_pdf=True)

    def add_arguments(self):
        """creates adds the arguments for pyami commandline

        """
        if self.parser is None:
            self.parser = argparse.ArgumentParser()
        self.parser.description = textwrap.dedent(
            'Manage and search UNFCCC resources and other climate stuff. \n'
            '----------------------------------------------------------\n'
            'see pyamihtmlx/UNFCCC.md (NYI)'
            '\nExamples:\n'
            'help'
            ''
            'parse foo.pdf and create default HTML'
            f'  pyamihtmlx UNFCCC --input <fccc diretctory> --sessions <session.<session>...\n'
            f''

        )
        self.parser.formatter_class = argparse.RawDescriptionHelpFormatter
        INPUT_HELP = f"input from:\n" \
                     f"   directories with sessions\n" \
                     f"   etc (NYI) \n"
        self.parser.add_argument(f"--{UNFCCCArgs.INPUT}", nargs="+",
                                 help=INPUT_HELP)

        self.parser.add_argument(f"--{UNFCCCArgs.KWARGS}", nargs="*",
                                 help="space-separated list of colon_separated keyword-value pairs, format kw1:val1 kw2:val2;\nif empty list gives help")

        OUTDIR_HELP = "output directory, required for URL input. If not given, autogenerated from file names"
        self.parser.add_argument(f"--{UNFCCCArgs.OUTDIR}", nargs=1,
                                 help=OUTDIR_HELP)
        #
        return self.parser

class IPCC:
    pass

    # styles for sections of IPCC chapters
    @classmethod
    def add_styles_to_head(cls, head):
        # generic styles acting as defaults
        HtmlLib.add_head_style(head, "div", [("border", "dotted red 0.5px"), ("margin", "5px")])
        HtmlLib.add_head_style(head, "img", [("width", f"50%"), ("margin", "5px")])

        HtmlLib.add_head_style(head, "header::before", [("content", "'HEADER'")])
        HtmlLib.add_head_style(head, "div.col-lg-10.col-12.offset-lg-0::before", [("content", "'BODY'")])
        HtmlLib.add_head_style(head, ".box-container::before",
                               [("margin", "15px"), ("background", "#dddddd"), ("border", "dashed blue 5px"),
                                ("content", "'BOX'")])
        HtmlLib.add_head_style(head, "#chapter-button-content::before", [("content", "'CHAPTER-BUTTONS'")])
        HtmlLib.add_head_style(head, "#chapter-authors::before", [("content", "'AUTHORS'")])
        HtmlLib.add_head_style(head, "#chapter-figures::before", [("content", "'FIGURES'")])
        HtmlLib.add_head_style(head, "#chapter-citation::before", [("content", "'CITATION'")])
        HtmlLib.add_head_style(head, "#references::before", [("content", "'REFERENCES'")])
        HtmlLib.add_head_style(head, "#executive-summary::before", [("content", "'EXECUTIVE-SUMMARY'")])
        HtmlLib.add_head_style(head, "#frequently-asked-questions::before", [("content", "'FAQs'")])

        HtmlLib.add_head_style(head, ".figure-cont", [("background", "#ffffdd"), ("padding", "5px")])
        HtmlLib.add_head_style(head, "p.Caption", [("background", "#eeeeff")])
        HtmlLib.add_head_style(head, "p.LR-salmon-grey-box", [("background", "#eedddd")])
        HtmlLib.add_head_style(head, "p", [("background", "#f3f3f3"), ("padding", "5px"), ("margin", "5px")])

        HtmlLib.add_head_style(head, ".h1-container", [("background", "#ffffff"), ("border", "solid red 2px"),
                                                       ("padding", "5px"), ("margin", "5px")])
        HtmlLib.add_head_style(head, ".h2-container", [("background", "#ffffff"), ("border", "solid red 1.3px"),
                                                       ("padding", "5px"), ("margin", "5px")])
        HtmlLib.add_head_style(head, ".h3-container", [("background", "#ffffff"), ("border", "solid red 0.8px"),
                                                       ("padding", "5px"), ("margin", "5px")])



    @classmethod
    def remove_unnecessary_containers(cls, html, debug=False):
        """
            <style> div.gx-3.gy-5.ps-2 {
            <style> div.gx-3.gy-5.ps-2.row {
            <style> div.col-lg-10.col-12.offset-lg-0 {
            <style> div.header__main {
            <style> div.header__content.pt-4 {
            <style> div.section-tooltip.footnote-tooltip {
            <style> #___gatsby {
            <style> #gatsby-focus-wrapper {
            <style> #gatsby-focus-wrapper>div {
            <style> div.s9-widget-wrapper.mt-3.mb-3 {
            <style> div[data-sal="slide-up"] {
            <style> div.container.chapters{
            """
        removable_xpaths = IPCC.get_removable_paths()
        removables = set()
        for xpath in removable_xpaths:
            elems = html.xpath(xpath)
            if debug:
                print(f"{xpath} => {len(elems)}")
            for elem in elems:
                removables.add(elem)
        for removable in removables:
            HtmlUtil.remove_element_in_hierarchy(removable)
        HtmlUtil.remove_empty_elements(html, "div")

    @classmethod
    def get_removable_paths(cls):
        removable_xpaths = [
            ".//div[contains(@class,'gx-3') and contains(@class,'gy-5') and contains(@class,'ps-2')]",
            # this fails
            # ".//div[contains(@class,'col-lg-10') and contains(@class,'col-12') and contains(@class,'offset-lg-0')]",
            ".//*[@id='___gatsby']",
            ".//*[@id='gatsby-focus-wrapper']/div",
            ".//*[@id='gatsby-focus-wrapper']",
            ".//*[@id='footnote-tooltip']",
            ".//div[contains(@class,'s9-widget-wrapper') and contains(@class,'mt-3') and contains(@class,'mb-3')]",
            ".//div[contains(@class,'chapter-figures')]",
            ".//header/div/div/div/div",
            ".//header/div/div/div",
            ".//header/div/div",
            ".//header/div",
            ".//section[contains(@class,'mb-5') and contains(@class, 'mt-5')]",
            ".//div[contains(@class,'container') and contains(@class, 'chapters') and contains(@class, 'chapter-')]",
            ".//*[contains(@id, 'footnote-tooltip-text')]",
            ".//div[@id='chapter-figures']/div/div/div/div",
            ".//div[@id='chapter-figures']/div/div/div",
            ".//div[@id='chapter-figures']/div/div",
            ".//div[@id='chapter-figures']/div",
            ".//div[@id='chapter-figures']//div[@class='row']",
        ]
        return removable_xpaths

    @classmethod
    def remove_gatsby_markup(cls, infile):
        """removes markukp from files downloaded from IPCC site
        """
        html = lxml.etree.parse(str(infile), HTMLParser())
        assert html is not None
        head = HtmlLib.get_head(html)
        IPCC.add_styles_to_head(head)
        IPCC.remove_unnecessary_containers(html)
        return html

    @classmethod
    def add_para_ids_and_make_id_list(cls, idfile, infile, outfile):
        
        inhtml = lxml.etree.parse(str(infile), HTMLParser())
        idset = set()
        elems = inhtml.xpath("//*[@id]")
        print(f"elems {len(elems)}")
        for elem in elems:
            id = elem.attrib.get("id")
            if id in idset:
                print(f"duplicate id {id}")
        pelems = inhtml.xpath("//p[text()]")
        print(f"pelems {len(pelems)}")
        """
            <div class="h2-container" id="3.1.2">
              <h2 class="Headings_•-H2---numbered" lang="en-GB">
                <span class="_idGenBNMarker-1">3.1.2</span>Linkages to Other Chapters in the Report <span class="arrow-up"></span>
                <span class="arrow-down"></span>
              </h2>
              <div class="h2-siblings" id="h2-2-siblings">
                <p class="Body-copy_•-Body-copy--full-justify-" lang="en-GB"><a class="section-link" data-title="Mitigation pathways
                <p...
               # id numbers may be off by 1 or more due to unnumbered divs (so 3.8 gives h1-9-siblings
            """
        pid_list = []
        for p in pelems:
            parent = p.getparent()
            if parent.tag == "div":
                pindex = parent.index(p) + 1  # 1-based
                id = parent.attrib.get("id")
                if id is None:
                    text = "".join(p.itertext())
                    if text is not None:
                        print(f"p without id parent: {text[:20]}")
                    else:
                        print(f"empty p without id-ed parent")
                else:
                    match = re.match("h\d\-\d+\-siblings", id)
                    if not match:
                        if id.startswith("chapter-") or (id.startswith("_idContainer") or id.startswith("footnote")):
                            pass
                        else:
                            print(f"cannot match {id}")
                    else:
                        grandparent = parent.getparent()
                        grandid = grandparent.get("id")
                        match = re.match(
                            "\d+(\.\d+)*|(box|cross\-chapter\-box|cross-working-group-box)\-\d+(\.\d+)*|executive\-summary|FAQ \d+(\.\d+)*|references",
                            grandid)
                        if not match:
                            print(f"grandid does not match {grandid}")
                        else:
                            pid = f"{grandid}_p{pindex}"
                            p.attrib["id"] = pid
                            pid_list.append(pid)
        idhtml = HtmlLib.create_html_with_empty_head_body()
        body = HtmlLib.get_body(idhtml)
        ul = lxml.etree.SubElement(body, "ul")
        for pid in pid_list:
            li = lxml.etree.SubElement(ul, "li")
            a = lxml.etree.SubElement(li, "a")
            a.attrib["href"] = f"./html_with_ids.html#{pid}"
            # a.attrib["href"] = f"./html_with_ids.html"
            a.text = pid
        HtmlLib.write_html_file(inhtml, outfile=outfile, debug=True)
        HtmlLib.write_html_file(idhtml, idfile)

