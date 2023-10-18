import glob
import re
import unittest
from collections import Counter
from pathlib import Path

import lxml.etree
from geopy.geocoders import Nominatim
from lxml.html import HTMLParser, Element, HtmlElement

from pyamihtml.ami_html import HtmlUtil
from pyamihtml.file_lib import AmiDriver, URL, XPATH, OUTFILE
from pyamihtml.xml_lib import XmlLib, HtmlLib, DECLUTTER_BASIC
from test.test_all import AmiAnyTest

# reset this yourself
OUT_DIR_TOP = Path("/", "Users", "pm286", "projects")

# input
IPCC_URL = "https://www.ipcc.ch/"
AR6_URL = IPCC_URL + "report/ar6/"
SYR_URL = AR6_URL + "syr/"
WG1_URL = AR6_URL + "wg1/"
WG2_URL = AR6_URL + "wg2/"
WG3_URL = AR6_URL + "wg3/"

SC_TEST_DIR = Path(OUT_DIR_TOP, "semanticClimate", "ipcc", "ar6", "test")

SYR_OUT_DIR = Path(SC_TEST_DIR, "syr")
WG1_OUT_DIR = Path(SC_TEST_DIR, "wg1")
WG2_OUT_DIR = Path(SC_TEST_DIR, "wg2")
WG3_OUT_DIR = Path(SC_TEST_DIR, "wg3")

TOTAL_GLOSS_DIR = Path(SC_TEST_DIR, "total_glossary")


def predict_encoding(file_path: Path, n_lines: int = 20) -> str:
    import chardet
    '''Predict a file's encoding using chardet'''

    # Open the file as binary data
    with Path(file_path).open('rb') as f:
        # Join binary lines for specified number of lines
        rawdata = b''.join([f.readline() for _ in range(n_lines)])

    return chardet.detect(rawdata)['encoding']


class MiscTest(AmiAnyTest):

    def test_geolocate(self):
        geolocator = Nominatim(timeout=10, user_agent="myGeolocator")
        results = []
        for name in [
            "Delhi",
            "Mysore",
            "Benares",
            "Mumbai",
            "Bengaluru",
            "Ladakh",
        ]:
            location = geolocator.geocode(name)
            tuple = (name, location[1], location.latitude, location.longitude)
            results.append(tuple)
        assert results == [('Delhi', (28.6273928, 77.1716954), 28.6273928, 77.1716954),
 ('Mysore', (12.3051828, 76.6553609), 12.3051828, 76.6553609),
 ('Benares', (25.3356491, 83.0076292), 25.3356491, 83.0076292),
 ('Mumbai', (18.9733536, 72.82810491917377), 18.9733536, 72.82810491917377),
 ('Bengaluru', (12.9767936, 77.590082), 12.9767936, 77.590082),
 ('Ladakh', (33.9456407, 77.6568576), 33.9456407, 77.6568576)]


def edit_title(dict_html):
    """edit main title, extracting brackets and guillemets"""
    h4 = dict_html.xpath(".//h4[contains(@class, 'bg-primary')]")
    if len(h4) == 1:
        title = h4[0].text
        parent = h4[0].getparent()
        title = extract_chunks(title, "(.*)«([^»]*)»(.*)", parent, "wg")
        title = extract_chunks(title, "(.*)\(([^\)]*)\)(.*)", parent, "paren")
        title = title.strip()
        # lowercase unless string has embedded uppercase
        if sum(i.isupper() for i in title[1:]) == 0:
            title = title.lower()
        h4[0].text = title
        return title


def extract_chunks(text, regex, parent, tag, count=999):
    """extracts inline chunks and closes up the text
    can be be iterative
    creates <div> children of <parent> and labels them with a class/tag attribute
    then adds chunks
    :param text: chunk to analyse
    :param regex: has 3 groups (pre, chunk, post)
    :param paraent: to add results to
    :param count: number of times to repeat (default = 999)
    :return: de-chunked text"""
    t = text
    while True:
        match = re.match(regex, t)
        if not match:
            return t
        wg = lxml.etree.SubElement(parent, "div")
        wg.attrib["class"] = tag
        wg.text = match.group(2)
        t = match.group(1) + match.group(3)
    return t


def analyze_parent(h6):
    p_string = """
<div class="p-3 small">
<h6 class="fs-6">Parent-term</h6>
<ul class="items text-muted fs-6"><li><span class="specificlink" data-report="AR6" data-phrase="Mass balance/budget (of glaciers or ice sheets)" data-phraseid="2202">Mass balance/budget (of glaciers or ice sheets)</span></li></ul>
</div>
"""
    id_phrases = extract_id_phrases(h6)
    if len(id_phrases) != 1:
        raise Exception(f"expected 1 parent, found {id_phrases}")
    return id_phrases[0]


