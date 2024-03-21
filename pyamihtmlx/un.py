import argparse
import ast
import csv
import glob
import logging
import re

# decisión 2/CMA.3, anexo, capítulo IV.B
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import json

import lxml
from lxml.etree import _Element, _ElementUnicodeResult

from lxml.html import HTMLParser, Element, HtmlComment, HtmlElement
import lxml.etree as ET

from pyamihtmlx.ami_html import HtmlUtil
from pyamihtmlx.file_lib import FileLib, AmiDriver
from pyamihtmlx.html_marker import HtmlPipeline
from pyamihtmlx.util import AbstractArgs
from pyamihtmlx.xml_lib import HtmlLib, XmlLib

LR = "longer-report"
SPM = "summary-for-policymakers"
TS = "technical-summary"
ANN_IDX = "annexes-and-index"

GATSBY = "gatsby"
GATSBY_RAW = "gatsby_raw"
DE_GATSBY = "de_gatsby"
HTML_WITH_IDS = "html_with_ids"
HTML_WITH_IDS_HTML = "html_with_ids.html"
ID_LIST = "id_list"
MANUAL = "manual"
PARA_LIST = "para_list"

WORDPRESS = "wordpress"
DE_WORDPRESS = "de_wordpress"

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

UNFCCC_DICT = {
    # "1" : {
    #
    # },
    # "*" : {
    "name": "UNFCCC reports",
    "footer_height": 50,  # from lowest href underlines
    "header_height": 70,  # from 68.44
    "header_bottom_line_xrange": [20, 700],
    "footnote_top_line_xrange": [50, 300],
    "box_as_line_height": 1
}

TITLE = "UNFCCC Publication Experiment"
AUTHOR = "UNFCCC"
FRONT_SUBTITLE = "#semanticClimate Research Demo"
GITHUB_SOURCE = "https://github.com/semanticClimate/unfccc/"

IPCC_URL = "https://www.ipcc.ch/"
AR6_URL = IPCC_URL + "report/ar6/"
SYR_URL = AR6_URL + "syr/"
WG1_URL = AR6_URL + "wg1/"
WG2_URL = AR6_URL + "wg2/"
WG3_URL = AR6_URL + "wg3/"

logger = logging.getLogger(__file__)


def save_args_to_global(kwargs_dict, overwrite=True):
    raise NotImplemented("save_args_to_global")


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

    def get_kwargs(self, save_global=False, debug=False):
        kwargs = self.arg_dict.get(UNFCCCArgs.KWARGS)
        if not kwargs:
            if debug:
                print(f"no keywords given\nThey would be added to kwargs_dict\n or to global args")
            return

        kwargs_dict = self.parse_kwargs_to_string(kwargs)
        # print(f"saving kywords to kwargs_dict {kwargs_dict} ; not fully working")
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

    def create_default_arg_dict(cls):
        """returns a new COPY of the default dictionary"""
        arg_dict = dict()
        # arg_dict[UNFCCCArgs.INFORMAT] = ['PDF']
        return arg_dict


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
    def extract_decision_files_posix(cls, in_dir, stem="marked"):
        """extracts all files with "Decision" in file name
        :param in_dir: top directory of corpus (immediate children are session directories e.g. CMP_3
        :param stem: file stem, e.g. 'split', 'marked'"""
        files = FileLib.posix_glob(str(in_dir) + f"/*/Decision*/{stem}.html")
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
        decision_files = UNFCCC.extract_decision_files_posix(in_dir)
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
        pdf_list = FileLib.posix_glob(str(in_sub_dir) + "/*.pdf")
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
            param_dict = UNFCCC_DICT
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

CURLY_RE = ".*\\{(?P<links>.+)\\}.*" # any matched non-empty curlies {...}

