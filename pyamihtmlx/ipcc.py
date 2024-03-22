import argparse
import copy
import csv
import glob
import logging
import re
import textwrap
from abc import ABC, abstractmethod
from collections import defaultdict, Counter
from io import BytesIO
from pathlib import Path

import lxml
import pandas as pd
import requests
from lxml.etree import _Element
from lxml.html import HTMLParser
import lxml.etree as ET

from pyamihtmlx.ami_html import URLCache, HtmlUtil, H_DIV, H_A, HtmlStyle, A_NAME, A_CLASS, A_ID, A_STYLE, H_SPAN
from pyamihtmlx.ami_integrate import HtmlGenerator
from pyamihtmlx.file_lib import FileLib
from pyamihtmlx.un import IPCC, GATSBY, DE_GATSBY, WORDPRESS, DE_WORDPRESS
from pyamihtmlx.util import AbstractArgs, Util
from pyamihtmlx.xml_lib import HtmlLib, XmlLib

logger = logging.getLogger(__file__)

IPCC_CHAP_TOP_REC = re.compile(""
                               "(Chapter\\s?\\d\\d?\\s?:.*$)|"
                               "(Table\\s?of Contents.*)|"
                               "(Executive [Ss]ummary.*)|"
                               "(Frequently [Aa]sked.*)|"
                               "(References)"
                               )
# components of path
ANNEXES = "annexes"
GLOSSARY = "glossary"
ACRONYMS = "acronyms"
HTML = "html"
AUTHOR = "author"
COUNTRY = "country"

# frontmatter
CORE_TEAM = "Core Writing Team"
EXTENDED_TEAM = 'Extended Writing Team'
CONTRIB_AUTHORS = 'Contributing Authors'
REVIEW_EDITORS = 'Review Editors'
SCIENTIFIC_STEERING = 'Scientific Steering Committee'
VISUAL_INFORM = 'Visual Conception and Information Design'

IP_WG1 = "wg1"
IP_WG2 = "wg2"
IP_WG3 = "wg3"
IP_SYR = "syr"
IP_SR15 = "sr15"
IP_SROCC = "srocc"
IP_SRCCL = "srccl"

REPORTS = [
    IP_WG1,
    IP_WG2,
    IP_WG3,
    IP_SYR,
    IP_SR15,
    IP_SROCC,
    IP_SRCCL,
]

LINKS_CSV = "links.csv"

HTML_WITH_IDS = "html_with_ids"
ID_LIST = "id_list"
PARA_LIST = "para_list"
MANUAL = "manual"

class IPCCCommand:

    @classmethod
    def get_paths(cls, inputs):

        """ expands any globs and also creates BytesIO from URLs
        """
        paths = []
        if not inputs:
            logger.warning(f"no inputs given")
            return paths
        if type(inputs) is not list:
            inputs = [inputs]

        _globbed_inputs = FileLib.expand_glob_list(inputs)
        if _globbed_inputs:
            logger.info(f"inputs {inputs}")
            paths = [Path(input) for input in _globbed_inputs if Path(input).exists() and not Path(input).is_dir()]
            return paths

        for input in inputs:
            if str(input).startswith("http"):
                response = requests.get(input)
                bytes_io = BytesIO(response.content)
                paths.append(bytes_io)
        return paths

    @classmethod
    def extract_authors_and_roles(cls, filename, author_roles=None, output_dir=None, outfilename="author_table.html"):
        """
        extracts author names and countries from frontmatter
        :param filename: input html file
        :param author_roles: Roles of authors (subsection titles)
        :param output_dir: if not, uses input file parent
        :param outfilename: output filename (default "author_table.html")
        """
        if not author_roles:
            author_roles = cls.get_author_roles()

        if not output_dir:
            output_dir = Path(filename).parent
        chap_html = lxml.etree.parse(str(Path(output_dir, filename)))
        table = []
        for role in author_roles:
            htmls = chap_html.xpath(f".//div/span[normalize-space(.)='{role}']")
            if len(htmls) == 0:
                logger.warning(f"{role} not found")
                continue
            following = htmls[0].xpath("following-sibling::span")
            if len(following) != 1:
                logger.warning(f"FAIL to find author_list")
            else:
                cls.extract_authors(following, role, table)
        df = pd.DataFrame(table, columns=["author", "country", "role"])
        # html_table = df.to_html()
        # HtmlLib.write_html_file(html_table, str(Path(output_dir, outfilename)))
        df.to_html()
        return df

    @classmethod
    def extract_authors(cls, following, role, table):
        AUTHOR_RE = re.compile("\\s*(?P<auth>.*)\\s+\\((?P<country>.*)\\)")
        authors = following[0].text.split(",")
        for author in authors:
            match = AUTHOR_RE.match(author)
            if match:
                auth = match.group('auth')
                country = match.group('country')
                table.append([auth, country, role])
            else:
                logger.warning(f"FAIL {author}")
                pass

    @classmethod
    def get_author_roles(cls):
        author_roles = [
            "Core Writing Team:",
            "Extended Writing Team:",
            "Contributing Authors:",
            "Review Editors:",
            "Scientific Steering Committee:",
            "Visual Conception and Information Design:",
        ]
        return author_roles

    @classmethod
    def save_args_to_global(cls, kwargs_dict, overwrite=False):
        from pyamihtmlx.ami_config import doc_info

        for key, value in kwargs_dict.items():
            if overwrite or key not in doc_info:
                doc_info[key] = value
        # print(f"config doc_info {doc_info}")


def normalize_id(text):
    if text:
        text = re.sub("[ ()@$#%^&*-+~<>,.?/:;'\\[\\]\"{}]", "_", text.lower().strip())
        text = text.replace('"', "_")
    return text


class IPCCGlossary:
    """builds/transforms/uses IPCC glossary
    """

    SECTIONED = "sectioned"
    ANNOTATED_GLOSSARY = "annotated_glossary"

    def __init__(self):
        self.style_class = None
        self.input_pdf = None
        self.glossary_elem = None
        self.glossary_top = None
        self.glossary_type = None
        self.report = None
        self.html_file = None
        self.sectioned_html_file = None
        self.annotated_glossary_file = None
        self.unlinked_set = set()
        self.entries = None
        self.link_table = None
        self.section_regexes = None
        self.lead_entries = None

    # class IPCCGlossary

    def create_annotated_glossary(self, style_class=None, link_class=None, write_glossary=True):
        """
        from a raw glossary html file (created from PDF) create an annotated glossary element
        """
        self.create_glossary_elem()
        if self.glossary_elem is None:
            logger.warning(f"no glossary element created")
            return
        if not len(self.glossary_elem.xpath("/*//div")):
            print(f"no divs in glossary_elem")
            return
        print(f"divs {len(self.glossary_elem.xpath('//div'))}")
        self.create_and_annotate_lead_entries(style_class, use_bold=True)
        self.add_links_to_terms(link_class)

        if write_glossary:
            if self.html_file is None:
                raise ValueError(f"self.html_file is None")
            self.annotated_glossary_file = Path(Path(self.html_file).parent, f"{IPCCGlossary.ANNOTATED_GLOSSARY}.html")
            HtmlLib.write_html_file(self.glossary_elem, self.annotated_glossary_file)
        return self.glossary_elem

    # def create_glossary_elem_x(self):
    #     if self.glossary_elem is None:
    #         if self.glossary_html_file:
    #             self.glossary_elem = lxml.etree.parse(self.glossary_html_file)

    def create_glossary_elem(self, fail_on_error=True):
        if self.glossary_elem is None:
            if self.html_file:
                self.glossary_elem = self.create_glossary_from_html_file(self.html_file)
        if self.glossary_elem is None and fail_on_error:
            raise ValueError(f"cannot create glossary_elem")

    # class IPCCGlossary

    def add_links_to_terms(self, link_class):
        self.unlinked_set = set()
        link_spans = self.glossary_elem.xpath(f".//div/span")
        print(f"spans {len(link_spans)}")
        bold_link_spans = [span for span in link_spans if HtmlStyle.is_bold(span)]
        if not len(bold_link_spans):
            print(f"*****Cannot find any bold link spans *******")
            return
        div_bolds = [div for div in self.glossary_elem.xpath(".//div")]
        if len(div_bolds) == 0:
            print(f"********Cannot find any bold leads********")
            return
        for div in div_bolds:
            a_ids = div.xpath("a/@id")
            tt = " @ ".join([id for id in a_ids])
            print(f">> {tt}")
            spans = div.xpath("./span")
            if len(spans) > 0 and HtmlStyle.is_bold(spans[0]):
                for span in spans[1:]:
                    if HtmlStyle.is_italic(span):
                        self.add_link(span)
                logger.info(f"is bold {spans[0].text}")

        attnames = ["style", "x0", "x1", "y0", "y1", "width", "top", "left", "right"]
        self.add_inline_links(attnames, link_class, link_spans)

        logger.warning(f"unlinked {len(self.unlinked_set)} {self.unlinked_set}")

    # class IPCCGlossary

    def add_inline_links(self, attnames, link_class, link_spans):
        for span in link_spans:
            XmlLib.delete_atts(attnames, span)

            span_class = span.attrib.get("class")
            logger.debug(f"span_class++ {span_class}")
            if span_class == link_class:
                self.add_link(span)

    # class IPCCGlossary

    def add_link(self, span):
        ref = normalize_id(span.text)
        targets = self.glossary_elem.xpath(f".//div/a[@class='lead' and @name='{ref}']")
        if len(targets) == 1:
            a_elem = lxml.etree.SubElement(span, "a")
            a_elem.attrib["href"] = "#" + ref
            a_elem.text = span.text
            span.text = ""
            logger.debug(f"... {ref}")
        elif len(targets) > 0:
            logger.warning(f"multiple targets {ref}")
        else:
            span.attrib["style"] = "color: red"
            self.unlinked_set.add(ref)

    # class IPCCGlossary

    def create_and_annotate_lead_entries(self, style_class, use_bold=False, debug=False):
        debug = True
        self.create_glossary_elem(fail_on_error=True)
        if self.lead_entries is None:
            if use_bold:
                self.lead_entries = [div for div in self.glossary_elem.xpath(f".//div[span]") if
                                     HtmlStyle.is_bold(div.xpath('./span')[0])]
            else:
                self.lead_entries = self.glossary_elem.xpath(f".//div[span[@class='{style_class}']]")
            logger.info(f"entries: {len(self.lead_entries)}")

            for div_entry in self.lead_entries:
                IPCCGlossary.add_anchor(div_entry)

    # class IPCCGlossary
    @classmethod
    def add_anchor(cls, div_entry):

        spans = div_entry.xpath(f'./{H_SPAN}')
        del (spans[0].attrib[A_STYLE])
        lead_text = spans[0].text.strip()
        lead_id = normalize_id(lead_text)
        a_elem = lxml.etree.SubElement(div_entry, f"{H_A}")
        a_elem.attrib[A_ID] = lead_id
        a_elem.attrib[A_NAME] = lead_text
        a_elem.attrib[A_CLASS] = "lead"
        div_entry.insert(0, a_elem)
        a_elem.attrib[A_STYLE] = "background: #ffeeee;"
        a_elem.text = " "

    # class IPCCGlossary

    @classmethod
    def create_glossary_from_html_file(cls, html_file):
        glossary = None
        if html_file:
            elem = lxml.etree.parse(str(html_file))
            if elem is not None:
                glossary = IPCCGlossary()
                glossary.glossary_elem = elem
                glossary.glossary_html_file = html_file
        return glossary

    # class IPCCGlossary

    def get_a_id_text_hrfs(self, entry, link_class=None):
        """

        """
        anchors = entry.xpath(f"{H_A}")
        # if len(anchors) != 1:
        #     continue
        anchor0 = anchors[0]
        id = anchor0.get(A_ID)
        print(f">a_id> {id}")
        spans = entry.xpath(f"{H_SPAN}")[1:]
        text = " ".join([' '.join(span.itertext()) for span in spans])
        print(f"lc {link_class}")
        href_as = entry.xpath(f"{H_SPAN}[@class='{link_class}']") if link_class is not None else []
        return anchor0, id, text, href_as

    # class IPCCGlossary

    def get_entries_by_id(self, id):
        elems = self.glossary_elem.xpath(f".//div[a[@id='{id}']]")
        return elems

    # class IPCCGlossary

    def create_link_table(self, max_text=100, link_class=None):
        self.link_table = []

        self.create_and_annotate_lead_entries(self.style_class, use_bold=False, debug=False)

        for entry in self.lead_entries:
            anchor, id, text, href_as = self.get_a_id_text_hrfs(entry, link_class=link_class)
            print(f"href_as {len(href_as)}")
            logger.debug(f"__ {id} $ {text} \n   $$ {[(a.text + ' % ') for a in href_as]}")
            text = text if text is not None else "??"
            for href_a in href_as:
                href_id = href_a.text
                href_id = normalize_id(href_id)
                logger.debug(f"href_id:: {href_id}")
                href_elems = self.get_entries_by_id(href_id)
                if len(href_elems) > 0:
                    logger.debug(f"&& {href_id}")
                for href_elem in href_elems:
                    href_text = ' '.join(href_elem.itertext()) if href_elem is not None else "?"
                    logger.debug(f"** {href_id} => {href_text}")
                    row = [id, text[:max_text], href_id, href_text[:max_text]]
                    self.link_table.append(row)
        return self.link_table

    # class IPCCGlossary

    def write_csv(self, path=None, debug=True):
        if not path:
            path = self.create_csv_file_name()
        if path:
            with open(str(path), 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["anchor", "a_text", "target", "t_text"])
                writer.writerows(self.link_table)
            if debug:
                print(f"wrote CSV {path}")
        return path

    # class IPCCGlossary
    @classmethod
    def get_id_and_text(cls, entry):
        anchors = entry.xpath(f"{H_A}")
        # if len(anchors) != 1:
        #     continue
        anchor0 = anchors[0]
        id = anchor0.get(A_ID)
        logger.debug(f">>{id}")
        spans = entry.xpath(f"{H_SPAN}")
        text = " ".join(spans[1:])

    # TODO add targets
    # class IPCCGlossary

    @classmethod
    def get_id_text_refs(cls, entry):
        anchors = entry.xpath(f"{H_A}")
        # if len(anchors) != 1:
        #     continue
        anchor0 = anchors[0]
        id = anchor0.get(A_ID)
        print(f">>{id}")
        spans = entry.xpath(f"{H_SPAN}")
        text = " ".join(spans[1:])
        href_as = entry.xpath(f"{H_SPAN}/{H_A}")
        return href_as

    # class IPCCGlossary

    @classmethod
    def create_input_pdf_name(cls, ar6_dir, report, g_type):
        """constructs pdf input name (file or URL) from omponents
        :param ar6_dir: parent directory of reports (either file/Path OR repository URL)
        :param report: e.g. "wg1"
        :param g_type: ipcc GLOSSARY OR ACRONYMS or None

        """
        if g_type:
            return IPCCGlossary.create_pdf_file_name(ar6_dir, g_type, report)

    # class IPCCGlossary

    @classmethod
    def make_html(cls, glossary_html, glossary_pdf, section_regexes=None):
        if Util.should_make(glossary_html, glossary_pdf):
            IPCCGlossary.create_glossary_from_pdf(input_pdf=glossary_pdf)

    # class IPCCGlossary

    @classmethod
    def create_glossary_from_pdf(
            cls,
            input_pdf=None,
            glossary_type=GLOSSARY,
            report=None,
            section_regexes=None,
            glossary_top=None,
            annotate_glossary=True,
    ):
        """

        """
        logger.error(f"REPORT {report}")
        print(f"logger {logger}")
        if not input_pdf:
            if not report:
                raise ValueError(f"report not given")
            if not section_regexes:
                # raise ValueError(f"section_regexes not given")
                logger.warning(f"section regexes not given")
            if not glossary_top:
                raise ValueError("glossary_top not given")
            input_pdf = IPCCGlossary.create_input_pdf_name(glossary_top, report, glossary_type)
            logger.warning(f"input {input_pdf}")
        if not input_pdf:
            raise FileNotFoundError("no input_pdf given")

        glossary = IPCCGlossary()
        glossary.input_pdf = input_pdf
        glossary.glossary_top = glossary_top
        glossary.glossary_type = glossary_type
        glossary.report = report
        glossary.glossary_elem = HtmlGenerator.create_sections(
            input_pdf=input_pdf, section_regexes=section_regexes, group_stem=glossary_type)
        glossary.glossary_html = IPCCGlossary.create_sectioned_dictionary_name(glossary_top, glossary_type, report)
        # glossary.glossary_pdf = IPCCGlossary.create_pdf_file_name(glossary_top, glossary_type, report)
        # glossary.sectioned_html_name = glossary.glossary_html
        HtmlLib.write_html_file(glossary.glossary_elem, glossary.glossary_html, debug=True)
        # glossary.html_file = glossary.sectioned_html_name
        # IPCCGlossary.make_html(glossary.glossary_html, glossary_pdf, section_regexes=section_regexes)
        #
        # assert glossary_html.exists()
        if annotate_glossary:
            glossary.html_file = glossary.glossary_html
            glossary.create_annotated_glossary(style_class="s1020", link_class='s100')
            glossary.create_link_table(link_class='s100')

        return glossary

    # class IPCCGlossary

    @classmethod
    def create_sectioned_dictionary_name(cls, glossary_top, glossary_type, report):
        return Path(glossary_top, report, ANNEXES, HTML, glossary_type, f"{IPCCGlossary.SECTIONED}.html")

    # class IPCCGlossary

    @classmethod
    def create_pdf_file_name(cls, glossary_top, glossary_type, report):
        print(f"gtop {glossary_top} gtype {glossary_type}, {report}")
        return Path(glossary_top, report, ANNEXES, f"{glossary_type}.pdf")

    # class IPCCGlossary

    def write_csv_top(self):
        csv_path = self.create_csv_file_name()
        self.write_csv(csv_path)
        assert csv_path.exists(), f"{csv_path} should exist"
        return csv_path

    def create_csv_file_name(self):
        return Path(self.glossary_top, self.report, ANNEXES, HTML, self.glossary_type, LINKS_CSV)


