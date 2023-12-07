import csv
import glob
import os
import re
from pathlib import Path

import lxml
import unittest

from pyamihtml.ami_html import HtmlStyle
from pyamihtml.ami_integrate import HtmlGenerator
from pyamihtml.ami_pdf import AmiPDFPlumber, AmiPlumberJson
# from pyamihtml. import SpanMarker
from pyamihtml.html_marker import SpanMarker
from pyamihtml.util import EnhancedRegex
from pyamihtml.xml_lib import HtmlLib
from test.resources import Resources
from test.test_all import AmiAnyTest
from pyamihtml.un import DECISION_SESS_RE, MARKUP_DICT, INLINE_DICT, UNFCCC

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
        NOT YET WORKING
        * reads MAXPDF unfccc reports in PDF,
        * transdlates to HTML,
        * adds semantic indexing for paragraphs
        * extracts targets from running text (NYI)
        * builds csv table (NYI)
        which can be fed into pyvis to create a knowledge graph
        """
        """TODO needs markup_dict"""
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments")
        pdf_list = glob.glob(f"{input_dir}/*.pdf")[:MAXPDF]


        span_marker = SpanMarker()
        span_marker.indir = input_dir
        span_marker.outdir = Path(Resources.TEMP_DIR, "unfcccOUT")
        span_marker.outfile = "links.csv"
        # span_marker.markup_dict = MARKUP_DICT
        span_marker.markup_dict = INLINE_DICT
        span_marker.read_and_process_pdfs(pdf_list)
        span_marker.analyse_after_match_NOOP()

    def test_read_unfccc_everything_MAINSTREAM(self):
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
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1")
        pdf_list = glob.glob(f"{input_dir}/*C*/*.pdf")[:MAXPDF] # select CMA/CMP/CP
        outcsv = "links.csv"
        outdir = Path(Resources.TEMP_DIR, "unfcccOUT")
        outhtmldir = str(Path(outdir, "newhtml"))
        markup_dict = MARKUP_DICT

        span_marker = SpanMarker(regex=DECISION_SESS_RE)
        span_marker.run_pipeline(input_dir=input_dir,
              outcsv=outcsv,
              outdir=outdir,
              pdf_list = pdf_list,
              markup_dict = markup_dict,
              outhtml=outhtmldir
              )


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
        pdfs = glob.glob(str(input_dir) + "/*C*/*.pdf")[:MAXPDF]
        assert MAXPDF >= len(pdfs) > 0
        for pdf in pdfs:
            print(f"parsing {pdf}")
            html_elem = HtmlGenerator.convert_to_html("foo", pdf)

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
            assert len (styles) > 5
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


    def test_find_unfccc_decisions_markup_regex_single_document_IMPORTANT(self):
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

        """INPUT is HTML"""
        regex = "[Dd]ecisions? \s*\d+/(CMA|CP)\.\d+"  # searches for strings of form fo, foo, for etc
        """ example: accordance with decision 9/CMA.1 ahead """
        regex = "[Dd]ecisions?\\s+(?P<decision>\\d+)/(?P<type>CMA|CP|CMP)\\.(?P<session>\\d+)"
        enhanced_re = EnhancedRegex(regex=regex)

        input_dir = Path(UNFCCC_DIR, "unfcccdocuments")
        html_infile = Path(input_dir, "1_CMA_3_section", "normalized.html") # not marked
        html_outdir = Path(Resources.TEMP_DIR, "unfccc", "html")
        span_marker = SpanMarker(regex=regex)
        outfile = Path(input_dir, "1_CMA_3_section", "normalized.marked.html")
        if outfile.exists():
            outfile.unlink()
        assert not outfile.exists()
        span_marker.split_spans_in_html(html_infile=html_infile, debug=True, regex=regex)
        print(f"marked sections {outfile}")
        """.../pyamihtml_top/test/resources/unfccc/unfcccdocuments/1_CMA_3_section/normalized.marked.html
