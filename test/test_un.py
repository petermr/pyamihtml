import csv
import glob
import os
import re
from pathlib import Path

import lxml
import unittest

from pyamihtml.ami_integrate import HtmlGenerator
from pyamihtml.ami_pdf import AmiPDFPlumber, AmiPlumberJson
from pyamihtml.un import UNFCCC
from pyamihtml.util import EnhancedRegex
from pyamihtml.xml_lib import HtmlLib
from test.resources import Resources
from test.test_all import AmiAnyTest

UNFCCC_DIR = Path(Resources.TEST_RESOURCES_DIR, "unfccc")
UNFCCC__TEMP_DIR = Path(Resources.TEMP_DIR, "unfccc")

UNFCCC_DIR = Path(Resources.TEST_RESOURCES_DIR, "unfccc")
UNFCCC_TEMP_DIR = Path(Resources.TEMP_DIR, "unfccc")

MAXPDF = 3
class TestIPCC(AmiAnyTest):
    pass

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
            report_dict = Resources.WG_REPORTS[report_name]
            print(f"\n==================== {report_name} ==================")
            input_pdf = report_dict["input_pdf"]
            if not input_pdf.exists():
                print(f"cannot find {input_pdf}")
                continue
            output_page_dir = report_dict["output_page_dir"]
            print(f"output dir {output_page_dir}")
            output_page_dir.mkdir(exist_ok=True, parents=True)
            ami_pdfplumber = AmiPDFPlumber(param_dict=report_dict)
            HtmlGenerator.create_html_pages(ami_pdfplumber, input_pdf, output_page_dir, debug=True,
                                            outstem="total_pages")


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
        files = glob.glob("*.html")
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

    def test_pdfplumber_json_longer_report_debug(self):
        """creates AmiPDFPlumber and reads pdf and debugs"""
        path = Path(Resources.TEST_IPCC_LONGER_REPORT, "fulltext.pdf")
        ami_pdfplumber = AmiPDFPlumber()
        # pdf_json = ami_pdfplumber.create_parsed_json(path)
        plumber_json = ami_pdfplumber.create_ami_plumber_json(path)
        assert type(plumber_json) is AmiPlumberJson
        metadata_ = plumber_json.pdf_json_dict['metadata']
        print(f"k {(plumber_json.keys), metadata_.keys} \n====Pages====\n"
              # f"{len(plumber_json['pages'])} "
              # f"\n\n page_keys {c['pages'][0].items()}"
              )
        pages = plumber_json.get_ami_json_pages()
        assert len(pages) == 85
        for page in pages:
            ami_pdfplumber.debug_page(page)
        # pprint.pprint(f"c {c}[:20]")



