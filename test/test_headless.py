import csv
import glob
import re
import unittest
from collections import Counter
from pathlib import Path

import lxml.etree
from geopy.geocoders import Nominatim
from lxml.html import HTMLParser, Element, HtmlElement

from pyamihtmlx.file_lib import AmiDriver, URL, XPATH, OUTFILE, FileLib, EXPAND_SECTION_PARAS
from pyamihtmlx.wikimedia import WikidataLookup, WikidataPage
from pyamihtmlx.xml_lib import XmlLib, HtmlLib, DECLUTTER_BASIC
from test.test_all import AmiAnyTest

# reset this yourself
FileLib
OUT_DIR_TOP = Path("/", "Users", "pm286", "projects")

# input
IPCC_URL = "https://www.ipcc.ch/"
AR6_URL = IPCC_URL + "report/ar6/"
SYR_URL = AR6_URL + "syr/"
WG1_URL = AR6_URL + "wg1/"
WG2_URL = AR6_URL + "wg2/"
WG3_URL = AR6_URL + "wg3/"

SC_TEST_DIR = Path(OUT_DIR_TOP, "ipcc", "ar6", "test")

SYR_OUT_DIR = Path(SC_TEST_DIR, "syr")
WG1_OUT_DIR = Path(SC_TEST_DIR, "wg1")
WG2_OUT_DIR = Path(SC_TEST_DIR, "wg2")
WG3_OUT_DIR = Path(SC_TEST_DIR, "wg3")

TOTAL_GLOSS_DIR = Path(SC_TEST_DIR, "total_glossary")

OMIT_LONG = True

SLEEP = 1

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
        geolocator = Nominatim(timeout=10, user_agent="semanticclimate@gmail.com")
        results = []
        for name in [
            "Benares",
            "Bengaluru",
            "Delhi",
            "Ladakh",
            # "Mumbai",
            "Mysore",
        ]:
            location = geolocator.geocode(name)
            tuple = (name, location[1], location.latitude, location.longitude)
            results.append(tuple)
        assert results == [
            ('Benares', (25.3356491, 83.0076292), 25.3356491, 83.0076292),
            ('Bengaluru', (12.9767936, 77.590082), 12.9767936, 77.590082),
            ('Delhi', (28.6273928, 77.1716954), 28.6273928, 77.1716954),
            ('Ladakh', (33.9456407, 77.6568576), 33.9456407, 77.6568576),
            # ('Mumbai', (18.9733536, 72.82810491917377), 18.9733536, 72.82810491917377), # Mumbai seems to move!
            ('Mysore', (12.3051828, 76.6553609), 12.3051828, 76.6553609),
        ]


def edit_title(dict_html):
    """edit main title, extracting brackets and guillemets"""
    h4 = dict_html.xpath(".//h4[contains(@class, 'bg-primary')]")
    if len(h4) == 1:
        title = h4[0].text
        parent = h4[0].getparent()
        title = extract_chunks(title, "(.*)«([^»]*)»(.*)", parent, "wg")
        title = extract_chunks(title, "(.*)\\(([^\\)]*)\\)(.*)", parent, "paren")
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
<h6 class="mb-0">References</h6> - SpanMarker, 2021: Reporting and accounting of LULUCF activities under the Kyoto Protocol. United Nations Framework Convention on Climate Change (SpanMarker), Bonn, Germany. Retrieved from: https://unfccc.int/topics/land-use/workstreams/land-use-land-use-change-and-forestry-lulucf/reporting-and-accounting-of-lulucf-activities-under-the-kyoto-protocol<br> - SpanMarker, 2021: Reporting and Review under the Paris Agreement. United Nations Framework Convention on Climate Change (SpanMarker), Bonn, Germany. Retrieved from: https://unfccc.int/process-and-meetings/transparency-and-reporting/reporting-and-review-under-the-paris-agreement<br>
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
    # TODO fix regex to find missinf first sentences
    regex = re.compile("(.)\\s+(.*)")
    # this may not be universal
    mainclass = "fs-6 p-2 mb-0"
    ps = entry_html.xpath(f"//p")
    for p in ps:
        if p.text == None:
            continue
        # if p.text.startswith("A change in functional or"):
        #     print(f"CHANGE")
        clazz = p.attrib.get('class')
        if clazz == mainclass:
            # this is crude; split first sentence into 2 paras
            text = lxml.etree.tostring(p, encoding=str)
            # find period to split sentence
            # TODO some paragraphs are not split
            # match = re.match(regex, s)
            split = re.split("\\.\\s+", text, 1)
            if len(split) == 1:
                make_definition_para(p)
            else:
                div = None
                for tag in ["p", "span"]:
                    ss = "<div>" + split[0] + "." + f"</{tag}><{tag}>" + split[1] + f"</div>"
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
                make_definition_para(p0)


