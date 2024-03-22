import csv
import glob
import os
import re
import unittest
from pathlib import Path

import lxml
import requests
from lxml import html
from lxml.html import HTMLParser
import lxml.etree as ET

from pyamihtmlx.ami_html import HtmlUtil
from pyamihtmlx.ami_integrate import HtmlGenerator
from pyamihtmlx.ami_pdf_libs import AmiPDFPlumber, AmiPlumberJson
from pyamihtmlx.file_lib import FileLib
from pyamihtmlx.html_marker import SpanMarker, HtmlPipeline
from pyamihtmlx.ipcc import Wordpress, Gatsby, IPCCChapter, IP_WG1, IPCCArgs, IP_WG2, IP_WG3
from pyamihtmlx.pyamix import PyAMI, REPO_DIR
from pyamihtmlx.un import DECISION_SESS_RE, MARKUP_DICT, INLINE_DICT, UNFCCC, UNFCCCArgs, IPCC, HTML_WITH_IDS_HTML, \
    AR6_URL, TS, GATSBY_RAW
from pyamihtmlx.un import LR, SPM, ANN_IDX
from pyamihtmlx.un import GATSBY, DE_GATSBY, HTML_WITH_IDS, ID_LIST, WORDPRESS, DE_WORDPRESS, MANUAL, PARA_LIST
from pyamihtmlx.util import Util
from pyamihtmlx.xml_lib import HtmlLib

from test.resources import Resources
from test.test_all import AmiAnyTest
from test.test_headless import SC_TEST_DIR

UNFCCC_DIR = Path(Resources.TEST_RESOURCES_DIR, "unfccc")
UNFCCC_TEMP_DIR = Path(Resources.TEMP_DIR, "unfccc")
UNFCCC_TEMP_DOC_DIR = Path(UNFCCC_TEMP_DIR, "unfcccdocuments1")

MAXPDF = 3

OMIT_LONG = True  # omit long tests

#
TEST_DIR = Path(REPO_DIR, "test")
TEMP_DIR = Path(REPO_DIR, "temp")

IPCC_TOP = Path(TEST_DIR, "resources", "ipcc", "cleaned_content")
assert IPCC_TOP.exists(), f"{IPCC_TOP} should exist"

QUERIES_DIR = Path(TEMP_DIR, "queries")
assert QUERIES_DIR.exists(), f"{QUERIES_DIR} should exist"

IPCC_DICT = {
    "_IPCC_REPORTS": IPCC_TOP,
    "_IPCC_QUERIES": QUERIES_DIR,
}

CLEANED_CONTENT = 'cleaned_content'
SYR = 'syr'
SYR_LR = 'longer-report'
IPCC_DIR = 'ipcc'


