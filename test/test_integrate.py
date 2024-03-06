import csv
import glob
import logging
import os.path
import re
import unittest
from io import BytesIO
from pathlib import Path
from urllib import request

import lxml
import pdfplumber
import requests

from pyamihtmlx.ami_html import HtmlUtil
from pyamihtmlx.ami_integrate import HtmlGenerator
from pyamihtmlx.ami_nlp import AmiNLP
from pyamihtmlx.file_lib import FileLib
from pyamihtmlx.ipcc import IPCCSections, IPCCCommand, IPCCGlossary, ACRONYMS, GLOSSARY, CORE_TEAM
from pyamihtmlx.pyamix import PyAMI
from pyamihtmlx.util import Util
from pyamihtmlx.wikimedia import WikidataLookup
from pyamihtmlx.ami_nlp import A_TEXT, T_TEXT
from pyamihtmlx.ipcc import REPORTS
from pyamihtmlx.xml_lib import XmlLib

from test.resources import Resources
from test.test_all import AmiAnyTest

"""
tests 'complete processes ; also aimed at testing different document types
may cross directories
"""
SEMANTIC_CLIMATE = "https://rawgithubuser.com/petermr/semanticClimate"
IPBES = SEMANTIC_CLIMATE + "/" + "ipbes"

# SEMANTIC_CLIMATE_DIR = Path(Resources.LOCAL_PROJECT_DIR, "semanticClimate")
# MISC_DIR = Path(SEMANTIC_CLIMATE_DIR, "misc")
# SC_OPEN_DOC_DIR = Path(SEMANTIC_CLIMATE_DIR, "openDocuments")
# IPBES_DIR = Path(SEMANTIC_CLIMATE_DIR, "ipbes")
# AR6_DIR = Path(SEMANTIC_CLIMATE_DIR, "ipcc", "ar6")
AR6_DIR = Path(Resources.TEST_IPCC_DIR)

# SEMANTIC_TOP = Path("/", "Users", "pm286", "projects", "semanticClimate")

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
    Path(AR6_DIR, "sr15", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "sr15", "glossary", "fulltext.pdf"),
    #
    # Path(AR6_DIR, "srccl", "chapters", "Chapter05.pdf"),
    # Path(AR6_DIR, "srccl", "spm", "fulltext.pdf"),
    # Path(AR6_DIR, "srccl", "ts", "fulltext.pdf"),
]

logger = logging.getLogger(__file__)

OMIT_LONG = True

class AmiIntegrateTest(AmiAnyTest):

# ======================HELPERS====================

    def write_annotated_glossary_to_csv(self, max_entries, report):
        gloss_dir = Path(AR6_DIR, report, "annexes", "html", "glossary")
        annotated_glossary = lxml.etree.parse(
            str(Path(gloss_dir, f"{IPCCGlossary.ANNOTATED_GLOSSARY}.html")))
        lead_divs = annotated_glossary.xpath(".//div[a]")
        table = []
        for div in lead_divs[:max_entries]:
            self.parse_div_to_glossary_row(div, table)
        with open(str(Path(gloss_dir, "glossary.csv")), "w") as csvf:
            row_writer = csv.writer(csvf)
            for row in table:
                row_writer.writerow(row)

    def assert_file_exists(self, directory, filename, label=""):
        """asserts that a file in a diirectory exists
        :param directory:
        :param filename:
        :return: name of file"""
        file = Path(directory, filename)
        assert file.exists(), f"{label} {file} should exist"
        return file

    def assert_element_count(self, file, elem_count, xpath="//*"):
        """asserts that an HTML file contains a give number of elements
        """
        assert file and Path(file).exists(), f"file {file} must be valid"
        assert xpath, f"xpath should not be None"
        assert elem_count, f"elem_count must not be None"
        html = lxml.etree.parse(str(file))
        assert html is not None, f"must have valid HTML file"
        elems = html.xpath(xpath)
        assert len(elems) == elem_count

    def parse_div_to_glossary_row(self, div, table):
        term = div.xpath("./a")[0].attrib["name"]
        term = div.xpath("span")[0].text
        brackets = None
        if "(" in term:
            term01 = term.split("(")
            term = term01[0]
            brackets = term01[1]
        qitem0, desc, wikidata_hits = WikidataLookup().lookup_wikidata(term)
        # Q13442814 is scientific article
        print(f"{term}: qitem {qitem0} desc {desc}")
        row = [term, brackets, qitem0, desc, wikidata_hits]
        table.append(row)

    def print_hh_sections(self, web_html, hh):
        # find sections
        """
        <div class="h2-container" id="2.3">
                     <h2 class="LR-1-1-Title" lang="en-US">2.3 Current Mitigation and Adaptation  Actions and Policies are not Sufficient <span class="arrow-up"/><span class="arrow-down"/><span class="share-block"/></h2>
        """

        container_ = f"//*[@class='{hh}-container']"
        container_divs = web_html.xpath(container_)
        print(f"container_divs {len(container_divs)}")
        for c_div in container_divs:
            id = c_div.get('id')
            hhx = c_div.xpath(f"./{hh}")
            if len(hhx) != 1:
                print(f"bad {hhx} {len(hhx)}")
                continue
            hhx = hhx[0]
            hhx_text = "???" if hhx.text is None else hhx.text
            if not hhx_text.startswith(id):
                print(f"id (id) and section title {hhx_text} out of sync")
            print(f"{hh} ==> {c_div.get('id')}; {hhx_text}")