class IPCCArgs(AbstractArgs):
    SECTIONS = "sections"
    VAR = "var"

    AUTHORS  = "authors"
    CHAPTER  = "chapter"
    DOWNLOAD = "download"
    HELP     = "help"
    PDF2HTML = "pdf2html"
    QUERY    = "query"
    REPORT   = "report"
    SEARCH   = "search"
    XPATH    = "xpath"

    OPERATIONS = [
        AUTHORS,
        DOWNLOAD,
        PDF2HTML,
        QUERY,
        SEARCH,
        XPATH,
        HELP,
    ]

    pyamihtmlx_dir = Path(__file__).parent
    pyamihtml_dir = pyamihtmlx_dir.parent
    SYMBOL_DICT = {
        "_PYAMIHTMLX": pyamihtmlx_dir,  # top of code
        "_PYAMIHTML": pyamihtml_dir,  # top of repo
        "_TEMP": Path(pyamihtml_dir, "temp"),  # temp tree
        "_QUERY_OUT": Path(pyamihtml_dir, "temp", "queries"),  # output for queries
        "_TEST": Path(pyamihtml_dir, "test"),  # top of test tree
        "_IPCC_REPORTS": Path(pyamihtml_dir, "test", "resources", "ipcc", "cleaned_content"),  # top of IPCC content
        # files
        "_HTML_IDS": "**/html_with_ids.html",
        # XPATHS
        # refs
        "_REFS": "//p[@id and ancestor::*[@id='references']]",  # select references section
        "_NOREFS": "//p[@id and not(ancestor::*[@id='references'])]",  # not selecr references
        "_EXEC_SUMM": "//p[@id and ancestor::*[@id='executive-summary']]", #executive summaries
        "_FAQ": "//div[h2 and ancestor::*[@id='frequently-asked-questions']]",  # FAQ Q+A
        "_FAQ_Q": "//h2[ancestor::*[@id='frequently-asked-questions']]",  # FAQ Q
        "_FAQ_A": "//p[ancestor::*[@id='frequently-asked-questions']]",  # FAQ A
        "_IMG_DIV": "//div[p[span[img]]]",  # div containing an img

    }

    def __init__(self):
        """arg_dict is set to default"""
        super().__init__()
        self.subparser_arg = "IPCC"

    # class IPCCArgs

    def add_arguments(self):
        """creates adds the arguments for pyami commandline

        """
        if self.parser is None:
            self.parser = argparse.ArgumentParser()
        self.parser.description = textwrap.dedent(
            'Manage and search IPCC resources and other climate stuff. \n'
            '----------------------------------------------------------\n'
            'see pyamihtmlx/IPCC.md'
            '\nExamples:\n'
            'help'
            ''
            'parse foo.pdf and create default HTML'
            f'  pyamihtmlx IPCC --input foo.pdf\n'
            f''

        )
        super().add_argumants()

        self.parser.formatter_class = argparse.RawDescriptionHelpFormatter
        INPUT_HELP = f"input from:\n" \
                     f"   file/s single, multiple, and glob/wildcard (experimental)\n" \
                     f"   directories (needs {self.INFORMAT})\n" \
                     f"   URL/s (must start with 'https:); provide {self.OUTDIR} for output' \n"
        # self.parser.add_argument(f"--{IPCCArgs.INPUT}", nargs="+",
        #                          help=INPUT_HELP)

        CHAPTER_HELP = "IPCC Chapter/s: SPM, TS, ANNEX, Chapter-1...Chapter-99"
        self.parser.add_argument(f"--{IPCCArgs.CHAPTER}", nargs="+",
                                 help=CHAPTER_HELP)

        INFORM_HELP = "input format/s; experimental"
        self.parser.add_argument(f"--{IPCCArgs.INFORMAT}", nargs="+", default="PDF",
                                 help=INFORM_HELP)

        OPERATION_HELP = f"operations from {IPCCArgs.OPERATIONS}"
        self.parser.add_argument(f"--{IPCCArgs.OPERATION}", choices=IPCCArgs.OPERATIONS, nargs="+",
                                 help=OPERATION_HELP)

        QUERY_HELP = "search word/s"
        self.parser.add_argument(f"--{IPCCArgs.QUERY}", nargs="+",
                                 help=QUERY_HELP)

        REPORT_HELP = f"IPCC Reports: lowercase from {REPORTS}"
        self.parser.add_argument(f"--{IPCCArgs.REPORT}", nargs="+",
                                 help=REPORT_HELP)

        XPATH_HELP = "xpath filter (e.g. './/section'"
        self.parser.add_argument(f"--{IPCCArgs.XPATH}", nargs="+",
                                 help=XPATH_HELP)
        return self.parser

    # class ProjectArgs:
    def process_args(self, debug=True):
        """runs parsed args
        :return:

        """

        if not self.arg_dict:
            print(f"cannot find self.arg_dict")
            return
        logger.info(f"argdict: {self.arg_dict}")
        print(f"arg_dict: {self.arg_dict}")
        informats = self.arg_dict.get(IPCCArgs.INFORMAT)
        paths = self.get_paths()
        operation = self.get_operation()

        input = self.create_input_files()
        outdir, output = self.create_output_files()

        chapter = self.get_chapter()
        report = self.get_report()

        kwargs = self.get_kwargs(save_global=True)  # not saved??
        section_regexes = self.get_section_regexes()
        author_roles = self.get_author_roles_nyi()
        query = self.get_query()
        xpath = self.get_xpath()
        if debug:
            if type(input) is list:
                print(f"inputs: {len(input)} > {input[:3]}...")
            else:
                print(f"input: {input}")
            print(f"debug: {debug}")
            print(f"report: {report}")
            print(f"chapter: {chapter}")
            print(f"outdir: {outdir}")
            print(f"output: {output}")
            print(f"kwargs: {kwargs}")
            print(f"query: {query}")
            print(f"xpath: {xpath}")

        logger.info(f"processing {len(paths)} paths")

        if self.process_operation(
                operation,
                outdir=outdir,
                paths=paths,
                section_regexes=section_regexes,
                author_roles=author_roles):
            pass
        elif query is not None:
            if not output:
                print(f"*** no output argument, no search")
            else:
                # parent = Path(output).parent
                # if parent is None:
                #     print(f"{output} has no parent")
                #     return
                # hitdictfile = Path(parent, "html_dict.html")
                # print(f"html_dict_file {hitdictfile}")
                self.search(input, query=query, xpath=xpath, outfile=output)
        else:
            logger.warning(f"Unknown operation {operation}")

    def process_operation(self, operation, outdir=None, paths=None, section_regexes=None, author_roles=None):
        done = True
        if operation == IPCCArgs.DOWNLOAD:
            self.download()
        elif operation == IPCCArgs.PDF2HTML:
            self.convert_pdf2html(outdir, paths, section_regexes)
        elif operation == IPCCArgs.AUTHORS:
            self.extract_authors(author_roles, paths)
        elif operation == IPCCArgs.KWARGS:
            self.get_kwargs(save_global=True)
        else:
            done = False
            return done

    def create_output_files(self):
        outdir = self.get_value_lookup_symbol(self.get_outdir, lookup=self.SYMBOL_DICT)
        output = self.get_value_lookup_symbol(self.get_output, lookup=self.SYMBOL_DICT)
        print(f"outdir {outdir} output {output}")

        output_list = self.join_filenames_expand_wildcards(outdir, output)
        if output_list is None:
            print(f"**NO OUTPUT parameter given")
        elif type(output_list) is list and len(output_list) == 1:
            output = output_list[0]
        return outdir, output

    def create_input_files(self, debug=False):
        home_dir = Path.home()
        print (f"home {home_dir}")
        indir = self.get_value_lookup_symbol(self.get_indir, lookup=self.SYMBOL_DICT)
        input = self.get_value_lookup_symbol(self.get_input, lookup=self.SYMBOL_DICT)
        input = self.join_filenames_expand_wildcards(indir, input)
        if debug:
            print(f"input {input}")
        return input

    def join_filenames_expand_wildcards(self, directory, filename, recursive=True, debug=False):
        """
        joins directory to filename. May or may not contain wildcards. result will be globbed
        Python metacharacters will be used ("**", "?", ".", etc.)
        :param directory: if None, ignored; may contain metacharacters
        :param filenme; if directory is none, fullfile = directory/filename
        :param recursive: recursive globbing (default True)
        """
        if not filename:
            return directory
        if not directory:
            fullfile = filename
        else:
            try:
                fullfile = FileLib.join_dir_and_file_as_posix(directory, filename)
            except Exception as e:
                print(f"failed to join {directory} , {filename} because {e}")
        if debug:
            print(f"fullfile {fullfile}")

        fullfile_list = FileLib.posix_glob(fullfile, recursive=recursive)
        if fullfile_list == []:
            print(f"empty list from {fullfile}")
        return fullfile_list

    def get_value_lookup_symbol(self, getter, lookup=None):
        """
        :param getter: function to get command parametr (e.g. get_indir)
        :param lookup: dictionary to substitute underscore variabls

        """
        if not lookup:
            raise ValueError(f"no value for lookup dict")
        value = getter()
        if value and str(value).startswith("_"):
            value1 = lookup.get(value)
            if value1 is None:
                print(f"allowed substitutions {self.lookup.keys()} but found {value}")
                raise ValueError(f"unknown symbol {value}")
            value = value1
        return value

    def convert_pdf2html(self, outdir, paths, section_regexes):
        for path in paths:
            HtmlGenerator.create_sections(path, section_regexes, outdir=outdir)

    def extract_authors(self, author_roles, paths):
        for path in paths:
            IPCCCommand.extract_authors_and_roles(path, author_roles)

    def get_section_regexes(self):
        section_regexes = self.arg_dict.get(IPCCArgs.SECTIONS)
        if not section_regexes:
            section_regexes = IPCCSections.get_section_regexes()
        return section_regexes

    def get_kwargs(self, save_global=False, debug=False):
        kwargs = self.arg_dict.get(IPCCArgs.KWARGS)
        if not kwargs and debug:
            print(f"no keywords given")
            return

        kwargs_dict = self.parse_kwargs_to_string(kwargs)
        # print(f"saving kywords to kwargs_dict {kwargs_dict} ; not fully working")
        logger.info(f"kwargs {kwargs_dict}")
        if save_global:
            IPCCCommand.save_args_to_global(kwargs_dict, overwrite=True)
        return kwargs_dict

    def get_paths(self):
        inputx = self.arg_dict.get(IPCCArgs.INPUT)
        logger.info(f"input {inputx}")
        paths = IPCCCommand.get_paths(inputx)
        return paths

    def get_chapter(self):
        inputx = self.arg_dict.get(IPCCArgs.CHAPTER)
        chapters = Util.get_list(inputx)
        return chapters

    def get_report(self):
        inputx = self.arg_dict.get(IPCCArgs.REPORT)
        paths = Util.get_list(inputx)
        return paths

    # class IPCCArgs:

    @classmethod
    def create_default_arg_dict(cls):
        """returns a new COPY of the default dictionary"""
        arg_dict = dict()
        arg_dict[IPCCArgs.INFORMAT] = ['PDF']
        return arg_dict

    def get_author_roles_nyi(self):
        pass

    def get_query(self):
        # returns a list
        query = self.arg_dict.get(IPCCArgs.QUERY)
        query = Util.get_list(query)
        return query

    def get_xpath(self):
        xpath = self._get_value_and_substitute_with_dict(arg=IPCCArgs.XPATH, dikt=self.SYMBOL_DICT)
        return xpath

    def _get_value_and_substitute_with_dict(self, arg=None, dikt=None):
        if arg is None:
            return None
        if dikt is None:
            return None
        value = self.arg_dict.get(arg)
        if value and value.startswith("_"):
            value1 = dikt.get(value)
            if value:
                value = value1
        return value

    def search(self, input, query=None, xpath=None, outfile=None, debug=False):
        if not input:
            print(f"no input files for search")
            return
        inputs = Util.get_list(input)
        IPCC.create_hit_html(inputs, phrases=query, xpath=xpath, outfile=outfile, debug=debug)

    def download(self):
        input = self.get_input()
        output = self.get_output()
        outdir = self.get_outdir()
        print(f"input {input}, output {output}, outdir {outdir}")