class TestUNFCCC(AmiAnyTest):
    """Tests high level operations relating to UN content (currently UNFCCC and UN/IPCC)
    """

    def test_read_unfccc(self):
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
            ".*decisión (?P<decision>\d+)/CMA\.(?P<cma>\d+), (?P<anex>(anexo)), (?P<capit>(capítulo)) (?P<roman>[IVX]+)\.?(?P<letter>[A-F])?.*")
        texts = html_elem.xpath("//*/text()")
        for text in texts:
            match = re.match(doclink, text)
            if match:
                for (k,v) in match.groupdict().items():
                    print(f"{k, v}", end="")
                print()

    def test_read_unfccc_many(self):
        """
        * reads unfccc reports in PDF,
        * transdlates to HTML,
        * adds semantic indexing for paragraphs
        * extracts targets from running text
        * builds csv table
        which can be fed into pyvis to create a knowledge graph
        """
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments")
        pdf_list = glob.glob(f"{input_dir}/*.pdf")[:MAXPDF]

        unfccc = UNFCCC()
        unfccc.indir = input_dir
        unfccc.outdir = Path(Resources.TEMP_DIR, "unfccc")
        unfccc.outfile = "links.csv"
        unfccc.read_and_process_pdfs(pdf_list)
        unfccc.analyse_after_match()

    def test_read_unfccc_everything_MAINSTREAM(self):
        """
        * reads unfccc reports in PDF,
        * transdlates to HTML,
        * adds semantic indexing for paragraphs
        * extracts targets from running text
        * builds csv table
        which can be fed into pyvis to create a knowledge graph
        (writes outout to wrong dir)
        MAINSTREAM!
        """
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1")
        pdf_list = glob.glob(f"{input_dir}/*C*/*.pdf")[:MAXPDF] # select CMA/CMP/CP

        unfccc = UNFCCC()
        unfccc.indir = input_dir
        unfccc.outdir = Path(Resources.TEMP_DIR, "unfcccOUT")
        unfccc.outfile = "links.csv"
        unfccc.read_and_process_pdfs(pdf_list)
        outhtml = str(Path(unfccc.outdir, "newhtml"))
        unfccc.analyse_after_match(outhtml)

    def test_plot_graph(self):
        """
        Test that pyvis works
        displays the file of links extracted from UNFCCC
        """
        unfccc = UNFCCC()
        unfccc.outcsv = str(Path(UNFCCC_TEMP_DIR, "links.csv"))
        outhtml = str(Path(UNFCCC_TEMP_DIR, "links.html"))
        unfccc.analyse_after_match(outhtml)

    def test_find_unfccc_decisions_many_docs(self):
        """
        as above but many documents
        """
        STYLES = [
            (".class0", [("color", "red;")]),
            (".class1", [("background", "#ccccff;")]),
            (".class2", [("color", "#00cc00;")]),
        ]

        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1")
        pdfs = glob.glob(str(input_dir) + "/*C*/*.pdf")[:MAXPDF]
        print(f"pdfs {len(pdfs)}")
        for pdf in pdfs:
            html = HtmlGenerator.convert_to_html("foo", pdf)

    def test_find_unfccc_decisions_single_document(self):
        """
        looks for strings such as decision 20/CMA.3:
        single

        takes simple HTML element:
        div
            span
        and splits the span with a regex, annotating the results
        adds classes
        tackles most of functionality

        """
        regex = "[Dd]ecisions? \s*\d+/(CMA|CP)\.\d+"  # searches for strings of form fo, foo, for etc
        regex = "[Dd]ecisions?\\s+(?P<decision>\\d+)/(?P<type>CMA|CP|CMP)\\.(?P<session>\\d+)"
        enhanced_re = EnhancedRegex(regex=regex)

        input_dir = Path(UNFCCC_DIR, "unfcccdocuments")
        html_infile = Path(input_dir, "1_CMA_3_section_target.html")
        UNFCCC.parse_unfccc_html_split_spans(html_infile, debug=True, regex=regex)

    def test_find_unfccc_decisions_multiple_documents(self):
        """
        looks for strings such as decision 20/CMA.3:
        over a complete recursive directory

        takes simple HTML element:
        """
        STYLES = [
            (".class0", [("color", "red;")]),
            (".class1", [("background", "#ccccff;")]),
            (".class2", [("color", "#00cc00;")]),
        ]

        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1")
        pdf_glob = "/*C*/*.pdf"
        # pdf_glob = "/CMA*/*.pdf"
        pdf_files = glob.glob(str(input_dir) + pdf_glob)[:MAXPDF]
        assert len(pdf_files) > 0

        for pdf_infile in pdf_files[:999]:
            html_elem = HtmlGenerator.convert_to_html("foo", pdf_infile,
                                                      section_regexes="")  # section_regexes forces styles
            stem = Path(pdf_infile).stem
            HtmlLib.write_html_file(html_elem, Path(UNFCCC_TEMP_DIR, "html", stem, f"{stem}.raw.html"), debug=True)
            # html_infile = Path(input_dir, "1_CMA_3_section target.html")
            # UNFCCC.parse_unfccc_doc(html_infile, debug=True)

    def test_split_infcc_on_decisions_single_file(self):
        unfccc = UNFCCC()
        unfccc.infile = Path(UNFCCC_TEMP_DIR, "html", "1_4_CMA_3", "1_4_CMA_3.raw.html")
        unfccc.parse_html(splitter_re="Decision\s+(?P<decision>\d+)/(?P<type>CMA|CP|CMP)\.(?P<session>\d+)\s*"
                          # ,id_gen=f"<decision>_<type>_<session>"
                        )
        outfile = Path(UNFCCC_TEMP_DIR, "html", "1_4_CMA_3", "1_4_CMA_3_decis.html")
        HtmlLib.write_html_file(unfccc.inhtml, outfile)

    def test_split_infcc_on_decisions_multiple_file_not_finished(self):
        unfccc = UNFCCC()
        html_files = glob.glob(str(Path(UNFCCC_TEMP_DIR, "html/*/*.raw.html")))
        decision = "dummy_decis"
        type = "dummy_type"
        session = "dummy_session"
        for html_file in html_files:
            print(f"html file {html_file}")
            unfccc.infile = str(html_file)
            unfccc.parse_html(splitter_re="Decision\s+(?P<decision>\d+)/(?P<type>CMA|CP|CMP)\.(?P<session>\d+)\s*"
                              # ,split_files=f"{decision}_{type}_{session}"
                            )
            if str(unfccc.infile).endswith(".decis.html"):
                continue
            outfile = unfccc.infile.replace(".raw.html", ".decis.html")
            HtmlLib.write_html_file(unfccc.inhtml, outfile)


    def test_pipeline(self):
        """
        sequential operations
        input set of PDFs , -> raw.html -> id.html
        """
        # input dir of raw (unsplit PDFs) . Either single decisions or concatenated ones
        indir = Path(UNFCCC_DIR, "unfcccdocuments1")

        subdirs = glob.glob(str(indir) + "/" + "C*" + "/") # docs of form <UNFCCC_DIR>/C*/

        assert len(subdirs) == 12 # CMA_1 ... CMA_2... CP_27
        pdf_list = glob.glob(subdirs[0] + "/" + "*.pdf") # only CMA_1 to start with
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


        # class for processing UNFCCC documents
        unfccc = UNFCCC()
        unfccc.indir = '/Users/pm286/workspace/pyamihtml_top/test/resources/unfccc/unfcccdocuments1' # inout dir
        unfccc.outdir = Path(Resources.TEMP_DIR, "unfcccOUT")
        print(f"output to dir: {unfccc.outdir}")
        unfccc.outfile = "links.csv" # probably in wrong place
        # convert to raw HTML
        unfccc.read_and_process_pdfs(pdf_list)
        unfccc.write_links("links.csv") # currently no-op
        unfccc.analyse_after_match()


    """NYI"""
    def test_add_ids_and_aplit(self):
        html_file = str(Path(UNFCCC_TEMP_DIR, "html/1_4_CMA_3/1_4_CMA_3.raw.html"))
        html = lxml.etree.parse(html_file)
        assert len(html.xpath("//*")) > 3000






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
        output_page_dir.mkdir(exist_ok=True, parents=True)
        ami_pdfplumber = AmiPDFPlumber()
        HtmlGenerator.create_html_pages(ami_pdfplumber, input_pdf, output_page_dir, pages=[1, 2, 3, 4, 5, 6, 7])

