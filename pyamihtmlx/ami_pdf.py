import argparse
import logging
import re
import sys
import textwrap
import traceback
from pathlib import Path

import lxml

from pyamihtmlx.ami_html import A_HREF, H_A, H_SPAN
from pyamihtmlx.ami_pdf_libs import AmiPage, PDFParser, DEBUG_OPTIONS
from pyamihtmlx.util import AbstractArgs, AmiArgParser, Util, AmiLogger

INDIR = "indir"
INFILE = "infile"
INFORM = "inform"
INPATH = "inpath"
INSTEM = "instem"
OFFSET = "offset"
OUTDIR = "outdir"
OUTFORM = "outform"
OUTPATH = "outpath"
OUTSTEM = "outstem"
ALL_PAGES = ['1_9999999']
MAXPAGE = "maxpage"

PAGES = "pages"
PDF2HTML = "pdf2html"

# ANNOTS = "annots"
# CURVES = "curves"
# HYPERLINKS = "hyperlinks"
# IMAGES = "images"
# LINES = "lines"
# PTS = 'pts'
# RECTS = "rects"
# TABLES = "tables"
# TEXTS = "texts"
# WORDS = "words"
#
# DEFAULT_CONVERT = "html"
# DEBUG_OPTIONS = [WORDS, LINES, RECTS, CURVES, IMAGES, TABLES, HYPERLINKS, TEXTS, ANNOTS]
# DEBUG_ALL = "debug_all"

MAX_MAXPAGE = 9999999
CONVERT = "convert"
FLOW = "flow"
FOOTER = "footer"
HEADER = "header"

DEFAULT_CONVERT = "html"
DEFAULT_MAXPAGES = 100

logger = AmiLogger.create_named_logger(__file__)