class IPCCChapter:

    @classmethod
    def make_pure_ipcc_content(cls, html_file=None, html_url=None, html_elem=None, outfile=None):
        """
        Strips non-content elements and attributes
        :param html_file: file to read
        :param html_url: url to download if html_file is None
        :param outfile: file to save parsed cleaned html
        :return: (html element,error)  errors or non-existent files return (None, error)
        """

        """
        <div class="nav2">
          <nav class="navbar py-0 fixed-top navbar navbar-expand navbar-light"><div class="navbar__wrapper d-flex align-items-center justify-content-between position-relative h-100">
            <div class="logo-box d-flex h-100 align-items-center hamburger">
              <div class="text-white d-flex justify-content-center align-items-center text-decoration-none nav-item dropdown">
                <a id="basic-nav-dropdown" aria-expanded="false" role="button" class="dropdown-toggle nav-link" tabindex="0">
                  <button class="menu bg-transparent h-100 border-0">
                    <i class="uil uil-bars text-white"></i>
                    <span class="d-block text-white fw-bold">Menu</span>
                    </button>
                    </a>
                    </div>
                    <a class="logo fw-bold text-white flex-column align-items-start text-decoration-none" href="https://www.ipcc.ch/report/ar6/wg3/">IPCC Sixth Assessment Report<small class="d-block opacity-75 nav-subtitle">Working Group III: Mitigation of Climate Change</small></a></div><div class=" h-100 d-flex list-top"><div class="text-white d-flex justify-content-center align-items-center text-decoration-none nav-item dropdown t-link nav-item dropend"><a id="basic-nav-dropdown" aria-expanded="false" role="button" class="dropdown-toggle nav-link" tabindex="0">About</a></div><div class="text-white d-flex justify-content-center align-items-center text-decoration-none nav-item dropdown t-link report-menu nav-item dropend"><a id="basic-nav-dropdown" aria-expanded="false" role="button" class="dropdown-toggle nav-link" tabindex="0">Report</a></div><div class="text-white d-flex justify-content-center align-items-center text-decoration-none nav-item dropdown t-link nav-item dropend"><a id="basic-nav-dropdown" aria-expanded="false" role="button" class="dropdown-toggle nav-link" tabindex="0">Resources</a></div><div class="text-white d-flex justify-content-center align-items-center text-decoration-none t-link nav-item dropend"><a id="basic-nav-dropdown" aria-expanded="false" role="button" class="dropdown-toggle nav-link" tabindex="0">Download</a></div><div class="text-white d-flex justify-content-center align-items-center text-decoration-none icon-download t-link nav-item dropdown"><a id="basic-nav-dropdown" aria-expanded="false" role="button" class="dropdown-toggle nav-link" tabindex="0"><div class="text-white d-flex justify-content-center align-items-center text-decoration-none"><i class="uil uil-import"></i></div></a></div><a class="text-white d-flex justify-content-center align-items-center text-decoration-none t-link nav-item dropend translations-icon" href="https://www.ipcc.ch/report/ar6/wg3/resources/translations"><svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="globe" class="svg-inline--fa fa-globe fa-w-16 " role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 496 512"><path fill="currentColor" d="M336.5 160C322 70.7 287.8 8 248 8s-74 62.7-88.5 152h177zM152 256c0 22.2 1.2 43.5 3.3 64h185.3c2.1-20.5 3.3-41.8 3.3-64s-1.2-43.5-3.3-64H155.3c-2.1 20.5-3.3 41.8-3.3 64zm324.7-96c-28.6-67.9-86.5-120.4-158-141.6 24.4 33.8 41.2 84.7 50 141.6h108zM177.2 18.4C105.8 39.6 47.8 92.1 19.3 160h108c8.7-56.9 25.5-107.8 49.9-141.6zM487.4 192H372.7c2.1 21 3.3 42.5 3.3 64s-1.2 43-3.3 64h114.6c5.5-20.5 8.6-41.8 8.6-64s-3.1-43.5-8.5-64zM120 256c0-21.5 1.2-43 3.3-64H8.6C3.2 212.5 0 233.8 0 256s3.2 43.5 8.6 64h114.6c-2-21-3.2-42.5-3.2-64zm39.5 96c14.5 89.3 48.7 152 88.5 152s74-62.7 88.5-152h-177zm159.3 141.6c71.4-21.2 129.4-73.7 158-141.6h-108c-8.8 56.9-25.6 107.8-50 141.6zM19.3 352c28.6 67.9 86.5 120.4 158 141.6-24.4-33.8-41.2-84.7-50-141.6h-108z"></path></svg></a><div class="logo-box d-flex h-100 align-items-center gap-5"><a id="nav-primary-logo" class="ipcc-logo-svg" href="https://www.ipcc.ch/"><svg version="1.1" x="0px" y="0px" viewBox="0 0 82 50"><path d="M7.8,4.6C7.8,6.4,6.2,8,4.4,8C2.5,8,1,6.4,1,4.6c0-1.9,1.5-3.4,3.4-3.4C6.2,1.2,7.8,2.7,7.8,4.6z M1.6,42.7h5.6V10.7H1.6
    V42.7z M29.3,13c2,1.8,2.9,4.1,2.9,7.2v13.4c0,3.1-1,5.5-2.9,7.2c-2,1.8-4,2.7-6.3,2.7c-2,0-3.7-0.5-5-1.5v6.8h-5.6V20.2
    c0-3.1,1-5.5,2.9-7.2c2-1.8,4.3-2.7,7-2.7C25,10.2,27.4,11.1,29.3,13z M26.7,20.2c0-3.7-1.9-5.3-4.3-5.3c-2.4,0-4.3,1.6-4.3,5.3....9-7.2v-3.2h-5.6v3.2
    c0,3.6-1.9,5.3-4.3,5.3c-2.4,0-4.3-1.6-4.3-5.2V20.2c0-3.7,1.9-5.3,4.3-5.3c2.4,0,4.3,1.6,4.3,5.3v0.6H81z"></path></svg></a></div></div></div></nav></div>
        """
        """
        <div class="ref-tooltip" id="ref-tooltip"><textarea class="ref-tooltip-text" id="ref-tooltip-text"></textarea><div class="reflinks"><button class="btn-ipcc btn btn-primary copy-reference" id="copy-reference">Copy</button><a href="https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-6/" id="doilink" target="_blank">doi</a></div></div>        
        """
        """
        The 3-circle 'share' icon
        <div class="share-tooltip" id="share-tooltip"><span><img id="section-twitter-share" class="twitter" src="./expanded_files/twitter-icon.png"><button id="section-twitter-share-button" class="btn-ipcc btn btn-primary">Share on Twitter</button></span><span><img id="section-facebook-share" class="facebook" src="./expanded_files/facebook-icon.png"><button id="section-facebook-share-button" class="btn-ipcc btn btn-primary">Share on Facebook</button></span><span><img id="section-link-copy" class="link" src="./expanded_files/link-icon.png"><button id="section-link-copy-button" class="btn-ipcc btn btn-primary">Copy link</button><input class="section-link-input" id="section-link-input"></span><span><img class="link" src="./expanded_files/email-icon.png"><a id="section-email-share" target="_blank" href="https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-6/"><button id="section-email-share-button" class="btn-ipcc btn btn-primary">Share via email</button></a></span><span class="ref-tooltip-close"></span></div>        
        """
        """
        Dropdown menus (e.g. from top of page)
        <div class="dropdown"><button id="dropdown-basic" aria-expanded="false" type="button" class="btn-ipcc btn btn-primary dl-dropdown dropdown-toggle btn btn-success">Downloads</button></div>
        """
        """
        <div class="section-tooltip" id="section-tooltip"><span class="section-tooltip-text" id="section-tooltip-text"></span><a href="https://www.ipcc.ch/report/ar6/wg3/chapter/chapter-6/" id="section-link" target="_blank"><button class="btn-ipcc btn btn-primary open-section">Open section</button></a><span class="section-tooltip-close"></span></div>
        """
        """
        rectangular buttons
        <div class="mt-auto gap-3 d-flex flex-row align-items-left pb-3"><button class="btn-ipcc btn btn-primary" id="authors-button">Authors</button><button class="btn-ipcc btn btn-primary" id="figures-button">Figures</button><button class="btn-ipcc btn btn-primary" id="citation-button">How to cite</button><button class="btn-ipcc btn btn-primary" id="toggle-all-content">Expand all sections</button></div>
        """
        """
        Figures
        <div class="col-lg-3 col-12"><h3>Figure&nbsp;6.4</h3><img src="./expanded_files/IPCC_AR6_WGIII_Figure_6_4.png" alt="" class="img-card" srl_elementid="11"><a href="https://www.ipcc.ch/report/ar6/wg3/figures/chapter-6/figure-6-4"><button type="button" class="btn-ipcc btn btn-primary"><svg aria-hidden="true" focusable="false" data-prefix="fas" data-icon="chart-bar" class="svg-inline--fa fa-chart-bar fa-w-16 " role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="currentColor" d="M332.8 320h38.4c6.4 0 12.8-6.4 12.8-12.8V172.8c0-6.4-6.4-12.8-12.8-12.8h-38.4c-6.4 0-12.8 6.4-12.8 12.8v134.4c0 6.4 6.4 12.8 12.8 12.8zm96 0h38.4c6.4 0 12.8-6.4 12.8-12.8V76.8c0-6.4-6.4-12.8-12.8-12.8h-38.4c-6.4 0-12.8 6.4-12.8 12.8v230.4c0 6.4 6.4 12.8 12.8 12.8zm-288 0h38.4c6.4 0 12.8-6.4 12.8-12.8v-70.4c0-6.4-6.4-12.8-12.8-12.8h-38.4c-6.4 0-12.8 6.4-12.8 12.8v70.4c0 6.4 6.4 12.8 12.8 12.8zm96 0h38.4c6.4 0 12.8-6.4 12.8-12.8V108.8c0-6.4-6.4-12.8-12.8-12.8h-38.4c-6.4 0-12.8 6.4-12.8 12.8v198.4c0 6.4 6.4 12.8 12.8 12.8zM496 384H64V80c0-8.84-7.16-16-16-16H16C7.16 64 0 71.16 0 80v336c0 17.67 14.33 32 32 32h464c8.84 0 16-7.16 16-16v-32c0-8.84-7.16-16-16-16z"></path></svg><span>View</span></button></a></div>
        """
        """
        <span class="share-block"><img class="share-icon" src="./expanded_files/share.png"></span>
        """
        """
        Related pages -  links to other chapters, etc
        <div class="related_pages pt-4"><div class="container"><div class="gx-3 gy-5 ps-2 row"><div class="col-lg-12 col-12 offset-lg-0"><div class="gx-3 gy-3 row"><div class="col-12"><h3 class="fw-bold color-heading mb-2">Explore more</h3></div><div class="col-lg-4 col-sm-6 col-12"><div class="card card-custom-1 bg-white d-flex flex-column justify-content-between"><div class="thumb-overlay"></div><div data-gatsby-image-wrapper="" class="gatsby-image-wrapper gatsby-image-wrapper-constrained img-card"><div><img alt="" role="presentation" aria-hidden="true" src="data:image/svg+xml;charset=utf-8,%3Csvg%20height='294'%20width='600'%20xmlns='http://www.w3.org/2000/svg'%20version='1.1'%3E%3C/svg%3E"></div></div><h3 class="pt-3 px-3">Fact Sheets</h3><p class=" text-20 fw-normal px-3">The regional and crosscutting fact sheets give a snapshot of the key findings, distilled from the relevant Chapters.</p><div class="d-flex flex-row align-items-center gap-3 pb-4 mt-auto"></div></div></div><div class="col-lg-4 col-sm-6 col-12"><div class="card card-custom-1 bg-white d-flex flex-column justify-content-between"><div class="thumb-overlay"></div><div data-gatsby-image-wrapper="" class="gatsby-image-wrapper gatsby-image-wrapper-constrained img-card"><div><img alt="" role="presentation" aria-hidden="true" src="data:image/svg+xml;charset=utf-8,%3Csvg%20height='345'%20width='600'%20xmlns='http://www.w3.org/2000/svg'%20version='1.1'%3E%3C/svg%3E"></div></div><h3 class="pt-3 px-3">Frequently Asked Questions</h3><p class=" text-20 fw-normal px-3">FAQs explain important processes and aspects that are relevant to the whole report for a broad audience</p><div class="d-flex flex-row align-items-center gap-3 pb-4 mt-auto"></div></div></div><div class="col-lg-4 col-sm-6 col-12"><div class="card card-custom-1 bg-white d-flex flex-column justify-content-between"><div class="thumb-overlay"></div><div data-gatsby-image-wrapper="" class="gatsby-image-wrapper gatsby-image-wrapper-constrained img-card"><div><img alt="" role="presentation" aria-hidden="true" src="data:image/svg+xml;charset=utf-8,%3Csvg%20height='225'%20width='500'%20xmlns='http://www.w3.org/2000/svg'%20version='1.1'%3E%3C/svg%3E"></div></div><h3 class="pt-3 px-3">Authors</h3><p class=" text-20 fw-normal px-3">234 authors from 64 countries assessed the understanding of the current state of the climate, including how it is changing and the role of human influence.</p><div class="d-flex flex-row align-items-center gap-3 pb-4 mt-auto"></div></div></div></div></div></div></div></div>
        """
        """
        Text at end of page
        <div id="gatsby-announcer" aria-live="assertive" aria-atomic="true">Navigated to Chapter 6: Energy systems</div>
        """
        """
        Footer - no semantic informatiin
        <footer class="footer"><div class="footer-logo"><a href="https://ipcc.ch/" target="_blank" rel="noreferrer"><div data-gatsby-image-wrapper="" class="gatsby-image-wrapper gatsby-image-wrapper-constrained w-100 h-100 img-fluid footer-img"><div><img alt="" role="presentation" aria-hidden="true" src="data:image/svg+xml;charset=utf-8,%3Csvg%20height='135'%20width='873'%20xmlns='http://www.w3.org/2000/svg'%20version='1.1'%3E%3C/svg%3E"></div></div></a></div><div class="footer-social"><a href="https://twitter.com/IPCC_CH" target="_blank" class="link text-white" rel="noreferrer"><i class="bx bxl-twitter"></i></a><a href="https://www.facebook.com/IPCC/" target="_blank" class="link text-white" rel="noreferrer"><i class="bx bxl-facebook-square"></i></a><a href="https://www.instagram.com/ipcc/?hl=en" target="_blank" class="link text-white" rel="noreferrer"><i class="bx bxl-instagram"></i></a><a href="https://vimeo.com/ipcc" target="_blank" class="link text-white" rel="noreferrer"><i class="bx bxl-vimeo"></i></a></div></footer>
        """
        # TODO move file/url code to more generic library
        html_elem = None
        error = None
        if html_elem is not None:
            pass
        elif html_file is not None:
            if not Path(html_file).exists():
                error = FileNotFoundError()
            else:
                """
                encoding = etree.ElementTree.detect_encoding(data)
                # Parse the HTML file using the correct encoding
                parsed_html = etree.HTML(data.decode(encoding))
                """
                try:
                    html_elem = lxml.etree.parse(str(html_file), parser=HTMLParser())
                except Exception as e:
                    error = e
        elif html_url is not None:
            try:
                html_elem = HtmlLib.retrieve_with_useragent_parse_html(html_url, user_agent='my-app/0.0.1', debug=True)
            except Exception as e:
                print(f"cannot read {html_url} because {e}")
                raise e
            outfile1 = f"{outfile}.html"
            HtmlLib.write_html_file(html_elem, outfile1, debug=True)
            response = requests.get(html_url)
            if response.reason == "Not Found":  # replace this by a code
                html_elem = None
                error = response
            else:
                # print (f"response code {response.status_code}")
                html_elem = lxml.html.fromstring(response.content)
                assert html_elem is not None
        else:
            return (None, "no file or url given")

        if html_elem is None:
            print(f"cannot find html {error}")
            return (None, error)
        xpath_list = [
            "/html/head/style",
            "/html/head/link",
            "/html/head//button",
            "/html/head/script",

            "/html/body/script",
            "/html/body/*[starts-with(., 'Read more')]",
            "/html/body//div[@class='nav2'][nav]",
            "/html/body//div[@class='ref-tooltip'][textarea]",
            "/html/body//div[@class='share-tooltip']",
            "/html/body//div[@class='dropdown'][button]",
            "/html/body//div[@class='section-tooltip']",
            "/html/body//div[button]",
            "/html/body//a[button]",
            "/html/body//span[@class='share-block']",
            "/html/body//button",
            "/html/body//div[contains(@class,'related_pages')]",
            "/html/body//div[@id='gatsby-announcer']",
            "/html/body//noscript",
            "/html/body//footer",

        ]
        for xpath in xpath_list:
            HtmlUtil.remove_elems(html_elem, xpath=xpath)
        HtmlUtil.remove_style_attributes(html_elem)
        if outfile:
            HtmlLib.write_html_file(html_elem, outfile, debug=True)
        return (html_elem, error)

    @classmethod
    def atrip_wordpress(cls, html_elem):
        xpath_list = [
            "/html/head/style",
            "/html/head/link",
            "/html/head//button",
            "/html/head/script",

            "/html/body/script",
            "/html/body/header[div[nav]]",
            "/html/body/nav",
            "/html/body/main/nav",
            "/html/body/footer",
            "/html/body/section[@id='chapter-next']",
            "//article[@id='article-chapter-downloads']",
            "//article[@id='article-supplementary-material']",
            "//div[@class='share']",
            # "/html/body//div[@class='nav2'][nav]",
            # "/html/body//div[@class='ref-tooltip'][textarea]",
            # "/html/body//div[@class='share-tooltip']",
            # "/html/body//div[@class='dropdown'][button]",
            # "/html/body//div[@class='section-tooltip']",
            # "/html/body//div[button]",
            # "/html/body//a[button]",
            # "/html/body//span[@class='share-block']",
            # "/html/body//button",
            # "/html/body//div[contains(@class,'related_pages')]",
            # "/html/body//div[@id='gatsby-announcer']",
            # "/html/body//noscript",
            # "/html/body//footer",

        ]
        for xpath in xpath_list:
            HtmlUtil.remove_elems(html_elem, xpath=xpath)
        HtmlUtil.remove_style_attributes(html_elem)


