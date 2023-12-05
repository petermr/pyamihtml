import re

# decisión 2/CMA.3, anexo, capítulo IV.B

DECISION_SESS_RE = re.compile("(?P<front>.*\\D)(?P<dec_no>\\d+)/(?P<body>.*)\.(?P<sess_no>\d+)\,?(?P<end>.*)")
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

RESERVED_WORDS1 = "(Also|[Ff]urther )?([Rr]ecalling|[Rr]ecogniz(es|ing)|Welcomes|[Cc]ognizant|[Nn]ot(ing|es)|Invit(es|ing)|Acknowledging|[Ex]pressing appreciation]|Recalls|Stresses|Urges|Requests|Expresses alarm)"
DOC_STRUCT = {
    'Annex',
    'Abbreviations and acronyms',
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
L_ROMAN = "i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xiv|xv|xvi|xvii|xviii|xix|xx"
# section dict
MARKUP_DICT = {
    "Decision": {
        "level": 0,
        "parent": [],
        "example": ["Decision 1/CMA.1", "Decision 1/CMA.3"],
        "regex": f"Decision (?P<Decision>\d+)/(?P<type>{CPTYPE})\.(?P<session>\d+)",
        "components": ["", ("Decision", "\d+"), "/", ("type", CPTYPE), "\.", ("session", "\d+"), ""],
        "names": ["roman", "title"],
        "class": "Decision",
        "background": "#ffaa00",
        "span_range": [0,1],
    },
    # "decision": {
    #     "example": "decision 12/CMP.23",
    #     "components": ["", ("decision", "\d+"), "/", ("type", CPTYPE), "\.", ("session", "\d+"), ""],
    #     "regex": f"decision (?P<decision>\d+)/(?P<type>{CPTYPE})\.(?P<session>)\d+",
    #     "background": "#ffffaa",  # light yellow
    #     "class": "decision",
    # },
    "chapter": {
        "level": 1,
        "parent": ["Decision"],
        "example": ["VIII.Collaboration", "I.Science and urgency"],
        "regex": f"(?P<dummy>)(?P<roman>{ROMAN})\.\s*(?P<title>[A-Z].*)",
        "components": [("dummy", ""), ("roman", f"{ROMAN}"), f"\\.\\s*", ("title", f"[A-Z].*")],
        "names": ["roman", "title"],
        "background": "#ffaa00",
        "class": "chapter",
        "span_range": [0, 1],
    },
    "para": {
        "level": 2,
        "parent": ["capital", "roman"],
        "example": ["26. "],
        "regex": "(?P<para>\\d+)\\.\\s*",
        "names": ["para"],
        "background": "#00ffaa",
        "class": "para",
        "parent": "preceeding::div[@class='roman'][1]",
        "idgen": {
            "parent": "Decision",
            "separator": ["_", "__"],
        },
        "span_range": [0, 1],
    },
    "subpara": {
        "level": 3,
        "parent": ["para"],
        "example": ["(a)Common time frames"],
        "regex": "\((?P<subpara>[a-z])\)",
        "names": ["subpara"],
        "background": "#ffff77",
        "class": "subpara",
        "span_range": [0, 1],
    },
    "subsubpara": {
        "level": 4,
        "parent": ["subpara"],
        "example": ["(i)Methods for establishing"],
        "regex": "\((?P<subsubpara>[ivx]+)\)",
        "names": ["subsubpara"],
        "background": "#aaffaa",
        "class": "subsubpara",
        "span_range": [0, 1],
    },
    "subchapter": {
        "level": "C",
        "parent": ["chapter"],
        "example": ["B.Annual information"],
        "regex": "(?P<capital>[A-Z])\\.",
        "names": ["subchapter"],
        "background": "#00ffff",
        "class": "subchapter",
        "span_range": [0, 1],
    },

}
SUBPARA = "(\(?P<subpara>[a-z])\)"
SUBSUBPARA = f"(\(?P<subsubpara>{L_ROMAN})\)"
INLINE_DICT = {
    "decision": {
        "example": ["decision 1/CMA.2", "noting decision 1/CMA.2, paragraph 10 and ", ],
        "regex": ["(?P<decres>[Dd])ecision\\s+(?P<decision>\\d+)/(?P<type>CMA|CP|CMP)(,\\s+paragraph(?P<paragraph>\\d+))",
                  ],
        "href": "FOO_BAR",
        "split_span": True,
        "idgen": "NYI",
    },
    "paragraph": {
        "example": [
            "paragraph 32 above",
            "paragraph 23 below",
            "paragraph 9 of decision 19/CMA.3",
            "paragraph 77(d)(iii)",
            "paragraph 37 of chapter VII of the annex",
                ],
        "regex": ["paragraph (?P<paragraph>\\d+ (above|below))",
                  f"paragraph (?P<paragraph>\\d+\([a-z]\)\({L_ROMAN}\))"
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
        "regex": "Article (?P<article>\\d+), paragraph (?P<paragraph>\\d+), (of the (?P<agreement>Paris Agreement))?",
    },
    "trust_fund": {
        "regex" : "Trust Fund for Supplementary Activities",
        "href": "https://unfccc.int/documents/472648",
    },
    "adaptation_fund": {
        "regex": "([Tt]he )?Adaptation Fund",
        "href": "https://unfccc.int/Adaptation-Fund",
    },
    "paris" : {
        "regex": "([Tt]he )?Paris Agreement",
        "href": "https://unfccc.int/process-and-meetings/the-paris-agreement",
    },
    "cop": {
        "regex": "(?P<cop>([Tt]he )?Conference of the Parties)",
        "href": "https://unfccc.int/process/bodies/supreme-bodies/conference-of-the-parties-cop",
    },
    "wmo": {
        "regex": "World Meteorological Organization",
        "href": "TDB",
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