"""
        assert outfile.exists()

    def test_inline_dict_IMPORTANT(self):
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments")
        html_infile = Path(input_dir, "1_CMA_3_section", "normalized.html") # not marked
        html_outdir = Path(Resources.TEMP_DIR, "unfccc", "html")
        span_marker = SpanMarker(markup_dict=INLINE_DICT)
        outfile = Path(input_dir, "1_CMA_3_section", "normalized.marked.html")
        if outfile.exists():
            outfile.unlink()
        assert not outfile.exists()
        html_elem = lxml.etree.parse(str(html_infile))
        span_marker.markup_html_element_with_markup_dict(
            html_elem,
            input_dir=input_dir,
            html_outdir=html_outdir,
            dict_name="dummy_dict",
            html_out=outfile,
            debug=True
        )



    def test_find_ids_markup_dict_single_document_IMPORTANT_2023_01_01(self):
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
        regex = "[Dd]ecisions? \s*\d+/(CMA|CP)\.\d+"  # searches for strings of form fo, foo, for etc
        dict_name = "sections"

        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1", "CMA_3")
        html_infile = Path(input_dir, "1_4_CMA_3_section", "normalized.html")  # not marked
        html_outdir = Path(Resources.TEMP_DIR, "unfccc", "html")
        outfile = Path(input_dir, "1_4_CMA_3_section", f"normalized.{dict_name}.html")
        markup_dict = MARKUP_DICT
        SpanMarker.markup_file_with_markup_dict(input_dir, html_infile, html_outdir=html_outdir, dict_name=dict_name, outfile=outfile, markup_dict=markup_dict)

    def test_split_into_files_at_id_single_IMPORTANT(self):
        """Splits files at Decisions"""
        """requires previous test to have been run"""

        dict_name = "sections"
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1", "CMA_3")
        infile = Path(input_dir, "1_4_CMA_3_section", f"normalized.{dict_name}.html")
        SpanMarker.split_by_class_into_files(infile, input_dir, splitter="./span[@class='Decision']/a/@href")


    def test_split_into_files_at_id_multiple_IMPORTANT(self):
        """Splits files at Decisions for all sessions"""
        """requires previous test to have been run"""

        dict_name = "sections"
        splitter = "./span[@class='Decision']/a/@href"
        MAXFILE = 3

        top_dir = Path(UNFCCC_DIR, "unfcccdocuments1")
        files = glob.glob(str(top_dir) + "/*/*/normalized.html")
        assert len(files) > 0
        for infile in files[:MAXFILE]:
            print(f"infile {infile} ")
            session_dir = Path(infile).parent.parent
            print(f"session {session_dir}")
            input_dir = session_dir
            SpanMarker.split_by_class_into_files(infile, input_dir, splitter=splitter)

    def test_make_nested_divs(self):
        """initial div files are 'flat' - all divs are siblings, Use parents in markup_dict to assemble
        """
        input_dir = Path(UNFCCC_DIR, "unfcccdocuments1", "CMA_3")
        infile = Path(input_dir, "1_4_CMA_3_section", f"normalized.sections.html")
        assert str(infile).endswith("test/resources/unfccc/unfcccdocuments1/CMA_3/1_4_CMA_3_section/normalized.sections.html")
        span_marker = SpanMarker(markup_dict=MARKUP_DICT)
        span_marker.infile = infile
        span_marker.move_implicit_children_to_parents()
        outfile = str(infile).replace("sections", "nested")
        HtmlLib.write_html_file(span_marker.html_elem, outfile, debug=True)


    @unittest.skip("not sure this is useful")
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
            # SpanMarker.parse_unfccc_doc(html_infile, debug=True)

    @unittest.skip("maybe obsolete")
    def test_split_infcc_on_decisions_single_file(self):
        span_marker = SpanMarker()
        span_marker.infile = Path(UNFCCC_TEMP_DIR, "html", "1_4_CMA_3", "1_4_CMA_3.raw.html")
        assert span_marker.infile.exists()
        span_marker.parse_html(splitter_re="Decision\s+(?P<decision>\d+)/(?P<type>CMA|CP|CMP)\.(?P<session>\d+)\s*"
                          # ,id_gen=f"<decision>_<type>_<session>"
                        )
        outfile = Path(UNFCCC_TEMP_DIR, "html", "1_4_CMA_3", "1_4_CMA_3_decis.html")
        HtmlLib.write_html_file(span_marker.inhtml, outfile, debug=True)

    @unittest.skip("maybe obsolete")
    def test_split_infcc_on_decisions_multiple_file_not_finished(self):
        span_marker = SpanMarker()
        html_files = glob.glob(str(Path(UNFCCC_TEMP_DIR, "html/*/*.raw.html")))
        decision = "dummy_decis"
        type = "dummy_type"
        session = "dummy_session"
        for html_file in html_files:
            print(f"html file {html_file}")
            span_marker.infile = str(html_file)
            span_marker.parse_html(splitter_re="Decision\s+(?P<decision>\d+)/(?P<type>CMA|CP|CMP)\.(?P<session>\d+)\s*"
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
        from pyamihtml.un import DECISION_SESS_RE

        print("lacking markup_dict")
        return
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


        # class for processing SpanMarker documents
        span_marker = SpanMarker(regex=DECISION_SESS_RE)

        span_marker.indir = '/Users/pm286/workspace/pyamihtml_top/test/resources/unfccc/unfcccdocuments1' # inout dir
        span_marker.outdir = Path(Resources.TEMP_DIR, "unfcccOUT")
        print(f"output to dir: {span_marker.outdir}")
        span_marker.outfile = "links.csv" # probably in wrong place
        # convert to raw HTML
        span_marker.read_and_process_pdfs(pdf_list)
        span_marker.write_links("links.csv") # currently no-op
        span_marker.analyse_after_match_NOOP()


    """NYI"""
    @unittest.skip("NYI")
    def test_add_ids_and_aplit(self):
        html_file = str(Path(UNFCCC_TEMP_DIR, "html/1_4_CMA_3/1_4_CMA_3.raw.html"))
        html = lxml.etree.parse(html_file)
        assert len(html.xpath("//*")) > 3000


    def test_explicit_conversion_pipeline_IMPORTANT(self):
        """reads PDF and sequentially applies transformation to generate increasingly semantic HTML
        define output structure
        1 ) read a PDF with several concatenated Decisions and convert to raw html incluing paragraph-like divs => raw.html
        2 ) extract styles into head (one style per div)  combined
        3 ) normalize styles syntactically => normalized.html
        4 ) tag sections by style and content
        5 ) split major sections into separate HTML files (CMA1_4 -> CMA1, CMA2 ...)
        6 ) markup sections with structural tags (para, subpara, etc.)
        7 ) assemble hierarchical documents
        8 ) search for substrings in spans and link to dictionaries
        9 ) add hyperlinks to substrings

        """
        sub_top = "unfcccdocuments1"
        in_dir = Path(UNFCCC_DIR, sub_top)
        in_sub_dir = Path(in_dir, "CMA_3")
        top_out_dir = Path(UNFCCC_TEMP_DIR, sub_top)
# STEP 1
        # in "/Users/pm286/workspace/pyamihtml_top/test/resources/unfccc/unfcccdocuments1/CMA_3/1_4_CMA_3.pdf
        # out "/Users/pm286/workspace/pyamihtml_top/temp/unfcccOUT/CMA_3/1_4_CMA_3/raw.html"

        instem = "1_4_CMA_3"
        pdf_in = Path(in_sub_dir, f"{instem}.pdf")
        print(f"parsing {pdf_in}")
        html_elem = HtmlGenerator.convert_to_html("foo", pdf_in)

        outsubsubdir, outfile = UNFCCC.create_initial_directories(
            in_sub_dir, pdf_in, top_out_dir, out_stem="raw", out_suffix="html")

        HtmlLib.write_html_file(html_elem, outfile=outfile, debug=True)
        assert Path(outfile).exists()

# STEP2

        """