class WebPublisherTool(ABC):

    @abstractmethod
    def get_removable_xpaths(self):
        pass

    @abstractmethod
    def create_and_add_id(self, id, p, parent, pindex):
        """
        :param id: id from document
        :param p: paragraph element
        :param parent of paragraph
        :param pindex index of p in parent
        """

    def create_pid(cls, p, debug=False):
        pid = None
        parent = p.getparent()
        if parent.tag == "div":
            pindex = parent.index(p) + 1  # 1-based
            id = parent.attrib.get("id")
            if id is None:
                text = "".join(p.itertext())
                if text is not None:
                    if debug:
                        print(f"p without id parent: {text[:20]}")
                else:
                    print(f"empty p without id-ed parent")
            else:
                pid = cls.create_and_add_id(id, p, parent, pindex)
        return pid

    def add_para_ids_and_make_id_list(self, infile, outfile=None, idfile=None, parafile=None, debug=False):
        """creates IDs for paragraphs
        :param idfile:"""
        inhtml = lxml.etree.parse(str(infile), HTMLParser())
        idset = set()
        elems = inhtml.xpath("//*[@id]")
        print(f"elems {len(elems)}")
        for elem in elems:
            id = elem.attrib.get("id")
            if id in idset:
                print(f"duplicate id {id}")
        pelems = inhtml.xpath("//p[text()]")
        print(f"pelems {len(pelems)}")
        """
            <div class="h2-container" id="3.1.2">
              <h2 class="Headings_•-H2---numbered" lang="en-GB">
                <span class="_idGenBNMarker-1">3.1.2</span>Linkages to Other Chapters in the Report <span class="arrow-up"></span>
                <span class="arrow-down"></span>
              </h2>
              <div class="h2-siblings" id="h2-2-siblings">
                <p class="Body-copy_•-Body-copy--full-justify-" lang="en-GB"><a class="section-link" data-title="Mitigation pathways
                <p...
               # id numbers may be off by 1 or more due to unnumbered divs (so 3.8 gives h1-9-siblings
            """
        pid_list = []
        pid_dict = dict()

        for p in pelems:
            pid = None
            pid = self.create_pid(p, debug=debug)
            if pid:
                pid_list.append(pid)
                pid_dict[pid] = p
        idhtml = HtmlLib.create_html_with_empty_head_body()
        idbody = HtmlLib.get_body(idhtml)
        idul = lxml.etree.SubElement(idbody, "ul")
        for pid in pid_list:
            idli = lxml.etree.SubElement(idul, "li")
            ida = lxml.etree.SubElement(idli, "a")
            ida.attrib["href"] = f"./html_with_ids.html#{pid}"
            ida.text = pid
        if outfile:
            HtmlLib.write_html_file(inhtml, outfile=outfile, debug=True)
        if idfile:
            HtmlLib.write_html_file(idhtml, idfile)
        if parafile and outfile:
            # this is too bulky normally
            print(f"searching {outfile} for p@ids")
            idhtml = lxml.etree.parse(str(outfile), HTMLParser())
            pids = idhtml.xpath(".//p[@id]")
            print(f"pids {len(pids)} {pids[:20]}")
            for pid in pids[:10]:
                print(f"pid: {pid.attrib['id']}")
            parahtml = HtmlLib.create_html_with_empty_head_body()
            parabody = HtmlLib.get_body(parahtml)
            paraul = ET.SubElement(parabody, "ul")
            for pid, p in pid_dict.items():
                if len(p) == 0:
                    print(f"cannot find id {pid}")
                    continue
                parali = ET.SubElement(paraul, "li")
                h2 = ET.SubElement(parali, "h2")
                h2.text = pid
                parali.append(copy.deepcopy(p))
            HtmlLib.write_html_file(parahtml, outfile=parafile, debug=True)


    @property
    @abstractmethod
    def raw_html(self):
        pass

    @property
    @abstractmethod
    def cleaned_html(self):
        pass

    def remove_unnecessary_markup(self, infile):
        """
        removes markukp from files downloaded from IPCC site
        :param infile: html file
        :return: html_elem for de_gatsby or de_wordpress etc.
        """

        html_elem = lxml.etree.parse(str(infile), HTMLParser())
        assert html_elem is not None
        head = HtmlLib.get_head(html_elem)
        IPCC.add_styles_to_head(head)
        removable_xpaths = self.get_removable_xpaths()
        IPCC.remove_unnecessary_containers(html_elem, removable_xpaths=removable_xpaths)
        return html_elem