class TestIPCC(AmiAnyTest):

    @unittest.skipUnless(True or AmiAnyTest.run_long(), "run occasionally, 1 min")
    def test_pdfplumber_doublecol_create_pages_for_WGs_HACKATHON(self):
        """
        creates AmiPDFPlumber and reads double-column pdf and debugs
        This is also an integration/project test
        """

        report_names = [
            # "SYR_LR",
            # "SYR_SPM",
            # "SR15_SPM",
            # "SR15_TS",
            # "SRCCL_SPM",
            # "SRCCL_TS",
            # "SROCC_SPM",
            # "SROCC_TS",
            # "WG1_SPM",
            # "WG1_TS",
            # "WG2_SPM",
            # "WG2_TS",
            # "WG3_SPM",
            # "WG3_TS",
            "WG3_CHAP08",
        ]
        # this needs mending
        for report_name in report_names:
            report_dict = self.get_report_dict_from_resources(report_name)
            HtmlGenerator.get_pdf_and_parse_to_html(report_dict, report_name)

    def get_report_dict_from_resources(self, report_name):
        return Resources.WG_REPORTS[report_name]

    def test_html_commands(self):
        """NYI"""
        print(f"directories NYI")
        return

        in_dir, session_dir, top_out_dir = self._make_query()
        outdir = "/Users/pm286/workspace/pyamihtml/temp/"
        PyAMI().run_command(
            ['IPCC', '--input', "WG3_CHAP08", '--outdir', str(top_out_dir),
             '--operation', UNFCCCArgs.PIPELINE])

    @unittest.skipUnless(AmiAnyTest.run_long(), "run occasionally, 1 min")
    def test_html_commands_shadow(self):
        """shadows above test - mainly development"""
        report_name = "WG3_CHAP08"
        report_dict = self.get_report_dict_from_resources(report_name)
        print(f"report_dict {report_dict}")
        outdir = report_dict.get("outdir")
        print(f"outdir {outdir}")
        HtmlGenerator.get_pdf_and_parse_to_html(report_dict, report_name)

    @unittest.skip("NYI")
    def test_clean_pdf_html_SYR_LR(self):
        """fails as there are no tables! (they are all bitmaps)"""
        inpdfs = [
            Path(Resources.TEST_IPCC_SROCC, "ts", "fulltext.pdf"),
            Path(Resources.TEST_IPCC_LONGER_REPORT, "fulltext.pdf"),
        ]
        for inpdf in inpdfs:
            pass

    def test_extract_target_section_ids_from_page(self):
        """The IPCC report and many others have hierarchical IDs for sections
        These are output in divs and spans
        test/resources/ipcc/wg2/spm/page_9.html
        e.g. <div>
        """
        input_html_path = Path(Resources.TEST_RESOURCES_DIR, "ipcc", "wg2", "spm", "page_9.html")
        assert input_html_path.exists()
        id_regex = r"^([A-F](?:.[1-9])*)\s+.*"

        spanlist = HtmlLib.extract_ids_from_html_page(input_html_path, regex_str=id_regex, debug=False)
        assert len(spanlist) == 4

    def test_extract_target_sections_from_pages(self):
        """The IPCC report and many others have hierarchical IDs for sections
        These are output in divs and spans
        test/resources/ipcc/wg2/spm/page_9.html
        e.g. <div>
        """
        id_regex = r"^([A-F](?:.[1-9])*)\s+.*"
        html_dir = Path(Resources.TEST_RESOURCES_DIR, "ipcc", "wg2", "spm", "pages")
        os.chdir(html_dir)
        total_spanlist = []
        files = FileLib.posix_glob("*.html")
        for i in range(len(files)):
            file = f"page_{i + 1}.html"
            try:
                spanlist = HtmlLib.extract_ids_from_html_page(file, regex_str=id_regex, debug=False)
            except Exception as e:
                print(f"cannot read {file} because {e}")
                continue
            total_spanlist.append((file, spanlist))
        # csvlist = []
        # csvlist.append(["qid", "Len"], "P1")
        output_dir = Path(Resources.TEMP_DIR, "html", "ipcc", "wg2", "spm", "pages")
        output_dir.mkdir(exist_ok=True, parents=True)
        section_file = Path(output_dir, 'sections.csv')
        with open(section_file, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile, quotechar='|')
            csvwriter.writerow(["qid", "Len", "P1"])
            for file, spanlist in total_spanlist:
                if spanlist:
                    print(f"========= {file} ==========")
                    for span in spanlist:
                        text_ = span.text[:50].strip()
                        qid = '\"' + text_.split()[0] + '\"'
                        # print(f" [{qid}]")
                        text = text_.split()[1] if len(text_) > 8 else span.xpath("following::span")[0].text
                        print(f"{qid}, {text}")
                        csvwriter.writerow(["", qid, "Q18"])
                        # csvlist.append(["", qid, "P18"])
        print(f" wrote {section_file}")
        assert section_file.exists()

    @unittest.skipUnless(AmiAnyTest.run_long(), "run occasionally")
    def test_pdfplumber_json_longer_report_debug(self):
        """creates AmiPDFPlumber and reads pdf and debugs"""
        path = Path(Resources.TEST_IPCC_LONGER_REPORT, "fulltext.pdf")
        ami_pdfplumber = AmiPDFPlumber()
        # pdf_json = ami_pdfplumber.create_parsed_json(path)
        plumber_json = ami_pdfplumber.create_ami_plumber_json(path)
        assert type(plumber_json) is AmiPlumberJson
        metadata_ = plumber_json.pdf_json_dict['metadata']
        print(f"k {plumber_json.keys, metadata_.keys} \n====Pages====\n"
              # f"{len(plumber_json['pages'])} "
              # f"\n\n page_keys {c['pages'][0].items()}"
              )
        pages = plumber_json.get_ami_json_pages()
        assert len(pages) == 85
        for page in pages:
            ami_pdfplumber.debug_page(page)
        # pprint.pprint(f"c {c}[:20]")

    def test_strip_decorations_from_raw_expand_wg3_ch09_old(self):
        """
        From manually downloaded HTML strip image paragraphs

        <p class="Figures--tables-etc_•-Figure-title---spans-columns" lang="en-US">
          <span class="•-Figure-table-number---title">
            <span class="•-Bold-condensed" lang="en-GB">
              <img alt="" class="_idGenObjectAttribute-2" id="figure-9-1" src="https://ipcc.ch/report/ar6/wg3/downloads/figures/IPCC_AR6_WGIII_Figure_9_1.png">
              </span>
              </span>
              </p>
        This is mainly to see if stripping the img@href improvdes the readability of the raw HTML

        and
        <div class="_idGenObjectLayout-1">
          <div class="_idGenObjectStyleOverride-1" id="_idContainer006">
            <img alt="" class="_idGenObjectAttribute-1" src="https://ipcc.ch/report/ar6/wg3/downloads/figures/IPCC_AR6_WGIII_Equation_9_1-2.png">
          </div>
        </div>
        """
        encoding = "utf-8"
        expand_file = Path(Resources.TEST_IPCC_WG3, "Chapter09", "online", "raw.expand.html")
        assert expand_file.exists()

        expand_html = lxml.etree.parse(str(expand_file), parser=HTMLParser(encoding=encoding))
        assert expand_html is not None

        # Note remove_elems() edits the expand_html
        # remove styles
        HtmlUtil.remove_elems(expand_html, xpath="/html/head/style")
        # remove links
        HtmlUtil.remove_elems(expand_html, xpath="/html/head/link")
        # remove share_blocks
        """<span class="share-block">
              <img class="share-icon" src="../../share.png">
            </span>
        """
        HtmlUtil.remove_elems(expand_html, xpath=".//span[@class='share-block']")
        """
        <div class="ch-figure-button-cont">
          <a href="/report/ar6/wg3/figures/chapter-9/box-9-1-figure" target="_blank">
            <button class="btn-ipcc btn btn-primary ch-figure-button">Open figure</button>
          </a> 
        </div>        
        """
        HtmlUtil.remove_elems(expand_html, xpath=".//div[@class='ch-figure-button-cont']")

        """
        <div class="dropdown">
          <button id="dropdown-basic" aria-expanded="false" type="button" class="btn-ipcc btn btn-primary dl-dropdown dropdown-toggle btn btn-success">Downloads</button>
        </div>
        """
        HtmlUtil.remove_elems(expand_html, xpath="/html/body//div[@class='dropdown']")
        HtmlUtil.remove_elems(expand_html, xpath="/html/body//button")
        HtmlUtil.remove_elems(expand_html, xpath="/html//script")

        no_decorations = expand_html
        no_decorations_file = Path(expand_file.parent, "no_decorations.html")
        HtmlLib.write_html_file(no_decorations, no_decorations_file, debug=True)

    def test_strip_non_content_from_raw_expand_wg3_ch06(self):
        """
        From manually downloaded HTML strip non-content (style, link, button, etc

        """
        from pyamihtmlx.ipcc import IPCCChapter

        expand_file = Path(Resources.TEST_IPCC_WG3, "Chapter06", "online", "expanded.html")
        IPCCChapter.make_pure_ipcc_content(expand_file)

    def test_strip_decorations_from_raw_expand_syr_longer(self):
        """
        From manually downloaded HTML strip decorations

        The xpaths may need editing - they started as the same for WG3
        """
        encoding = "utf-8"
        expand_file = Path(Resources.TEST_IPCC_SYR, "lr", "online", "expanded.html")
        assert expand_file.exists()

        expand_html = lxml.etree.parse(str(expand_file), parser=HTMLParser(encoding=encoding))
        assert expand_html is not None

        # Note remove_elems() edits the expand_html
        # remove styles
        HtmlUtil.remove_elems(expand_html, xpath="/html/head/style")
        # remove links
        HtmlUtil.remove_elems(expand_html, xpath="/html/head/link")
        # remove share_blocks
        """<span class="share-block">
              <img class="share-icon" src="../../share.png">
            </span>
        """
        HtmlUtil.remove_elems(expand_html, xpath=".//span[@class='share-block']")
        """
        <div class="ch-figure-button-cont">
          <a href="/report/ar6/wg3/figures/chapter-9/box-9-1-figure" target="_blank">
            <button class="btn-ipcc btn btn-primary ch-figure-button">Open figure</button>
          </a> 
        </div>        
        """
        HtmlUtil.remove_elems(expand_html, xpath=".//div[@class='ch-figure-button-cont']")

        """
        <div class="dropdown">
          <button id="dropdown-basic" aria-expanded="false" type="button" class="btn-ipcc btn btn-primary dl-dropdown dropdown-toggle btn btn-success">Downloads</button>
        </div>
        """
        HtmlUtil.remove_elems(expand_html, xpath="/html/body//div[@class='dropdown']")
        HtmlUtil.remove_elems(expand_html, xpath="/html/body//button")
        HtmlUtil.remove_elems(expand_html, xpath="/html/body//script")

        no_decorations = expand_html
        no_decorations_file = Path(expand_file.parent, "no_decorations.html")
        HtmlLib.write_html_file(no_decorations, no_decorations_file, debug=True)

    def test_download_sr15_chapter1_and_strip_non_content(self):
        """read single chapter from "view" button and convert to raw semantic HTML
        Tests the encoding
        """
        debug = False
        rep = "sr15"
        chapter_no = 1
        chapter_no_out = "01"
        url = f"https://www.ipcc.ch/{rep}/chapter/chapter-{chapter_no}/"
        html_tree = HtmlLib.retrieve_with_useragent_parse_html(url, debug=debug)
        title = html_tree.xpath('/html/head/title')[0].text
        assert title == "Chapter 1 — Global Warming of 1.5 ºC"
        p0text = html_tree.xpath('//p')[0].text
        assert p0text[:41] == "Understanding the impacts of 1.5°C global"
        IPCCChapter.atrip_wordpress(html_tree)
        HtmlLib.write_html_file(html_tree,
                                Path(Resources.TEMP_DIR, "ipcc", rep, f"Chapter{chapter_no_out}", f"{WORDPRESS}.html"),
                                debug=True)
        IPCC.add_styles_to_head(HtmlLib.get_head(html_tree))
        HtmlLib.write_html_file(html_tree,
                                Path(Resources.TEMP_DIR, "ipcc", rep, f"Chapter{chapter_no_out}",
                                     f"{WORDPRESS}_styles.html"),
                                debug=True)

    @unittest.skipUnless(AmiAnyTest.run_long(), "run occasionally")
    def test_download_special_reports_and_strip_non_content(self):
        """read single chapter from "view" button and convert to raw semantic HTML
        Tests the encoding
        """
        chapters = [
            ("sr15", "chapter-1", "Chapter01"),
            ("sr15", "chapter-2", "Chapter02"),
            ("sr15", "chapter-3", "Chapter03"),
            ("sr15", "chapter-4", "Chapter04"),
            ("sr15", "chapter-5", "Chapter05"),
            ("sr15", "spm", "spm"),
            ("sr15", "ts", "ts"),
            ("sr15", "glossary", "glossary"),

            ("srccl", "chapter-1", "Chapter01"),
            ("srccl", "chapter-2", "Chapter02"),
            ("srccl", "chapter-3", "Chapter03"),
            ("srccl", "chapter-4", "Chapter04"),
            ("srccl", "chapter-5", "Chapter05"),
            ("srccl", "chapter-6", "Chapter06"),
            ("srccl", "chapter-7", "Chapter07"),
            ("srccl", "spm", "spm"),
            ("srccl", "ts", "ts"),
            # ("srccl", "glossary", "glossary"),  # points to PDF

            ("srocc", "chapter-1", "Chapter01"),
            ("srocc", "chapter-2", "Chapter02"),
            ("srocc", "chapter-3", "Chapter03"),
            ("srocc", "chapter-4", "Chapter04"),
            ("srocc", "chapter-5", "Chapter05"),
            ("srocc", "chapter-6", "Chapter06"),
            ("srocc", "spm", "spm"),
            ("srocc", "ts", "ts"),
            ("srocc", "glossary", "glossary"),

        ]
        debug = False
        for chapter in chapters:
            rep = chapter[0]
            chapter_no = chapter[1]
            chapter_no_out = chapter[2]
            url = f"https://www.ipcc.ch/{rep}/chapter/{chapter_no}/"
            print(f"reading: {url}")
            html = HtmlLib.retrieve_with_useragent_parse_html(url, debug=debug)
            HtmlLib.write_html_file(html,
                                    Path(Resources.TEMP_DIR, "ipcc", rep, chapter_no_out, f"{WORDPRESS}.html"),
                                    debug=True)
            IPCCChapter.atrip_wordpress(html)
            HtmlLib.write_html_file(html,
                                    Path(Resources.TEMP_DIR, "ipcc", rep, chapter_no_out, f"{DE_WORDPRESS}.html"),
                                    debug=True)
            IPCC.add_styles_to_head(HtmlLib.get_head(html))
            HtmlLib.write_html_file(html,
                                    Path(Resources.TEMP_DIR, "ipcc", rep, chapter_no_out,
                                         f"{DE_WORDPRESS}_styles.html"),
                                    debug=True)

    @unittest.skip("probably redundant")
    def test_download_sr15_as_utf8(self):
        """
        maybe obsolete
        """
        url = "https://www.ipcc.ch/sr15/chapter/chapter-1/"
        response = requests.get(url, headers={"user-agent": "myApp/1.0.0"})
        content = response.content
        content_string = content.decode("UTF-8")
        chapter_no_out = "01"
        rep = "sr15"
        outfile = Path(Resources.TEMP_DIR, "ipcc", rep, f"Chapter{chapter_no_out}", f"{WORDPRESS}_1.html")
        with open(outfile, "w", encoding="UTF-8") as f:
            f.write(content_string)

        content_html = lxml.etree.fromstring(content_string, HTMLParser())

        paras = content_html.xpath("//p")
        # check degree character is encoded
        assert paras[0].text[:41] == "Understanding the impacts of 1.5°C global"
        for p in paras[:10]:
            print(f"p> {p.text}")
        head_elems = content_html.xpath("/html/head/*")
        for head_elem in head_elems:
            print(f"h> {lxml.html.tostring(head_elem)}")

    def test_download_wg_chapter_and_strip_non_content(self):
        """read single chapter from "EXPLORE" button and convert to raw semantic HTML
        """
        wg = "wg3"
        # correct chapter url
        chapter_no = 10
        url = f"https://www.ipcc.ch/report/ar6/{wg}/chapter/chapter-{chapter_no}/"
        outfile = Path(Resources.TEMP_DIR, "ipcc", wg, f"Chapter{chapter_no}", f"{GATSBY}.html")
        (html, error) = IPCCChapter.make_pure_ipcc_content(html_url=url, outfile=outfile)
        assert error is None
        assert outfile.exists()
        assert len(html.xpath("//div")) > 20

        # test non-existent chapter
        chapter_no = 100
        url = f"https://www.ipcc.ch/report/ar6/{wg}/chapter/chapter-{chapter_no}/"
        outfile = None
        (html, error) = IPCCChapter.make_pure_ipcc_content(html_url=url, outfile=outfile)
        assert error.status_code == 404
        assert html is None

        # non-existent file
        file = "foo.bar"
        outfile = None
        (html, error) = IPCCChapter.make_pure_ipcc_content(html_file=file, outfile=outfile)

    @unittest.skipUnless(AmiAnyTest.run_long(), "run occasionally")
    def test_download_all_wg_chapters_and_strip_non_content(self):
        """
        download over all chapters in reports and convert to raw semantic form
        """

        for section in [
            LR,
            SPM,
            ANN_IDX,
        ]:
            url = f"https://www.ipcc.ch/report/ar6/syr/{section}/"
            outfile = Path(Resources.TEMP_DIR, "ipcc", "syr", f"{section}", "content.html")
            (html_elem, error) = IPCCChapter.make_pure_ipcc_content(html_url=url, outfile=outfile)
            if error is not None and error.status_code == 404:
                print(f"no online chapter or {url}, assume end of chapters")

        for report in [
            "report/ar6/wg1",
            "report/ar6/wg2",
            "report/ar6/wg3",
            # "sr15",
            # "srocc",
            # "srccl",
        ]:
            for section in [
                SPM,
                "technical-summary",
            ]:
                url = f"https://www.ipcc.ch/{report}/chapter/{section}/"
                outfile = Path(Resources.TEMP_DIR, "ipcc", report, f"{section}", f"{GATSBY}.html")
                (html_elem, error) = IPCCChapter.make_pure_ipcc_content(html_url=url, outfile=outfile)
                if error is not None and error.status_code == 404:
                    print(f"no online chapter or {url}, assume end of chapters")

            for chapter_no in range(1, 99):
                outchap_no = chapter_no if chapter_no >= 10 else f"0{chapter_no}"
                url = f"https://www.ipcc.ch/{report}/chapter/chapter-{chapter_no}/"
                outfile = Path(Resources.TEMP_DIR, "ipcc", report, f"Chapter{outchap_no}", f"{GATSBY}.html")
                (html_elem, error) = IPCCChapter.make_pure_ipcc_content(html_url=url, outfile=outfile)
                if error is not None and error.status_code == 404:
                    print(f"no online chapter or {url}, assume end of chapters")
                    break

    def test_remove_gatsby_markup_for_report_types(self):
        """take output after downloading anc converting and strip all gatsby stuff, etc.
        """
        for rep_chap in [
            # ("sr15", "Chapter02"),
            # ("srccl", "Chapter02"),
            # ("srocc", "Chapter02"),
            ("wg1", "Chapter02"),
            ("wg2", "Chapter02"),
            ("wg3", "Chapter03"),
            ("syr", "longer-report")

        ]:
            publisher = Gatsby()
            infile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", rep_chap[0], rep_chap[1], f"{publisher.raw_html}.html")
            outfile = Path(Resources.TEMP_DIR, "ipcc", rep_chap[0], rep_chap[1], f"{publisher.cleaned_html}.html")
            html = publisher.remove_unnecessary_markup(infile)
            HtmlLib.write_html_file(html, outfile, encoding="UTF-8", debug=True)

    def test_remove_wordpress_markup_for_report_types(self):
        """take output after downloading anc converting and strip all wordpress stuff, etc.
        """
        for rep_chap in [
            ("sr15", "Chapter02"),
            ("srccl", "Chapter02"),
            ("srocc", "Chapter02"),
            # ("wg1", "Chapter02"),
            # ("wg2", "Chapter02"),
            # ("wg3", "Chapter03"),
            # ("syr", "longer-report")

        ]:
            publisher = Wordpress()
            infile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", rep_chap[0], rep_chap[1], f"{publisher.raw_html}.html")
            outfile = Path(Resources.TEMP_DIR, "ipcc", rep_chap[0], rep_chap[1], f"{publisher.cleaned_html}.html")
            html = publisher.remove_unnecessary_markup(infile)

            HtmlLib.write_html_file(html, outfile, encoding="UTF-8", debug=True)

    def test_remove_wordpress_markup_from_all_srs_and_add_ids(self):
        """take output after downloading anc converting and strip all wordpress stuff, etc.
        """
        publisher = Wordpress()
        globx = f"{Path(Resources.TEMP_DIR, 'ipcc')}/sr*/**/{publisher.cleaned_html}.html"
        infiles = FileLib.posix_glob(globx)
        assert len(infiles) > 10
        print(f"de_publisher files {len(infiles)}")
        cleaned_path = Path(Resources.TEST_RESOURCES_DIR, "ipcc", "cleaned_content")
        for infile in infiles:
            chap = Path(infile).parent.stem
            sr = Path(infile).parent.parent.stem
            print(f"sr {sr} chap {chap}")
            outfile = Path(cleaned_path, sr, chap, f"{publisher.cleaned_html}.html")
            htmlx = publisher.remove_unnecessary_markup(infile)
            HtmlLib.write_html_file(htmlx, outfile, encoding="UTF-8", debug=True)
            infile = Path(cleaned_path, sr, chap, f"{publisher.cleaned_html}.html")
            outfile = Path(cleaned_path, sr, chap, f"{HTML_WITH_IDS}.html")
            idfile = Path(cleaned_path, sr, chap, f"{ID_LIST}.html")
            parafile = Path(cleaned_path, sr, chap, f"{PARA_LIST}.html")
            publisher.add_para_ids_and_make_id_list(infile, idfile=idfile, outfile=outfile, parafile=parafile)
            assert outfile.exists(), f"{outfile} should exist"
            assert idfile.exists(), f"{idfile} should exist"

    def test_remove_gatsby_markup_from_all_chapters(self):

        """
        input raw_html
        output_de-gatsby

        take output after downloading anc converting and strip all gatsby stuff, etc.
        """
        web_publisher = Gatsby()
        globx = f"{Path(Resources.TEST_RESOURCES_DIR, 'ipcc')}/**/{web_publisher.raw_html}.html"
        infiles = FileLib.posix_glob(globx, recursive=True)
        for infile in infiles:
            html_elem = web_publisher.remove_unnecessary_markup(infile)
            outfile = Path(Path(infile).parent, f"{DE_GATSBY}.html")
            HtmlLib.write_html_file(html_elem, outfile, debug=True)

    def test_gatsby_add_ids_to_divs_and_paras(self):
        """
        outputs:
            html_with_ids
            id_filr
            paras_ids - paragraphs with ids

        """

        publisher = Gatsby()
        globx = f"{Path(Resources.TEST_RESOURCES_DIR, 'ipcc')}/**/{publisher.raw_html}.html"
        infile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", "wg3", "Chapter03", f"{DE_GATSBY}.html")
        outfile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", "wg3", "Chapter03", f"{HTML_WITH_IDS}.html")
        idfile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", "wg3", "Chapter03", f"{ID_LIST}.html")
        parafile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", "wg3", "Chapter03", f"{PARA_LIST}.html")

        publisher.add_para_ids_and_make_id_list(infile, idfile=idfile, outfile=outfile, parafile=parafile)
        assert outfile.exists(), f"{outfile} should exist"
        assert idfile.exists(), f"{idfile} should exist"

    def test_add_ids_to_divs_and_paras_wordpress(self):
        """
        runs Chapter02 and Chapter03 in SR15, SROCC and SRCCL
        takes D_WORDPRESS output (stripped) and adds p(aragraph) ids in HTML_WITH_IDS
        also outputs simple list of links into paras ID_LIST
        """
        publisher = Wordpress()

        for rep in ["sr15", "srocc", "srccl"]:
            for chap in ["Chapter02", "Chapter03"]:
                infile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", rep, chap, f"{DE_WORDPRESS}.html")
                outfile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", rep, chap, f"{HTML_WITH_IDS}.html")
                idfile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", rep, chap, f"{ID_LIST}.html")
                parafile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", rep, chap, f"{PARA_LIST}.html")
                if not infile.exists():
                    print(f"cannot find: {infile}")
                    continue

                publisher.add_para_ids_and_make_id_list(infile, idfile=idfile, outfile=outfile)
                assert outfile.exists(), f"{outfile} should exist"
                assert idfile.exists(), f"{idfile} should exist"

    def test_add_ids_to_divs_and_paras_for_all_reports(self):
        publisher = Gatsby()
        top_dir = str(Path(Resources.TEST_RESOURCES_DIR, "ipcc"))
        globx = f"{top_dir}/**/{DE_GATSBY}.html"
        gatsby_files = FileLib.posix_glob(globx, recursive=True)
        assert len(gatsby_files) >= 4, f"found {len(gatsby_files)} in {globx}"
        for infile in gatsby_files:
            outfile = str(Path(Path(infile).parent, f"{HTML_WITH_IDS}.html"))
            idfile = str(Path(Path(infile).parent, f"{ID_LIST}.html"))
            parafile = str(Path(Path(infile).parent, f"{PARA_LIST}.html"))
            publisher.add_para_ids_and_make_id_list(infile, idfile=idfile, outfile=outfile, parafile=parafile)

    def test_gatsby_mini_pipeline(self):
        publisher = Gatsby()
        topdir = Path(Resources.TEST_RESOURCES_DIR, 'ipcc')
        publisher.raw_to_paras_and_ids(topdir, )

    def test_search_wg3_and_index_chapters_with_ids(self):
        """
        read chapter, search for words and return list of paragraphs/ids in which they occur
        simple, but requires no server
        """
        infile = Path(Resources.TEST_RESOURCES_DIR, "ipcc", "wg3", "Chapter03", f"{HTML_WITH_IDS}.html")
        assert infile.exists(), f"{infile} does not exist"
        html = lxml.etree.parse(str(infile), HTMLParser())
        paras = HtmlLib.find_paras_with_ids(html)
        assert len(paras) == 1163

        phrases = [
            "greenhouse gas",
            "pathway",
            "emissions",
            "global warming",
        ]
        para_phrase_dict = HtmlLib.create_para_ohrase_dict(paras, phrases)

        print(f"{para_phrase_dict.get('executive-summary_p1')}")
        keys = para_phrase_dict.keys()
        assert len(keys) == 334
        multi_item_paras = [item for item in para_phrase_dict.items() if len(item[1]) > 1]
        assert len(multi_item_paras) == 60

    def test_search_all_chapters_with_query_words(self, outfile=None):
        """
        read chapter, search for words and return list of paragraphs/ids in which they occur
        simple, but requires no server
        """
        query = "south_asia"
        indir = Path(Resources.TEST_RESOURCES_DIR, 'ipcc')
        outfile = Path(indir, f"{query}.html")
        debug = False
        globstr = f"{str(indir)}/**/{HTML_WITH_IDS}.html"
        infiles = FileLib.posix_glob(globstr, recursive=True)
        print(f"{len(infiles)} {infiles[:2]}")
        phrases = [
            "bananas",
            "South Asia",
        ]
        html1 = IPCC.create_hit_html(infiles, phrases=phrases, outfile=outfile, debug=debug)
        assert html1 is not None
        assert len(html1.xpath("//p")) > 0

    def test_search_all_chapters_with_query_words_commandline(self, outfile=None):
        """
        read chapter, search for words and return list of paragraphs/ids in which they occur
        simple, but requires no server
        """
        query = "south_asia"
        path = Path(Resources.TEST_RESOURCES_DIR, 'ipcc')
        outfile = Path(path, f"{query}.html")
        debug = False
        infiles = FileLib.posix_glob(f"{str(path)}/**/{HTML_WITH_IDS}.html", recursive=True)
        phrases = [
            "bananas",
            "South Asia"
        ]
        html1 = IPCC.create_hit_html(infiles, phrases=phrases, outfile=outfile, debug=debug)

    def test_arguments_no_action(self):

        # run args help
        PyAMI().run_command(
            ['IPCC', '--help'])

        # run args
        query_name = "south_asia1"
        ss = str(Path(Resources.TEST_RESOURCES_DIR, 'ipcc'))
        infiles = FileLib.posix_glob(f"{ss}/**/{HTML_WITH_IDS}.html", recursive=True)
        infiles2 = infiles[:100]
        queries = ["South Asia", "methane"]
        outdir = f"{Path(Resources.TEMP_DIR, 'queries')}"
        output = f"{Path(outdir, query_name)}.html"
        PyAMI().run_command(
            ['IPCC', '--input', infiles2, '--output', output])
        assert Path(output).exists(), f"{output} should exist"

    def test_commandline_search(self):

        # run args
        query_name = "methane"
        indir_path = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content')
        infiles = [
            str(Path(indir_path, "wg2/Chapter12/html_with_ids.html")),
            str(Path(indir_path, "wg3/Chapter08/html_with_ids.html")),
        ]
        queries = ["South Asia", "methane"]
        outdir = f"{Path(Resources.TEMP_DIR, 'queries')}"
        output = f"{Path(outdir, query_name)}.html"
        PyAMI().run_command(
            ['IPCC', '--input', infiles, '--query', queries,
             '--output', output])
        assert Path(output).exists()

    def test_commandline_search_with_indir(self):

        # run args
        query_name = "methane"
        indir_path = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content')
        infile = "wg2/Chapter12/html_with_ids.html"
        queries = ["South Asia", "methane"]
        outdir = f"{Path(Resources.TEMP_DIR, 'queries')}"
        output = f"{Path(outdir, query_name)}.html"
        PyAMI().run_command(
            ['IPCC', '--indir', str(indir_path), '--input', infile, '--query', queries,
             '--output', output])
        assert Path(output).exists()

    def test_commandline_search_with_wildcards(self):
        """generate inpout files """

        # run args
        query_name = "methane"
        indir_path = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content')
        glob_str = f"{indir_path}/**/html_with_ids.html"
        infiles = FileLib.posix_glob(glob_str)
        assert len(infiles) > 10
        queries = ["South Asia", "methane"]
        queries = "methane"
        outdir = f"{Path(Resources.TEMP_DIR, 'queries')}"
        output = f"{Path(outdir, query_name)}.html"
        PyAMI().run_command(
            ['IPCC', '--input', infiles, '--query', queries, '--output', output])

        assert Path(output).exists()
        assert len(ET.parse(output).xpath("//ul")) > 0


    def test_not_reference_ids_xpaths(self):
        """include/omit paras by xpath """

        # run args
        infile = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content', 'wg1', 'Chapter02', 'html_with_ids.html')

        html_tree = lxml.html.parse(str(infile))

        p_id = "//p[@id]"
        p_ids = html_tree.xpath(p_id)
        assert len(p_ids) == 1946, f"p_ids {len(p_ids)}"

        xpath_ref = "//p[@id and ancestor::*[@id='references']]"
        p_refs = html_tree.xpath(xpath_ref)
        assert len(p_refs) == 1551, f"p_refs {len(p_refs)}"

        xpath_not_ref = "//p[@id and not(ancestor::*[@id='references'])]"
        p_not_refs = html_tree.xpath(xpath_not_ref)
        assert len(p_not_refs) == 395, f"p_not_refs {len(p_not_refs)}"

    def test_search_with_xpaths(self):
        """include/omit paras by xpath """

        query = ["methane"]
        infile = str(Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content', 'wg1', 'Chapter02', 'html_with_ids.html'))
        outdir = f"{Path(Resources.TEMP_DIR, 'queries')}"

        output = f"{Path(outdir, 'methane_all')}.html"
        PyAMI().run_command(
            ['IPCC', '--input', infile, '--query', query, '--output', output])
        html_tree = ET.parse(output)
        assert (pp := len(html_tree.xpath(".//a[@href]"))) == 11, f"found {pp} paras in {output}"

        output = f"{Path(outdir, 'methane_ref')}.html"
        xpath_ref = "//p[@id and ancestor::*[@id='references']]"
        PyAMI().run_command(
            ['IPCC', '--input', infile, '--query', query, '--output', output, '--xpath', xpath_ref])
        html_tree = ET.parse(output)
        assert (pp := len(html_tree.xpath(".//a[@href]"))) == 10, f"found {pp} paras in {output}"

        query = "methane"
        output = f"{Path(outdir, 'methane_noref')}.html"
        xpath_ref = "//p[@id and not(ancestor::*[@id='references'])]"
        PyAMI().run_command(
            ['IPCC', '--input', infile, '--query', query, '--output', output, '--xpath', xpath_ref])
        self.check_output_tree(output, expected = 1, xpath = ".//a[@href]")


    def test_symbolic_xpaths(self):

        infile = str(Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content', 'wg1', 'Chapter02', 'html_with_ids.html'))
        outdir = f"{Path(Resources.TEMP_DIR, 'queries')}"
        query = "methane"

        output = f"{Path(outdir, 'methane_refs1')}.html"
        PyAMI().run_command(
            ['IPCC', '--input', infile, '--query', query, '--output', output, '--xpath', "_REFS"])
        self.check_output_tree(output, expected = 10, xpath = ".//a[@href]")

        output = f"{Path(outdir, 'methane_norefs1')}.html"
        PyAMI().run_command(
            ['IPCC', '--input', infile, '--query', query, '--output', output, '--xpath', "_NOREFS"])
        self.check_output_tree(output, expected = 1, xpath = ".//a[@href]")

    def test_symbol_indir(self):

        infile = "**/html_with_ids.html"
        outdir = f"{Path(Resources.TEMP_DIR, 'queries')}"
        output = f"{Path(outdir, 'methane_norefs2')}.html"
        query = "methane"

        PyAMI().run_command(
            ['IPCC', '--indir', "_IPCC_REPORTS", '--input', "_HTML_IDS", '--query', "methane", '--outdir', "_QUERY_OUT", "--output",  "methane.html", '--xpath',
             "_NOREFS"])
        self.check_output_tree(output, expected=276, xpath=".//a[@href]")

    def test_commandline_search_with_wildcards_and_join_indir(self):
        """generate inpout files """

        # run args
        query_name = "methane"
        indir_path = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content')
        input = f"{indir_path}/**/html_with_ids.html"

        queries = ["South Asia", "methane"]
        outdir = f"{Path(Resources.TEMP_DIR, 'queries')}"
        output = f"{Path(outdir, query_name)}.html"
        PyAMI().run_command(
            ['IPCC', '--indir', str(indir_path), '--input', input, '--query', queries,
             '--output', output])
        assert Path(output).exists()
        assert len(ET.parse(output).xpath("//ul")) > 0

    def test_parse_kwords(self):
        PyAMI().run_command(
            ['IPCC', '--kwords'])
        PyAMI().run_command(
            ['IPCC', '--kwords', 'foo:bar'])
        PyAMI().run_command(
            ['IPCC', '--kwords', 'foo:bar', 'plugh: xyzzy'])


    def test_output_bug(self):
        """PMR only, fails if output does not exist"""
        """IPCC --input /Users/pm286/workspace/pyamihtml/test/resources/ipcc/cleaned_content/**/html_with_ids.html --query "south asia"
          --output /Users/pm286/workspace/pyamihtml/temp/queries/south_asiax.html --outdir /Users/pm286/ --xpath "//p[@id and ancestor::*[@id='frequently-asked-questions']]
        """
        PyAMI().run_command(
            ['IPCC',
             "--input", "/Users/pm286/workspace/pyamihtml/test/resources/ipcc/cleaned_content/**/html_with_ids.html",
             "--query", "south asia",
             "--output", "/Users/pm286/workspace/pyamihtml/temp/queries/south_asia.html",
             "--xpath", "//p[@id and ancestor::*[@id='frequently-asked-questions']]",
             ]
        )
        print("=======================================================")

        PyAMI().run_command(
            ['IPCC', "--input",
             "/Users/pm286/workspace/pyamihtml/test/resources/ipcc/cleaned_content/**/html_with_ids.html",
             "--query", "south asia",
             "--output", "/Users/pm286/workspace/pyamihtml/temp/queries/south_asia_not_exist.html",
             "--xpath", "//p[@id and ancestor::*[@id='frequently-asked-questions']]",
             ]
        )

    def test_faq_xpath(self):
        """"""
        PyAMI().run_command(
            ['IPCC', "--input",
             "/Users/pm286/workspace/pyamihtml/test/resources/ipcc/cleaned_content/**/html_with_ids.html",
             "--query", "asia",
             "--output", "/Users/pm286/workspace/pyamihtml/temp/queries/asia_faq.html",
             "--xpath", "_FAQ",
             ]
        )

    def test_version(self):
        PyAMI().run_command(["--help"])
        PyAMI().run_command(["IPCC", "--help"])

    def test_ipcc_reports(self):
        """tests components of IPCC
        Not yet fully implemented
        """
        indir_path = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content')
        reports = [f for f in list(indir_path.glob("*/")) if f.is_dir()]
        report_stems = [Path(f).stem for f in reports]
        assert len(report_stems) == 7
        reports_set = set(["sr15", "srocc", "srccl", "syr", "wg1", "wg2", "wg3"])
        assert reports_set == set(report_stems)

    def test_ipcc_syr_contents(self):
        """analyses contents for IPCC syr
        """
        syr_path = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content', 'syr')
        assert syr_path.exists()
        child_dirs = [f for f in list(syr_path.glob("*")) if f.is_dir()]
        child_stems = set([Path(f).stem for f in child_dirs])
        child_set = set(["annexes-and-index", "longer-report", "summary-for-policymakers"])
        assert child_set == child_stems

    def test_ipcc_syr_child_dirs(self):
        """analyses contents for IPCC syr child dirs
        """
        syr_path = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content', 'syr')
        child_list = ["annexes-and-index", "longer-report", "summary-for-policymakers"]
        annexe_dir = Path(syr_path, "annexes-and-index")
        annexe_content = Path(annexe_dir, "content.html")
        assert annexe_content.exists()
        lr_dir = Path(syr_path, "longer-report")
        lr_content = Path(lr_dir, "html_with_ids.html")
        assert lr_content.exists()
        spm_dir = Path(syr_path, "summary-for-policymakers")
        spm_content = Path(spm_dir, "content.html")
        assert spm_content.exists()

    def test_ipcc_syr_annexes(self):
        """analyses contents for IPCC syr annexes
        """
        syr_annexe_content = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content', 'syr', 'annexes-and-index', "content.html")
        assert syr_annexe_content.exists()
        annexe_html = ET.parse(syr_annexe_content, HTMLParser())
        assert annexe_html is not None
        body = HtmlLib.get_body(annexe_html)
        header1 = body.xpath("./div/div/div/div/header")[0]
        assert len(header1) == 1
        header_h1 = header1.xpath("div/div/div/div/h1")[0]
        assert header_h1 is not None
        header_h1_text = header_h1.text
        assert header_h1_text == "Annexes and Index"

        section = body.xpath("./div/div/div/div/div/section")[0]
        assert section is not None
        annexe_divs = section.xpath("div/div/div[@class='h1-container']")
        assert len(annexe_divs) == 6

        annexe_titles = []
        for annexe_div in annexe_divs:
            text = annexe_div.xpath("h1")[0].text
            text = text.replace('\r', '').replace('\n', '').strip()
            annexe_titles.append(text)
            print(f" text {text}")
        assert annexe_titles == [
            'Annex I: Glossary',
            'Annex II: Acronyms, Chemical Symbols and Scientific Units',
            'Annex III: Contributors',
            'Annex IV: Expert Reviewers AR6 SYR',
            'Annex V: List of Publications of the Intergovernmental Panel on Climate Change',
            'Index'
        ]

    def test_ipcc_syr_lr_toc(self):
        """analyses contents for IPCC syr longer report
        """
        """
            <!-- TOC (from UNFCCC)-->
            <div class="toc">

                <div>
                    <span>Decision</span><span>Page</span></a>
                </div>

                <nav role="doc-toc">
                    <ul>
                        <li>
                            <a href="../Decision_1_CMA_3/split.html"><span class="descres-code">1/CMA.3</span><span
                                    class="descres-title">Glasgow Climate Pact</span></a>
                        </li>
                       ...
                    </ul>
                </nav> 
            </div>
        """
        report = 'longer-report'
        syr_lr_content = Path(Resources.TEST_RESOURCES_DIR, IPCC_DIR, CLEANED_CONTENT, SYR,
                              SYR_LR, HTML_WITH_IDS_HTML)
        assert syr_lr_content.exists()
        lr_html = ET.parse(syr_lr_content, HTMLParser())
        assert lr_html is not None
        body = HtmlLib.get_body(lr_html)
        header_h1 = body.xpath("div//h1")[0]
        assert header_h1 is not None
        header_h1_text = header_h1.text
        toc_title = "SYR Longer Report"
        assert header_h1_text == toc_title
        publisher = Gatsby()
        toc_html, ul = publisher.make_nav_ul(toc_title)

        h1_containers = body.xpath("./div//div[@class='h1-container']")
        assert len(h1_containers) == 4
        texts = []
        for h1_container in h1_containers:
            print(f"id: {h1_container.attrib['id']}")
            text = ''.join(h1_container.xpath("./h1")[0].itertext()).strip()
            texts.append(text)
            li = ET.SubElement(ul, "li")
            a = ET.SubElement(li, "a")
            target_id = h1_container.attrib["id"]
            a.attrib["href"] = f"./html_with_ids.html#{target_id}"
            span = ET.SubElement(a, "span")
            span.text = text

        assert texts == [
            '1. Introduction',
            'Section 2: Current Status and Trends',
            'Section 3: Long-Term Climate and Development Futures',
            'Section 4: Near-Term Responses in a Changing Climate',
        ]
        toc_title = Path(syr_lr_content.parent, "toc.html")
        HtmlLib.write_html_file(toc_html, toc_title, debug=True)

    def test_ipcc_syr_lr_toc_full(self):
        """creates toc recursively for IPCC syr longer report
        """
        filename = HTML_WITH_IDS_HTML
        syr_lr_content = Path(Resources.TEST_RESOURCES_DIR, IPCC_DIR, CLEANED_CONTENT, SYR ,
                              SYR_LR, filename)
        lr_html = ET.parse(syr_lr_content, HTMLParser())
        body = HtmlLib.get_body(lr_html)
        publisher = Gatsby()
        toc_html, ul = publisher.make_header_and_nav_ul(body)
        level = 0
        publisher.analyse_containers(body, level, ul, filename=filename)

        toc_title = Path(syr_lr_content.parent, "toc.html")
        HtmlLib.write_html_file(toc_html, toc_title, debug=True)

    def test_find_ipcc_curly_links(self):
        """
        IPCC links are dumb text usually either in text nodes or spans
        Not finished
        """
        syr_lr_content = Path(Resources.TEST_RESOURCES_DIR, 'ipcc', 'cleaned_content', 'syr',
                              'longer-report', HTML_WITH_IDS_HTML)
        lr_html = ET.parse(syr_lr_content, HTMLParser())
        span_texts = lr_html.xpath(".//span[text()[normalize-space(.)!='' "
                                   # "and startswith(normalize-space(.),'{') "
                                   # "and endswith(normalize-space(.),'}') "
                                   "]]")
        for span_text in span_texts:
            texts = span_text.xpath(".//text()")
            if len(texts) > 1:
                # ends = [t for t in texts]
                # print(f"==={len(texts)}")
                # c = '\u25a0'
                # c = '\u00b6'
                # c = '\u33af'
                print(f"texts [{''.join(tx for tx in texts)}]")


    def test_add_ipcc_hyperlinks(self):
        """resolves dumb links (e.g.
        {WGII SPM D.5.3; WGIII SPM D.1.1}) into hyperllinks
        target relies on SYR being sibling of WGIII, etc)
        The actual markup of the links is horrible. Sometime in spans, sometimes in naked text()
        nodes. Somes the nodes are labelled "refs", sometimes not. The safest way is to try to
        locate the actual text and find the relevant node.
        """

        syr_lr_content = Path(Resources.TEST_RESOURCES_DIR, IPCC_DIR, CLEANED_CONTENT, SYR,
                              SYR_LR, HTML_WITH_IDS_HTML)
        lr_html = ET.parse(syr_lr_content, HTMLParser())
        para_with_ids = lr_html.xpath("//p[@id]")
        assert len(para_with_ids) == 206
        IPCC.find_analyse_curly_refs(para_with_ids)
        outpath = Path(Resources.TEST_RESOURCES_DIR, IPCC_DIR, CLEANED_CONTENT, SYR,
                       SYR_LR, "links.html")
        HtmlLib.write_html_file(lr_html, outpath, debug=True)

    # ========= helpers ============
    def check_output_tree(self, output, expected=None, xpath=None):
        html_tree = ET.parse(output)
        if not expected or not xpath:
            print(f"must give expected and xpath")
            return
        assert (pp := len(html_tree.xpath(xpath))) == expected, f"found {pp} elements in {output}"




class TestUNFCCC(AmiAnyTest):
    """Tests high level operations relating to UN content (currently SpanMarker and UN/IPCC)
    """

    @unittest.skip("Spanish language")
    def test_read_unfccc(self):
        """Uses a file in Spanish"""
        input_pdf = Path(UNFCCC_DIR, "cma2023_10a02S.pdf")
        assert input_pdf.exists()
        outdir = Path(Resources.TEMP_DIR, "unfccc")
        outdir.mkdir(exist_ok=True)
        # PDFDebug.debug_pdf(input_pdf, outdir, debug_options=[WORDS, IMAGES, TEXTS])
        html_elem = HtmlGenerator.create_sections(input_pdf)
        # html_elem.xpath("//*")
        """decisión 2/CMA.3, anexo, capítulo IV.B"""
        # doclink = re.compile(".*decisión (?P<decision>\d+)/CMA\.(?P<cma>\d+), (?P<anex>anexo), (?P<capit>capítulo) (?P<roman>[IVX]+)\.(?P<letter>5[A-F]).*")
        doclink = re.compile(
            ".*decisión (?P<decision>\\d+)/CMA\\.(?P<cma>\\d+), (?P<anex>(anexo)), (?P<capit>(capítulo)) (?P<roman>[IVX]+)\\.?(?P<letter>[A-F])?.*")
        texts = html_elem.xpath("//*/text()")
        for text in texts:
            match = re.match(doclink, text)
            if match:
                for (k, v) in match.groupdict().items():
                    print(f"{k, v}", end="")
                print()

    @unittest.skip("probably obsolete")
    def test_read_unfccc_many(self):
        """
        NOT YET WORKING
        * reads MAXPDF unfccc reports in PDF,
        * transdlates to HTML,
        * adds semantic indexing for paragraphs
        * extracts targets from running text (NYI)
        * builds csv table (NYI)
        which can be fed into pyvis to create a knowledge graph
        """
        """TODO needs markup_dict"""
        """currently matches but does not output"""
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments")
        pdf_list = FileLib.posix_glob(f"{input_dir}/*.pdf")[:MAXPDF]

        span_marker = SpanMarker()
        span_marker.indir = input_dir
        span_marker.outdir = Path(Resources.TEMP_DIR, "unfcccOUT")
        span_marker.outfile = "links.csv"
        # span_marker.markup_dict = MARKUP_DICT
        span_marker.markup_dict = INLINE_DICT
        span_marker.read_and_process_pdfs(pdf_list)
        span_marker.analyse_after_match_NOOP()

    @unittest.skip("not the current approach. TODO add make to spanmarker pipeline")
    def test_read_unfccc_everything_MAINSTREAM(self):
        """"""
        """
        * reads unfccc reports in PDF,
        * transdlates to HTML,
        * adds semantic indexing for paragraphs
        * writes markedup html
        * extracts targets from running text (NYI)
        * builds csv table (NYI)
        which can be fed into pyvis to create a knowledge graph
        (writes outout to wrong dir)
        MAINSTREAM!
        """
        """
        Doesn't outut anything
        """
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1")
        pdf_list = FileLib.posix_glob(f"{input_dir}/*C*/*.pdf")[:MAXPDF]  # select CMA/CMP/CP
        outcsv = "links.csv"
        outdir = Path(Resources.TEMP_DIR, "unfcccOUT")
        outhtmldir = str(Path(outdir, "newhtml"))
        markup_dict = MARKUP_DICT

        span_marker = SpanMarker(regex=DECISION_SESS_RE)
        span_marker.run_pipeline(input_dir=input_dir,
                                 outcsv=outcsv,
                                 outdir=outdir,
                                 pdf_list=pdf_list,
                                 markup_dict=markup_dict,
                                 outhtml=outhtmldir,
                                 debug=True
                                 )

    @unittest.skip("probably redundant")
    def test_convert_pdfs_to_raw_html_IMPORTANT_STEP_1(self):
        """
        FIRST OPERATION
        tests reading the whole PDFs
        creates HTML elements
        OUTPUT - RAW HTML
        (raw HTML contains raw styles (e.g. .s1 ... .s78) in head/style)
        <style>.s15 {font-family: Times New Roman; font-size: 9.96;}</style>
        NOT normalized so we get
        <style>.s16 {font-family: Times New Roman; font-size: 9.96;}</style>

        steps:

        html_elem = HtmlGenerator.convert_to_html("foo", pdf)

        """

        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1")
        pdfs = FileLib.posix_glob(str(input_dir) + "/*C*/*.pdf")[:MAXPDF]
        assert MAXPDF >= len(pdfs) > 0
        for pdf in pdfs:
            print(f"parsing {pdf}")
            html_elem = HtmlGenerator.read_pdf_convert_to_html("foo", pdf)

            # assertions
            assert html_elem is not None
            # does element contain styles?
            head = HtmlLib.get_head(html_elem)
            """
<head>
    <style>div {border : red solid 0.5px}</style>
    ...
</head>
"""
            styles = head.xpath("style")
            assert len(styles) > 5
            # are there divs?
            """
    <div left="113.42" right="123.75" top="451.04">
        <span x0="113.42" y0="451.04" x1="123.75" style="x0: 113.42; x1: 118.4; y0: 451.04; y1: 461.0; width: 4.98;" class="s34">1. </span>
        <span x0="141.74" y0="451.04" x1="184.67" style="x0: 141.74; x1: 150.04; y0: 451.04; y1: 461.0; width: 8.3;" class="s35">Welcomes </span>
        <span x0="184.7" y0="451.04" x1="451.15" style="x0: 184.7; x1: 187.47; y0: 451.04; y1: 461.0; width: 2.77;" class="s36">the entry into force of the Paris Agreement on 4 November 2016;  </span>
    </div>"""
            divs = HtmlLib.get_body(html_elem).xpath("div")
            assert len(divs) > 5
            # do they have spans with styles?
            spans = HtmlLib.get_body(html_elem).xpath("div/span[@class]")
            assert len(spans) > 20

            # outdir, outfile = SpanMarker.create_dir_and_file(pdf, stem="raw", suffix="html")
            outfile = pdf + ".raw.html"
            HtmlLib.write_html_file(html_elem, outfile=outfile, debug=True)

            assert Path(outfile).exists()

    def test_find_unfccc_decisions_INLINE_markup_regex_single_document_IMPORTANT(self):
        """
        INLINE marking
        looks for strings such as decision 20/CMA.3 using regex
        single

        takes simple HTML element and marks it with the in-span "decision"
        div
            span
        and splits the span with a regex, annotating the results
        adds classes
        tackles most of functionality



        """
        """
        Does inline markup
        """

        html_infile = self._normalized_test_file()
        targets = [
            "decision",
            "paris",
            # "adaptation_fund"
        ]

        span_marker = SpanMarker()
        span_marker.split_spans_in_html(html_infile=html_infile, targets=targets, markup_dict=INLINE_DICT, debug=True)

    def _normalized_test_file(self):
        input_dir = Path(UNFCCC_TEMP_DOC_DIR, "CMA_3")
        html_infile = Path(input_dir, "1_4_CMA_3", "normalized.html")  # not marked
        return html_infile

    def test_inline_dict_IMPORTANT(self):
        """
        This matches keywords but doesn't markup file .
        DOESNT do hyperlinks
        """
        html_infile = self._normalized_test_file()
        input_dir = html_infile.parent
        html_outdir = Path(Resources.TEMP_DIR, "unfccc", "html")
        span_marker = SpanMarker(markup_dict=INLINE_DICT)
        outfile = Path(html_outdir, "1_CMA_3", "normalized.marked.html")
        Util.delete_file_and_check(outfile)
        html_elem = lxml.etree.parse(str(html_infile))
        span_marker.markup_html_element_with_markup_dict(
            html_elem,
            input_dir=input_dir,
            html_outdir=html_outdir,
            dict_name="dummy_dict",
            html_out=outfile,
            debug=True
        )
        assert outfile.exists()
        html_out_elem = HtmlLib.parse_html(outfile)
        ahrefs = html_out_elem.xpath(".//a/@href")
        print(f"hrefs: {len(ahrefs)}")

    def test_download_wg_chapter_spm_ts(selfself):
        """downlaods all parts of WG reports
        """
        reports = [
            IP_WG1,
            IP_WG2,
            IP_WG3,
        ]
        chapters = [
            SPM,
            TS,
            "chapter-1",
            "chapter-2",
            "chapter-3",
            "chapter-4",
            "chapter-5",
            "chapter-6",
            "chapter-7",
            "chapter-8",
            "chapter-9",
            "chapter-10",
            "chapter-11",
            "chapter-12",
            "chapter-13",
            "chapter-14",
            "chapter-15",
            "chapter-16",
            "chapter-17",
            "chapter-18",
            "chapter-19",
        ]
        web_publisher = Gatsby()
        for report in reports:
            wg_url = f"{AR6_URL}{report}/"
            print(f"report: {report}")
            for chap in chapters:
                print(f"chapter: {chap}")
                outdir = Path(SC_TEST_DIR, report, chap)
                IPCC.download_save_chapter(report, chap, wg_url,outdir=SC_TEST_DIR, sleep=1)
                raw_outfile = Path(outdir, f"{GATSBY_RAW}.html")
                FileLib.assert_exist_size(raw_outfile, minsize=20000, abort=False)

                gatsby_file = Path(outdir, f"{GATSBY}.html")
                html_elem = web_publisher.remove_unnecessary_markup(gatsby_file)
                body = HtmlLib.get_body(html_elem)
                elems = body.xpath(".//*")
                if len(elems) < 2:
                    # no significant content
                    continue
                de_gatsby_file = Path(outdir, f"{DE_GATSBY}.html")
                HtmlLib.write_html_file(html_elem, outfile=de_gatsby_file, debug=True)

                html_ids_file, idfile, parafile = web_publisher.add_ids(de_gatsby_file, outdir, assert_exist=True, min_id_sizs=10, min_para_size=10)


    def test_cmdline_download_wg_reports(selfself):
        """downal;od WG reports
        output in petermr/semanticClimate
        """
        PyAMI().run_command(["IPCC", "--help"])

        args = [
            "IPCC",
            "--input", f"{AR6_URL}{IP_WG1}/",
            "--outdir", f"{SC_TEST_DIR}/{IP_WG1}",
            "--informat", GATSBY,
            "--chapter", "SPM", "TS",
            "--report", "wg1", "srocc",
            "--operation", IPCCArgs.DOWNLOAD,
            "--kwords", "chapter:chapter", # for test
            "--debug",
        ]

        PyAMI().run_command(args)

    def test_cmdline_search(selfself):
        """
        search reports with keywords
        """
        args = [
            "IPCC",
            "--indir", f"{SC_TEST_DIR}",
            "--outdir", f"{SC_TEST_DIR}/{IP_WG1}",
            "--chapter", "Chapter*",
            "--report", "wg1", "srocc",
            "--query", "birds", "methane",
            "--operation", IPCCArgs.SEARCH,
            "--debug",
        ]

        PyAMI().run_command(args)

    def test_find_ids_markup_dict_single_document_IMPORTANT_2023_01_01(self):

        """TODO generate ids of section tags"""
        """
        looks for strings , especially with IDs ,
        single

        takes simple HTML element and marks it with the MARKUP_DICT
        div
            span
        and splits the span with a regex, annotating the results
        adds classes
        tackles most of functionality

        """
        """output_id of form DEC_1_CMA_3__VII__78__b"""
        """output_id of form RES_1_CMA_3__VII__78__b__iv"""
        """INPUT is HTML"""
        """WORKS - outputs marked up sections in files"""
        # regex = "[Dd]ecisions? \s*\d+/(CMA|CP)\.\d+"  # searches for strings of form fo, foo, for etc
        dict_name = "sections"

        html_infile = self._normalized_test_file()
        input_dir = html_infile.parent

        html_outdir = Path(Resources.TEMP_DIR, "unfccc", "html")
        outfile = Path(html_outdir, "1_4_CMA_3", f"split.{dict_name}.html")
        markup_dict = MARKUP_DICT
        html_elem = SpanMarker.markup_file_with_markup_dict(
            input_dir, html_infile, html_outdir=html_outdir, dict_name=dict_name, outfile=outfile,
            markup_dict=markup_dict, debug=True)
        assert outfile.exists()
        assert len(HtmlLib.get_body(html_elem).xpath("div")) > 0

    @unittest.skip("obsolete approach to splitting files. TODO needs mending")
    def test_split_into_files_at_id_single_IMPORTANT(self):

        dict_name = "sections"
        input_dir = Path(UNFCCC_TEMP_DOC_DIR, "CMA_3")
        infile = Path(input_dir, "1_CMA_3_section", f"normalized.{dict_name}.html")

        splitter = "./span[@class='Decision']"
        output_dir = input_dir
        SpanMarker.presplit_by_regex_into_sections(infile, output_dir, splitter=splitter, debug=True)

    @unittest.skip("until we fix the previous")
    def test_split_into_files_at_id_multiple_IMPORTANT(self):
        """Splits files at Decisions for all sessions"""
        """requires previous test to have been run"""

        dict_name = "sections"
        splitter = "./span[@class='Decision']/a/@href"
        MAXFILE = 3

        top_dir = Path(UNFCCC_DIR, "unfcccdocuments1")
        files = FileLib.posix_glob(str(top_dir) + "/*/*/normalized.html")
        assert len(files) > 0
        for infile in files[:MAXFILE]:
            print(f"infile {infile} ")
            session_dir = Path(infile).parent.parent
            print(f"session {session_dir}")
            output_dir = session_dir
            SpanMarker.presplit_by_regex_into_sections(infile, output_dir, splitter=splitter)

    def test_make_nested_divs(self):
        """IMPORTANT not finished"""
        """initial div files are 'flat' - all divs are siblings, Use parents in markup_dict to assemble
        """
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1", "CMA_3")
        infile = Path(input_dir, "1_4_CMA_3_section", f"normalized.sections.html")
        assert str(infile).endswith(
            "test/resources/unfccc/unfcccdocuments1/CMA_3/1_4_CMA_3_section/normalized.sections.html")
        span_marker = SpanMarker(markup_dict=MARKUP_DICT)
        span_marker.parse_html(infile)
        span_marker.move_implicit_children_to_parents(span_marker.inhtml)
        outfile = str(infile).replace("sections", "nested")
        HtmlLib.write_html_file(span_marker.inhtml, outfile, debug=True)

    @unittest.skip("not sure this is useful")
    def test_find_unfccc_decisions_multiple_documents(self):
        """
        looks for strings such as decision 20/CMA.3:
        over a complete recursive directory

        takes simple HTML element:
        """

        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1")
        pdf_glob = "/*C*/*.pdf"
        # pdf_glob = "/CMA*/*.pdf"
        pdf_files = FileLib.posix_glob(str(input_dir) + pdf_glob)[:MAXPDF]
        assert len(pdf_files) > 0

        for pdf_infile in pdf_files[:999]:
            html_elem = HtmlGenerator.read_pdf_convert_to_html("foo", pdf_infile,
                                                               section_regexes="")  # section_regexes forces styles
            stem = Path(pdf_infile).stem
            HtmlLib.write_html_file(html_elem, Path(UNFCCC_TEMP_DIR, "html", stem, f"{stem}.raw.html"), debug=True)
            # html_infile = Path(input_dir, "1_CMA_3_section target.html")
            # SpanMarker.parse_unfccc_doc(html_infile, debug=True)

    @unittest.skip("obsolete splitting approach")
    def test_presplit_then_split_on_decisions_single_file(self):
        span_marker = SpanMarker()
        topdir = Path(UNFCCC_TEMP_DIR, "html", "1_4_CMA_3", "unfcccdocuments1", "CMA_3")
        span_marker.infile = Path(topdir, "1_4_CMA_3", "raw.html")
        assert span_marker.infile.exists(), f"{span_marker.infile} should exist"
        outhtml = span_marker.parse_html(
            splitter_re="Decision\\s+(?P<decision>\\d+)/(?P<type>CMA|CP|CMP)\\.(?P<session>\\d+)\\s*")
        presplit_file = Path(UNFCCC_TEMP_DIR, "html", "1_4_CMA_3", "presplit.html")
        # this contains the sections
        # now split

        HtmlLib.write_html_file(outhtml, presplit_file, debug=True)
        # assertions
        topdivs = HtmlLib.get_body(outhtml).xpath("div")
        assert len(topdivs) == 1
        split_divs = topdivs[0].xpath("div")
        assert len(split_divs) == 5
        for div in split_divs:
            assert div.get('class') == 'section'

        # now split it
        SpanMarker.split_presplit_into_files(presplit_file, outdir=topdir, outstem="split")

    @unittest.skip("maybe obsolete")
    def test_split_infcc_on_decisions_multiple_file_not_finished(self):
        span_marker = SpanMarker()
        html_files = FileLib.posix_glob(str(Path(UNFCCC_TEMP_DIR, "html/*/*.raw.html")))
        decision = "dummy_decis"
        type = "dummy_type"
        session = "dummy_session"
        for html_file in html_files:
            print(f"html file {html_file}")
            span_marker.infile = str(html_file)
            span_marker.parse_html(
                splitter_re="Decision\\s+(?P<decision>\\d+)/(?P<type>CMA|CP|CMP)\\.(?P<session>\\d+)\\s*"
                # ,split_files=f"{decision}_{type}_{session}"
            )
            if str(span_marker.infile).endswith(".decis.html"):
                continue
            outfile = span_marker.infile.replace(".raw.html", ".decis.html")
            HtmlLib.write_html_file(span_marker.inhtml, outfile, debug=True)

    @unittest.skip("needs mending")
    def test_pipeline(self):
        """
        sequential operations
        input set of PDFs , -> raw.html -> id.html
        """

        print("lacking markup_dict")
        return
        # input dir of raw (unsplit PDFs) . Either single decisions or concatenated ones
        indir = Path(UNFCCC_DIR, "unfcccdocuments1")

        subdirs = FileLib.posix_glob(str(indir) + "/" + "C*" + "/")  # docs of form <UNFCCC_DIR>/C*/

        assert len(subdirs) == 12  # CMA_1 ... CMA_2... CP_27
        pdf_list = FileLib.posix_glob(subdirs[0] + "/" + "*.pdf")  # only CMA_1 to start with
        assert len(pdf_list) == 4
        # contains 4 PDFs as beloe
        skip = True
        if not skip:
            # TODO use symbolic top directory
            unittest.TestCase().assertListEqual(sorted(pdf_list), [
                '/Users/pm286/workspace/pyamihtml_top/test/resources/unfccc/unfcccdocuments1/CMA_1/13_20_CMA_1.pdf',
                '/Users/pm286/workspace/pyamihtml_top/test/resources/unfccc/unfcccdocuments1/CMA_1/1_CMA_1.pdf',
                '/Users/pm286/workspace/pyamihtml_top/test/resources/unfccc/unfcccdocuments1/CMA_1/2_CMA_1.pdf',
                '/Users/pm286/workspace/pyamihtml_top/test/resources/unfccc/unfcccdocuments1/CMA_1/3_12_CMA_1.pdf'
            ])

        # class for processing SpanMarker documents
        span_marker = SpanMarker(regex=DECISION_SESS_RE)

        span_marker.indir = '/Users/pm286/workspace/pyamihtml_top/test/resources/unfccc/unfcccdocuments1'  # inout dir
        span_marker.outdir = Path(Resources.TEMP_DIR, "unfcccOUT")
        print(f"output to dir: {span_marker.outdir}")
        span_marker.outfile = "links.csv"  # probably in wrong place
        # convert to raw HTML
        span_marker.read_and_process_pdfs(pdf_list)
        span_marker.write_links("links.csv")  # currently no-op
        span_marker.analyse_after_match_NOOP()

    """NYI"""

    @unittest.skip("NYI")
    def test_add_ids_and_aplit(self):
        html_file = str(Path(UNFCCC_TEMP_DIR, "html/1_4_CMA_3/1_4_CMA_3.raw.html"))
        html = lxml.etree.parse(html_file)
        assert len(html.xpath("//*")) > 3000

    def test_explicit_conversion_pipeline_IMPORTANT_DEFINITIVE(self):
        """reads PDF and sequentially applies transformation to generate increasingly semantic HTML
        define output structure
        1 ) read a PDF with several concatenated Decisions and convert to raw html incluing paragraph-like divs => raw.html
           a) clip / extract headers and footers
           b) footnotes
        2 ) extract styles into head (one style per div)  combined
        3 ) normalize styles syntactically => normalized.html (syntactic styles)
        4 ) tag divs by style and content
        5 ) split major sections into separate HTML files (CMA1_4 -> CMA1, CMA2 ...)
        6 ) obsolete
        7 ) assemble hierarchical documents NYI
        8 ) search for substrings in spans and link to (a) dictionaries (b) other reports
        9 ) add hyperlinks to substrings
        10 ) create (a) manifest (b) reading order (c) ToC from HTML

        """
        # skip = {"step1"}
        in_dir, session_dir, top_out_dir = self._make_top_in_and_out_and_session()
        # sub_session_list = ["1_4_CMA_3", "5_CMA_3", "6_24_CMA_3"]

        # in_sub_dir = Path(in_dir, session_dir)
        # out_sub_dir = Path(top_out_dir, session_dir)
        force_make_pdf = True  # overrides the "make"
        # file_splitter = "span[@class='Decision']"  # TODO move to dictionary
        # targets = ["decision", "paris", "article", "temperature"]
        # debug = True

        UNFCCC.run_pipeline_on_unfccc_session(
            in_dir,
            session_dir,
            top_out_dir=top_out_dir
        )

    def _make_top_in_and_out_and_session(self, in_top=UNFCCC_DIR, out_top=UNFCCC_TEMP_DIR, sub_top="unfcccdocuments1",
                                         session_dir="CMA_3"):
        in_dir = Path(in_top, sub_top)
        top_out_dir = Path(out_top, sub_top)
        return in_dir, session_dir, top_out_dir

    @unittest.skipUnless(AmiAnyTest.run_long(), "run occasionally")
    def test_explicit_conversion_pipeline_IMPORTANT_CORPUS(self):
        """reads a corpus of 12 sessions and generates split.html for each
        See test_explicit_conversion_pipeline_IMPORTANT_DEFINITIVE(self): which is run for each session document
        """
        sub_top = "unfcccdocuments1"
        in_dir = Path(UNFCCC_DIR, sub_top)
        top_out_dir = Path(UNFCCC_TEMP_DIR, sub_top)

        session_files = FileLib.posix_glob(str(in_dir) + "/*")
        session_dirs = [d for d in session_files if Path(d).is_dir()]
        print(f">session_dirs {session_dirs}")
        assert len(session_dirs) >= 12

        maxsession = 5  # otyherwise runs for ever
        for session_dir in session_dirs[:maxsession]:
            UNFCCC.run_pipeline_on_unfccc_session(
                in_dir,
                session_dir,
                top_out_dir=top_out_dir
            )

    def test_create_decision_hyperlink_table(self):
        """creates table of hyperlinks from inline markuo to decisions
        """
        sub_top = "unfcccdocuments1"
        in_dir = Path(UNFCCC_TEMP_DIR, sub_top)
        in_sub_dir = Path(in_dir, "CMA_1")
        insub_sub_dir = Path(in_sub_dir, "Decision_4_CMA_1")
        marked_file = Path(insub_sub_dir, "marked.html")
        marked_elem = HtmlLib.parse_html(marked_file)
        a_elems = UNFCCC.extract_hyperlinks_to_decisions(marked_file)
        assert len(a_elems) > 12

    def test_extract_decision_hyperlinks_from_CORPUS(self):
        """iterates over all marked.html and extracts hyperlinks to Decisions
        """
        sub_top = "unfcccdocuments1"
        in_dir = Path(UNFCCC_TEMP_DIR, sub_top)
        outcsv = Path(in_dir, "decision_links.csv")
        outcsv_wt = Path(in_dir, "decision_links_wt.csv")
        UNFCCC.create_decision_table(in_dir, outcsv, outcsv_wt=None)

        print(f"wrote csv {outcsv}")

    def test_OBOE_error_for_split_to_marked(self):
        """converting a list of split.html to marked.html loses the last element
        """

        session = "CP_21"
        session = "CP_20"

        # infile = Path(UNFCCC_DIR, "unfcccdocuments1", session, "1_CP_21.pdf")
        sub_top = "unfcccdocuments1"
        in_dir = Path(UNFCCC_DIR, sub_top)

        # instem_list = ["1_CP_21", "2_13_CP_21"]
        instem_list = ["1_CP_20", "2_12_CP_20"]

        in_sub_dir = Path(in_dir, session)
        top_out_dir = Path(UNFCCC_TEMP_DIR, sub_top)
        out_sub_dir = Path(top_out_dir, session)
        skip_assert = True
        file_splitter = "span[@class='Decision']"  # TODO move to dictionary
        targets = ["decision", "paris"]

        for instem in instem_list:
            HtmlPipeline.stateless_pipeline(
                file_splitter=file_splitter, in_dir=in_dir, in_sub_dir=in_sub_dir, instem=instem,
                out_sub_dir=out_sub_dir,
                # skip_assert=skip_assert,
                top_out_dir=top_out_dir,
                directory_maker=UNFCCC, markup_dict=MARKUP_DICT, inline_dict=INLINE_DICT, targets=targets)
        decision = "Decision_1_CP_20"
        split_file = Path(out_sub_dir, decision, "split.html")
        assert split_file.exists()
        marked_file = Path(out_sub_dir, decision, "marked.html")
        assert marked_file.exists()

    def test_subcommands_simple(self):

        # run args
        PyAMI().run_command(
            ['UNFCCC', '--help'])

    @unittest.skipUnless(AmiAnyTest.run_long(), "run occasionally")
    def test_subcommands_long(self):

        in_dir, session_dir, top_out_dir = self._make_top_in_and_out_and_session()
        PyAMI().run_command(
            ['UNFCCC', '--indir', str(in_dir), '--outdir', str(top_out_dir), '--session', session_dir, '--operation',
             UNFCCCArgs.PIPELINE])


class UNMiscTest(AmiAnyTest):
    """
    May really belone in PDFPlumber tests
    """

    def test_pdfplumber_singlecol_create_spans_with_CSSStyles(self):
        """
        creates AmiPDFPlumber and reads single-column pdf and debugs
        """
        input_pdf = Path(Resources.TEST_IPCC_LONGER_REPORT, "fulltext.pdf")
        output_page_dir = Path(AmiAnyTest.TEMP_DIR, "html", "ipcc", "LongerReport", "pages")
        # page_json_dir = output_page_dir
        page_json_dir = None
        output_page_dir.mkdir(exist_ok=True, parents=True)
        ami_pdfplumber = AmiPDFPlumber()
        HtmlGenerator.create_html_pages(
            ami_pdfplumber, input_pdf=input_pdf, outdir=output_page_dir, page_json_dir=page_json_dir,
            pages=[1, 2, 3, 4, 5, 6, 7])
