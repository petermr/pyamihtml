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
        "example": ["Decision 1/CMA.1", "Decision 1/CMA.3"],
        "regex": f"Decision (?P<Decision>\d+)/(?P<type>{CPTYPE})\.(?P<session>\d+)",
        "components": ["", ("Decision", "\d+"), "/", ("type", CPTYPE), "\.", ("session", "\d+"), ""],
        "names": ["roman", "title"],
        "class": "Decision",
        "background": "#ffaa00",
    },
    "decision": {
        "example": "decision 12/CMP.23",
        "components": ["", ("decision", "\d+"), "/", ("type", CPTYPE), "\.", ("session", "\d+"), ""],
        "regex": f"decision (?P<decision>\d+)/(?P<type>{CPTYPE})\.(?P<session>)\d+",
        "background": "#ffffaa",  # light yellow
        "class": "decision",
    },
    "major": {
        "level": "1",
        "parent": ["decision"],
        "example": ["VIII.Collaboration", "I.Science and urgency"],
        "regex": f"(?P<dummy>)(?P<roman>{ROMAN})\.\s*(?P<title>[A-Z].*)",
        "components": [("dummy", ""), ("roman", f"{ROMAN}"), f"\\.\\s*", ("title", f"[A-Z].*")],
        "names": ["roman", "title"],
        "background": "#ffaa00",
        "class": "roman",
    },
    "para": {
        "level": "2",
        "parent": ["major"],
        "example": ["26. "],
        "regex": "(?P<para>\d+)\.\s*",
        "names": ["para"],
        "background": "#00ffaa",
        "class": "para",
        "idgen": {
            "parent": "Decision",
            "separator": ["_", "__"],
        },
    },
    "subpara": {
        "level": "3",
        "parent": ["para"],
        "example": ["(a)Common time frames"],
        "regex": "\((?P<subpara>[a-z])\)",
        "names": ["subpara"],
        "background": "#ffff77",
        "class": "subpara",
    },
    "subsubpara": {
        "level": "4",
        "parent": ["subpara"],
        "example": ["(i)Methods for establishing"],
        "regex": "\((?P<subsubpara>[ivx]+)\)",
        "names": ["subsubpara"],
        "background": "#aaffaa",
        "class": "subsubpara",
    },
    "capital": {
        "level": "C",
        "parent": [],
        "example": ["B.Annual information"],
        "regex": "(?P<capital>[A-Z])\.",
        "names": ["capital"],
        "background": "#00ffff",
        "class": "capital",
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