class Gatsby(WebPublisherTool):

    def __init__(self, filename=None):
        self.filename = filename if filename else HTML_WITH_IDS
        self.container_levels = ["h1-container", "h2-container", "h3-container", "h4-container"]

    def get_removable_xpaths(self):
        removable_xpaths = [
            ".//div[contains(@class,'gx-3') and contains(@class,'gy-5') and contains(@class,'ps-2')]",
            # this fails
            # ".//div[contains(@class,'col-lg-10') and contains(@class,'col-12') and contains(@class,'offset-lg-0')]",
            ".//*[@id='___gatsby']",
            ".//*[@id='gatsby-focus-wrapper']/div",
            ".//*[@id='gatsby-focus-wrapper']",
            ".//*[@id='footnote-tooltip']",
            ".//div[contains(@class,'s9-widget-wrapper') and contains(@class,'mt-3') and contains(@class,'mb-3')]",
            ".//div[contains(@class,'chapter-figures')]",
            ".//header/div/div/div/div",
            ".//header/div/div/div",
            ".//header/div/div",
            ".//header/div",
            ".//section[contains(@class,'mb-5') and contains(@class, 'mt-5')]",
            ".//div[contains(@class,'container') and contains(@class, 'chapters') and contains(@class, 'chapter-')]",
            ".//*[contains(@id, 'footnote-tooltip-text')]",
            ".//div[@id='chapter-figures']/div/div/div/div",
            ".//div[@id='chapter-figures']/div/div/div",
            ".//div[@id='chapter-figures']/div/div",
            ".//div[@id='chapter-figures']/div",
            ".//div[@id='chapter-figures']//div[@class='row']",
        ]
        return removable_xpaths

    def create_and_add_id(self, id, p, parent, pindex, debug=False):
        pid = None
        match = re.match("h\d-\d+-siblings", id)
        if not match:
            if id.startswith("chapter-") or (id.startswith("_idContainer") or id.startswith("footnote")):
                pass
            else:
                if debug:
                    print(f"cannot match {id}")
        else:
            grandparent = parent.getparent()
            grandid = grandparent.get("id")

            match = grandid is not None and re.match(
                "\\d+(\\.\\d+)*|(box|cross-chapter-box|cross-working-group-box)-\\d+(\\.\\d+)*|executive-summary|FAQ \d+(\\.\\d+)*|references",
                grandid)
            if not match:
                if debug:
                   print(f"grandid does not match {grandid}")
            else:
                pid = f"{grandid}_p{pindex}"
                p.attrib["id"] = pid
        return pid

    @property
    def raw_html(self):
        return GATSBY

    @property
    def cleaned_html(self):
        return DE_GATSBY

    def raw_to_paras_and_ids(self, topdir, outdir=None):
        globx = f"{topdir}/**/{self.raw_html}.html"
        infiles = FileLib.posix_glob(globx, recursive=True)
        for infile in infiles:
            htmlx = self.remove_unnecessary_markup(infile)
            if not outdir:
                outdir = Path(infile).parent
                outdir.mkdir(parents=False, exist_ok=True)

            outfile = Path(outdir, f"{self.cleaned_html}.html")
            HtmlLib.write_html_file(htmlx, outfile, debug=True)
            infile = outfile
            # add ids
            outfile = str(Path(outdir, f"{HTML_WITH_IDS}.html"))
            idfile = str(Path(outdir, f"{ID_LIST}.html"))
            parafile = str(Path(outdir, f"{PARA_LIST}.html"))
            self.add_para_ids_and_make_id_list(infile, idfile=idfile, parafile=parafile, outfile=outfile)

    def analyse_containers(self, container, level, ul, filename=None, debug=False):
        """Part of ToC making"""
        container_xpath = f".//div[contains(@class,'{self.container_levels[level]}')]"
        h_containers = container.xpath(container_xpath)

        texts = []
        for h_container in h_containers:
            self.add_container_infp_to_tree(debug, filename, h_container, level, texts, ul)

    def add_container_infp_to_tree(self, debug, filename, h_container, level, texts, ul):
        if debug:
            print(f"id: {h_container.attrib['id']}")
        h_elems = h_container.xpath(f"./h{level + 1}")
        text = "???" if len(h_elems) == 0 else ''.join(h_elems[0].itertext()).strip()
        if debug:
            print(f"text: {text}")
        texts.append(text)
        li = ET.SubElement(ul, "li")
        a = ET.SubElement(li, "a")
        target_id = h_container.attrib["id"]
        a.attrib["href"] = f"./{filename}#{target_id}"
        span = ET.SubElement(a, "span")
        span.text = text
        ul1 = ET.SubElement(li, "ul")
        if level < len(self.container_levels):
            self.analyse_containers(h_container, level + 1, ul1, filename=filename)

    def make_header_and_nav_ul(self, body):
        """Part of ToC making"""
        header_h1 = body.xpath("div//h1")[0]
        toc_title = header_h1.text
        toc_html, ul = self.make_nav_ul(toc_title)
        return toc_html, ul

    def make_nav_ul(self, toc_title):
        """Part of ToC making"""
        toc_html = HtmlLib.create_html_with_empty_head_body()
        body = HtmlLib.get_body(toc_html)
        toc_div = ET.SubElement(body, "div")
        toc_div.attrib["class"] = "toc"
        toc_div_div = ET.SubElement(toc_div, "div")
        toc_div_span = ET.SubElement(toc_div_div, "span")
        toc_div_span.text = toc_title
        nav = ET.SubElement(toc_div, "nav")
        nav.attrib["role"] = "doc-top"
        ul = ET.SubElement(nav, "ul")
        return toc_html, ul

    def add_ids(self, de_gatsby_file, outdir, assert_exist=False, min_id_sizs=10000, min_html_size=100000, min_para_size=100000):
        """adds ids to paras (and possibly sections)
        relies on convention naming
        creates
        * html_with_ids.html
        * id_list.html
        * para_list.html
        :param de_gatsby_file: outputb from gatsby-raw => gatsby => de_gatsby (may change)
        :param outdir: ouput directory
        :param assert_exist: ifg True runs assrt on existence and file_size
        :return:  html_ids_file, idfile, parafile
        """
        html_ids_file = Path(outdir, f"{HTML_WITH_IDS}.html")
        idfile = Path(outdir, f"{ID_LIST}.html")
        parafile = Path(outdir, f"{PARA_LIST}.html")
        self.add_para_ids_and_make_id_list(
            infile=de_gatsby_file, idfile=idfile, outfile=html_ids_file, parafile=parafile)
        if assert_exist:
            abort = False
            FileLib.assert_exist_size(idfile, minsize=min_id_sizs, abort=abort)
            FileLib.assert_exist_size(html_ids_file, minsize=min_html_size, abort=abort)
            FileLib.assert_exist_size(parafile, minsize=min_para_size, abort=abort)
        return html_ids_file, idfile, parafile



