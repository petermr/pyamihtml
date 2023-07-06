import glob
import logging
import re
import unittest
from io import BytesIO
from pathlib import Path
from urllib import request

import lxml
import pandas as pd
import pdfplumber
import pyvis
import requests
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from pyamihtml.ami_integrate import HtmlGenerator
# from pyamihtml.ami_html import HtmlStyle
# from pyamihtml.ami_integrate import HtmlGenerator
# from pyamihtml.file_lib import FileLib
# from pyamihtml.ipcc import IPCCSections, IPCCCommand
from pyamihtml.ami_nlp import AmiNLP
from pyamihtml.file_lib import FileLib
from pyamihtml.ipcc import IPCCSections, IPCCCommand, IPCCGlossary
from pyamihtml.pyamix import PyAMI
# from pyamihtml.wikimedia import WikidataLookup
# from pyamihtml.xml_lib import HtmlLib
from pyamihtml.util import Util
from pyamihtml.wikimedia import WikidataLookup
from pyamihtml.ami_nlp import A_TEXT, T_TEXT

from test.resources import Resources
from test.test_all import AmiAnyTest

"""
tests 'complete processes ; also aimed at testing different document types
may cross directories
"""
SEMANTIC_CLIMATE = "https://rawgithubuser.com/petermr/semanticClimate"
IPBES = SEMANTIC_CLIMATE + "/" + "ipbes"

SEMANTIC_CLIMATE_DIR = Path(Resources.LOCAL_PROJECT_DIR, "semanticClimate")
MISC_DIR = Path(SEMANTIC_CLIMATE_DIR, "misc")
SC_OPEN_DOC_DIR = Path(SEMANTIC_CLIMATE_DIR, "openDocuments")
IPBES_DIR = Path(SEMANTIC_CLIMATE_DIR, "ipbes")
AR6_DIR = Path(SEMANTIC_CLIMATE_DIR, "ipcc", "ar6")

INPUT_PDFS = [
    # Path(SC_OPEN_DOC_DIR, "SR21914094338.pdf"),
    # Path(SC_OPEN_DOC_DIR, "Phd_thesis_granceri_pdfA.pdf"),
    # Path(SC_OPEN_DOC_DIR, "Malmo_onyok.pdf"),
    # Path(SC_OPEN_DOC_DIR, "Guo_Ying.pdf"),
    # Path(SC_OPEN_DOC_DIR, "skarin.pdf"),
    # Path(SC_OPEN_DOC_DIR, "hampton.pdf"),
    # Path(SC_OPEN_DOC_DIR, "sustainable_livelihoods.pdf"),
    # Path(IPBES_DIR, "ipbes_global_assessment_report_summary_for_policymakers.pdf"), # something wrong with IPBES
    # Path(IPBES_DIR, "2020 IPBES GLOBAL REPORT (CHAPTER 1)_V5_SINGLE.pdf"),
    # # Path(MISC_DIR, "2502872.pdf"),
    # Path(AR6_DIR, "misc", "AR6_FS_review_process.pdf"),
    # Path(AR6_DIR, "misc", "2018-03-Preface-3.pdf"),
    # Path(AR6_DIR, "syr", "lr", "fulltext.pdf"),
    # Path(AR6_DIR, "syr", "spm", "fulltext.pdf"),
    #
    # Path(AR6_DIR, "wg1", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "wg1", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "wg1", "faqs", "faqs.pdf"),
    # Path(AR6_DIR, "wg1", "chapters/*.pdf" ),
    # Path(AR6_DIR, "wg1", "annexes/*.pdf"), # repeat
    # Path(AR6_DIR, "wg1", "annexes", "glossary.pdf")

    # Path(AR6_DIR, "wg2", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "wg2", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "wg2", "chapters/*.pdf"),
    # Path(AR6_DIR, "wg2", "faqs/*.pdf"),

    # Path(AR6_DIR, "wg3", "annexes/*.pdf"),
    # Path(AR6_DIR, "wg3", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "wg3", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "wg3", "Chapter07.pdf"),

    # Path(AR6_DIR, "srocc", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "srocc", "ts", "fulltext.pdf"),
    # Path(AR6_DIR, "srocc", "chapters", "Ch02.pdf"),
    # Path(AR6_DIR, "srocc", "annexes/*.pdf"),
    #
    # Path(AR6_DIR, "sr15", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "sr15", "glossary", "fulltext.pdf"),
    #
    Path(AR6_DIR, "srccl", "chapters", "Chapter05.pdf"),
    # Path(AR6_DIR, "srccl", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "srccl", "ts", "fulltext.pdf"),
]

REPORTS = [
    "wg1",
    "wg2",
    "wg3",
    "syr",
    "sr15",
    "srocc",
    "srccl",
]

logger = logging.getLogger(__file__)