def make_definition_para(p):
    p.attrib["style"] = "font-weight: bold"
    p.attrib["class"] = "definition"


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


def make_targets(text):
    """creates a list to search with
    if text ends with 's' returns ['foos', 'foo']"""
    ss = []
    if text is not None:
        text = make_title_id(text)
        ss.append(text)
        if text[-1:] == 's':
            ss.append(text[:-1])
    return ss

def markup_em_and_write_files(entry_html_list, entry_by_id):
    """create a Counter of <em> to see which might be terms"""
    em_counter = Counter()
    missing_targets = set()
    for entry in entry_html_list:
        entry_html = entry[0]
        out_path = entry[1]
        name = entry_html.xpath(".//body/a/@name")
        name = name[0] if len(name) > 0 else ""
        # TODO include parent/subterms
        find_mentions(em_counter, entry_by_id, entry_html, missing_targets)
        HtmlLib.write_html_file(entry_html, out_path, debug=True)
    return missing_targets, em_counter


def find_mentions(em_counter, entry_by_id, entry_html, missing_targets):
    """TODO Badly need a class to manage this"""
    ems = entry_html.xpath(".//em")
    for em in ems:
        text = make_title_id(em.text)
        em_targets = make_targets(text)
        matched = None
        for em_target in em_targets:
            matched0 = match_target_in_dict(em_target, entry_by_id)
            matched = matched0 if matched0 is not None else matched
        if matched:
            em_counter[em.text] += 1
            a = lxml.etree.SubElement(em, "a")
            a.attrib["href"] = "#" + em_target
            a.attrib["class"] = "mention"
            a.text = em.text
            em.text = ""
        else:
            missing_targets.add(em.text)

def find_wikidata(entry_html):
    term = entry_html.xpath("//a/name")[0]
    term = term.replace("_", " ").strip()
    print(f"term {term}")

    wikidata_lookup = WikidataLookup()
    qitem0, desc, wikidata_hits = wikidata_lookup.lookup_wikidata(term)
    print(f"qitem {qitem0}")


def match_target_in_dict(em_target, entry_by_id):
    target_id = make_title_id(em_target)
    match = entry_by_id.get(target_id)
    if match is not None:
        # print(f"MATCHED {match}")
        pass
    return match is not None


def extract_term_from_title(entry_html):
    """
    <h4 class="fw-bold fs-5 bg-primary text-light p-2">Aerosol effective radiative forcing (ERFari+aci)  « WGI »</h4>
    NYI
    """
    h4_fs_5 = entry_html.xpath(".//h4[contains(@class,'fs-5') and contains(@class, 'fw-bold')]")

def make_title_id(title):
    if title is None:
        return None
    # strip brackets
    match = re.match("(.*)\\(.*", title)
    if match:
        title = match.group(1)
    title_id = title.strip().replace(" ", "_").lower()
    return title_id


def write_missing(missing_targets, filename):
    targets = [t for t in missing_targets if t is not None]
    with open(filename, "w") as f:
        for t in sorted(targets):
            f.write(t + "\n")


def extract_mention_links(entry_html_list, filename):
    with open(filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["source", "role", "target", ])
        for (entry_html, _) in entry_html_list:
            name = entry_html.xpath(".//a/@name")[0]
            refs = entry_html.xpath(".//a[@class='mention']")
            for ref in refs:
                href = ref.attrib["href"][1:] # first char is hash
                csvwriter.writerow([name,"mentions", href,])