class Wordpress(WebPublisherTool):

    @property
    def raw_html(self):
        return WORDPRESS

    @property
    def cleaned_html(self):
        return DE_WORDPRESS

    def create_and_add_id(self, id, p, parent, pindex, debug=False):
        """ NOT YET FINALISED"""
        pid = None
        # section-2-1-2-block-1
        section_res = [
            "section-\\d+(-\\d+)*-block-\\d+",
            "article-executive-summary-chapter(-\\d+)+-block-\\d+",
            "article-chapter(-\\d+)+-references-block-1",
            "article(-\\d+)+-about-the-chapter-block-\\d+",
            "article(-\\d+)+-block-\\d+",
            "article-frequently-asked-questions-chapter(-\\d+)+-block-\\d+",
        ]
        for section_re in section_res:
            match = re.match(section_re, id)
            if match:
                break
        if not match:
            if debug:
                print(f"cannot match |{id}|")
        else:
            if debug:
                print(f"matched id |{id}|")
            if not pindex:
                pindex = parent.index(p)
            pid = f"{id}_p{pindex}"
            p.attrib["id"] = pid
        return pid

    @classmethod
    def get_removable_xpaths(self):
        removable_xpaths = [
            "/html/head/style",
            "/html/head/link",
            "/html/head//button",
            "/html/head/script",

            "/html/body/script",
            "/html/body/header[div[nav]]",
            "/html/body/nav",
            "/html/body/main/nav",
            "/html/body/footer",
            "/html/body/section[@id='chapter-next']",
            "//article[@id='article-chapter-downloads']",
            "//article[@id='article-supplementary-material']",
            "//div[@class='share']",
            # "/html/body//div[@class='nav2'][nav]",
            # "/html/body//div[@class='ref-tooltip'][textarea]",
            # "/html/body//div[@class='share-tooltip']",
            # "/html/body//div[@class='dropdown'][button]",
            # "/html/body//div[@class='section-tooltip']",
            # "/html/body//div[button]",
            # "/html/body//a[button]",
            # "/html/body//span[@class='share-block']",
            # "/html/body//button",
            # "/html/body//div[contains(@class,'related_pages')]",
            # "/html/body//div[@id='gatsby-announcer']",
            # "/html/body//noscript",
            # "/html/body//footer",

        ]
        return removable_xpaths

    def get_pid(self):
        return "PID NYI"


class IPCCSections:

    @classmethod
    def get_ipcc_regexes(cls, front_back="Table of Contents|Frequently Asked Questions|Executive Summary|References"):
        """
        :param front_back: common section headings (not numbered)
        :return: (section_regex_dict, section_regexes) to manage regexes (largely for IPCC).

        The dict is more powerful but doesn't work properly yet

        """
        return cls.get_section_regexes(), cls.get_section_regex_dict(front_back)

    @classmethod
    def get_section_regexes(cls):
        section_regexes = [
            # C: Adaptation...
            ("section",
             #                f"\s*(?P<id>Table of Contents|Frequently Asked Questions|Executive Summary|References|(?:(?:[A-G]|\d+)[\.:]\d+\s+[A-Z]).*"),
             fr"\s*(?P<id>Table of Contents|Frequently Asked Questions|Executive Summary|References"
             fr"|(?:[A-Z]|\d+)[.:]\d*)\s+[A-Z].*"),
            # 7.1 Introduction
            ("sub_section",
             fr"(?P<id>FAQ \d+\.\d+"
             fr"|(?:\d+\.\d+"
             fr"|[A-Z]\.\d+)"
             fr"\.\d+)"
             fr"\s+[A-Z]*"),  # 7.1.2 subtitle or FAQ 7.1 subtitle D.1.2 Subtitle
            ("sub_sub_section",
             fr"(?P<id>"
             fr"(?:\d+\.\d+\.\d+\.\d+"  # 7.1.2.3 subsubtitle
             fr"|[A-Z]\.\d+\.\d+)"
             fr")\s+[A-Z].*")  # D.1.3
        ]
        return section_regexes

    @classmethod
    def get_section_regex_dict(cls, front_back):
        section_regex_dict = {
            "num_faq": {
                "file_regex": "NEVER.*/spm/.*",  # check this
                "sub_section": fr"(?P<id>FAQ \d+\.\d+)"
            },
            "alpha_sect": {
                "file_regex": ".*(srocc).*/spm/.*",  # check this
                "desc": "sections of form 'A: Foo', 'A.1 Bar', 'A.1.2 'Baz'",
                "section": fr"\s*(?P<id>[A-Z][.:]\s+[A-Z].*)",  # A: Foo
                "sub_section": fr"\s(?P<id>[A-Z]\.\d+\.\d+)\s+[A-Z]*",  # A.1 Bar
                "sub_sub_section": fr"\s(?P<id>[A-Z]\.\d+\.\d+)\s+[A-Z]*"  # A.1.2 Plugh
            },
            "num_sect_old": {
                "file_regex": ".*NEVER.*",
                "desc": "sections of form '1. Introduction', "
                        "subsections '1.2 Bar' "
                        "subsubsections '1.2.3 Plugh'"
                        "subsubsubsections  '1.2.3.4 Xyzzy (may not be any)",
                "section": fr"\s*(?P<id>(?:{front_back}|\s*\d+[.:]?)\s+[A-Z].*",  # A: Foo
                "sub_section": fr"\s(?P<id>\d+\.\d+)\s+[A-Z].*",  # A.1 Bar
                "sub_sub_section": fr"\s(?P<id>\d+\.\d+\.\d+)\s+[A-Z].*"  # A.1.2 Plugh

            },
            "num_sect": {
                "file_regex": ".*/syr/lr.*",
                "desc": "sections of form '1. Introduction', "
                        "subsections '1.2 Bar' "
                        "subsubsections '1.2.3 Plugh'"
                        "subsubsubsections  '1.2.3.4 Xyzzy (may not be any)",
                "section": fr"\s*(?P<id>{front_back})"
                           fr"|Section\s*(?P<id1>\d+):\s*[A-Z].*"
                           fr"|\s*(?P<id2>\d+)\.\s+[A-Z].*",  # A: Foo
                "sub_section": fr"\s*(?P<id>\d+\.\d+)\s+[A-Z].*",  # 1.1 Bar
                "sub_sub_section": fr"\s(?P<id>\d+\.\d+\.\d+)\s+[A-Z].*"  # A.1.2 Plugh

            },
            "num_sect_new": {
                "file_regex": fr"NEW.*/syr/lr.*",
                "sections": {
                    "desc": f"sections of form '1. Introduction', "
                            f"subsections '1.2 Bar' "
                            f"subsubsections '1.2.3 Plugh'"
                            f"subsubsubsections  '1.2.3.4 Xyzzy (may not be any)",
                    "section": {
                        "desc": "sections of form '1. Introduction' ",
                        "regex": fr"\s*(?P<id>{front_back}|\s*\d+[.:]?)\s+[A-Z].*",  # A: Foo
                    },
                    "sub_section": {
                        "desc": "sections of form ''1.2 Bar' ",
                        "regex": fr"\s(?P<id>\d+\.\d+)\s+[A-Z].*",  # A.1 Bar
                    },
                    "sub_sub_section": fr"\s(?P<id>\d+\.\d+\.\d+)\s+[A-Z].*",  # A.1.2 Plugh
                },
                "references": "dummy"

            },
        }
        return section_regex_dict

    @classmethod
    def get_major_section_names(cls):
        return "Table of Contents|Frequently Asked Questions|Executive Summary|References"

    def xxx(entry):
        anchors = entry.xpath(f"{H_A}")
        # if len(anchors) != 1:
        #     continue
        anchor0 = anchors[0]
        id = anchor0.get(A_ID)
        print(f">>{id}")
        spans = entry.xpath(f"{H_SPAN}")
        text = " ".join(spans[1:])
        href_as = entry.xpath(f"{H_SPAN}/{H_A}")
        return href_as

    @classmethod
    def get_body_for_syr_lr(cls, ar6_dir):
        path = Path(ar6_dir, "syr", "lr", "html", "fulltext", "groups_groups.html")
        group_html = lxml.etree.parse(str(path))
        body = group_html.xpath("//body")[0]
        return body

    @classmethod
    def create_author_dict_from_sections(cls, body):
        """
        extracts authors and countries from
        <div left="56.64" right="156.14" top="709.44">
          <span ... class="s0">Core Writing Team: </span>
          <span ... class="s1001">Hoesung Lee (Chair), Katherine Calvin (USA), Dipak Dasgupta (India/USA), Gerhard Krinner (France/Germany),
        where there are several labels for author lists ("author_sects")
        """

        # for splitting author/country
        author_re = re.compile(f"\\s*(?P<author>.*\\S)\\s*\\((?P<country>.*\\S)\\).*")
        author_sects = [
            CORE_TEAM,
            EXTENDED_TEAM,
            CONTRIB_AUTHORS,
            REVIEW_EDITORS,
            SCIENTIFIC_STEERING,
            VISUAL_INFORM,
        ]
        author_dict = dict()
        for author_sect in author_sects:
            author_dict[author_sect] = dict()
            text = cls.extract_text_from_following_span(author_sect, body)
            authors = text.split(", ")
            for author in authors:
                author_match = author_re.match(author)
                if author_match:
                    author_name = author_match.group(AUTHOR)
                    country = author_match.group(COUNTRY)
                    author_dict[author_sect][author_name] = country
        return author_dict

    @classmethod
    def extract_text_from_following_span(cls, sect_name, body):
        """extracts text from normal span (1) following bold text (0)
        """
        _div = body.xpath(f"//div[span[contains(., '{sect_name}')]]")
        return _div[0].xpath("./span")[1].text if len(_div) > 0 else None


class IPCCAnchor:
    """holds statements from IPCC Reports and outward links"""

    @classmethod
    def create_confidences(cls, div):
        """iterates over all spans in div, terminating if "* confidence is found,
         starting new div until end. ignores {targets}
        some chunks may not make grammatical sense
        :return: divs with original span"""
        curly_re = re.compile("(?P<pre>.*)\\{(?P<targets>.*)\\}(?P<post>.*)")
        confidence_re = re.compile("\\s*\\(?(?P<level>.*)\\s+confidence\\s*\\)?\\s*(?P<post>.*)")
        parent = div.getparent()
        current_div = None
        spans = list(div.xpath("./span"))
        for span in spans:
            if not span.text:
                continue
            if current_div is None:
                current_div = lxml.etree.SubElement(parent, H_DIV)
            if "confidence" in span.text and len(span.text) < 50:  # because confidence can occur elsewhere
                current_div.append(span)
                match = confidence_re.match(span.text)
                level = match.group("level")
                span.attrib["confidence"] = level
                logger.debug(f"confidence: {level}")
                span.attrib["class"] = "confidence"
                span.attrib["style"] = "background: #ddffff"
                # confidence ends div
                current_div = None
            else:
                match = curly_re.match(span.text)
                if match:
                    span = lxml.etree.SubElement(current_div, "span")
                    span.text = match.group("pre")
                    span = lxml.etree.SubElement(current_div, "span")
                    span.attrib["class"] = "targets"
                    span.text = match.group("targets")
                    span = lxml.etree.SubElement(current_div, "span")
                    span.text = match.group("post")
                else:
                    current_div.append(span)
        parent.remove(div)