class AmiIntegrateTest(AmiAnyTest):

    def test_chapter_toolchain_chapters_HACKATHON(self):
        front_back = "Table of Contents|Frequently Asked Questions|Executive Summary|References"
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back=front_back)

        input_pdfs = FileLib.expand_glob_list(INPUT_PDFS)
        for input_pdf in input_pdfs:
            HtmlGenerator.create_sections(input_pdf, section_regexes)

    @unittest.skip("not yet developed nested sections")
    def test_chapter_toolchain_chapters_DEVELOP(self):
        """nested sections"""
        front_back = IPCCSections.get_major_section_names()
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back=front_back)
        input_pdfs = [glob.glob(str(input_pdf)) for input_pdf in INPUT_PDFS]
        for input_pdf in input_pdfs:
            filename = str(input_pdf)
            print(f"===={filename}====")
            print(f" section_regex_dict_keys {section_regex_dict.keys()}")
            for name, rx in section_regex_dict.items():
                print(f"key {name} : {rx}")
                file_regex = rx.get('file_regex')
                if re.match(str(file_regex), filename):
                    print(f"MATCHED {name}: {file_regex}")
                    section_regexes_new = [
                        ('section', rx.get("section")),
                        ('sub_section', rx.get("sub_section")),
                        ('sub_sub_section', rx.get("sub_sub_section"))
                    ]
                    HtmlGenerator.create_sections(input_pdf, section_regexes_new)
                # raise e

    def test_small_pdf_with_styles_KEY(self):

        input_pdfs = [
            Path(AR6_DIR, "misc", "AR6_FS_review_process.pdf"),
            Path(AR6_DIR, "misc", "2018-03-Preface-3.pdf"),
        ]
        front_back = ""
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back)

        use_svg = True
        for input_pdf in input_pdfs:
            HtmlGenerator.create_sections(input_pdf, section_regexes, group_stem="styles")

    def test_glossaries_KEY(self):
        """
        iterates over 6 reports , glossaries and adds internal links
        """

        front_back = ""
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back)

        max_reports = 99
        use_svg = True
        for report in REPORTS[:max_reports]:
            for g_type in [
                "glossary",
                "acronyms"
            ]:
                logger.warning(f"REPORT {report}")
                input_pdf = Path(AR6_DIR, report, "annexes", f"{g_type}.pdf")
                HtmlGenerator.create_sections(input_pdf, section_regexes, group_stem="glossary")
                glossary_html = Path(AR6_DIR, report, "annexes", "html", "glossary", "glossary_groups.html")
                assert glossary_html.exists()
                glossary = IPCCGlossary.create_annotated_glossary(glossary_html, style_class="s1020",
                                                                  link_class='s100')
                glossary.create_link_table(link_class='s100')
                glossary.write_csv(Path(AR6_DIR, report, "annexes", "html", "glossary", "links.csv"))

    def test_pyvis(self):

        from pyvis.network import Network
        import pandas as pd

        got_net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")

        # set the physics layout of the network
        got_net.barnes_hut()
        got_data = pd.read_csv(str(Path(AR6_DIR, "wg1", "annexes", "html", "glossary", "links.csv")))
        print(f"got {got_data}")
        sources = got_data['anchor']
        targets = got_data['target']
        # weights = got_data['Weight']
        weights = [1.0 for s in sources]

        edge_data = zip(sources, targets, weights)

        for e in edge_data:
            src = e[0]
            dst = e[1]
            w = e[2]

            got_net.add_node(src, src, title=src)
            got_net.add_node(dst, dst, title=dst)
            got_net.add_edge(src, dst, value=w)

        neighbor_map = got_net.get_adj_list()

        # add neighbor data to node hover data
        for node in got_net.nodes:
            node["title"] += " Neighbors:<br>" + "<br>".join(neighbor_map[node["id"]])
            node["value"] = len(neighbor_map[node["id"]])

        got_net.show("glossary_network.html")

    def test_pyvis2(self):

        for report in REPORTS:
            inpath = Path(AR6_DIR, report, "annexes", "html", "glossary", "links.csv")
            outpath = Path(AR6_DIR, report, "annexes", "html", "glossary", "graph.html")
            print(f"read {inpath} to {outpath}")
            Util.create_pyviz_graph(inpath, outpath=outpath)
            print(f"finished {outpath.exists()}")

    def test_merge_glossaries_KEY(self):
        """iterates over 6 glossaries and adds internal links"""

        name_set = set()
        for report in REPORTS:
            glossary_file = Path(AR6_DIR, report, "annexes", "html", "glossary", "annotated_glossary.html")
            if not glossary_file.exists():
                print(f"files does not exist {glossary_file}")
                continue
            glossary_elem = lxml.etree.parse(str(glossary_file))
            head_divs = glossary_elem.xpath("//div[span]")
            for head_div in head_divs:
                name = head_div.xpath("span")[0].text
                if not name:
                    continue
                name = name.strip()
                if name[:2] != "AI" and name[:2] != "AV" and name[:1] != "(" and name[:5] != "[Note":
                    name_set.add(name)
            print(f"entries {len(head_divs)}")
        print(f"names {len(name_set)}")
        sorted_names = sorted(name_set)
        for name in sorted_names:
            print(f"> {name}")

    def test_lookup_wikidata(self):
        max_entries = 50
        report = "wg1"
        annotated_glossary = lxml.etree.parse(
            str(Path(AR6_DIR, report, "annexes", "html", "glossary", "annotated_glossary.html")))
        lead_divs = annotated_glossary.xpath(".//div[a]")
        for div in lead_divs[:max_entries]:
            term = div.xpath("./a")[0].attrib["name"]
            term = div.xpath("span")[0].text
            qitem0, desc, wikidata_hits = WikidataLookup().lookup_wikidata(term)
            print(f"{term}: qitem {qitem0} desc {desc}")

    def test_extract_authors(self):
        """
        extract authors from chapters using regex
        """
        html_dir = Path(AR6_DIR, "srccl", "chapters", "html", "Chapter05")
        filename = "groups_groups.html"
        author_roles = IPCCCommand.get_author_roles()
        df = IPCCCommand.extract_authors_and_roles(filename, author_roles, html_dir)
        print(f"df {df}")

    def test_github_hyperlinks(self):
        """tests that Github links can retrieve and display content"""
        SC_REPO = "https://github.com/petermr/semanticClimate"
        GITHUB_DISPLAY = "https://htmlpreview.github.io/?"
        BLOB_MAIN = "blob/main"
        test_url = f"{SC_REPO}/{BLOB_MAIN}/test.html"

        print(f"test: {test_url}")

        with request.urlopen(test_url) as f:
            s = f.read().decode()  # the decode turns the bytes into a string for printing
            # this is NOT the raw content, but wrapped to display as raw htnl
        assert " <title>semanticClimate/test.html at main · petermr/semanticClimate · GitHub</title>" in s

        # this is the HTML for web display
        display_url = f"{GITHUB_DISPLAY}{SC_REPO}/{BLOB_MAIN}/test.html"
        print(f"display url: {display_url}")
        try:
            page = requests.get(display_url)
            content = page.content
            print(content)
            html = lxml.html.fromstring(content)
        except OSError as e:
            print(f"error {e}")
        body = html.xpath("/html/body")[0]
        print(f"body {lxml.etree.tostring(body)}")
        assert body is not None

    def test_commandline(self):
        """converts a 36-page PDF to structured HTML
        """
        input_pdf = str(Path(AR6_DIR, "syr", "spm", "fulltext.pdf"))
        args = ["IPCC", "--input", input_pdf]
        pyami = PyAMI()
        pyami.run_command(args)

    def test_read_urls_through_bytes_io(self):
        url = "https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_SPM.pdf"
        response = requests.get(url)
        bytes_io = BytesIO(response.content)
        with pdfplumber.open(bytes_io) as f:
            pages = f.pages
            assert len(pages) == 40

    def test_read_urls_with_raw_pdfplumber_fails(self):
        input_pdf = "https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_SPM.pdf"
        try:
            with pdfplumber.open(input_pdf) as f:
                pages = f.pages
                assert len(pages) == 40
                assert False, f"should throw FileNotFoundError {input_pdf}"
        except FileNotFoundError as e:
            assert f"file not found {e}"

    def test_commandline_read_urls(self):
        """reads URL for PDF on commandline
        """
        input_pdf = "https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_SPM.pdf"
        outdir = str(Path(AR6_DIR, "temp", "spm"))
        pyami = PyAMI()
        args = ["IPCC", "--input", input_pdf, "--outdir", outdir]
        pyami.run_command(args)
        html_file = Path(AR6_DIR, "syr", "spm", "html", "fulltext", "total_pages.html")
        assert html_file.exists()

    def test_command_line_read_url_no_output(self):
        input_pdf = "https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_SPM.pdf"
        pyami = PyAMI()
        args = ["IPCC", "--input", input_pdf]
        pyami.run_command(args)

    def test_tfidf_on_interentry_text_glossaries(self):
        """
        finds textual differences between descripns in glossary entries

        """
        omit_dict = {
            A_TEXT: 'See |see ',
            T_TEXT: 'See |see ',
        }

        for report in REPORTS:
            csv_path = Path(AR6_DIR, report, "annexes", "html", "glossary", "links.csv")
            if not(csv_path.exists()):
                logger.error(f"file does not exist {csv_path}")
                continue
            ami_nlp = AmiNLP()
            ami_nlp.find_text_similarities(csv_path, maxt=1000, min_sim=0.25, omit_dict=omit_dict)

    def test_distance_matrix(self):
        """
        """

        omit_dict = {
            A_TEXT: 'See |see ',
            T_TEXT: 'See |see ',
        }
        duplicates = [A_TEXT]
        n_clusters = 25
        random_state = 42
        for report in REPORTS:
            csv_path = Path(AR6_DIR, report, "annexes", "html", "glossary", "links.csv")
            print(f"\n==========================={report}========================")

            if not(csv_path.exists()):
                logger.error(f"file does not exist {csv_path}")
                continue
            ami_nlp = AmiNLP()
            ami_nlp.read_csv_remove_duplicates_and_unwanted_values(csv_path, omit_dict, duplicates=duplicates)
            texts = ami_nlp.data[A_TEXT]
            print(f"texts: ++++++ {len(texts)} ++++++ {texts}")
            ami_nlp.calculate_distance_matrices(texts, omit_dict=omit_dict, n_clusters=n_clusters, random_state=random_state)