class PDFArgs(AbstractArgs):
    """
    Holds argument values for pyamihtmlx PDF commands and runs conversions
    Also holds much of the document data

        self.convert = DEFAULT_CONVERT
        self.html = None

        self.footer = None
        self.header = None

        self.indir = None
        self.inform = 'PDF'
        self.inpath = None
        self.instem = 'fulltext'

        self.maxpage = DEFAULT_MAXPAGES

        self.outdir = None
        self.outform = DEFAULT_CONVERT
        self.outpath = None
        self.outstem = None

        self.pages = None

        self.pdf2html = None
        self.raw_html = None
        self.flow = None
        self.unwanteds = None

    """

    def __init__(self):
        """arg_dict is set to default"""
        super().__init__()
        self.convert = DEFAULT_CONVERT
        self.html = None

        self.footer = None
        self.header = None

        self.indir = None
        self.inform = 'PDF'
        self.inpath = None
        self.instem = 'fulltext'

        self.maxpage = DEFAULT_MAXPAGES

        self.outdir = None
        self.outform = DEFAULT_CONVERT
        self.outpath = None
        self.outstem = None

        self.pages = None

        self.pdf2html = None
        self.raw_html = None
        self.flow = None
        self.unwanteds = None

        self.subparser_arg = "PDF"

    def add_arguments(self):
        """creates adds the arguments for pyami commandline

        """
        if self.parser is None:
            # self.parser = argparse.ArgumentParser(
            #     usage="pyamihtmlx always uses subcommands (DICT,GUI,HTML,PDF,PROJECT)\n e.g. pyamihtmlx PDF --help"
            # )
            self.parser = AmiArgParser(
                usage="pyamihtmlx always uses subcommands (DICT,GUI,HTML,PDF,IPCC,PROJECT)\n e.g. pyamihtmlx PDF --help"
            )

        self.parser.description = textwrap.dedent(
            'PDF tools. \n'
            '----------\n'
            'Typically reads one or more PDF files and converts to HTML\n'
            'can clip parts of page, select page ranges, etc.\n'
            '\nExamples:\n'
            '  * PDF --help\n'
        )
        self.parser.formatter_class = argparse.RawDescriptionHelpFormatter
        # self.parser.add_argument("--convert", type=str, choices=[], help="conversions (NYI)")
        self.parser.add_argument("--debug", type=str, choices=DEBUG_OPTIONS, help="debug these during parsing (NYI)")
        self.parser.add_argument("--flow", type=bool, nargs=1,
                                 help="create flowing HTML, e.g. join lines, pages (heuristics)", default=True)
        self.parser.add_argument("--footer", type=float, nargs=1, help="bottom margin (clip everythimg above)",
                                 default=80)
        self.parser.add_argument("--header", type=float, nargs=1, help="top margin (clip everything below", default=80)
        self.parser.add_argument("--imagedir", type=str, nargs=1, help="output images to imagedir")

        self.parser.add_argument("--indir", type=str, nargs=1, help="input directory (might be calculated from inpath)")
        self.parser.add_argument("--inform", type=str, nargs="+",
                                 help="input formats (might be calculated from inpath)")
        self.parser.add_argument("--inpath", type=str, nargs=1,
                                 help="input file or (NYI) url; might be calculated from dir/stem/form")
        self.parser.add_argument("--infile", type=str, nargs=1, help="input file (synonym for inpath)")
        self.parser.add_argument("--instem", type=str, nargs=1,
                                 help="input stem (e.g. 'fulltext'); maybe calculated from 'inpath`")

        self.parser.add_argument("--maxpage", type=int, nargs=1,
                                 help="maximum number of pages (will be deprecated, use 'pages')",
                                 default=self.arg_dict.get(MAXPAGE))

        self.parser.add_argument("--offset", type=int, nargs=1, help="number of pages before numbers page 1, default=0",
                                 default=0)
        self.parser.add_argument("--outdir", type=str, nargs=1, help="output directory")
        self.parser.add_argument("--outpath", type=str, nargs=1,
                                 help="output path (can be calculated from dir/stem/form)")
        self.parser.add_argument("--outstem", type=str, nargs=1, help="output stem", default="fulltext.flow")
        self.parser.add_argument("--outform", type=str, nargs=1, help="output format ", default="html")

        self.parser.add_argument("--pdf2html", type=str, choices=['pdfminer', 'pdfplumber'], help="convert PDF to html",
                                 default='pdfminer')
        self.parser.add_argument("--pages", type=str, nargs="+",
                                 help="reads '_2 4_6 8 11_' as 1-2, 4-6, 8, 11-end ; all ranges inclusive (not yet debugged)",
                                 default=ALL_PAGES)
        self.parser.add_argument("--resolution", type=int, nargs=1, help="resolution of output images (if imagedir)",
                                 default=400)
        self.parser.add_argument("--template", type=str, nargs=1, help="file to parse specific type of document (NYI)")
        return self.parser

    # class PDFArgs:
    def process_args(self):
        """runs parsed args
        :return:
  --maxpage MAXPAGE     maximum number of pages
  --indir INDIR         input directory
  --infile INFILE [INFILE ...]
                        input file
  --outdir OUTDIR       output directory
  --outform OUTFORM     output format
  --flow FLOW           create flowing HTML (heuristics)
  --images IMAGES       output images
  --resolution RESOLUTION
                        resolution of output images
  --template TEMPLATE   file to parse specific type of document"""

        if self.arg_dict:
            #            logging.warning(f"ARG DICTXX {self.arg_dict}")
            self.read_from_arg_dict()

        if not self.check_input():
            # self.parser.print_help() # self.parser is null
            print("for help, run 'pyamihtmlx PDF -h'")
            return
        self.create_consistent_output_filenames_and_dirs()
        self.calculate_headers_footers()

        newstyle = True
        if newstyle:
            infile = self.arg_dict.get(INFILE)
            inpath = infile if infile is not None else self.arg_dict.get(INPATH)
            maxpage = int(self.arg_dict.get(MAXPAGE))
            outdir = self.arg_dict.get(OUTDIR)
            outpath = self.arg_dict.get(OUTPATH)
            if outdir is None and outpath is not None:
                outdir = outpath.parent
            if outpath is None:
                if outdir is None:
                    raise FileNotFoundError(f"no outdir or outpath given")
                outpath = Path(outdir, "outpath.html")

            style_dict = self.pdf_to_styled_html_CORE(
                inpath=inpath,
                maxpage=maxpage,
                outdir=outdir,
                outpath=outpath
            )
            return

        if self.pdf2html:
            self.create_consistent_output_filenames_and_dirs()
            # range_list = self.create_range_list()
            AmiPage.create_html_pages_pdfplumber(
                bbox=AmiPage.DEFAULT_BBOX,
                input_pdf=self.inpath,
                output_dir=self.outdir,
                output_stem=self.outstem,
                range_list=self.pages
            )

    def check_input(self):
        if not self.inpath:
            print(f"No input file, no action taken")
            return False
            # raise FileNotFoundError(f"input file not given")
        if not Path(self.inpath).exists():
            raise FileNotFoundError(f"input file/path does not exist: ({self.inpath}")
        self.indir = Path(self.inpath).parent
        return True

    def create_consistent_output_filenames_and_dirs(self):
        logging.warning(f" *** ARG_DICT {self.arg_dict}")
        self.arg_dict[OUTSTEM] = Path(f"{self.inpath}").stem
        # self.arg_dict[OUTPATH] = Path(Path(self.inpath).parent, f"{self.arg_dict[OUTSTEM]}.{self.arg_dict[OUTFORM]}")
        if not self.outdir:
            self.outdir = self.arg_dict.get(OUTDIR)
        if not self.outpath:
            self.outpath = self.arg_dict.get(OUTPATH)

        # # if no outdir , create from outpath
        # if not Path(self.outdir).exists():
        #     raise FileNotFoundError(f"output stem not given and cannot be generated")

        if self.outpath and not self.outdir:
            self.outdir = (Path(self.outpath).parent)
        if not self.outdir:
            raise FileNotFoundError("No outdir given")
        Path(self.outdir).mkdir(exist_ok=True, parents=True)
        if not Path(self.outdir).is_dir():
            raise ValueError(f"output dir {self.outdir} is not a directory")
        else:
            logging.debug(f"output dir {self.outdir}")
        return True

    def read_from_arg_dict(self):
        #        logging.warning(f"ARG DICT0 {self.arg_dict}")
        self.flow = self.arg_dict.get(FLOW) is not None

        self.footer = self.arg_dict.get(FOOTER)
        if not self.footer:
            self.footer = 80
        self.header = self.arg_dict.get(HEADER)
        if not self.header:
            self.header = 80

        self.indir = self.arg_dict.get(INDIR)
        self.infile = self.arg_dict.get(INFILE)
        self.inform = self.arg_dict.get(INFORM)
        self.inpath = self.arg_dict.get(INPATH)
        self.inpath = self.infile if self.infile else self.inpath  # infile takes precedence
        self.instem = self.arg_dict.get(INSTEM)

        self.maxpage = self.arg_dict.get(MAXPAGE)
        if not self.maxpage:
            maxpage = MAX_MAXPAGE

        self.offset = self.arg_dict.get(OFFSET)

        self.outdir = self.arg_dict.get(OUTDIR)
        self.outform = self.arg_dict.get(OUTFORM)
        self.outpath = self.arg_dict.get(OUTPATH)
        self.outstem = self.arg_dict.get(OUTSTEM)

        #        logging.warning(f"ARG DICT {self.arg_dict}")
        pages = self.arg_dict.get(PAGES)
        if not pages:
            # create from maxpage
            if self.maxpage:
                pages = [f'1_{self.maxpage}']
        self.pages = PDFArgs.make_page_ranges(pages, offset=self.arg_dict.get(OFFSET))
        logging.info(f"pages {pages}")

        self.pdf2html = self.arg_dict.get(PDF2HTML)

        # self.convert_write(maxpage=maxpage, outdir=outdir, outstem=outstem, fmt=fmt, inpath=inpath, flow=True)

    # class PDFArgs:

    @classmethod
    def create_default_arg_dict(cls):
        """returns a new COPY of the default dictionary"""
        arg_dict = dict()
        arg_dict[CONVERT] = "html"
        arg_dict[FLOW] = True
        arg_dict[FOOTER] = 80
        arg_dict[HEADER] = 80

        arg_dict[INDIR] = None
        arg_dict[INFORM] = None
        arg_dict[INPATH] = None
        arg_dict[INSTEM] = None

        arg_dict[MAXPAGE] = 5

        arg_dict[OUTDIR] = None
        arg_dict[OUTFORM] = "html"
        arg_dict[OUTPATH] = None
        arg_dict[OUTSTEM] = None

        arg_dict[PAGES] = None
        arg_dict[PDF2HTML] = None
        arg_dict[FLOW] = True
        return arg_dict

    # class PDFArgs:

    def calculate_headers_footers(self):
        # header_offset = -50
        self.header = 90
        # page_height = 892
        # page_height_cm = 29.7
        self.footer = 90

    def convert_write(
            self,
            flow=True,
            indir=None,
            inpath=None,
            maxpage=None,
            outform=None,
            outpath=None,
            outstem=None,
            outdir=None,
            pdf2html=None,
            process_args=True,
    ):
        """
        Convenience method to run PDFParser.convert_pdf on self.inpath, self.outform, and self.maxpage
        writes output to self.outpath
        if self.flow runs self.tidy_flow
        :return: outpath
        """
        print(f"flow {flow} indir {indir} inpath {inpath} maxpage {maxpage} outform {outform} \n"
              f"outpath {outpath} outstem {outstem} outdir {outdir} pdf2html {pdf2html} process_args {process_args}")
        print(f"==============CONVERT================")
        # process arguments into a dictionary
        if flow:
            self.arg_dict[FLOW] = flow
        if indir:
            self.arg_dict[INDIR] = indir
        if inpath:
            self.arg_dict[INPATH] = inpath
            self.arg_dict[INFILE] = inpath
        else:
            inpath = self.arg_dict[INPATH]
        if maxpage:
            self.arg_dict[MAXPAGE] = int(maxpage)
        if outdir:
            self.arg_dict[OUTDIR] = outdir
        else:
            outdir = self.arg_dict[OUTDIR]
        if outform:
            self.arg_dict[OUTFORM] = outform

        if outpath:
            self.arg_dict[OUTPATH] = outpath
        else:
            outpath = self.arg_dict[OUTPATH]

        if outstem:
            self.arg_dict[OUTSTEM] = outstem
        if pdf2html:
            self.arg_dict[PDF2HTML] = pdf2html
        # run the argument commands

        if process_args:
            self.process_args()
        if inpath is None:
            raise ValueError("No input path in convert_write()")
        # out_html is tidied
        out_html = self.pdf_to_raw_then_raw_to_tidy(
            pdf_path=inpath,
            flow=flow,
            outdir=outdir,
            outpath=outpath,
        )
        if out_html is None:
            raise ValueError(f" out_html is None")
        if outpath is None:
            print(f"no outpath given")
            return None, None
        outpath1 = str(outpath)
        with Util.open_write_utf8(outpath1) as f:
            f.write(out_html)
            print(f"wrote partially tidied html {outpath}")
        return outpath, out_html

    def pdf_to_raw_then_raw_to_tidy(
            self,
            pdf_path=None,
            flow=True,
            write_raw=True,
            outpath=None,
            outdir=None,
            header=80,
            footer=80,
            maxpage=9999
    ):

        from pyamihtmlx.ami_html import HtmlTidy

        """converts PDF to raw_html and (optionally raw_html to tidy_html
        Uses PDFParser.convert_pdf to create raw_html_element

        raw_html_element is created by pdfplumber and contains Page information
        Example at page break: We think pdfplumber emits "Page 1..." and this can be used for
        finding page-relative coordinates rather than absolute ones

<br><span style="position:absolute; border: gray 1px solid; left:0px; top:6293px; width:595px; height:841px;"></span>
<div style="position:absolute; top:6293px;"><a name="8">Page 8</a></div>
<div style="position:absolute; border: textbox 1px solid; writing-mode:lr-tb; left:72px; top:6330px; width:141px; height:11px;"><span style="font-family: TimesNewRomanPSMT; font-size:11px">Final Government Distribution
<br></span></div><div style="position:absolute; border: textbox 1px solid; writing-mode:lr-tb; left:276px; top:6330px; width:45px; height:11px;"><span style="font-family: TimesNewRomanPSMT; font-size:11px">Chapter 4

    then make HtmlTidy and execute commands to clean
        URGENT

        :return: tidied html
        """
        self.pdf_parser = PDFParser()
        raw_html_element = self.pdf_parser.convert_pdf_CURRENT(
            path=pdf_path,
            # fmt=self.outform,
            maxpages=maxpage)
        page_tops = ['%.2f' % (pt) for pt in self.pdf_parser.page_tops]
        logger.debug(f"page_tops {page_tops}")
        if raw_html_element is None:
            raise ValueError(f"null raw_html in convert_write()")
        if not flow:
            return raw_html_element
        if write_raw:
            if not outpath and not outdir:
                raise FileNotFoundError(f"outpath and outdir are None")
            if outpath and not outdir:
                outdir = Path(Path(outpath).parent)
            if not Path(outdir).exists():
                outdir.mkdir(exist_ok=True, parents=True)
            if not outpath:
                outpath = Path(outdir, "tidied.html")  # bad hardcoding
            with Util.open_write_utf8(Path(outdir, "raw.html")) as f:
                f.write(raw_html_element)
        logger.debug(f"outpath {outpath}")

        html_tidy = HtmlTidy()
        # might need a data transfer object
        html_tidy.page_tops = page_tops
        html_tidy.header = header
        html_tidy.footer = footer
        # html_tidy.unwanteds = self.unwanteds
        html_tidy.outdir = outdir
        out_html_element = html_tidy.tidy_flow(raw_html_element)
        assert len(out_html_element) > 0
        return out_html_element

    # class PDFArgs:

    def markup_parentheses(self, result_elem):
        """iterate over parenthesised fields
        iterates over HTML spans
        NYI
        should be in HTML
        """
        xpath = ".//span"
        spans = result_elem.xpath(xpath)
        for span in spans:
            # self.extract_brackets(span)
            pass

    def extract_brackets(self, span):
        """extract (...) from text, and add hyperlinks for refs, NYI
        (IPCC 2018a)
        (Roy et al. 2018)
        (SpanMarker 2016a, 2021)
        (Bertram et al. 2015; Riahi et al. 2015)
        """
        text = ''.join(span.itertext())
        par = span.getparent()
        # (FooBar& Biff 2012a)
        refregex = r"(" \
                   r"[^\(]*" \
                   r"\(" \
                   r"(" \
                   r"[A-Z][^\)]{1,50}(20\d\d|19\d\d)" \
                   r")" \
                   r"\s*" \
                   r"\)" \
                   r"(.*)" \
                   r")"

        result = re.compile(refregex).search(text)
        if result:
            # print(f"matched: {result.group(1)} {result.group(2)}, {result.group(3)} {result.groups()}")
            elem0 = lxml.etree.SubElement(par, H_SPAN)
            elem0.text = result.group(1)
            for k, v in elem0.attrib.items():
                elem0.attrib[k] = v
            idx = par.index(span)
            span.addnext(elem0)
            current = elem0
            for ref in result.group(2).split(";"):  # e.g. in (Foo and Bar, 2018; Plugh 2020)
                ref = ref.strip()
                if not self.ref_counter[ref]:
                    self.ref_counter[ref] == 0
                self.ref_counter[ref] += 1
                a = lxml.etree.SubElement(par, H_A)
                for k, v in elem0.attrib.items():
                    a.attrib[k] = v
                a.attrib[A_HREF] = "https://github.com/petermr/discussions"
                a.text = "([" + ref + "])"
                current.addnext(a)
                current = a
            elem2 = lxml.etree.SubElement(par, H_SPAN)
            for k, v in elem0.attrib.items():
                elem2.attrib[k] = v
            elem2.text = result.group(3)

            par.remove(span)

            # print(f"par {lxml.etree.tostring(par)}")

    @property
    def module_stem(self):
        """name of module"""
        return Path(__file__).stem

    # def create_range_list(self):
    #     """makes list of ranges from pairs on numbers"""
    #     range_list = range(1,999)
    #     if type(self.pages) is list:
    #         range_list = []
    #         ll = list(map(int, self.pages))
    #         for i in range(0, len(ll), 2):
    #             range_list.append(ll[i:i + 2])
    #     return range_list

    @classmethod
    def make_page_ranges(cls, raw_page_ranges, offset=0):
        """expand pages arg to list of ranges
        typical input _2 4_5 8 9_11 13 16_
        These are *inclusive* so expand to
        range(1,3) range(4,6) range(8,9) range (9,12) range(13,14) range(16-maxint)
        converts raw_pages to page ranges
        uses 1-based pages

        :param raw_page_ranges: page ranges before expansion
        :param offset: number of leading unnumbered pages (when page 1 is not the first)
        :return: the list of page ranges (ranges are absolute numbers
        """
        if not offset:
            offset = 0
        if not type(raw_page_ranges) is list:
            strlist = []
            strlist.append(raw_page_ranges)
        else:
            strlist = raw_page_ranges
        ranges = []
        if strlist == ALL_PAGES:
            strlist = ['1_9999999']
        if strlist:
            logging.warning(f"**** raw pages: {raw_page_ranges}")
            if not hasattr(strlist, "__iter__"):
                logging.error(f"{raw_page_ranges} is not iterable {type(raw_page_ranges)}")
                return
            for chunk in strlist:
                if not chunk == "":
                    chunk0 = chunk
                    try:
                        if chunk.startswith("_"):  # prepend 1
                            chunk = f"{1}{chunk}"
                        if chunk.endswith("_"):  # append Maxint
                            chunk = f"{chunk}{sys.maxsize}"
                        if not "_" in chunk:  # expand n to n_n (inclusive)
                            chunk = f"{chunk}_{chunk}"
                        ints = chunk.split("_")
                        logging.debug(f"ints {ints}")
                        rangex = range(int(ints[0]) + int(offset),
                                       (int(ints[1]) + 1 + int(offset)))  # convert to upper-exclusive
                        logging.info((f"ranges: {rangex}"))
                        ranges.append(rangex)
                    except Exception as e:
                        raise ValueError(f"Cannot parse {chunk0} as int range {e}")
        return ranges

    @classmethod
    def create_pdf_args_for_chapter(cls,
                                    chapter=None,
                                    chapter_dir=None,
                                    chapter_dict=None,
                                    outdir=None,
                                    infile="fulltext.pdf",
                                    unwanteds=None,
                                    ):
        """
        populate args (mainly relevant to chapter-based corpus)
        :param chapter: (in chapter_dir) to process
        :param chapter_dir:
        :param chapter_dict: parameters of chapters (Chapter01: {"pages": 123}} currently only pages
        :param outdir:
        :param infile: PDF file (defalut fulltext.pdf)
        :param unwanteds: sections to omit
        :return: PDFArgs object with populated fields
        """
        # populate arg commands
        pdf_args = PDFArgs()  # also supports commands

        pdf_args.arg_dict[INDIR] = chapter_dir
        assert pdf_args.arg_dict[INDIR].exists(), f"dir does not exist {chapter_dir}"
        inpath = Path(chapter_dir, infile)
        pdf_args.arg_dict[INPATH] = inpath
        assert pdf_args.arg_dict[INPATH].exists(), f"file does not exist {inpath}"
        if chapter_dict is not None:
            print(f"chapter_dict {chapter_dict}")
            maxpage = chapter_dict[chapter]["pages"]
            pdf_args.arg_dict[MAXPAGE] = int(maxpage)
        if outdir is not None:
            outdir.mkdir(exist_ok=True, parents=True)
        pdf_args.arg_dict[OUTDIR] = outdir
        pdf_args.arg_dict[OUTPATH] = Path(outdir, "ipcc_spans.html")
        pdf_args.unwanteds = unwanteds
        print(f"arg_dict {pdf_args.arg_dict}")
        return pdf_args

    def pdf_to_styled_html_CORE(
            self,
            inpath=None,
            maxpage=None,
            outdir=None,
            outpath=None,
    ):
        from pyamihtmlx.ami_html import CSSStyle  # messy
        from pyamihtmlx.ami_html import HtmlStyle

        """
        main routine for converting PDF all the way to tidied styled HTML
        uses a lot of defaults. will be better when we have a converter tool
        :param inpath: input PDF
        :param maxpage: maximum number of pages to convert (starts at 1)
        :param outdir: output directory
        :param outpath1: "final"  html file
        :return: style_dict

        """
        if inpath is None:
            raise ValueError(F"No inpath in pdf_to_styled_html_CORE()")
        if outdir is None:
            raise ValueError(F"No outdir in pdf_to_styled_html_CORE()")
        outpath1 = Path(outdir, "tidied.html")
        outpath, html_str = self.convert_write(
            inpath=inpath,
            outpath=outpath1,
            outdir=outdir,
            maxpage=maxpage,
            process_args=False,
        )
        assert len(html_str.strip()) > 0
        try:
            html_elem = lxml.etree.fromstring(html_str)
        except Exception as e:
            raise Exception(f"***HTML PARSE ERROR {e} in [{html_str[:150]}...] from PDF {inpath} (outpath {outpath1}")
        HtmlStyle.extract_styles_and_normalize_classrefs(html_elem)
        CSSStyle.normalize_styles_in_fonts_in_html_head(html_elem)
        styles = CSSStyle.extract_styles_from_html_head_element(html_elem)
        with open(outpath1, "wb") as f:
            f.write(lxml.etree.tostring(html_elem, encoding="UTF-8"))
        print(f"wrote styled html {outpath1}")
        style_dict = CSSStyle.create_style_dict_from_styles(style_elems=styles)
        return style_dict


def parse_and_process_1(pdf_args):
    """
    Convenience method to run pdf_args
    Runs pdf_args.parse_and_process()
        pdf_args.convert_write()
    :param pdf_args: previously populated args
    """
    try:
        pdf_args.parse_and_process()
        pdf_args.convert_write()
    except Exception as e:
        print(f"traceback: {traceback.format_exc()}")
        print(f"******Cannot run pyami******; see output for errors: {e} ")


def main(argv=None):
    """entry point for PDF conversiom
    typical:
    python -m pyamihtmlx.ami_pdf \
        --inpath /Users/pm286/workspace/pyami/test/resources/ipcc/Chapter06/fulltext.pdf \
        --outdir /Users/pm286/workspace/pyami/temp/pdf/chap6/
        --maxpage 100

    """
    print(f"running PDFArgs main")
    pdf_args = PDFArgs()
    parse_and_process_1(pdf_args)


if __name__ == "__main__":
    main()
else:
    pass