class IPCCTargetLink:
    """link between IPCC reports"""

    def __init__(self, ipcc_id, span_link):
        self.ipcc_id = ipcc_id
        self.span_link = span_link
        self.link_factory = None
        self.bad_links = set()

    def _follow_ipcc_target_link(
            self,
            ipcc_target_link,
            anchor_link,
            wg_dict=None,
            url_cache=None,
            stem="ipcc/ar6",
            leaf_name=None):

        if not leaf_name:
            logger.warning(f"must give leaf name")
            return None, None
        if anchor_link is not None:
            anchor = lxml.etree.SubElement(anchor_link, "a")
            anchor.text = ipcc_target_link

        if not self.make_report_chapter_id(ipcc_target_link, wg_dict):
            self.bad_links.add(ipcc_target_link)
            return None, None
        (chapter, id, report) = self.make_report_chapter_id(ipcc_target_link, wg_dict)

        filepath = f"{stem}/{report}/{chapter}/{leaf_name}"
        html = None
        branch = "main"
        site = self.link_factory.target.site
        site = "https://raw.githubusercontent.com" if not site else site
        username = self.link_factory.target.username
        repository = self.link_factory.target.repository
        target_url = f"{site}/{username}/{repository}/{branch}/{filepath}"
        try:
            html = XmlLib.read_xml_element_from_github(github_url=target_url, url_cache=url_cache)
        except Exception as e:
            logger.warning(f"failed to read HTML {e}")
        if html is None:
            logger.warning(f"failed to read HTML")
            return None, None
        sections = html.xpath(f"//*[@id='{id}']")
        target_text = ""
        for i, section in enumerate(sections):
            target_text += ("" if i == 0 else "SEP") + ''.join(section.getparent().itertext())
        return (id, target_text) if target_text else (None, None)

    def make_report_chapter_id(self, ipcc_link, wg_dict):
        """splits REPORT CHAP ID string
        e.g. WGI SPM A.1.2.3 => wg1/spm#A.1.2.3
        :return: None if cannot parse
        """
        href = ipcc_link.strip().split()
        if len(href) != 3:
            logger.info(f"target must have 3 components {ipcc_link}")
            return None
        report = wg_dict.get(href[0])
        if not report:
            logger.info(f"cannot find report from {href[0]}")
            return None
        chapter = href[1].lower() if len(href) > 1 else None
        chapters = ["spm", "lr", "ts"]
        if chapter not in chapters:
            logger.info(f"only chapters : {chapters} allowed")
            return None

        id = href[2] if len(href) > 2 else None
        if not id:
            return None
        return chapter, id, report

    def follow_ipcc_target_link(self, url_cache=None, leaf_name=None):
        """
        :return: tuple (id, target text)
        """
        link_factory = self.link_factory
        ipcc_id = self.ipcc_id
        anchor_link = self.span_link

        # github_url = link_factory.create_github_url()

        target_result_tuple = self._follow_ipcc_target_link(ipcc_id, anchor_link, wg_dict=link_factory.wg_dict,
                                                            url_cache=url_cache, leaf_name=leaf_name, )
        logger.info(f"type {type(target_result_tuple)} len {len(target_result_tuple)}")
        (idx, target_text) = target_result_tuple
        logger.info(f"id {type(idx)} text {type(target_text)}")
        return (idx, target_text)

    @classmethod
    def read_links_from_span_and_follow_to_ipcc_repository_KEY(cls, anchor_div, leaf_name, link_factory,
                                                               span_with_curly_ids):
        """
        reads a span in an chor_div and extracts curly link_ids
        splits the curly content into target ids (curly_count)

        Follows these to repository
        USES links to github repo, so SLOW!
        returns a table with (<= curly_count

        :param anchor_div: if not None adds an anchor
        """
        if anchor_div is None:
            raise ValueError(f" anchor_div must not be None")

        anchor_id = anchor_div.attrib.get("id")
        if not anchor_id:
            spans = anchor_div.xpath("./span")
            if len(spans) > 0:
                anchor_id = spans[0].get("id")
        target_to_anchor_table = []
        bad_links = set()
        text = ''.join(anchor_div.itertext())
        if not anchor_id:
            logger.warning(f" anchor_id is None for {text[:50]}")
            return target_to_anchor_table, bad_links
        curly_brace_link_content_parser = re.compile(".*{(?P<links>[^}]+)}.*")
        match = curly_brace_link_content_parser.match(span_with_curly_ids.text)
        if match:
            cls.resolve_links(anchor_div, anchor_id, bad_links, leaf_name, link_factory, match, span_with_curly_ids,
                              target_to_anchor_table)
        if target_to_anchor_table:
            # this is just debug
            logger.debug(f"**ROWS**{len(target_to_anchor_table)}\n{target_to_anchor_table}")
            anchor_target_df = pd.DataFrame(target_to_anchor_table,
                                            columns=["a_id", "a_text", "ipcc_id", "t_id", "t_text"])
            logger.info(f"anchor_to_target dataframe:\n {anchor_target_df}")
        logger.debug(f"bad links {bad_links}")
        return target_to_anchor_table, bad_links

    @classmethod
    def resolve_links(cls, anchor_div, anchor_id, bad_links, leaf_name, link_factory, match, span_with_curly_ids,
                      target_to_anchor_table):
        links_text = match.group("links")
        ipcc_ids = re.split(",|;", links_text)
        anchor_span_link = ET.SubElement(anchor_div, "span")
        anchor_span_link.attrib["id"] = anchor_id
        url_cache = URLCache()
        parent_div = span_with_curly_ids.getparent()
        anchor_text = ''.join(parent_div.itertext())
        for ipcc_id in ipcc_ids:
            target_link = link_factory.create_target_link(ipcc_id, anchor_span_link)
            (target_id, target_text) = target_link.follow_ipcc_target_link(url_cache=url_cache,
                                                                           leaf_name=leaf_name)
            if (target_id, target_text):
                anchor_to_target_row = [anchor_id, anchor_text, ipcc_id, target_id, target_text]
                target_to_anchor_table.append(anchor_to_target_row)
            bad_links.update(target_link.bad_links)

    @classmethod
    def create_dataframe_from_IPCC_target_ids_in_curly_brackets_divs_KEY(
            cls, divs, leaf_name, link_factory, max_divs=9999999):

        tables = []
        bad_link_set = set()
        tables.append(["anchor_text", "anchor_id", "target_id", "target_text"])
        curly_re = re.compile(".*\\{(P<curly>[.^\\}]*)\\}.*")
        for div in divs[:max_divs]:
            cls.follow_ids_in_curly_links(bad_link_set, curly_re, div, leaf_name, link_factory, tables)
            IPCCAnchor.create_confidences(div)
        logger.debug(f" tables {len(tables)}")
        logger.warning(f"bad_link_set {bad_link_set}")
        df = pd.DataFrame(tables)
        return df

    @classmethod
    def follow_ids_in_curly_links(cls, bad_link_set, curly_re, div, leaf_name, link_factory, table):
        id_spans = div.xpath(f"./{H_SPAN}[@id]")
        anchor_id = None if len(id_spans) == 0 else id_spans[0].attrib.get(A_ID)
        spans = div.xpath(f"./{H_SPAN}[@class='targets']")
        for span in spans:
            match = curly_re.match(span.text)
            if match:
                logger.info(f"match group {match.group('curly')}")
            rows, bad_links = IPCCTargetLink.read_links_from_span_and_follow_to_ipcc_repository_KEY(div, leaf_name,
                                                                                                    link_factory,
                                                                                                    span)
            bad_link_set.update(bad_links)
            if rows:
                table.extend(rows)


class IPCCTarget:
    """
    parses target string and maybe caches some data
    """

    def __init__(self):
        self.raw = ""  # raw text
        self.package = ""  # WG2, SRCCL, etc.
        self.section = ""  # Chapter, Annexe, etc
        self.object = ""  # Figure, Table, etc
        self.subsection = ""  # A, B,   A.1.2, etc
        self.unparsed_str = ""  # anything else

    # class Target:

    def __str__(self):
        ss = self.__repr__()
        return ss

    def create_list(self):
        ll = [self.package, self.section, self.object, self.subsection, self.unparsed_str, self.raw]
        return ll

    def __repr__(self):
        return "|".join(self.create_list())

    # class Target:

    @classmethod
    def create_target_from_fields(cls, string):
        """
        parse __str__ string into field where possible

        package, section, object, subsection, unparsed, raw
        :param string: stringn with space-separated fields in the Target
        """
        target = None
        strings = string.split(',')
        if strings and len(strings) >= 5:
            target = IPCCTarget()
            target.package = strings[0]
            target.section = strings[1]
            target.object = strings[2]
            target.subsection = strings[3]
            target.unparsed_str = strings[4]
        if strings and len(strings) == 6:
            target.raw = strings[5]

        # assert target is not None, f"cannot create target from {str}"
        return target

    # class Target:

    @classmethod
    def create_target_from_str(cls, string):
        """
        parse string into hierarchy where possible
        package, section, object, subsection, section
        """
        target = IPCCTarget()
        target.raw = string
        # string = cls.add_missing_commas(string)
        strings = re.split("\\s+", string)
        ptr = 0
        target.package, ptr = cls.parse_chunk(strings, ptr, package_re, "package")
        target.section, ptr = cls.parse_chunk(strings, ptr, section_re, "section")
        target.object, ptr = cls.parse_chunk(strings, ptr, object_re, "object")
        target.subsection, ptr = cls.parse_chunk(strings, ptr, subsection_re, "subsection")
        # target.subsubsection, ptr = cls.parse_chunk(strings, ptr, subsubsection_re, "subsubsection")
        if len(strings) > ptr:
            target.unparsed_str = ' '.join(strings[ptr:])
        return target

    # class Target:

    @classmethod
    def parse_chunk(cls, strings, ptr, pattern, name):
        """
        takes new chunk off the list (should be a stack) and parsers
        If successful returns the chunk and advances pointer; else returns "" and no advance
        """
        if ptr >= len(strings):
            return "", ptr
        try:
            match = re.match(pattern, strings[ptr])
        except Exception as e:
            raise ValueError(f"regex error {e} in {pattern}")
        if match:
            return strings[ptr], ptr + 1
        return "", ptr

    # class Target:

    def normalize(self):
        """removes porse errors and inconsistency of formats, etc
        """
        unparsed_words = self.unparsed_str.split()
        if len(unparsed_words) >= 1:
            # print(f">>>> norm {self}")
            first = unparsed_words[0]
            if first == 'SPM':
                pass
            # section in unparsed and missing/duplicated in self.section
            if re.match(section_re, first) and self.section == '' or self.section == first:
                self.section = first
                unparsed_words.pop(0)
            # move single unparsed to empty subsection
            if len(unparsed_words) == 1 and self.subsection == '':
                self.transfer_first_unparsed_to_subsection(unparsed_words)
            # named CCBox
            if self.object == 'CCBox':
                # print(f" self ccbox: {self}")
                if self.subsection == '':
                    if len(self.unparsed_str) == 1 or \
                            len(self.unparsed_str) >= 1 and self.unparsed_str[0].isupper():
                        self.transfer_first_unparsed_to_subsection(unparsed_words)
                        unparsed_words.pop()
            # chapter/ES ['WGII', '', '', '7', ['ES'], 'WGII 7 ES']
            if unparsed_words == ['ES']:
                print("self ES {self}")
            if len(unparsed_words) == 3 and unparsed_words[:2] == ["in", "Chapter"]:
                if self.section == '':
                    self.section = unparsed_words[1]  # type
                    section_number = unparsed_words[2]  # number
                    self.subsection = section_number + "." + self.subsection
                    unparsed_words = unparsed_words[3:]
                    # print(f"in_Chapter {self}")

            if unparsed_words and self.subsection == unparsed_words[0]:
                unparsed_words = unparsed_words[1:]
            self.unparsed_str = " ".join(unparsed_words)
            if self.unparsed_str != "":
                print(f"UNPARSED {self}")

    @classmethod
    def make_dirs_from_targets(cls, common_target_tuples, temp_dir):
        assert temp_dir is not None, f"must have temp_dir"
        for target_string in common_target_tuples:
            target_strs = target_string[0]
            # TODO make parsable target string
            target = IPCCTarget.create_target_from_fields(target_strs)
            if not target:
                # print(f"bad target {target_string}")
                continue
            target.make_directories(temp_dir)

    def make_directories(self, temp_dir):
        """makes directories from sections/subsections, etc"""
        if not self.package:
            pass
        package_dir = Path(temp_dir, self.package)
        package_dir.mkdir(exist_ok=True)
        parent_dir = package_dir
        if self.section:
            section_dir = Path(parent_dir, self.section)
            section_dir.mkdir(exist_ok=True)
            parent_dir = section_dir
        if self.object:
            object_dir = Path(parent_dir, self.object)
            object_dir.mkdir(exist_ok=True)
            parent_dir = object_dir
        if self.subsection:
            subsection_file = Path(parent_dir, self.subsection)
            subsection_file.touch()

    # class Target:

    def transfer_first_unparsed_to_subsection(self, unparsed_words):
        # words = self.unparsed_str.split()
        self.subsection = unparsed_words[0]
        # words = " ".join(words[1:])
        # return words

    def type(self):
        pass