# ===============TESTS============


    @unittest.skipUnless(AmiAnyTest.run_long(), "run occasionally")
    def test_chapter_toolchain_chapters_HACKATHON_SRCCL_Chapter05_File(self):
        """Convert one or more PDFs into HTML. Tests only that it produces output """

        # this will have a child "ar6" and everything under it is standard
        user_top = Path("/", "Users", "pm286", "projects", "semanticClimate") # TODO make this user-independent
        ar6_dir = Path(user_top, "ipcc", "ar6")
        output_dir = Path(ar6_dir, "srccl", "chapters", "html")

        front_back = "Table of Contents|Frequently Asked Questions|Executive Summary|References"
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back=front_back)


        # input_pdfs = FileLib.expand_glob_list(INPUT_PDFS)
        # assert len(input_pdfs) == 1, f"number of input PDFS {len(input_pdfs)}" # this will change frequently with different tests
        # for input_pdf in input_pdfs:
        input_pdf = Path(AR6_DIR, "srccl", "chapters", "Chapter05.pdf")
        output_dir = Path(output_dir, "Chapter05")
        # clean existing directory
        # shutil.rmtree(output_dir)
        FileLib.delete_directory_contents(output_dir, delete_directory=True)
        assert not output_dir.exists(), f"should have deleted {output_dir}"
        HtmlGenerator.create_sections(input_pdf, section_regexes)

        assert output_dir.exists(), f"output dir should exist {output_dir}"
        files = sorted(os.listdir(output_dir))
        expected_file_count = [100, 152]
        assert expected_file_count[0] <= len(files) <= expected_file_count[1] , f"found {len(files)} files in {output_dir}, expected {expected_file_count}"
        assert files[0] == 'groups_groups.html', f"first file should be {files[0]}"

    def test_parse_ipcc_syr_longer_report_html_simple(self):
        """some reports now have HTML! This tries to parse one directly and fails because they use dynamic loading (I think)
        """
        input = "https://www.ipcc.ch/report/ar6/syr/longer-report/"
        try:
            html = lxml.etree.parse(input)
            raise Exception("should raise parse/read exception")
        except Exception as e:
            print ("failed to load as expected {e}")


    def test_parse_ipcc_html_download(self):
        """some reports now have HTML! This tries to parse them directly and fails because they use dynamic loading (I think)
        """
        input = "https://www.ipcc.ch/report/ar6/syr/longer-report/"
        try:
            html = lxml.etree.parse(input)
            raise Exception("should raise parse/read exception")
        except Exception as e:
            print ("failed to load as expected {e}")

    def test_read_manually_edited_syr_longer_report(self):
        """Takes manually edited html (without scripts) which is roughly the DOM after loading """
        # new style format in WG3/SPM manually downloaded and slightly edited. Possibly HTMLParser should obviate this
        html_dir = Path("/", "Users", "pm286", "projects", "semanticClimate", "ipcc", "ar6", "wg3", "spm", "web_html")

        count = 3795
        raw_html = "fulltext_edit.html"
        out_html = "fulltext_clean.html"
        longer_path = Path(html_dir, raw_html)
        longer_html = lxml.etree.parse(str(longer_path), lxml.etree.HTMLParser())
        elems = longer_html.xpath("//*")
        count = len(elems)
        assert count == count, f"longer elems = {count}"
        outfile = Path(html_dir, out_html)
        with open(outfile, 'wb') as doc:
            doc.write(lxml.etree.tostring(longer_html, pretty_print=True))

    def test_read_downloaded_ipcc_html_syr_longer_report(self):
        """processes manually downloaded HTML file from IPCC, parse, clean"""

        # web_dir =   Path(SEMANTIC_CLIMATE_DIR, "ipcc", "ar6", "syr", "lr", "web_html")
        web_dir =   Path(Resources.TEST_IPCC_DIR, "syr", "lr", "web_html")
        web_file = Path(web_dir, "longer_report.html")
        assert web_file.exists()
        web_html = lxml.etree.parse(str(web_file), lxml.etree.HTMLParser())
        head_elem = web_html.xpath("/html/head")
        assert len(head_elem) == 1
        body_elem = web_html.xpath("/html/body")
        assert len(body_elem) == 1
        # remove all scripts
        XmlLib.remove_all(web_html, "//script")
        # remove all styles, links, noscripts, button
        XmlLib.remove_all(web_html, "//style")
        XmlLib.remove_all(web_html, "//link")
        XmlLib.remove_all(web_html, "//noscript")
        XmlLib.remove_all(web_html, "//button")
        XmlLib.remove_all(web_html, "//meta")
        # XmlLib.remove_all(web_html, "//svg")
        XmlLib.remove_all(web_html, "//textarea")
        XmlLib.remove_all(web_html, "//input") # this is definitely a problem for display
        XmlLib.remove_all(web_html, "//nav")
        XmlLib.remove_all(web_html, "//header")
        XmlLib.remove_all(web_html, "//img")
        elems = web_html.xpath("//*")
        names = set()
        for e in elems:
            names.add(e.tag)
        print (names)
        for hh in ['h1', 'h2', 'h3', 'h4']:
            self.print_hh_sections(web_html, hh=hh)

        # print_all_sections()


        # write cleaned html
        outfile = str(Path(web_dir, "longer_report_cleaned.html"))
        with open(outfile, 'wb') as doc:
            doc.write(lxml.etree.tostring(web_html, pretty_print=True))

    def test_web_glossary(self):
        """read web html glossary and parse
        """
        # web_dir =   Path(Resources.TEST_IPCC_DIR, "syr", "annexes", "web_html")
        web_dir =   Path(Resources.TEST_IPCC_DIR, "syr", "annexes", "web_html")
        web_file = Path(web_dir, "glossary.html")
        assert web_file.exists()
        web_html = lxml.etree.parse(str(web_file), lxml.etree.HTMLParser())
        # textarea is a bad one
        XmlLib.remove_all(web_html,
                          ["//link", "//input", "//button", "//iframe", "//script", "//noscript", "//source", "//nav", "//textarea", "//style"]) # this is definitely a problem for display
        elems = web_html.xpath("//*")
        names = set()
        for e in elems:
            names.add(e.tag)
        print (names)
        for hh in ['h1', 'h2', 'h3', 'h4']:
            self.print_hh_sections(web_html, hh=hh)

        outfile = str(Path(web_dir, "glossary_cleaned.html"))
        with open(outfile, 'wb') as doc:
            doc.write(lxml.etree.tostring(web_html, pretty_print=True))




    @unittest.skip("not yet developed nested sections")
    def test_chapter_toolchain_chapters_DEVELOP(self):
        """nested sections"""
        front_back = IPCCSections.get_major_section_names()
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back=front_back)
        input_pdfs = [glob.glob(str(input_pdf)) for input_pdf in INPUT_PDFS]
        input_pdfs = FileLib.convert_files_to_posix(input_pdfs)
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

    @unittest.skipIf(OMIT_LONG, "Too long")
    def test_glossaries_KEY(self):
        """
        BAD Output - FIXME
        iterates over 1-6 reports , glossaries and adds internal links
        """
        front_back = ""
        section_regex_dict, section_regexes = IPCCSections.get_ipcc_regexes(front_back)
        g_types = [
                GLOSSARY,
                ACRONYMS,
            ]

        max_reports = 1
        use_svg = True
        write_csv = True
        for report in REPORTS[:max_reports]:
            for g_type in g_types:
                input_pdf = IPCCGlossary.create_input_pdf_name(AR6_DIR, report, g_type)
                glossary = IPCCGlossary.create_glossary_from_pdf(
                    glossary_top=AR6_DIR,
                    glossary_type=g_type,
                    report=report,
                    section_regexes=None
                )
                HtmlUtil.analyze_styles(glossary.glossary_elem)

                glossary.create_annotated_glossary()

                csv_path = glossary.write_csv()
                with open(csv_path, "r") as f:
                    reader = csv.reader(f)
                    assert len(list(reader)) == 123

    @unittest.skip("Not yet working")
    def test_pyvis(self):

        from pyvis.network import Network
        import pandas as pd

        got_net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")

        # set the physics layout of the network
        got_net.barnes_hut()
        got_data = pd.read_csv(str(Path(AR6_DIR, "wg1", "annexes", "html", "glossary", "links.csv")))
        print(f"got data_frame {got_data}")
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
            glossary_file = Path(AR6_DIR, report, "annexes", "html", "glossary", f"{IPCCGlossary.ANNOTATED_GLOSSARY}.html")
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

    def test_write_annotated_csv(self):
        max_entries = 1000
        max_reports = 3
        reports = [
            "wg1",
            # "wg2",
            # "wg3",
            # "syr",
            # "sr15",
            # "srocc",
            # "srccl"
        ]
        for report in reports[:max_reports]:
            self.write_annotated_glossary_to_csv(max_entries, report)

    def test_extract_authors(self):
        """

        """
        # html_dir = Path(Resources.TEST_IPCC_DIR, "srccl", "chapters", "html", "Chapter05")
        html_dir = Path(Resources.TEST_IPCC_SRCCL, "chapters", "html", "Chapter05")
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
            assert 40 <= len(pages) <= 43

    @unittest.skip("Don't know what this does")
    def test_read_urls_with_raw_pdfplumber_fails(self):
        input_pdf = "https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_SPM.pdf"
        #  this file/URL exists 2024-01-03
        try:
            assert input_pdf.exists(), f"file {input_pdf} exists"
            with pdfplumber.open(input_pdf) as f:
                pages = f.pages
                assert len(pages) == 40
                assert False, f"should throw FileNotFoundError {input_pdf}"
        except FileNotFoundError as e:
            assert f"file not found {e}"
            raise e

    @unittest.skipUnless(AmiAnyTest.run_long(), "run occasionally")
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

    @unittest.skipUnless(AmiAnyTest.run_long(), "run occasionally")
    def test_command_line_read_url(self):
        """
        primary commandline for pyamihtmlx IPCC
        creates 114 pages of HTML from PDF online
        takes about 30 seconds.
        """
        """FAIL doesn't create output file; cause not yet known
        """
        test = True # tests the tests
        # test = False

        # input_pdf = "https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_SPM.pdf"
        input_pdf = "https://www.ipcc.ch/site/assets/uploads/sites/4/2022/11/SRCCL_Chapter_5.pdf"
        input_pdf = "https://www.ipcc.ch/report/ar6/syr/downloads/report/IPCC_AR6_SYR_LongerReport.pdf"
        element_count = 13
        pyami = PyAMI()
        outdir = str(Path(Resources.TEMP_DIR, "myjunk1"))
        if not test:
            FileLib.delete_directory_contents(outdir, delete_directory=True)
            print(f"deleting outdir {outdir} before writing")
        # args = ["IPCC", "--input", input_pdf, "--outdir", outdir]
        pyami = PyAMI()
        args = ["IPCC", "--input", input_pdf, "--outdir", outdir]
        pyami.run_command(args)

        outdir = Path(outdir)
        if not outdir.exists():
            outdir.mkdir(parents=True, exist_ok=False)
            pyami1 = PyAMI()
            args1 = ["IPCC", "--input", input_pdf, "--outdir", outdir]
            pyami1.run_command(args1)

        """
total_pages elems: 1661
total_pages content 1661
"""
        print(f"testing {outdir}")
        file = self.assert_file_exists(outdir, "page_1.raw.html", label="first page")
        self.assert_element_count(file, element_count)
        self.assert_file_exists(outdir, "page_81.raw.html", label="last page")
        self.assert_file_exists(outdir, "styles1.html", label="styles extracted to head")
        self.assert_file_exists(outdir, "groups_styles.html", label="split into sections (groups)")
        self.assert_file_exists(outdir, "groups_groups.html", label="how is this different?")
        self.assert_file_exists(outdir, "total_pages.html", label="initial raw concatenated HTML file")
        self.assert_file_exists(outdir, "groups_statements.html", label="split into statements (IPCC only)")


    def test_tfidf_on_interentry_text_glossaries(self):
        """
        finds differences between descripns in glossary entries
        """
        omit_dict = {
            A_TEXT: 'See |see ',
            T_TEXT: 'See |see ',
        }
        maxreport = 1

        for report in REPORTS[:maxreport]:
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

    @unittest.skip("can't get it to work in PyCharm")
    def test_logger(self):
        import sys
        # logging.error = print
        handler = logger.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        logging.error(f"ERROR!!!")

        logger.setLevel(logging.DEBUG)
        logger.error(f"ERROR {__name__}")
        logger1 = logging.getLogger("FOO")
        logger1.error("ERROR1")
        print(f"logging {logging.DEBUG}")

    @unittest.skip("test not yet developed")
    def test_syr_fr(self):
        """SYR FullVoume reads pages badly (wrong orintation)
        """
        input_pdf = Path(AR6_DIR, "syr", "fr", "fulltext.pdf")
        HtmlGenerator.create_sections(input_pdf)

    def test_pyami2jats_authors(self):
        """create JATS-like output from HTML
        takes sectioned file (currently groups.html) and creates JATS
        sections/
          head/
            contrib/
          body/
            introduction/
        (or something similar)

        """
        body = IPCCSections.get_body_for_syr_lr(AR6_DIR)
        author_dict = IPCCSections.create_author_dict_from_sections(body)
        assert len(author_dict) == 6
        core_writing = author_dict[CORE_TEAM]
        assert len(core_writing) == 49
        assert core_writing["Hoesung Lee"] == "Chair"

    @unittest.skip("NYI")
    def test_pyami2jats_authors(self):
        """create JATS-like output from HTML
        takes sectioned file (currently groups.html) and creates JATS
        sections/
          head/
            contrib/
          body/
            introduction/
        (or something similar)

        """
        body = IPCCSections.get_body_for_syr_lr(AR6_DIR)
        meta_dict = IPCCSections.create_metadata_dict_from_sections(body)
        # assert len(meta_dict) == 6
        # core_writing = meta_dict["Core Writing Team"]
        # assert len(core_writing) == 49
        # assert core_writing["Hoesung Lee"] == "Chair"


    def test_kwords(self):
        """
        the kwords in our argparse is a catch-all to allow new keywords to be added into a global dictionary
        for example
        pyamihtmlx kwords foo:bar plugh:xyzzy
        will add these to the gloabl dictionary where they can be retrieved later

        """
        from pyamihtmlx.ami_config import doc_info
        pyami = PyAMI()
        args = ["IPCC", "--kwords", "mediabox:[[0,100],[0,50]]", "maxpage:5" ]
        pyami.run_command(args)
        print (f" pyami.config {pyami.config}")
        assert doc_info == {'mediabox': '[[0,100],[0,50]]', 'margins_ltrb': [30, 40, 35, 40], 'maxpage': '5'}
        assert doc_info["mediabox"] == '[[0,100],[0,50]]'
        assert doc_info["maxpage"] == "5"