def extract_id_phrases(h6):
    """"""

    lis = h6.xpath("../ul/li")
    id_phrases = []
    for li in lis:
        span = li.xpath("span")[0]
        phrase = span.text
        data_phrase = span.attrib["data-phrase"]
        if phrase != data_phrase:
            print(f"phrase {phrase} != data_phrase {data_phrase}")
        phrase_id = span.attrib["data-phraseid"]
        id_phrases.append((phrase_id, phrase))
    return id_phrases


def analyze_sub_terms(entry_html):
    """
    <div class="ms-2 p-1 small text-muted">
<h6 class="mb-0">Sub-terms</h6>
<ul class="items mb-0">
<li><span class="specificlink" data-report="AR6" data-phrase="Agricultural and ecological drought" data-phraseid="5559">Agricultural and ecological drought</span></li>
<li><span class="specificlink" data-report="AR6" data-phrase="Hydrological drought" data-phraseid="5557">Hydrological drought</span></li>
<li><span class="specificlink" data-report="AR6" data-phrase="Megadrought" data-phraseid="209">Megadrought</span></li>
<li><span class="specificlink" data-report="AR6" data-phrase="Meteorological drought" data-phraseid="5587">Meteorological drought</span></li>
</ul>
</div>
    :return: list of (id, term) triples
    """
    id_phrases = extract_id_phrases(entry_html)
    if len(id_phrases) == 0:
        raise Exception(f"expected 1 or more sub-terms, found {id_phrases}")
    return id_phrases


def analyze_references(entry_html):

    """
    the text is messy. Seems to be
    - text <br>
    - text <br>
    <div class="ms-2 p-1 small text-muted">
<h6 class="mb-0">References</h6> - UNFCCC, 2021: Reporting and accounting of LULUCF activities under the Kyoto Protocol. United Nations Framework Convention on Climate Change (UNFCCC), Bonn, Germany. Retrieved from: https://unfccc.int/topics/land-use/workstreams/land-use-land-use-change-and-forestry-lulucf/reporting-and-accounting-of-lulucf-activities-under-the-kyoto-protocol<br> - UNFCCC, 2021: Reporting and Review under the Paris Agreement. United Nations Framework Convention on Climate Change (UNFCCC), Bonn, Germany. Retrieved from: https://unfccc.int/process-and-meetings/transparency-and-reporting/reporting-and-review-under-the-paris-agreement<br>
</div>
    """
    divs = entry_html.xpath(".//div[h6]")
    ld = len(divs) > 1
    for div in divs:
        if ld:
            # print(f" DIV: {lxml.etree.tostring(div, pretty_print=True)}")
            pass
        nodes = div.xpath("./node()")
        texts = []
        text = "NONE"
        for node in nodes:
            # print(f"type {type(node)} == {node}")
            if type(node) is HtmlElement:
                if node.tag == "h6":
                    pass
                elif node.tag == "br":
                    texts.append(text)
                else:
                    raise Exception(f"unexpected tag: {node.tag}")
            elif type(node) is lxml.etree._ElementUnicodeResult:
                text = str(node)
            else:
                # print(f":text {node}")
                raise Exception(f" unknown node {type(node)}")
            if len(texts) == 0:
                # print("NO TEXTS")
               pass
            else:
                print(f"texts: {len(texts)}:: {texts}")

def remove_styles(entry_html):
    """

    """
    style_elems = entry_html.xpath(".//*[@style]")
    for style_elem in style_elems:
        style_elem.attrib["style"] = None

def edit_paras(entry_html):
    """

    """
    regex = re.compile("([^\.]+\.)\s+(.*)")
    mainclass = "fs-6 p-2 mb-0"
    ps = entry_html.xpath(f"//p")
    for p in ps:
        clazz = p.attrib.get('class')
        if clazz == mainclass:
            # this is crude; split first sentence into 2 paras
            s = lxml.etree.tostring(p, encoding=str)
            # find period to split sentence
            match = re.match(regex, s)
            if match:
                div = None
                for tag in ["p", "span"]:
                    ss = "<div>" + match.group(1) + f"</{tag}><{tag}>" + match.group(2) + "</div>"
                    # reparse; there may be subelements such as span
                    try:
                        div = lxml.etree.fromstring(ss)
                        break
                    except Exception as e:
                        pass
                if div is None:
                    print(f"FAIL {ss}")
                    continue
                p.getparent().replace(p, div)
                p0 = div.xpath("./p")[0]
                p0.attrib["style"] = "font-weight: bold"
                # print(f"div: {lxml.etree.tostring(div)}")