class TargetExtractor:
    """
    extracts nodes/hyperlinks in text
    """
    UNMATCHED = "unmatched"
    TARGET_LIST_RE = "node_re"
    TARGET_RE = "split_node_re"
    TARGET_VALUE_RE = "name_value_re"

    def __init__(self):
        self.column_dict = dict()

    # class TargetExtractor

    def read_columns(self, names):
        assert names and type(names) is list, f"must give list of names"
        for col_no, name in enumerate(names):
            if name.strip() == "" or " " in name:
                raise ValueError(f"names must not be/have whitespace [{name}]")
            if name in self.column_dict:
                raise ValueError(f"duplicate column name {name}")
            self.column_dict[name] = col_no

    @classmethod
    def create_target_extractor(cls, column_names):
        try:
            target_extractor = TargetExtractor()
            target_extractor.read_columns(column_names)
            return target_extractor
        except ValueError as e:
            raise e

    # class TargetExtractor

    def extract_node_dict_lists_from_file(self, xml_inpath, div_xp=None, regex_dict=None):
        """
        extracts lists of nodes in text. Nodes are defined by xpath and regex
        :param xml_inpath: file with divs
        :param div_xp: Must return <div> elements at present
        :param regex_dict: dict of regexes to extract nodes
        """
        assert xml_inpath.exists(), f"{xml_inpath} should exist"
        tree = ET.parse(str(xml_inpath))
        root = tree.getroot()
        HtmlUtil.add_generated_ids(root)  # adds ids to each element
        if div_xp is None or regex_dict is None:
            return None
        print(f"div_xp {div_xp}")
        divs_with_text = list(root.xpath(div_xp))
        ll = len(divs_with_text)
        print(f"xpath/tree texts {ll}")
        node_dict_list_list = list()
        for div in divs_with_text:
            if type(div) is not _Element:
                raise ValueError(f"div_xpath must return divs")
            node_dict_list = self.extract_nodes_by_regex(div, regex_dict=regex_dict)
            node_dict_list_list.append(node_dict_list)
        return node_dict_list_list

    # class TargetExtractor

    def extract_nodes_by_regex(self, div_with_text, regex_dict=None) -> list:
        """
        Searches text with hierachical regexes
        """
        div_id = div_with_text.attrib.get('id')
        text_in_div = ''.join(div_with_text.itertext())
        print(f"{div_id} {text_in_div[:100]}")

        ptr = 0
        node_dict_list = list()
        if regex_dict is None:
            return node_dict_list
        reg1 = regex_dict.get(TargetExtractor.TARGET_LIST_RE)
        reg2 = regex_dict.get(TargetExtractor.TARGET_RE)
        reg3 = regex_dict.get(TargetExtractor.TARGET_VALUE_RE)
        if reg1 is None or reg2 is None or reg3 is None:
            return node_dict_list
        while text_in_div[ptr:] is not None:
            ptr_ = text_in_div[ptr:]
            match = re.search(reg1, ptr_)
            if match is None:
                break
            ptr += match.span()[1]
            nodestr = match.group(1)
            nodes = re.split(reg2, nodestr)
            node_dict = defaultdict(list)
            node_dict_list.append(node_dict)
            for node in nodes:
                m = re.match(reg3, node)
                if m:
                    node_dict[m.group(1)].append(m.group(2))
                    node_dict["div_id"] = div_id
                    print(f"node_dict {node_dict}")
                    continue
                node_dict[TargetExtractor.UNMATCHED].append(node)
            pass
        pass
        return node_dict_list

    # class TargetExtractor

    def extract_anchor_paragraphs(self, div_xp, file, target_dict_from_text):
        """
        reads xml file , finds divs, applies regexes to find targetrefss in text
        """
        node_dict_list_list = self.extract_node_dict_lists_from_file(
            file,
            div_xp=div_xp,  # all paras wit curly {...
            regex_dict=target_dict_from_text)

        def_dict = defaultdict()

        for node_dict_list in node_dict_list_list:
            ll = len(node_dict_list)
            if ll > 1:
                print(f"*****node_dict_list {ll}")
                for node_dict in node_dict_list:
                    print(f"----{len(node_dict.keys())}----")
                    for key in node_dict.keys():
                        print(f"key {key} ")  # mainly unmatched but also Table, div_id
                        value_list = node_dict[key]
                        print(f"value_list {value_list}")
                        for value in value_list:
                            if value not in def_dict:
                                def_dict[value] = 0
                            def_dict[value] += 1
                    print("")
        return def_dict

    # class TargetExtractor

    @classmethod
    def add_missing_commas(cls, string):
        """
        some targets are (wrongly) concatenated
        """
        string = string.replace(" WG", ", WG")
        string = string.replace(" SR", ", SR")
        return string

    # class TargetExtractor

    @classmethod
    def create_normalized_target(cls, target_str):

        target_str = cls.clean_target_string(target_str)
        target = IPCCTarget.create_target_from_str(target_str)
        target.normalize()
        return target

    # class TargetExtractor

    @classmethod
    def clean_target_string(cls, target_str):
        """
        cleans typos from target string
        """
        subst_list = [
            ["SR\\s*1\\.5", "SR1.5 ", "rejoin package name"],
            ["WG1\\.", "WG1 ", "separate package from section"],
            ["TS\\.", "TS ", "separate subpackage from sections"],
            ["SPM\\.", "SPM ", "separate subpackage from sections"],
            ["\\s+", " ", "normalise to 1 space"],
            ["WPM", "SPM", "single instance"],
            ["WG\\s*I", "WGI", "remove internal sp ('WG II')"],
            ["Cross\\-([Cc]hapter)\\s*[Bb]ox", "CCBox", "Cross Chapter Box"],
            ["Cross\\-([Ss]ection)\\s*[Bb]ox", "CSBox", "Cross Section Box"],
            ["Cross\\-([Ww]orking\\s+[Gg]roup|WG)\\s+[Bb]ox", "CWGBox", "Cross Working Group"],
        ]

        for subst in subst_list:
            target_str = re.sub(subst[0], subst[1], target_str)  # separate subpackage from sections
        return target_str

    # class TargetExtractor

    @classmethod
    def extract_ipcc_fulltext_into_source_target_table(cls, file):
        """
        partly written by ChatGPT (2023-04-06) but mainly by PMR
        """
        tree = lxml.etree.parse(str(file))
        root = tree.getroot()
        # Initialize the table
        table = []
        unparsed = 0
        # TODO extract source_id from IPCC paragraphs
        section_re = re.compile("^([A-Z]|\\d)(\\.\\d+)*$")
        last_section_id = ""
        for paragraph in root.findall('.//div'):
            paragraph_id = paragraph.get('id')
            para_text = ''.join(paragraph.itertext())
            label = paragraph.findall("./span")
            strip = "no span" if not label else label[0].text.strip()
            section_match = section_re.match(strip)
            section_id = section_match.group(0) if section_match else ""
            if section_id != '':
                # print(f"section_id {section_id}")
                last_section_id = section_id
            unp, para_table = cls.match_id_and_targets_in_para(para_text, paragraph_id, last_section_id)
            unparsed += unp
            if para_table == []:
                continue
            table.extend(para_table)
        print(f"un/parsed: {unparsed}/{len(table)}")
        return table

    # class TargetExtractor

    @classmethod
    def match_id_and_targets_in_para(cls, para_text, paragraph_id, last_section_id):
        """

        """
        # print(f" IN last {last_section_id}")
        curly_re = re.compile("(.*){(.*)}(.*)")
        match_curly = curly_re.match(para_text)
        # targets = []
        subtable = []
        unparsed = 0
        max_para_text = 50
        if match_curly:
            curly_text = match_curly.group(2)
            curly_text = cls.add_missing_commas(curly_text)
            clause_parts = re.split('\\s*[:;,]\\s*', curly_text)
            for part in clause_parts:
                target_str = part.strip()
                if target_str == '':
                    continue
                target = cls.create_normalized_target(target_str)
                if len(target.unparsed_str) > 0:
                    unparsed += 1
                row = [paragraph_id, last_section_id,
                       target.raw, target.package, target.section, target.object, target.unparsed_str,
                       para_text[:max_para_text]]
                subtable.append(row)
        return unparsed, subtable

    # class TargetExtractor

    def find_commonest_in_node_lists(self, table, node_name=None):

        if not node_name:
            raise ValueError(f"node names are none")
        node_col = self.column_dict.get(node_name)
        if not node_col:
            raise ValueError(f"node name '{node_name}' not in column_dict {self.column_dict.keys()}")
        node_dict = defaultdict(int)
        for row in table:
            node_dict[row[node_col]] += 1
        node_counter = Counter(node_dict)
        common_node = [n for n in node_counter.most_common() if n[1] > 1]
        return common_node


packages = ["WGI", "WG1", "WGII", "WG2", "WGIII", "WG3", "SRCCL", "SR1.5", "SR15", "SROCC"]
subpackages = ["Chapter", "SPM", "TS", "ES"]
objects = ["Table", "Figure", "CCBox"]
subsections = ["A", "B", "C", "D", "E", "F"]

package_re = "WGI+|WG[123]|SR(?:CCL|OCC|1\\.?5)"
section_re = "Chapter|Anne(xe)?|SPM|SM|TS|ES|[Ss]ections?"
object_re = "[Ff]ig(ure)?|[Tt]ab(le)?|[Ff]ootnote|Box|CCBox|CSBox"
subsection_re = "^\\d+$|^[A-F]$|^ES|([A-E]?\\.?\\d+(\\.\\d+)?(\\.\\d+)?)"


# subsubsection_re = "[1-9](?:\\.[1-9]){0, 2}"


class LinkFactory:
    """"""

    class LinkNode:
        """filepath = stem/leaf_name and takes precedence over those"""

        def __init__(self, site=None, username=None, repository=None, branch=None,
                     stem=None, leaf_name=None, filepath=None):
            self.site = site
            self.username = username
            self.repository = repository
            self.branch = branch
            self.stem = stem
            self.leaf_name = leaf_name
            self.filepath = filepath

        def set_file_path(
                self,
                stem,
                leaf_name,
                filepath
        ):
            self.filepath = filepath if filepath else (stem + "/" + leaf_name) if stem and leaf_name else None

    #    class LinkFactory:

    def __init__(self):
        self.anchor = LinkFactory.LinkNode(site="https://raw.githubuser.com")
        self.target = LinkFactory.LinkNode(site="https://raw.githubuser.com")
        self.wg_dict = None

        self.link = None
        self.span_link = None

    #    class LinkFactory:

    @classmethod
    def create_factory(
            cls,
            anchor_site=None,
            anchor_username=None,
            anchor_repository=None,
            anchor_branch=None,
            anchor_stem=None,
            anchor_leaf_name=None,
            anchor_filepath=None,

            target_site=None,
            target_username=None,
            target_repository=None,
            target_branch=None,
            target_stem=None,
            target_leaf_name=None,
            target_filepath=None,

            wg_dict=None
    ):
        link_factory = LinkFactory()

        link_factory.anchor.site = anchor_site
        link_factory.anchor.username = anchor_username
        link_factory.anchor.repository = anchor_repository
        link_factory.anchor.branch = anchor_branch
        link_factory.anchor.set_file_path(anchor_stem,
                                          anchor_leaf_name,
                                          anchor_filepath)

        link_factory.target.site = target_site
        link_factory.target.username = target_username
        link_factory.target.repository = target_repository
        link_factory.target.branch = target_branch
        link_factory.target.set_file_path(target_stem,
                                          target_leaf_name,
                                          target_filepath)

        link_factory.wg_dict = wg_dict
        return link_factory

    #    class LinkFactory:

    # def create_ipcc_target_link(self, link, span_link):
    #     target_link = IPCCTargetLink(link, span_link)
    #     return target_link

    @classmethod
    def create_default_ipcc_link_factory(cls):
        anchor_username = target_username = "petermr"
        anchor_repository = target_repository = "semanticClimate"
        anchor_branch = target_branch = "main"
        anchor_stem = target_stem = "ipcc/ar6"
        target_leaf_name = "fulltext.annotations.id.html"
        wg_dict = {
            "WGI": "wg1",
            "wgi": "wg1",
            "WG2": "wg2",
            "wg2": "wg2",
            "WG3": "wg3",
            "wg3": "wg3",
        }
        link_factory = LinkFactory.create_factory(
            anchor_username=anchor_username,
            anchor_repository=anchor_repository,
            anchor_branch=anchor_branch,
            anchor_stem=anchor_stem,

            target_username=target_username,
            target_repository=target_repository,
            target_branch=target_branch,
            target_stem=target_stem,

            target_leaf_name=target_leaf_name,

            wg_dict=wg_dict
        )
        return link_factory

    #    class LinkFactory:

    def create_target_link(self, ipcc_id, anchor_span_link):
        target_link = IPCCTargetLink(ipcc_id, anchor_span_link)
        target_link.link_factory = self
        return target_link

    def create_github_url(self):
        github_url = HtmlLib.create_rawgithub_url(
            branch=self.anchor.branch,
            filepath=self.anchor.filepath,
            repository=self.anchor.repository,
            username=self.anchor.username
        )
        return github_url