class IPCC:

    # styles for sections of IPCC chapters
    @classmethod
    def add_styles_to_head(cls, head):
        # generic styles acting as defaults

        HtmlLib.add_head_style(head, "div.col-lg-10.col-12.offset-lg-0::before", [("content", "'COL-LG'")])
        HtmlLib.add_head_style(head, ".box-container::before",
                               [("margin", "15px"), ("background", "#dddddd"), ("border", "dashed blue 5px"),
                                ("content", "'BOX'")])
        # IDs
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

        HtmlLib.add_head_style(head, "header", [("background", "#ffffff"), ("border", "solid black 0.5px")])
        HtmlLib.add_head_style(head, "header::before", [("background", "#ddffdd"), ("content", "'HEADER'")])
        HtmlLib.add_head_style(head, "main", [("background", "#ffffff"), ("border", "solid black 0.5px")])
        HtmlLib.add_head_style(head, "main::before", [("background", "#ddffdd"), ("content", "'MAIN'")])
        HtmlLib.add_head_style(head, "footer", [("background", "#ffffff"), ("border", "solid black 0.5px")])
        HtmlLib.add_head_style(head, "footer::before", [("background", "#ddffdd"), ("content", "'FOOTER'")])
        HtmlLib.add_head_style(head, "section", [("background", "#ffffff"), ("border", "solid black 0.5px")])
        HtmlLib.add_head_style(head, "section::before", [("background", "#ddffdd"), ("content", "'SECTION'")])
        HtmlLib.add_head_style(head, "article", [("background", "#ffffff"), ("border", "solid black 0.5px")])
        HtmlLib.add_head_style(head, "article::before", [("background", "#ddffdd"), ("content", "'ARTICLE'")])


        HtmlLib.add_head_style(head, "h1::before", [("background", "#ddffdd"), ("border", "solid brown 0.5px"), ("content", "'H1>'")])
        HtmlLib.add_head_style(head, "h2::before", [("background", "#ddffdd"), ("border", "solid brown 0.5px"), ("content", "'H2>'")])
        HtmlLib.add_head_style(head, "h3::before", [("background", "#ddffdd"), ("border", "solid brown 0.5px"), ("content", "'H3>'")])
        HtmlLib.add_head_style(head, "h4::before", [("background", "#ddffdd"), ("border", "solid brown 0.5px"), ("content", "'H4>'")])
        HtmlLib.add_head_style(head, "h5::before", [("background", "#ddffdd"), ("border", "solid brown 0.5px"), ("content", "'H5>'")])
        HtmlLib.add_head_style(head, "h6::before", [("background", "#ddffdd"), ("border", "solid brown 0.5px"), ("content", "'H6>'")])
        HtmlLib.add_head_style(head, "h1", [("background", "#dd77dd"), ("border", "dashed brown 0.5px")])
        HtmlLib.add_head_style(head, "h2", [("background", "#dd77dd"), ("border", "dashed brown 0.5px")])
        HtmlLib.add_head_style(head, "h3", [("background", "#dd77dd"), ("border", "dashed brown 0.5px")])
        HtmlLib.add_head_style(head, "h4", [("background", "#dd77dd"), ("border", "dashed brown 0.5px")])
        HtmlLib.add_head_style(head, "h5", [("background", "#dd77dd"), ("border", "dashed brown 0.5px")])
        HtmlLib.add_head_style(head, "h6", [("background", "#dd77dd"), ("border", "dashed brown 0.5px")])

        HtmlLib.add_head_style(head, "i,em", [("background", "#ffddff"), ("border", "dashed brown 0.5px")])
        HtmlLib.add_head_style(head, "b,strong", [("background", "#ffaaff"), ("border", "dashed brown 0.5px")])

        HtmlLib.add_head_style(head, "a[href]::before", [("background", "#ddffdd"), ("content", "'AHREF'")])
        HtmlLib.add_head_style(head, "a[href]", [("background", "#ddffdd"), ("border", "dashed orange 0.5px")])

        HtmlLib.add_head_style(head, "sup::before", [("background", "#ddffdd"), ("content", "'SUP'")])
        HtmlLib.add_head_style(head, "sup", [("background", "#ddffdd"), ("border", "dashed orange 0.5px")])
        HtmlLib.add_head_style(head, "sub::before", [("background", "#ddffdd"), ("content", "'SUB'")])
        HtmlLib.add_head_style(head, "sub", [("background", "#ddffdd"), ("border", "dashed orange 0.5px")])

        HtmlLib.add_head_style(head, "ul::before,ol::before", [("background", "gray"), ("border", "solid blue 1px"), ("content", "'LIST>'")])
        HtmlLib.add_head_style(head, "ul,ol", [("border", "solid blue 1px")])
        HtmlLib.add_head_style(head, "li::before", [("background", "yellow"), ("border", "solid cyan 2px"), ("content", "'LI>'")])
        HtmlLib.add_head_style(head, "li", [("border", "solid blue 1px")])

        HtmlLib.add_head_style(head, "table:before", [("background", "yellow"), ("border", "solid brown 2px"), ("content", "'TABLE>'")])
        HtmlLib.add_head_style(head, "table", [("background", "#ddffff"), ("border", "solid black 1px")])

        HtmlLib.add_head_style(head, "figure:before", [("background", "cyan"), ("border", "solid brown 0.5px"), ("content", "'FIG>'")])
        HtmlLib.add_head_style(head, "figure", [("background", "#ffddff"), ("border", "solid black 1px")])
        HtmlLib.add_head_style(head, "figcaption:before", [("background", "cyan"), ("border", "solid brown 0.5px"), ("content", "'FIGCAP>'")])
        HtmlLib.add_head_style(head, "figcaption", [("background", "#ddffff"), ("border", "solid black 0.5px")])


        HtmlLib.add_head_style(head, "div", [("background", "#ddffff"), ("border", "dashed orange 2px")])
        HtmlLib.add_head_style(head, "div", [("border", "dotted red 0.5px"), ("margin", "5px")])
        HtmlLib.add_head_style(head, "div::before", [("background", "#ddffdd"), ("content", "'DIV'")])

        HtmlLib.add_head_style(head, "img", [("width", f"50%"), ("margin", "5px")])
        HtmlLib.add_head_style(head, "img::before", [("background", "#ddffdd"), ("content", "'IMG'")])

        HtmlLib.add_head_style(head, "dl", [("width", f"50%"), ("margin", "5px")])
        HtmlLib.add_head_style(head, "dl::before", [("background", "#ddffdd"), ("content", "'DL'")])
        HtmlLib.add_head_style(head, "dt", [("width", f"50%"), ("margin", "5px")])
        HtmlLib.add_head_style(head, "dt::before", [("background", "#ddffdd"), ("content", "'DT'")])
        HtmlLib.add_head_style(head, "dd", [("width", f"50%"), ("margin", "5px")])
        HtmlLib.add_head_style(head, "dd::before", [("background", "#ddffdd"), ("content", "'DD'")])


        HtmlLib.add_head_style(head, "p", [("background", "#ffffdd"), ("border", "dashed orange 0.5px")])
        HtmlLib.add_head_style(head, "*", [("background", "pink"), ("border", "solid black 5px")])
        HtmlLib.add_head_style(head, "span", [("background", "#ffdddd"), ("border", "dotted black 0.5px")])

    @classmethod
    def remove_unnecessary_containers(cls, html, removable_xpaths=None, debug=False):
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
        if removable_xpaths is None:
            return None
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
    def add_hit_with_filename_and_para_id(cls, all_dict, hit_dict, infile, para_phrase_dict):
        """adds non-empty hits in hit_dict and all to all_dict
        :param all_dict
        """
        item_paras = [item for item in para_phrase_dict.items() if len(item[1]) > 0]
        if len(item_paras) > 0:
            all_dict[infile] = para_phrase_dict
            for para_id, hits in para_phrase_dict.items():
                for hit in hits:
                    # TODO should write file with slashes (on Windows we get %5C)
                    infile_s = f"{infile}"
                    infile_s = infile_s.replace("\\", "/")
                    infile_s = infile_s.replace("%5C", "/")
                    url = f"{infile_s}#{para_id}"
                    hit_dict[hit].append(url)

    @classmethod
    def create_hit_html(cls, infiles, phrases=None, outfile=None, xpath=None, debug=False):
        all_paras = []
        all_dict = dict()
        hit_dict = defaultdict(list)
        if type(phrases) is not list:
            phrases = [phrases]
        for infile in infiles:
            assert Path(infile).exists(), f"{infile} does not exist"
            html_tree = lxml.etree.parse(str(infile), HTMLParser())
            paras = HtmlLib.find_paras_with_ids(html_tree, xpath=xpath)
            all_paras.extend(paras)

            # this does the search
            para_phrase_dict = HtmlLib.create_para_ohrase_dict(paras, phrases)
            if len(para_phrase_dict) > 0:
                if debug:
                    print(f"para_phrase_dict {para_phrase_dict}")
                IPCC.add_hit_with_filename_and_para_id(all_dict, hit_dict, infile, para_phrase_dict)
        if debug:
            print(f"para count~: {len(all_paras)}")
        outfile = Path(outfile)
        outfile.parent.mkdir(exist_ok=True, parents=True)
        html1 = cls.create_html_from_hit_dict(hit_dict)
        if outfile:
            with open(outfile, "w") as f:
                if debug:
                    print(f" hitdict {hit_dict}")
                HtmlLib.write_html_file(html1, outfile, debug=True)
        return html1

    @classmethod
    def create_html_from_hit_dict(cls, hit_dict):
        html = HtmlLib.create_html_with_empty_head_body()
        body = HtmlLib.get_body(html)
        ul = ET.SubElement(body, "ul")
        for term, hits in hit_dict.items():
            li = ET.SubElement(ul, "li")
            p = ET.SubElement(li, "p")
            p.text = term
            ul1 = ET.SubElement(li, "ul")
            for hit in hits:
                # TODO manage hits with Paths
                # on windows some hits have "%5C' instead of "/"
                hit = str(hit).replace("%5C", "/")
                li1 = ET.SubElement(ul1, "li")
                a = ET.SubElement(li1, "a")
                a.text = hit.replace("/html_with_ids.html", "")
                ss = "ipcc/"
                try:
                    idx = a.text.index(ss)
                except Exception as e:
                    print(f"cannot find substring {ss} in {a}")
                    continue
                a.text = a.text[idx + len(ss):]
                a.attrib["href"] = hit
        return html

    @classmethod
    def find_analyse_curly_refs(cls, para_with_ids):
        for para in para_with_ids:
            text = ''.join(para.itertext()).strip()
            match = re.match(CURLY_RE, text)
            if match:
                IPCC._parse_curly(match, para)


    @classmethod
    def _parse_curly(cls, match, para):
        # strip any enclosing curly brackets and whitespace
        curly_content = match.groupdict()["links"].strip()
        print(f"====={curly_content}=====")
        nodes = para.xpath(".//node()")
        matches = 0
        matched_node = None
        for node in nodes:

            # print(f"TYPE {type(node)}")
            if type(node) is _ElementUnicodeResult:
                txt = str(node)
                matched_node = node
            elif type(node) is HtmlComment:
                continue
            else:
                txt = ''.join(node.itertext())
                matched_node = node
                # continue
            # print(f"TXT>> {txt}")
            if curly_content in txt:
                # print(f"MATCHED {tag} => {txt}")
                matches += 1
            else:
                # print(f"NO MATCH {txt}")
                pass
        if matches:
            node_parent = matched_node.getparent()
            # replace curly text with span to receive matched and unmatched links
            br = ET.SubElement(node_parent, "br")
            link_span = ET.SubElement(node_parent, "span")
            # this is a mess. The curlies are sometimes separate spans, sometimes not
            # just add the hyperlinks. Messy but best we can do
            # this is logically correct biut not supported by lxml
            # idx = node_parent.index(matched_node)
            # node_parent.insert(idx, link_span)
            # node_parent.remove(matched_node)

            link_texts = re.split("[;,]\\s+", curly_content)
            # print(f"links: {link_texts}")
            for link_text in link_texts:
                # print(f"link: {link_text}")
                cls._parse_link_add_anchor(link_text, link_span)

    @classmethod
    def _parse_link_add_anchor(cls, link_text, link_span):
        a = ET.SubElement(link_span, "a")
        spanlet = ET.SubElement(link_span, "span")
        spanlet.text = ", "
        links_re = "(?P<report>WGI|WG1|WGII|WGIII||SYR|SRCCL|SROCC|SR1\\.?5)\\s+(?P<chapter>SPM|TS|Box|CCB|Cross-(Section|Chapter)\\s+Box|Figure|Global to Regional Atlas Annex|Table|Annex|\\d+)(\\s+|\\.)(?P<section>.*)"
        link_match = re.match(links_re, link_text)
        if link_match:
            report = link_match['report']
            chapter = link_match['chapter']
            section = link_match['section']
            href = cls._create_href(report, chapter, section)
            a.attrib["href"] = href
            a.text = link_text
        else:
            i = ET.SubElement(a, "i")
            i.text = link_text
            print(f" FAILED TO MATCH Rep_chap_sect [{link_text}]")

    @classmethod
    def _create_href(cls, report, chapter, section):
        report = cls.normalize_report(report)
        chapter = cls.normalize_chapter(chapter)
        file = f"../../{report}/{chapter}/{HTML_WITH_IDS_HTML}#{section}"
        return file
        # print(f">> {file}")

    @classmethod
    def normalize_report(cls, report):
        report = report.replace("III", "3")
        report = report.replace("II", "2")
        report = report.replace("I", "1")
        report = report.lower()
        return report

    @classmethod
    def normalize_chapter(cls, chapter):
        return chapter.lower()

    @classmethod
    def download_save_chapter(self, report, chap, wg_url, outdir=None, sleep=2):
        ami_driver = AmiDriver(sleep=sleep)
        gatsby_ignore = Path(outdir, f"{report}", f"{chap}", f"{GATSBY}-ignore.html")
        gatsby = Path(outdir, f"{report}", f"{chap}", f"{GATSBY}.html")
        gatsby_raw = Path(outdir, f"{report}", f"{chap}", f"{GATSBY_RAW}.html")
        root_elem = ami_driver.download_and_save(gatsby_raw, chap, report, wg_url)
        htmlx = HtmlLib.create_html_with_empty_head_body()
        # create a new div to receive the driver output
        div = lxml.etree.SubElement(HtmlLib.get_body(htmlx), "div")
        # remove some clutter
        XmlLib.remove_elements(root_elem, xpath="//div[contains(@class, 'col-12')]",
                               new_parent=div, debug=True)
        # write the in-driver tree
        XmlLib.write_xml(root_elem, gatsby_ignore)
        # remove coloured page
        XmlLib.remove_elements(htmlx, xpath="//div[@data-gatsby-image-wrapper]/div[@aria-hidden='true']", debug=True)
        XmlLib.write_xml(htmlx, gatsby)







