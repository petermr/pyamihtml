import json
import logging
from io import BytesIO
from pathlib import Path

import lxml
import pdfplumber

from pyamihtmlx.ami_html import HtmlUtil, P_FONTNAME, P_HEIGHT, P_STROKING_COLOR, P_NON_STROKING_COLOR, AmiSpan, P_TEXT, \
    HtmlGroup, HtmlStyle
from pyamihtmlx.ami_pdf_libs import create_thin_line_from_rect, AmiPDFPlumber
from pyamihtmlx.file_lib import FileLib
from pyamihtmlx.util import AmiLogger
from pyamihtmlx.xml_lib import HtmlLib, XmlLib

logger = AmiLogger.create_named_logger(__file__)
logger = logging.getLogger(__file__)

DICT_KEYSET = set([
    'annots',
    'bbox',
    'chars',
    'curves',
    'cropbox',
    'height',
    'images',
    'initial_doctop',
    'mediabox',
    'page_number',
    'rects',
    'rotation',
    'width',
])


class HtmlGenerator:
    # class HtmlGenerator
    """generates HTML from PDF
    """
    OUTPUT_PAGE_DIR = "output_page_dir"
    INPUT_PDF = "input_pdf"
    TOTAL_PAGES = "total_pages"


    @classmethod
    def create_sections(
            cls, input_pdf=None, section_regexes=None, total_pages="total_pages", outdir=None,
            group_stem="groups", use_svg=True, debug=False):
        """Messy. Requires writing html to pages and then stictching together
        """
        svg_dir = None
        if type(input_pdf) is BytesIO:
            if not outdir:
                logger.warning("No outdir so no files written")
        else:
            path = Path(input_pdf)
            if not path.exists():
                logger.warning(f"path does not exist {path}")
                return
            svg_dir = Path(path.parent, "svg") if use_svg else None
        logger.info(f"section_regexes ========== {section_regexes}")

        try:
            html_elem = cls.read_pdf_convert_to_html(
                group_stem=group_stem,
                input_pdf=input_pdf,
                section_regexes=section_regexes,
                outdir=outdir,
                debug=debug,
                svg_dir=svg_dir,
                max_edges=5000)
            print(f"debug divs: {len(html_elem.xpath('//div'))}")
            return html_elem
        except Exception as e:
            raise e

    # class HtmlGenerator

    @classmethod
    def read_pdf_convert_to_html(cls,
                                 input_pdf=None, group_stem="dummy_group", section_regexes=None,
                                 total_pages="total_pages", outdir=None, write=True,
                                 svg_dir=None, max_edges=10000, param_dict=None, max_lines=10, page_json_dir=None,
                                 debug=False):
        from pyamihtmlx.ami_pdf_libs import AmiPDFPlumber  # HORRIBLE

        if not input_pdf:
            raise FileNotFoundError("missing pdf")
        if type(input_pdf) is BytesIO:
            svg_dir = None
        else:
            input_pdf = Path(input_pdf)
            print(f"\n==================== {input_pdf} ==================")
            if not input_pdf.exists():
                raise FileExistsError(f"cannot find {input_pdf}")
            stem = input_pdf.stem
            outdir = outdir if outdir else Path(input_pdf.parent, "html", stem)
        ami_pdfplumber = AmiPDFPlumber(param_dict=param_dict)
        total_html_elem = cls.create_html_pages(
            ami_pdfplumber, input_pdf=input_pdf, outdir=outdir, debug=debug, outstem=total_pages,
            svg_dir=svg_dir, max_edges=max_edges, page_json_dir=page_json_dir, max_lines=max_lines)
        if total_html_elem is None:
            print(f" null element in {input_pdf}")
            return None
        print(f"total_pages elems: {len(total_html_elem.xpath('//div'))}")
        if outdir:
            input_html_path = str(Path(outdir, f"{total_pages}.html"))
            html_elem = lxml.etree.parse(input_html_path)
            print(f"total_pages content {len(html_elem.xpath('//div'))}")

            if section_regexes:
                HtmlGroup.make_hierarchical_sections_KEY(
                    html_elem, group_stem, section_regexes=section_regexes, outdir=outdir)
                print(f"after sections: {len(html_elem.xpath('//div'))}")
            HtmlStyle.extract_all_style_attributes_to_head(html_elem)
            return html_elem
        else:
            return None

    # class HtmlGenerator

    @classmethod
    def create_html_pages(cls, ami_pdfplumber, input_pdf=None, outdir=None, pages=None, debug=False,
                          outstem="total_pages", svg_dir=None, max_edges=10000, max_lines=100,
                          tidy_prims=True, page_json_dir=None):
        """
        :param tidy_primitives: convert thin rects to lines, and other layout stuff
        """
        from pyamihtmlx.ami_pdf_libs import AmiPlumberJson

        pre_plumber = HtmlGenerator.pmr_time()
        ami_plumber_json = ami_pdfplumber.create_ami_plumber_json(input_pdf, pages=pages)
        if ami_plumber_json is None:
            print(f" cannot create JSON {input_pdf}")
            return None
        assert (t := type(ami_plumber_json)) is AmiPlumberJson, f"expected {t}"
        total_html = HtmlLib.create_html_with_empty_head_body()
        if outdir:
            Path(outdir).mkdir(exist_ok=True, parents=True)
        total_html_page_body = HtmlLib.get_body(total_html)

        pre_parse = HtmlGenerator.pmr_time()
        logger.debug(f"PRE {round(pre_parse - pre_plumber)}")
        ami_json_pages = list(ami_plumber_json.get_ami_json_pages())
        post_parse = HtmlGenerator.pmr_time()
        logger.debug(f"PARSE {post_parse - pre_parse}")

        for i, ami_json_page in enumerate(ami_json_pages):
            page_start_time = HtmlGenerator.pmr_time()
            page_no = i + 1
            if debug:
                print(f"==============PAGE {page_no}================")
            html_page = cls.create_html_page(
                ami_pdfplumber, ami_json_page, outdir, debug=debug, page_no=page_no,
                svg_dir=svg_dir,
                page_json_dir=page_json_dir,
                max_edges=max_edges,
                max_lines=max_lines)
            if tidy_prims:
                cls.early_tidy_primitives(html_page)
                if debug:
                    HtmlLib.write_html_file(html_page, Path(outdir, f"page_{page_no}.tidy.html"), debug=debug)
            cls.time_page(page_start_time)
            cls.append_html_to_total_page(html_page, total_html_page_body)

        if debug and outdir:
            cls._check_html_pages(ami_json_pages, outdir)

        if outdir:
            path = Path(outdir, f"{outstem}.html")
            HtmlStyle.add_head_styles_orig(
                total_html,
                [
                    ("div", [("border", "red solid 0.5px")]),
                    ("span", [("border", "blue dotted 0.5px")]),
                ]
            )
            XmlLib.write_xml(total_html, path, debug=debug)
        return total_html

    @classmethod
    def append_html_to_total_page(cls, html_page, total_html_page_body):
        if html_page is not None:
            body_elems = HtmlLib.get_body(html_page).xpath("*")
            for body_elem in body_elems:
                total_html_page_body.append(body_elem)

    @classmethod
    def time_page(cls, page_start_time):
        page_end_time = HtmlGenerator.pmr_time()
        total_page_time = HtmlGenerator.pmr_time()
        page_time = round(page_end_time - page_start_time, 2)
        html_time = round(total_page_time - page_end_time, 2)
        if page_time > 1 or html_time > 1:
            logger.warning(
                f"=====================\nLONG PARSE  create_page {page_time} {html_time}\n====================")

    @classmethod
    def pmr_time(cls, ndec=2):
        # return round(float(datetime.second), ndec)
        return 0

    # class HtmlGenerator

    @classmethod
    def _check_html_pages(cls, ami_json_pages, outdir):
        """checks that HTML can be parsed (not normally necessary)
        """
        for i, _ in enumerate(ami_json_pages):
            page_file = Path(outdir, f"page_{i + 1}.html")
            try:
                html_elem = lxml.etree.parse(str(page_file))
            except Exception as e:
                logger.error(f"could not read XML {page_file} because {e}")

    @classmethod
    def create_html_page(
        cls,
        ami_plumber, ami_json_page, outdir, debug=False, page_no=None, svg_dir=None, page_json_dir=None,
        max_edges=10000,
        max_lines=10,
        max_rects=10,
        max_curves=10,
        rawname="raw"
    ):
        from pyamihtmlx.ami_pdf_libs import PDFDebug

        if page_json_dir:
            cls.write_dict_as_json(ami_json_page, page_json_dir, page_no)

        cls.broad_overview(ami_json_page, max_curves, max_rects)

        t1 = HtmlGenerator.pmr_time()
        # LINES, CURVES, TABLES
        # These are RAW primitives without convering rects to llines, curves to edges, etc.
        rects_g, lines_g, curves_g, table_div, svg = ami_json_page.create_rects_lines_curves_tables_svg(
            svg_dir=svg_dir,
            max_edges=max_edges,
            max_lines=max_lines, debug=debug)

        t2 = HtmlGenerator.pmr_time()
        # TABLES
        if table_div is not None and len(table_div.xpath("*")) > 0 and outdir:
            table_html = HtmlLib.create_html_with_empty_head_body()
            HtmlLib.get_body(table_html).append(table_div)
            HtmlLib.write_html_file(table_div, Path(outdir, f"tables_{page_no}.html"), debug=True)

        # CURVES
        if svg_dir:
            PDFDebug().print_curves(ami_json_page.plumber_page_dict, svg_dir=svg_dir, page_no=page_no)
            if svg is not None and len(svg.xpath("*")) > 1:  # skip if only a box
                XmlLib.write_xml(svg, Path(svg_dir, f"table_box_{page_no}.svg"), debug=debug)

        # CROP PAGE?
        html_page, footer_span_list, header_span_list = ami_json_page.create_html_page_and_header_footer(ami_plumber)
        if debug:
            ami_json_page.print_header_footer_lists(footer_span_list, header_span_list)

        body = HtmlLib.get_body(html_page)

        cls.append_non_text_primitives(body, curves_g, lines_g, rects_g, svg, table_div)

        if outdir:
            try:
                path = Path(outdir, f"page_{page_no}.{rawname}.html")
                XmlLib.write_xml(html_page, path, debug=debug)
            except Exception as e:
                logger.error(f"*******Cannot serialize page (probably strange fonts)******page{page_no} {e}")
                html_page = None
        return html_page

    @classmethod
    def broad_overview(cls, ami_json_page, max_curves, max_rects):
        page_dict = ami_json_page.plumber_page_dict
        for key in page_dict.keys():
            if key not in DICT_KEYSET:
                print(f" ***** unknown pdf key {key}")

        print(f"*** DICT {page_dict.get('mediabox')}")
        print(f"*** LINES {ami_json_page.plumber_page.lines}")
        rects = ami_json_page.plumber_page.rects
        print(f"*** RECTS {len(rects)} {rects[:max_rects]}")
        curves = ami_json_page.plumber_page.curves
        print(f"*** CURVES {len(curves)} {curves[:max_curves]}")


    @classmethod
    def write_dict_as_json(cls, ami_json_page, page_json_dir, page_no):
        FileLib.force_mkdir(page_json_dir)
        assert (f := page_json_dir).exists(), f"dir: {f} should exist"
        json_path = Path(page_json_dir, f"page_{page_no}.json")
        print(f"writing ami_json_page.plumber_page_dict as JSON {json_path}")
        FileLib.write_dict(ami_json_page.plumber_page_dict, json_path, debug=True)

    @classmethod
    def append_non_text_primitives(cls, body, curves_g, lines_g, rects_g, svg, table_div, debug=False):
        if table_div is not None and len(table_div.xpath('*')) > 0:
            body.append(table_div)
        if lines_g is not None and len(lines_g.xpath('*')) > 0:
            body.append(lines_g)
        if rects_g is not None and len(rects_g.xpath('*')) > 0:
            body.append(rects_g)
        if curves_g is not None and len(curves_g.xpath('*')) > 0:
            body.append(curves_g)
        if svg is not None and len(svg.xpath('*')) > 0:
            body.append(svg)

    @classmethod
    def early_tidy_primitives(cls, html_page):
        """
        tidies graphics primitives which are necessary for page manipulation
        modifies HTML page
        :param html_page: contains prives appended to page (maybe as SVG)
        :return: html_page
        """
        cls.tidy_thin_rects_to_lines(html_page, max_thickness=1)
        cls.approximate_curves_by_polylines(html_page)

    @classmethod
    # TODO should be new class
    # Maybe should be lower and wrapped?
    def chars_to_spans_using_pdfplumber(cls, bbox, input_pdf, page_no):
        from pyamihtmlx.ami_pdf_libs import AmiPage
        from pyamihtmlx.ami_html import H_BODY, H_DIV
        from pyamihtmlx.ami_pdf_libs import TextStyle

        with pdfplumber.open(input_pdf) as pdf:
            pdf_page = pdf.pages[page_no]
            ami_page = AmiPage()
            # (f"crop: {page0.cropbox} media {page0.mediabox}, bbox {page0.bbox}")
            # (f"rotation: {page0.rotation} doctop {page0.initial_doctop}")
            # (f"width {page0.width} height {page0.height}")
            # (f"text {page0.extract_text()[:2]}")
            # (f"words {page0.extract_words()[:3]}")
            #
            # (f"char {page0.chars[:1]}")
            span = None
            span_list = []
            maxchars = 999999
            ndec_coord = 3  # decimals for coords
            ndec_fontsize = 2
            html = HtmlUtil.create_skeleton_html()
            top_div = lxml.etree.SubElement(html.xpath(H_BODY)[0], H_DIV)
            top_div.attrib["class"] = "top"
            for ch in pdf_page.chars[:maxchars]:
                if AmiPage.skip_rotated_text(ch):
                    continue
                x0, x1, y0, y1 = AmiPage.get_xy_tuple(ch, ndec_coord)
                if bbox and not bbox.contains_point((x0, y0)):
                    logger.warning(f" outside box: {x0, y0}")
                    continue

                text_style = TextStyle()
                text_style.set_font_family(ch.get(P_FONTNAME))
                text_style.set_font_size(ch.get(P_HEIGHT), ndec=ndec_fontsize)
                text_style.stroke = ch.get(P_STROKING_COLOR)
                text_style.fill = ch.get(P_NON_STROKING_COLOR)

                # style or y0 changes
                if not span or not span.text_style or span.text_style != text_style or span.y0 != y0:
                    # cls.debug_span_changed(span, text_style, y0)
                    span = AmiSpan()
                    span_list.append(span)
                    span.text_style = text_style
                    span.y0 = y0
                    span.x0 = x0  # set left x
                span.x1 = x1  # update right x, including width
                span.string += ch.get(P_TEXT)

            # top_div = lxml.etree.Element(H_DIV)
            div = lxml.etree.SubElement(top_div, H_DIV)
            last_span = None
            for span in span_list:
                if last_span is None or last_span.y0 != span.y0:
                    div = lxml.etree.SubElement(top_div, H_DIV)
                last_span = span
                span.create_and_add_to(div)
        for ch in pdf_page.chars[:maxchars]:
            col = ch.get('non_stroking_color')
            if col:
                logging.debug(f"txt {ch.get('text')} : col {col}")
        return html

    @classmethod
    def tidy_thin_rects_to_lines(cls, html_page, max_thickness):
        body = HtmlLib.get_body(html_page)
        rects = body.xpath("*[@title='rects']/*[local-name()='rect']")
        for rect in rects:
            line = create_thin_line_from_rect(rect, max_thickness=1)
            if line is not None:
                rect.getparent().replace(rect, line)


    @classmethod
    def approximate_curves_by_polylines(cls, html_page):
        pass

    @classmethod
    def get_pdf_and_parse_to_html(cls, report_dict, report_name, debug=False):

        print(f"\n==================== {report_name} ==================")
        input_pdf = report_dict[cls.INPUT_PDF]
        if not input_pdf.exists():
            print(f"cannot find {input_pdf}")
            return
        output_page_dir = report_dict[cls.OUTPUT_PAGE_DIR]
        output_page_dir.mkdir(exist_ok=True, parents=True)
        ami_pdfplumber = AmiPDFPlumber(param_dict=report_dict)
        HtmlGenerator.create_html_pages(
            ami_pdfplumber,
            input_pdf=input_pdf,
            outdir=output_page_dir,
            debug=debug,
            page_json_dir=output_page_dir,
            outstem=cls.TOTAL_PAGES
        )