def edit_lists(entry_html, parent_id_set=None, subterm_id_set=None):

    """div class="p-3 small"><h6 class="fs-6">Parent-term<"""

    # h6s = entry_html.xpath(f".//div[@class='p-3 small']/h6")
    dh6s = entry_html.xpath(f".//div[h6]")
    if len(dh6s) == 0:
        # print(f"No div/h6 found")
        return
    for dh6 in dh6s:
        h6 = dh6.xpath("./h6")[0]
        txt = h6.text.strip()
        if txt == "Parent-term":
            parent_id = analyze_parent(h6)
            parent_id_set.add(parent_id)
        elif txt == "Sub-terms":
            subterm_id_list = analyze_sub_terms(h6)
            for id_phrase in subterm_id_list:
                subterm_id_set.add(id_phrase[0])
        elif txt == "References":
            analyze_references(h6)
        else:
            raise Exception(f"unknown list title {txt}")

    """
    
    <div class="ms-2 p-1 small text-muted">
<h6 class="mb-0">Sub-terms</h6>
<ul class="items mb-0"><li><span class="specificlink" data-report="AR6" data-phrase="Household carbon footprint" data-phraseid="5376">Household carbon footprint</span></li></ul>
</div>
<div class="ms-2 p-1 small text-muted">
<h6 class="mb-0">References</h6> - Wiedmann, T. and Minx, J. C. (2008). A definition of carbon footprint, in C. Pertsova (ed.), Ecological Economics Research Trends, Nova Science Publishers, Hauppauge NY, chapter 1, pp. 1â11. URL: https://www.novapublishers.com/catalog/product info.php?products id=5999<br>
</div>"""


def extract_em_elements(entry_html_list, entry_dict):
    """create a Counter of <em> to see which might be terms"""
    em_counter = Counter()
    missing_targets = set()
    for entry_html in entry_html_list:
        # print(f"> {lxml.etree.tostring(entry_html)}")
        ems = entry_html.xpath(".//em")
        for em in ems:
            target = em.text
            target_id = make_title_id(target)
            entry_target = entry_dict.get(target_id)
            if entry_target is not None:
                print(f"found: {target_id} in {lxml.etree.tostring(entry_target)}")
            else:
                missing_targets.add(target_id)
            em_counter[em.text] += 1
    return missing_targets, em_counter


def extract_term_from_title(entry_html):
    """
    <h4 class="fw-bold fs-5 bg-primary text-light p-2">Aerosol effective radiative forcing (ERFari+aci)  « WGI »</h4>
    NYI
    """
    h4_fs_5 = entry_html.xpath(".//h4[contains(@class,'fs-5') and contains(@class, 'fw-bold')]")


class DriverTest(AmiAnyTest):