def extract_parent_subterms(entry_html_list, filename):
    with open(filename, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(["source", "role", "target", ])
        for role_name, role in [("Parent-term", "parent"), ("Sub-terms", "subterm") ]:
            for (entry_html, _) in entry_html_list:
                name = entry_html.xpath(".//a/@name")[0]
                refs = entry_html.xpath(f".//div[h6[.='{role_name}']]/ul/li/span")
                # TODO move to earlier
                for ref in refs:
                    if ref.text is None:
                        print(f"Null text for name {name}")
                        continue
                    ref_id = make_title_id(ref.text)
                    a = lxml.etree.SubElement(ref, "a")
                    a.attrib["href"] = "#" + ref_id
                    a.text = ref.text
                    ref.text = ""
                    csvwriter.writerow([name, role, ref_id,])





def make_glossary(dict_files, out_dir, debug=True):
    titles = set()
    parent_id_set = set()
    subterm_id_set = set()
    encoding = "UTF-8"
    entry_by_id = dict()
    entry_html_list = []
    for dict_file in dict_files:
        entry_html = lxml.etree.parse(str(dict_file), parser=HTMLParser(encoding=encoding)).getroot()
        # remove "Cloae" button
        XmlLib.remove_all(entry_html, ".//div[@class='modal-footer']", debug=False)
        # remove "AR6" button
        XmlLib.remove_all(entry_html, ".//h5[button]", debug=False)

        title = edit_title(entry_html)
        title_id = make_title_id(title)
        dict_body = HtmlLib.get_body(entry_html)
        # html anchor for every element
        entry_a = lxml.etree.SubElement(dict_body, "a")
        entry_a.attrib["name"] = title_id
        # are there duplicate titles after trimming and lowercasing
        if entry_by_id.get(title_id) is not None:
            print(f"duplicate title_id {title_id}")
            continue
        entry_by_id[title_id] = entry_html

        remove_styles(entry_html)
        extract_term_from_title(entry_html)
        edit_paras(entry_html)
        edit_lists(entry_html, parent_id_set=parent_id_set, subterm_id_set=subterm_id_set)
        titles.add(title)

        # output
        html_out = HtmlLib.create_html_with_empty_head_body()
        HtmlLib.add_charset(html_out)
        body = HtmlLib.get_body(html_out)

        body.getparent().replace(body, dict_body)
        a = lxml.etree.SubElement(dict_body, "a")
        a.attrib["name"] = title_id

        path = create_out_path(dict_file, out_dir)
        if not path:
            continue
        entry_html_list.append((html_out, path))
    print(f"parent: {len(parent_id_set)} {parent_id_set}")
    print(f"parent: {len(subterm_id_set)} {subterm_id_set}")

    print(f"Must fix to write the modified HTML file")

    extract_mention_links(entry_html_list, Path(TOTAL_GLOSS_DIR, "mentions.csv"))
    extract_parent_subterms(entry_html_list, Path(TOTAL_GLOSS_DIR, "parents.csv"))
    missing_targets, em_counter = markup_em_and_write_files(entry_html_list, entry_by_id)
    write_missing(missing_targets, Path(TOTAL_GLOSS_DIR, "missing_em_targets.txt"))
    print(f"entry_dict {len(entry_by_id)}")
    gloss_ids_file = str(Path(TOTAL_GLOSS_DIR, "ids.txt"))
    with open(gloss_ids_file, "w") as f:
        for key in sorted(entry_by_id.keys()):
            entry = entry_by_id.get(key)
            f.write(f"{key} {entry.xpath('/html/body/a/@name')}\n")
    if debug:
        print(f"wrote {gloss_ids_file}")
    print(f"missing targets: {len(missing_targets)} {missing_targets}")
    print(f"em_counter {len(em_counter)} {em_counter}")

def make_header(tr):
    th = lxml.etree.SubElement(tr, "th")
    th.text = "input"
    tr.append(th)
    th = lxml.etree.SubElement(tr, "th")
    th.text = "output"
    tr.append(th)


def make_cell(file, output_name, tr, style=None, filename=False):
    td = lxml.etree.SubElement(tr, "td")
    td.attrib["style"] = "padding : 4px; margin : 4px; background : #fee;"
    if (filename):
        h3 = lxml.etree.SubElement(td, "h3")
        h3.text = output_name
    # html in output glossary
    try:
        body = lxml.etree.parse(str(file), parser=HTMLParser()).xpath("//body")[0]
    except Exception as e:
        print(f"failed to parse {file} giving {e}")
        return
    a = body.xpath("./a")
    divtop = lxml.etree.parse(str(file), parser=HTMLParser()).xpath("//body/div")[0]
    if len(a) > 0:
        divtop.insert(0, a[0])
    div = lxml.etree.SubElement(td, "div")
    if True or not style:
        style = "margin : 8px; padding : 8px; background : #eee;"
    div.attrib["style"] = style

    div.append(divtop)


def create_out_path(dict_file, out_dir):
    path = dict_file
    stem0 = Path(dict_file).stem
    match = re.match("(.+)_(?:[A-Z]|123)$", stem0)
    if match:
        stem = match.group(1)
        path = Path(out_dir, f"{stem}.html")
    return path

force = False
force = True # uncomment to run tests with this keyword
class DriverTest(AmiAnyTest):

    """ Currently 8 minutes"""
    """
    Many of these tests run a headless Chrome browser and may flash up web pages while running
    """
# helper

    # ===================tests=======================

    @unittest.skipUnless(AmiAnyTest.run_long() or force, "run occasionally")
    def test_download_ipcc_syr_longer_report(self):
        driver = AmiDriver(sleep=SLEEP)
        url = SYR_URL + "longer-report/"
        level = 99
        click_list = EXPAND_SECTION_PARAS

        html_out = Path(SC_TEST_DIR, f"complete_text_{level}.html")
        driver.download_expand_save(url, click_list, html_out, level=level)
        print(f"elem {driver.get_lxml_element_count()}")
        XmlLib.remove_common_clutter(driver.lxml_root_elem)

        print(f"elem {driver.get_lxml_element_count()}")
        driver.write_html(Path(html_out))
        driver.quit()

    @unittest.skipUnless(AmiAnyTest.run_long() or force, "run occasionally")
    def test_download_syr_annexes_and_index(self):
        """
        A potential multiclick download
        """
        url = SYR_URL + "annexes-and-index/"
        driver = AmiDriver(sleep=SLEEP)
        click_list = EXPAND_SECTION_PARAS

        html_out = Path(SYR_OUT_DIR, "annexes-and-index", "gatsby.html")
        driver.download_expand_save(url, click_list, html_out)
        XmlLib.remove_common_clutter(driver.lxml_root_elem)
        driver.write_html(html_out, debug=True)
        driver.quit()


    @unittest.skipUnless(AmiAnyTest.run_long() or force, "run occasionally")
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
            driver = AmiDriver(sleep=SLEEP)
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
            AmiDriver().run_from_dict(outfile, rep_dict, keys=keys)
            driver.quit()

    @unittest.skipUnless(AmiAnyTest.run_long() or force, "run occasionally")
    def test_download_with_dict(self):
        """download single integrated glossary
        """
        # "https://apps.ipcc.ch/glossary/"

        """useful if we can't download the integrated glossary"""
        driver = AmiDriver(sleep=SLEEP)
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

    @unittest.skipUnless(AmiAnyTest.run_long() or force, "run occasionally")
    def test_download_all_toplevel(self):
        """
        download toplevel material from WG1
        likely to expand as we find more resources in it.
        """

        MAX_REPORTS = 1
        for report_base in [
            (AR6_URL,"wg1"),
            (AR6_URL,"wg2"),
            (AR6_URL,"wg3"),
            (AR6_URL,"syr"),
            (IPCC_URL,"srocc"),
            (IPCC_URL,"sr15"),
            (IPCC_URL,"srccl"),
        ][:MAX_REPORTS]:
            driver = AmiDriver(sleep=SLEEP)
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
            AmiDriver().run_from_dict(outfile, rep_dict, keys=keys)
            driver.quit()

    @unittest.skipUnless(AmiAnyTest.run_long() or force, "run occasionally")
    def test_download_wg1_chapter_1(self):
        """
        download Chapter_1 from WG1
        """

        driver = AmiDriver(sleep=SLEEP)
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
        AmiDriver().run_from_dict(outfile, wg1_dict, keys=keys)

        driver.quit()

    @unittest.skipUnless(AmiAnyTest.run_long() or force, "run occasionally")
    def test_download_wg_chapters(self):
        """
        download all chapters from WG1/2/3
        saves output in petermr/semanticClimate and creates noexp.html as main output
        """
        CHAP_PREF = "Chapter"
        for wg in range(3, 4):
            print(f"wg = {wg}")
            wg_url = AR6_URL + f"wg{wg}/"
            print(f"downloading from {wg_url}")
            for ch in range(1,18):
                chs = str(ch)
                if len(chs) == 1:
                    chs = "0" + chs
                driver = AmiDriver(sleep=SLEEP)
                ch_url = wg_url + f"chapter/chapter-{ch}/"

                outfile = Path(SC_TEST_DIR, f"wg{wg}", f"{CHAP_PREF}{chs}", "noexp.html")
                outfile_clean = Path(SC_TEST_DIR, f"wg{wg}", f"{CHAP_PREF}{chs}", "clean.html")
                outfile_figs = Path(SC_TEST_DIR, f"wg{wg}", f"{CHAP_PREF}{chs}", "figs.html")
                wg_dict = {
                    f"wg{wg}_ch":
                        {
                            URL: ch_url,
                            XPATH: None, # no expansiom
                            OUTFILE: outfile
                        },
                }
                AmiDriver().run_from_dict(outfile, wg_dict, keys=wg_dict.keys())
                html = HtmlLib.create_html_with_empty_head_body()
                # create a new div to receive the driver output
                div = lxml.etree.SubElement(HtmlLib.get_body(html), "div")
                # remove some clutter
                XmlLib.remove_elements(driver.lxml_root_elem, xpath="//div[contains(@class, 'col-12')]",
                                       new_parent=div, debug=True)
                # write the in-driver tree
                XmlLib.write_xml(driver.lxml_root_elem, outfile_clean)

                XmlLib.write_xml(html, outfile_figs)

                driver.quit()
                # print(f"break for test, remove later")
                # break

    def test_total_glossary(self):
        """Ayush has written code to download the total glossary.
        This test assumes it is local as single files in a directory

        THIS DOES NOT DO DOWNLOAD
        """
        GLOSS_INPUT_DIR = Path(TOTAL_GLOSS_DIR, "input")
        assert GLOSS_INPUT_DIR.exists()
        dict_files = sorted(FileLib.posix_glob(f"{GLOSS_INPUT_DIR}/*.html"))
        print(f"making glossary from {len(dict_files)} files in {GLOSS_INPUT_DIR}")
        out_dir = Path(TOTAL_GLOSS_DIR, "output")
        make_glossary(dict_files, out_dir, debug=True)

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
        """
        hack to create output with input and output compares
        """
        # input of raw glossary files
        input_dir = Path(TOTAL_GLOSS_DIR, "input")
        # processed files in XML
        output_dir = Path(TOTAL_GLOSS_DIR, "output")
        input_files = FileLib.posix_glob(f"{input_dir}/*.html")


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
            make_cell(output_file, output_name, tr, style="border: 1px blue; background: #eee; margin : 3px;")

        HtmlLib.write_html_file(html, Path(TOTAL_GLOSS_DIR, "total.html"), encoding="UTF-8", debug=True)

    def test_merge_PDF_HTML_glosaries(self):
        glossaries = [
            "sr15",
            "srocc",
            "srccl",
            "wg1",
            "wg2",
            "wg3",
            "syr",
        ]
        for gloss in glossaries:
            glossary_dir = Path(TOTAL_GLOSS_DIR, "glossaries", gloss)
            glossary_file = Path(glossary_dir, "annotated_glossary.html")
            assert glossary_file.exists(), f"file shouls exist {glossary_file}"
            gloss_html = lxml.etree.parse(str(glossary_file))
            elements = gloss_html.xpath("//*")
            print(f"elements {len(elements)}")

    def test_wikimedia(self):
        """

        """
        total_html = lxml.etree.parse(str(Path(TOTAL_GLOSS_DIR, "total_old.html")))
        entries = total_html.xpath(".//div/h4")
        start = 190
        end = 200
        print(f"downloading {start} - {end} from {len(entries)} entries")
        csvfile = Path(TOTAL_GLOSS_DIR, "wiki", f"{start}_{end}.csv")
        csvfile.parent.mkdir(parents=True, exist_ok=True)
        print(f"writing to {csvfile}")
        with open (csvfile, "w")  as f:
            wikiwriter = csv.writer(f, quoting=csv.QUOTE_ALL)
            wikiwriter.writerow(["term", "highestQid", "highest_desc", "list_of_others"])
            for i, entry in enumerate(entries):
                if i < start or i > end:
                    continue
                term = entry.text
                print(f"entry: {i}; term {term}")
                wikidata_lookup = WikidataLookup()
                qitem0, desc, wikidata_hits = wikidata_lookup.lookup_wikidata(term)
                print(f"qitem {qitem0, desc}")
                wikiwriter.writerow([term, qitem0, desc, wikidata_hits])

    @unittest.skipIf(OMIT_LONG, "toolong")
    def test_abbreviations_wikimedia(self):
        """
        reads an acronym file as CSV and looks up entries in Wikidata and Wikipedia
        TODO move elsewhere
        """
        abbrev_file = Path(TOTAL_GLOSS_DIR, "glossaries", "total", "acronyms.csv")
        print(f"looking up acronym file {abbrev_file} in Wikidata")
        offset = 1000
        count = 0
        MAXCOUNT = 3
        for start in range(0, 1700, offset):
            count += 1
            if count > MAXCOUNT:
                break
            end = start + offset
            lookup = WikidataLookup()
            output_file = Path(TOTAL_GLOSS_DIR, "glossaries", "total", f"acronyms_wiki_{start}_{end}.csv")
            with open(output_file, "w") as fout:
                csvwriter = csv.writer(fout)
                csvwriter.writerow(['abb', 'term', 'qid', 'desc', 'hits'])
                with open(abbrev_file, newline='') as input:
                    csvreader = csv.reader(input)
                    for i, row in enumerate(csvreader):
                        if i < start or i > end:
                            continue
                        abb = row[0]
                        term = row[1]
                        qitem0, desc , hits = lookup.lookup_wikidata(term)
                        if qitem0 is None:
                            print(f"failed on text: {row}")
                            # qitem0, desc, hits = lookup.lookup_wikidata(abb)
                            if qitem0 is None:
                                print(f"failed on text {term} and abbreviation: {abb}")
                                out_row = [abb, term, "?", "?", "?"]
                            else:
                                out_row = [abb, term, qitem0, desc, hits]
                        else:
                            out_row = [abb, term, qitem0, desc, hits]
                        csvwriter.writerow(out_row)

    def test_add_wikipedia_to_abbreviations(self):
        """reads an abbreviations and looks up wikipedia"""
        abbrev_file = Path(TOTAL_GLOSS_DIR, "glossaries", "total", "acronyms_wiki.csv")
        output_file = Path(TOTAL_GLOSS_DIR, "glossaries", "total", "acronyms_wiki_pedia.csv")
        maxout = 20 # 1700 in total
        lookup = WikidataLookup()
        with open(output_file, "w") as fout:
            csvwriter = csv.writer(fout)
            # csv header
            csvwriter.writerow(['abb', 'term', 'qid', 'desc', 'hits', 'wikipedia'])
            with open(abbrev_file, newline='') as input:
                csvreader = csv.reader(input)
                for i, row in enumerate(csvreader):
                    if i > maxout:
                        break
                    abb = row[0]
                    term = row[1]
                    qid = row[2]
                    desc = row[3]
                    hits = row[4]
                    if qid is None or not qid.startswith("Q"):
                        print(f"no QID")
                        continue
                    wikidata_page = WikidataPage(qid)
                    wikipedia_links = wikidata_page.get_wikipedia_page_links(["en"])
                    print(f"wikipedia links {wikipedia_links}")
                    out_row = [abb, term, qid, desc, hits, wikipedia_links]
                    csvwriter.writerow(out_row)

                print(f"ENDED")

# def test_plot_mentions(self):
    #
    #     from pyvis.network import Network
    #     import networkx as nx
    #     nx_graph = nx.cycle_graph(10)
    #     nx_graph.nodes[1]['title'] = 'Number 1'
    #     nx_graph.nodes[1]['group'] = 1
    #     nx_graph.nodes[3]['title'] = 'I belong to a different group!'
    #     nx_graph.nodes[3]['group'] = 10
    #     nx_graph.add_node(20, size=20, title='couple', group=2)
    #     nx_graph.add_node(21, size=15, title='couple', group=2)
    #     nx_graph.add_edge(20, 21, weight=5)
    #     nx_graph.add_node(25, size=25, label='lonely', title='lonely node', group=3)
    #     nt = Network('500px', '500px')
    #     # populates the nodes and edges data structures
    #     nt.from_nx(nx_graph)
    #     nt.show('nx.html')


    # cleaned_ipcc_graph = pd.read_csv(str(Path(TOTAL_GLOSS_DIR, "mentions.csv")))
    #
    # # cleaned_ipcc_graph = cleaning_nan(mention_df, ['source', 'package','target', 'section'])
    # ipcc_graph_with_coloured_nodes = get_package_names(cleaned_ipcc_graph, "package.json")
    # ipcc_graph_with_coloured_nodes.to_csv('coloured.csv')
    # make_graph(ipcc_graph_with_coloured_nodes, source='source', target='target', colour ='node_colour')

class TestUtils1:

    @unittest.skip("not written")
    def test_strip_guillemets(self):
        text = "Adjustments (in relation to effective radiative forcing) « WGI »"
        extract_chunks()
