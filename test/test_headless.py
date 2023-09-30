import unittest
from pathlib import Path

from geopy.geocoders import Nominatim

from pyamihtml.ami_html import HtmlUtil
from pyamihtml.file_lib import Driver, URL, XPATH, OUTFILE
from pyamihtml.xml_lib import XmlLib, HtmlLib, DECLUTTER_BASIC
from test.test_all import AmiAnyTest

# reset this yourself
OUT_DIR_TOP = Path("/", "Users", "pm286", "projects")

# input
AR6_URL = "https://www.ipcc.ch/report/ar6/"
SYR_URL = AR6_URL + "syr/"
WG1_URL = AR6_URL + "wg1/"
WG2_URL = AR6_URL + "wg2/"
WG3_URL = AR6_URL + "wg3/"

OUT_DIR = Path(OUT_DIR_TOP, "semanticClimate", "ipcc", "ar6", "test")

SYR_OUT_DIR = Path(OUT_DIR, "syr")
WG1_OUT_DIR = Path(OUT_DIR, "wg1")
WG2_OUT_DIR = Path(OUT_DIR, "wg2")
WG3_OUT_DIR = Path(OUT_DIR, "wg3")


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


class DriverTest(AmiAnyTest):

    def test_download_ipcc_syr_longer_report(self):
        driver = Driver()
        url = SYR_URL + "longer-report/"
        level = 99
        click_list = [
            '//button[contains(@class, "chapter-expand") and contains(text(), "Expand section")]',
            '//p[contains(@class, "expand-paras") and contains(text(), "Read more...")]'
        ]
        html_out = Path(OUT_DIR, f"complete_text_{level}.html")
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

    def test_download_all_syr_glossaries(self):
        """useful if we can't download the integrated glossarh"""
        driver = Driver()
        gloss_dict = {
            "syr":
                {
                    URL: SYR_URL + "annexes-and-index/",
                    XPATH: "//button[contains(@class, 'chapter-expand') and contains(text(), 'Expand section')]",
                    OUTFILE: Path(SYR_OUT_DIR, "annexes2.html")
                }
        }

        driver.execute_instruction_dict(gloss_dict)
        outfile = gloss_dict.get("syr").get(OUTFILE)
        print(f"outfile {outfile}")

        lxml_root = HtmlUtil.parse_html_file_to_xml(outfile)
        assert lxml_root.tag == "html"
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
                    OUTFILE: Path(OUT_DIR, "total_glossary.html")
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

    def test_download_wg1_toplevel(self):
        """
        download material from WG1
        likely to expand as we find more resources in it.
        """

        driver = Driver()
        outfile = Path(WG1_OUT_DIR, "toplevel.html")
        wg1_dict = {
            "wg1_top":
                {
                    URL: WG1_URL,
                    XPATH: None,
                    OUTFILE: outfile
                }
        }
        keys = ["wg1_top"]
        self.run_from_dict(driver, outfile, wg1_dict, keys=keys)
        driver.quit()

    def run_from_dict(self, driver, outfile, wg1_dict, keys=None):
        driver.execute_instruction_dict(wg1_dict, keys=keys)
        root = driver.get_lxml_root_elem()
        XmlLib.remove_common_clutter(root, declutter=DECLUTTER_BASIC)
        HtmlLib.add_base_url(root, WG1_URL)
        driver.write_html(outfile, pretty_print=True, debug=True)
        assert Path(outfile).exists(), f"{outfile} should exist"

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



    @unittest.skip("not yet written")
    def test_total_glossary(self):
        """This is a series of clickable alphabetic index pages which lead to individual entries
        Ayush will look at writing code"""
        total_dict = {
            "top":
                {
                    URL: "https://apps.ipcc.ch/glossary/",
                    XPATH: None,
                    OUTFILE: Path(OUT_DIR, "top", "total.html")
                }
        }