# helper

    def run_from_dict(self, driver, outfile, control, declutter=None, keys=None):
        """
        reads doc names from dict and creates HTML

        :param driver: the wrapped driver
        :param outfile: file to write
        :param control: control dict
        :param declutter: elements to remove (default DECLUTTER_BASIC)
        :param keys: list of control keys (default = all)

        """
        keys = keys if keys else control.keys()
        driver.execute_instruction_dict(control, keys=keys)
        root = driver.get_lxml_root_elem()
        XmlLib.remove_common_clutter(root, declutter=DECLUTTER_BASIC)
        HtmlLib.add_base_url(root, WG1_URL)
        driver.write_html(outfile, pretty_print=True, debug=True)
        assert Path(outfile).exists(), f"{outfile} should exist"

    # ===================tests=======================

    def test_download_ipcc_syr_longer_report(self):
        driver = AmiDriver()
        url = SYR_URL + "longer-report/"
        level = 99
        click_list = [
            '//button[contains(@class, "chapter-expand") and contains(text(), "Expand section")]',
            '//p[contains(@class, "expand-paras") and contains(text(), "Read more...")]'
        ]
        html_out = Path(SC_TEST_DIR, f"complete_text_{level}.html")
        driver.download_expand_save(url, click_list, html_out, level=level)
        print(f"elem {driver.get_lxml_element_count()}")
        XmlLib.remove_common_clutter(driver.lxml_root_elem)

        print(f"elem {driver.get_lxml_element_count()}")
        driver.write_html(Path(html_out))
        elem_count = 4579
        # assert elem_count - 2 < driver.get_lxml_element_count() < elem_count + 2, f"expected {elem_count}"
        driver.quit()

    def test_download_annexes_and_index(self):
        """
        A potential multiclick download
        """
        url = SYR_URL + "annexes-and-index/"
        driver = AmiDriver()
        full = True and False
        click_list = [
            '//button[contains(@class, "chapter-expand") and contains(text(), "Expand section")]',
            '//p[contains(@class, "expand-paras") and contains(text(), "Read more...")]'
            ]

        out_name = "annexes_full.html" if full else "annexes_first.html"
        html_out = Path(SYR_OUT_DIR, out_name)
        driver.download_expand_save(url, click_list, html_out)
        XmlLib.remove_common_clutter(driver.lxml_root_elem)
        driver.write_html(Path(SYR_OUT_DIR, "annexes_1.html"))
        driver.quit()


    def test_download_ancillary_html(self):
        """tries to find SPM, TS, glossary, etc"""
        for doc in [
            (AR6_URL,"wg1"),
            (AR6_URL,"wg2"),
            (AR6_URL,"wg3"), # https://www.ipcc.ch/report/ar6/wg3
            (AR6_URL, "wg3", "spm",
                 "https://www.ipcc.ch/report/ar6/wg3/chapter/summary-for-policymakers/"),
            (AR6_URL, "wg3", "ts",
             "https://www.ipcc.ch/report/ar6/wg3/chapter/technical-summary/"),
            (AR6_URL,"syr"), # https://www.ipcc.ch/report/ar6/syr/annexes-and-index/
            (IPCC_URL,"srocc", "chapter"),# https://www.ipcc.ch/srocc/chapter/glossary/ - has sections
            (IPCC_URL,"sr15", "chapter"), # https://www.ipcc.ch/sr15/chapter/glossary/ - has sections
            (IPCC_URL,"srccl", "chapter"), # https://www.ipcc.ch/srccl/chapter/glossary/ - NO HTML found
        ]:
            driver = AmiDriver()
            outfile = Path(SC_TEST_DIR, doc[1], "glossary.html")
            url = doc[0] + doc[1] + "/"
            if len(doc) == 3:
                url = url + doc[2] + "/"
            url = url + "glossary" + "/"
            print(f"url: {url}")
            GLOSSARY_TOP = "glossary"
            rep_dict = {
                GLOSSARY_TOP:
                    {
                        URL: url,
                        XPATH: None,
                        OUTFILE: outfile
                    }
            }
            keys = [GLOSSARY_TOP]
            self.run_from_dict(driver, outfile, rep_dict, keys=keys)
            driver.quit()

    def test_download_with_dict(self):
        """download single integrated glossary"""
        # "https://apps.ipcc.ch/glossary/"

        """useful if we can't download the integrated glossary"""
        driver = AmiDriver()
        gloss_dict = {
            "syr":
                {
                    URL: "https://apps.ipcc.ch/glossary/",
                    XPATH: None,  # this skips any button pushes
                    OUTFILE: Path(SC_TEST_DIR, "total_glossary.html")
                },
            "wg1_ch1":
                {
                    URL: WG1_URL + "chapter/chapter-1/",
                    XPATH: None,
                    OUTFILE: Path(WG1_OUT_DIR, "chapter_1.html")
                },
            "wg1_ch2":
                {
                    URL: WG1_URL + "chapter/chapter-2/",
                    XPATH: "//button[contains(@class, 'chapter-expand') and contains(text(), 'Expand section')]",
                    OUTFILE: Path(WG1_OUT_DIR, "chapter_2.html")
                },
            "wg1_spm":
                {
                    URL: WG1_URL + "chapter/summary-for-policymakers/",
                    XPATH: ["//button[contains(text(), 'Expand all sections')]",
                            "//span[contains(text(), 'Expand')]"],
                    OUTFILE: Path(WG1_OUT_DIR, "wg1", "spm.html")
                }
        }

        # driver.execute_instruction_dict(gloss_dict, keys=["wg1_ch1"])
        # driver.execute_instruction_dict(gloss_dict, keys=["wg1_ch2"])
        driver.execute_instruction_dict(gloss_dict, keys=["wg1_spm"])
        driver.quit()

    def test_download_all_toplevel(self):
        """
        download toplevel material from WG1
        likely to expand as we find more resources in it.
        """

        for report_base in [
            (AR6_URL,"wg1"),
            (AR6_URL,"wg2"),
            (AR6_URL,"wg3"),
            (AR6_URL,"syr"),
            (IPCC_URL,"srocc"),
            (IPCC_URL,"sr15"),
            (IPCC_URL,"srccl"),
        ]:
            driver = AmiDriver()
            outfile = Path(SC_TEST_DIR, report_base[1], "toplevel.html")
            url = report_base[0] + report_base[1] + "/"
            REPORT_TOP = "report_top"
            rep_dict = {
                REPORT_TOP:
                    {
                        URL: url,
                        XPATH: None,
                        OUTFILE: outfile
                    }
            }
            keys = [REPORT_TOP]
            self.run_from_dict(driver, outfile, rep_dict, keys=keys)
            driver.quit()

    def test_download_wg1_chapter_1(self):
        """
        download Chapter_1 from WG1
        """

        driver = AmiDriver()
        ch1_url = WG1_URL + "chapter/chapter-1/"
        outfile = Path(WG1_OUT_DIR, "chapter_1_noexp.html")
        wg1_dict = {
            "wg1_ch1":
                {
                    URL: ch1_url,
                    XPATH: None, # no expansiom
                    OUTFILE: outfile
                },
        }
        keys = ["wg1_ch1"]
        self.run_from_dict(driver, outfile, wg1_dict, keys=keys)

        driver.quit()

    def test_download_wg_chapters(self):
        """
        download all chapters from WG1/2/3
        """
        for wg in range(3, 4):
            WG_URL = AR6_URL + f"wg{wg}/"
            for ch in range(1,18):
                driver = AmiDriver()
                ch_url = WG_URL + f"chapter/chapter-{ch}/"
                outfile = Path(SC_TEST_DIR, f"wg{wg}", f"chapter_{ch}", "noexp.html")
                outfile_clean = Path(SC_TEST_DIR, f"wg{wg}", f"chapter_{ch}", "clean.html")
                outfile_figs = Path(SC_TEST_DIR, f"wg{wg}", f"chapter_{ch}", "figs.html")
                wg_dict = {
                    f"wg{wg}_ch":
                        {
                            URL: ch_url,
                            XPATH: None, # no expansiom
                            OUTFILE: outfile
                        },
                }
                self.run_from_dict(driver, outfile, wg_dict)
                html = HtmlLib.create_html_with_empty_head_body()
                div = lxml.etree.SubElement(HtmlLib.get_body(html), "div")
                XmlLib.remove_elements(driver.lxml_root_elem, xpath="//div[contains(@class, 'col-12')]",
                                       new_parent=div, debug=True)
                XmlLib.write_xml(driver.lxml_root_elem, outfile_clean)
                XmlLib.write_xml(html, outfile_figs),

                driver.quit()
                print(f"break for test, remove later")
                break

    def test_total_glossary(self):
        """Ayush has written code to download the total glossary. We assume it is local as single files in a directory"""
        DICT_LEN = 931
        GLOSS_INPUT_DIR = Path(TOTAL_GLOSS_DIR, "input")
        out_dir = Path(TOTAL_GLOSS_DIR, "output")
        dict_files = sorted(glob.glob(f"{GLOSS_INPUT_DIR}/*.html"))
        make_glossary(dict_files, out_dir)


