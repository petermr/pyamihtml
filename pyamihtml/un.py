import ast
import csv
import glob
import re

# decisión 2/CMA.3, anexo, capítulo IV.B
from collections import Counter
from pathlib import Path

import json

import lxml
import pandas as pd

ROMAN = "I|II|III|IIII|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI*"
L_ROMAN = "i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xiv|xv|xvi|xvii|xviii|xix|xx"
INT = "\\d+" # integer of any length
DIGIT = "\\d" # single digit
SP = "\\s" # single space
WS = "\\s+" # spaces
ANY = ".*"
DOT = f"\\." # dot
SL = "/" # slash
LP = "\\(" # left parenthesis
RP = "\\)" # right parenthesis
LC = "[a-z]" # single uppercase
UC = "[A-Z]" # single uppercase
#
DECISION_SESS_RE = re.compile(f"(?P<front>{ANY}\\D)(?P<dec_no>{INT})/(?P<body>{ANY}){DOT}(?P<sess_no>{INT}){DOT}?(?P<end>{ANY})")
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

CPTYPE = "CP|CMA|CMP"

TARGET_DICT = {
    "decision": {
        "example": "decision 12/CMP.23",
        "components": ["", ("decision", f"{INT}"), "/", ("type", CPTYPE), f"{DOT}", ("session", f"{INT}"), ""],
        "regex": f"decision {INT}/({CPTYPE})\.{INT}",

    }
}

# section dict
MARKUP_DICT = {
    "Decision": {
        "level": 0,
        "parent": [],
        "example": ["Decision 1/CMA.1", "Decision 1/CMA.3"],
        "regex": f"Decision (?P<Decision>{INT})/(?P<type>{CPTYPE})\.(?P<session>{INT})",
        "components": ["", ("Decision", f"{INT}"), "/", ("type", {CPTYPE}), f"{DOT}", ("session", f"{INT}"), ""],
        "names": ["roman", "title"],
        "class": "Decision",
        "background": "#ffaa00",
        "span_range": [0,1],
        "template": "Decision_{Decision}_{type}_{session}",
    },
    "Resolution": {
        "level": 0,
        "parent": [],
        "example": ["Resolution 1/CMA.1", "Resolution 1/CMA.3"],
        "regex": f"Resolution (?P<Resolution>{INT})/(?P<type>{CPTYPE})\.(?P<session>{INT})",
        "components": ["", ("Resolution", f"{INT}"), "/", ("type", {CPTYPE}), f"{DOT}", ("session", f"{INT}"), ""],
        "names": ["roman", "title"],
        "class": "Resolution",
        "background": "#ffdd00",
        "span_range": [0,1],
        "template": "Resolution{Resolution}_{type}_{session}",
    },
    "chapter": {
        "level": 1,
        "parent": ["Decision"],
        "example": ["VIII.Collaboration", "I.Science and urgency"],
        "regex": f"(?P<dummy>)(?P<roman>{ROMAN}){DOT}\s*(?P<title>{UC}.*)",
        "components": [("dummy", ""), ("roman", f"{ROMAN}"), f"{DOT}{WS}", ("title", f"{UC}{ANY}")],
        "names": ["roman", "title"],
        "background": "#ffaa00",
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
        "background": "#00ffff",
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
        "background": "#00ffaa",
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
        "regex": f"{LP}(?P<subpara>{LC})\)",
        "names": ["subpara"],
        "background": "#ffff77",
        "class": "subpara",
        "span_range": [0, 1],
        "template": "subpara_{subpara}",

},
    "subsubpara": {
        "level": 4,
        "parent": ["subpara"],
        "example": ["(i)Methods for establishing"],
        "regex": f"\((?P<subsubpara>{L_ROMAN})\)",
        "names": ["subsubpara"],
        "background": "#aaffaa",
        "class": "subsubpara",
        "span_range": [0, 1],
    },

}
SUBPARA = f"(\(?P<subpara>{LC})\)"
SUBSUBPARA = f"(\(?P<subsubpara>{L_ROMAN})\)"
PARENT_DIR = "unfccc/unfcccdocuments1" # probably temporary
TARGET_DIR = "../../../../../temp/unfccc/unfcccdocuments1/"

# markup against terms in spans
TARGET_STEM = "marked" # was "split"
INLINE_DICT = {
    "decision": {
        "example": ["decision 1/CMA.2", "noting decision 1/CMA.2, paragraph 10 and ", ],
        "regex":
            # f"decision{WS}(?P<decision>{INT})/(?P<type>{CPTYPE}){DOT}(?P<session>{INT})",
            f"decision{WS}(?P<decision>{INT})/(?P<type>{CPTYPE}){DOT}(?P<session>{INT})(,{WS}paragraph(?P<paragraph>{WS}{INT}))?",

        "href": "FOO_BAR",
        "split_span": True,
        "idgen": "NYI",
        "_parent_dir": f"{TARGET_DIR}",
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
    "exhort" : {
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
        "regex" : "Trust Fund for Supplementary Activities",
        "href_template": "https://unfccc.int/documents/472648",
    },
    "adaptation_fund": {
        "regex": "([Tt]he )?Adaptation Fund",
        "href_template": "https://unfccc.int/Adaptation-Fund",
    },
    "paris" : {
        "regex": "([Tt]he )?Paris Agreement",
        "href_template": "https://unfccc.int/process-and-meetings/the-paris-agreement",
    },
    "cop": {
        "regex": "([Tt]he )?Conference of the Parties",
        "href_template": "https://unfccc.int/process/bodies/supreme-bodies/conference-of-the-parties-cop",
    },
    "wmo": {
        "regex": "World Meteorological Organization",
        "href": "TDB",
    }
}

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

class UNFCCC:
    """syntax/structure specific to UNFCCC"""

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
        html_elem = lxml.etree.parse(str(marked_file))
        a_elems = html_elem.xpath(".//a[@href][contains(.,'ecision')]")
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
            source_id = str(decision_path.parent.stem)
            for a_elem in a_els:
                text = a_elem.text
                splits = text.split(",")
                # thss should use idgen
                target_id = splits[0].replace("d", "D").replace(" ", "_").replace("/", "_").replace(".", "_")
                para = splits[1] if len(splits) == 2 else ""
                edge = (source_id, target_id, para)
                weight_dict[edge] += 1
        print(f"edge dict {len(weight_dict)} {weight_dict}")
        with open(outcsv, "w") as fw:
            csvwriter = csv.writer(fw)
            csvwriter.writerow(["source", "link_type", "target", "para", "weight"])
            for (edge, wt) in weight_dict.items():
                csvwriter.writerow([edge[0], typex, edge[1], edge[2], wt])
        print(f"wrote {outcsv}")
        # df.to_csv(outcsv, encoding='utf-8', index=False)
        # df2 = pd.DataFrame(np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
        #                    columns=['a', 'b', 'c'])
        # if outcsv_wt:
        #     links_dict = dict()
        #     with open(outcsv_wt, "w") as out:



        # write table with weights



