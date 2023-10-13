import glob
import re
import unittest
from pathlib import Path

import lxml.etree
from geopy.geocoders import Nominatim
from lxml.html import HTMLParser

from pyamihtml.ami_html import HtmlUtil
from pyamihtml.file_lib import Driver, URL, XPATH, OUTFILE
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
    h4 = dict_html.xpath(".//h4[contains(@class, 'bg-primary')]")
    if len(h4) == 1:
        title = h4[0].text
        parent = h4[0].getparent()
        extract_chunks(title, "(.*)«([^»]*)»(.*)", parent, "wg")
        extract_chunks(title, "(.*)\(([^\)]*)\)(.*)", parent, "paren")
        h4[0].text = title


def extract_chunks(text, regex, parent, tag, count=999):
    """extracts inline chunks and closes up the text
    can be be iterative
    creates <div> children of <parent> and labels them with a class/tag attribute
    :param text: chunk to analyse
    :param regex: has 3 groups (pre, chunk, post)
    :param paraent: to add results to
    :param count: number of times to repeat (default = 999)"""
    while True:
        match = re.match(regex, text)
        if not match:
            return title
        wg = lxml.etree.SubElement(parent, "div")
        wg.attrib["class"] = tag
        wg.text = match.group(2)
        title = match.group(1) + match.group(3)



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
        driver = Driver()
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
        driver = Driver()
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
            driver = Driver()
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
        driver = Driver()
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
            driver = Driver()
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

        driver = Driver()
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
                driver = Driver()
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
        dict_files = glob.glob(f"{GLOSS_INPUT_DIR}/*.html")
        assert len(dict_files) == DICT_LEN, f"HTML files in {TOTAL_GLOSS_DIR}  {len(dict_files)}"
        # somethiing wrong with the algorithm, so repeat
        SUBS1 = [
            ("Â«", '«'),
            ("Â»", '»')
        ]
        SUBS2 = [
            ("Â°", "°")
        ]
        for dict_file in dict_files:
            dict_html = lxml.etree.parse(dict_file, parser=HTMLParser()).getroot()
            XmlLib.remove_all(dict_html, ".//div[@class='modal-footer']", debug=True)
            XmlLib.remove_all(dict_html, ".//h5[button]", debug=True)
            # I think the glossary file has an undeclared encoding. This is a horrible hack
            XmlLib.replace_all_child_texts(dict_html, SUBS1)
            XmlLib.replace_all_child_texts(dict_html, SUBS2)
            edit_title(dict_html)

            dict_body = HtmlLib.get_body(dict_html)


            # print(f"{stem} => {len(dict_html.xpath('//*'))} elems")
            html_out = HtmlLib.create_html_with_empty_head_body()
            HtmlLib.add_charset(html_out)
            body = HtmlLib.get_body(html_out)
            body.getparent().replace(body, dict_body)

            path = create_out_path(dict_file, out_dir)
            if not path:
                continue
            print(f"writing {path}")
            HtmlLib.write_html_file(html_out, str(path), pretty_print=True)

    def test_compare_input_output(self):
        """hack to create output with input and output compares
        """
        # input of raw glossary files
        input_dir = Path(TOTAL_GLOSS_DIR, "input")
        # processed files in XML
        output_dir = Path(TOTAL_GLOSS_DIR, "output")
        input_files = glob.glob(f"{input_dir}/*.html")
        print(len(input_files))

        html = HtmlLib.create_html_with_empty_head_body()
        # table of input and output text in glossary elements
        table = lxml.etree.SubElement(HtmlLib.get_body(html), "table")

        for input_file in sorted(input_files):
            input_name = Path(input_file).name
            # make output fulename from input name
            output_file = Path(output_dir, input_name)
            output_file = Path(output_dir, str(output_file.stem)[:-2] +".html") # strip letter
            if not output_file.exists():
                print(f"cannot read {output_file}")
                continue
            output_name = output_file.name
            print(f"{input_file} : {output_file}")
            # row of table
            tr = lxml.etree.SubElement(table, "tr")
            # input cell
            tdi = lxml.etree.SubElement(tr, "td")
            # html in input glossary
            in_html = lxml.etree.parse(str(input_file), parser=HTMLParser()).getroot()
            tdih = lxml.etree.SubElement(tdi, "h3")
            tdih.text = input_name

            tdi.append(in_html)

            tdo = lxml.etree.SubElement(tr, "td")
            tdoh = lxml.etree.SubElement(tdo, "h3")
            # html in output glossary

            out_html = lxml.etree.parse(str(output_file), parser=HTMLParser()).getroot()

            tdoh.text = output_name
            div = lxml.etree.SubElement(tdo, "div")
            div.append(out_html)

        HtmlLib.write_html_file(html, Path(TOTAL_GLOSS_DIR, "total.html"))

def create_out_path(dict_file, out_dir):
    stem0 = Path(dict_file).stem
    match = re.match("(.*)_(?:[A-Z]|123)$", stem0)
    if not match:
        print(f"bad file: {dict_file}")
    else:
        stem = match.group(1)
        path = Path(out_dir, f"{stem}.html")
    return path