def make_title_id(title):
    if title is None:
        return None
    title_id = title.strip().replace(" ", "_").lower()
    return title_id



def make_glossary(dict_files, out_dir):
    titles = set()
    parent_id_set = set()
    subterm_id_set = set()
    encoding = "UTF-8"
    entry_by_id = dict()
    entry_html_list = []
    for dict_file in dict_files:
        entry_html = lxml.etree.parse(dict_file, parser=HTMLParser(encoding=encoding)).getroot()
        entry_html_list.append(entry_html)
        XmlLib.remove_all(entry_html, ".//div[@class='modal-footer']", debug=False)
        XmlLib.remove_all(entry_html, ".//h5[button]", debug=False)

        title = edit_title(entry_html)
        title_id = make_title_id(title)
        entry_a = lxml.etree.SubElement(entry_html, "a")
        entry_a.attrib["name"] = title_id
        if entry_by_id.get(title_id) is not None:
            print(f"duplicate title_id {title_id}")
            continue
        entry_by_id[title_id] = entry_html

        remove_styles(entry_html)
        extract_term_from_title(entry_html)
        edit_paras(entry_html)
        edit_lists(entry_html, parent_id_set=parent_id_set, subterm_id_set=subterm_id_set)
        titles.add(title)

        dict_body = HtmlLib.get_body(entry_html)
        html_out = HtmlLib.create_html_with_empty_head_body()
        HtmlLib.add_charset(html_out)
        body = HtmlLib.get_body(html_out)
        body.getparent().replace(body, dict_body)

        path = create_out_path(dict_file, out_dir)
        if not path:
            continue
        print(f"writing {path}")
        entry_html_list.append(html_out)
        HtmlLib.write_html_file(html_out, str(path), pretty_print=True)
    print(f"parent: {len(parent_id_set)} {parent_id_set}")
    print(f"parent: {len(subterm_id_set)} {subterm_id_set}")

    missing_targets, em_counter = extract_em_elements(entry_html_list, entry_by_id)
    print(f"missing targets: {len(missing_targets)} {missing_targets}")
    print(f"em_counter {len(em_counter)} {em_counter}")

    def test_convert_characters(self):
            """
            The original files are in an unknown encoding which we are gradually discovering by finding characters
            ?should be irrelevant if the encoding is known
            """


            text = """The point at which an actorâs objectives (or system needs) cannot be secured from intolerable risks through adaptive actions.
            â¢ Hard adaptation limit â No adaptive actions are possible to avoid intolerable risks.
            â¢ Soft adaptation limit â"""

            encodings_to_try = ["utf-8", "iso-8859-1", "windows-1252"]

            for encoding in encodings_to_try:
                try:
                    decoded_text = text.encode(encoding).decode('utf-8')
                    print(f"Decoded with {encoding}: {decoded_text}")
                except UnicodeDecodeError as e1:
                    print(f"Failed to decode with {encoding} goves {e1}")
                except UnicodeEncodeError as e2:
                    print(f"failed encode with {encoding} gives {e2}")

    def test_glossary_encoding(self):
        """Adaptation_limits_A.html"""
        input = Path(TOTAL_GLOSS_DIR, "input", "Adaptation_limits_A.html")
        with open(str(input), "r", encoding="UTF-8") as f:
            content = f.read()
            print(f"content {content}")

    def test_make_input_output_table(self):
            """hack to create output with input and output compares
            """
            # input of raw glossary files
            input_dir = Path(TOTAL_GLOSS_DIR, "input")
            # processed files in XML
            output_dir = Path(TOTAL_GLOSS_DIR, "output")
            input_files = glob.glob(f"{input_dir}/*.html")


            html = HtmlLib.create_html_with_empty_head_body()
            # table of input and output text in glossary elements
            table = lxml.etree.SubElement(HtmlLib.get_body(html), "table")
            make_header(table)
            for input_file in sorted(input_files):
                input_file = Path(input_file)
                input_name = input_file.name
                # html in input glossary
                # make output filename from input name
                output_file = Path(output_dir, str(input_file.stem)[:-2] +".html") # strip letter
                if not output_file.exists():
                    print(f"cannot read {output_file}")
                    continue
                output_name = output_file.name
                tr = lxml.etree.SubElement(table, "tr")
                make_cell(input_file, input_name, tr, style="border: 1px blue; background: pink;")
                make_cell(output_file, output_name, tr, style="border: 1px blue; background: yellow;")

            HtmlLib.write_html_file(html, Path(TOTAL_GLOSS_DIR, "total.html"), encoding="UTF-8", debug=True)

def make_header(tr):
    th = lxml.etree.SubElement(tr, "th")
    th.text = "input"
    tr.append(th)
    th = lxml.etree.SubElement(tr, "th")
    th.text = "output"
    tr.append(th)


def make_cell(file, output_name, tr, style=None):
    td = lxml.etree.SubElement(tr, "td")
    h3 = lxml.etree.SubElement(td, "h3")
    # html in output glossary
    html = lxml.etree.parse(str(file), parser=HTMLParser()).xpath("//body/div")[0]
    h3.text = output_name
    div = lxml.etree.SubElement(td, "div")
    if style:
        div.attrib["style"] = style
    div.append(html)


def create_out_path(dict_file, out_dir):
    path = dict_file
    stem0 = Path(dict_file).stem
    match = re.match("(.+)_(?:[A-Z]|123)$", stem0)
    if match:
        stem = match.group(1)
        path = Path(out_dir, f"{stem}.html")
    return path

class TestUtils1:

    def test_strip_guillemets(self):
        text = "Adjustments (in relation to effective radiative forcing) « WGI »"
        extract_chunks()