may include generating styles1.html in ami_html.py
    def extract_styles_and_normalize_classrefs(cls, html_elem, outdir=None):
        if outdir:
            HtmlLib.write_html_file(html_elem, Path(outdir, "styles1.html"), debug=True)

        """
        """
may include generatinng normalized.html in ami_html

    @classmethod
    def normalize_head_styles(cls, elem, italic_bold=True, outdir=None):
        creates multidict fot head styles
        :param elem: document to analyse
        :return: dict of classref_sets indexed by style strings

        e.g. item {font-family: TimesNewRomanPSMT; font-size: 6px;}: ['.s17', '.s19', '.s21', '.s27', '.s5', '.s7']
        
        style_to_classref_set = defaultdict(set)
        head_styles = HtmlStyle.get_head_styles(elem)
        # we use one classref - style per HTML style
        for html_style in head_styles:
            # consists of classref snd style_string
            classref, style_s = cls.extract_classref_and_cssstring_from_html_style(html_style)
            style_value = style_s
            if italic_bold:
                new_css_s = AmiFont.create_font_edited_style_from_css_style_object(style_s)
                css_style = CSSStyle.create_css_style_from_css_string(new_css_s)
                if css_style is not None:
                    css_style.extract_bold_italic_from_font_family()
                    style_value = css_style.get_css_value(wrap_with_curly=True)
                    HtmlStyle.replace_curly(html_style, style_value)
            html_style.attrib[CLASSREF] = classref
            style_to_classref_set[style_value].add(classref)
        if outdir:
            HtmlLib.write_html_file(elem, Path(outdir, "normalized.html"))
        return style_to_classref_set

        """
        html_elem = lxml.etree.parse(str(outfile))
        HtmlStyle.extract_styles_and_normalize_classrefs(html_elem, font_styles=True) # TODO has minor bugs in joinig spans
        outfile_normalized = Path(outfile.parent, "normalized.html")
        HtmlLib.write_html_file(html_elem, outfile_normalized, debug=True)
        assert outfile_normalized.exists()


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

