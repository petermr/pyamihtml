from pathlib import Path

from geopy.geocoders import Nominatim

from pyamihtml.ami_html import HtmlUtil
from pyamihtml.file_lib import Driver, URL, XPATH, OUTFILE
from pyamihtml.xml_lib import XmlLib
from test.test_all import AmiAnyTest

# reset this yourself
TOP_DIR = Path("/", "Users", "pm286", "projects")
OUT_DIR = Path(TOP_DIR, "semanticClimate", "ipcc", "ar6", "test")

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
        url = "https://www.ipcc.ch/report/ar6/syr/longer-report/"
        level = 99
        click_list = [
            '//button[contains(@class, "chapter-expand") and contains(text(), "Expand section")]',
            '//p[contains(@class, "expand-paras") and contains(text(), "Read more...")]'
        ]
        html_out = Path(OUT_DIR, f"complete_text_{level}.html")
        driver.download_expand_save(url, click_list, html_out, level=level)
        print(f"elem {driver.get_lxml_element_count()}")
        XmlLib.remove_all(driver.lxml_root_elem, [
            "//style", "//script", "//noscript", "//meta", "//link", "//button", "//picture", "//svg",
            "//footer", "//textarea", "//img"])
        print(f"elem {driver.get_lxml_element_count()}")
        driver.write_html(Path(html_out))
        elem_count = 4579
        # assert elem_count - 2 < driver.get_lxml_element_count() < elem_count + 2, f"expected {elem_count}"
        driver.quit()

    def test_download_annexes_and_index(self):
        """
        A potential multiclick download
        """
        url = "https://www.ipcc.ch/report/ar6/syr/annexes-and-index/"
        driver = Driver()
        full = True and False
        click_list = [
            '//button[contains(@class, "chapter-expand") and contains(text(), "Expand section")]'
        ]
        if full:
            click_list.append('//p[contains(@class, "expand-paras") and contains(text(), "Read more...")]')

        out_dir = "/Users/pm286/projects/semanticClimate/ipcc/ar6/test/"
        Path(out_dir).mkdir(exist_ok=True)
        out_name = "syr_annexes_full.html" if full else "syr_annexes_first.html"
        html_out = Path(out_dir, out_name)
        driver.download_expand_save(url, click_list, html_out)
        driver.quit()

    def test_download_all_syr_glossaries(self):
        """useful if we can't download the integrated glossarh"""
        driver = Driver()
        print(f"DR {driver}")
        out_dir = Path(OUT_DIR, "/Users/pm286/projects", "semanticClimate/ipcc/ar6/test/")
        gloss_dict = {
            "syr":
                {
                    URL: "https://www.ipcc.ch/report/ar6/syr/annexes-and-index/",
                    XPATH: "//button[contains(@class, 'chapter-expand') and contains(text(), 'Expand section')]",
                    OUTFILE: Path(out_dir, "syr_annexes.html")
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
        out_dir = Path("/Users/pm286/projects/semanticClimate/ipcc/ar6/test/")
        gloss_dict = {
            "syr":
                {
                    URL: "https://apps.ipcc.ch/glossary/",
                    XPATH: None,  # this skips any button pushes
                    OUTFILE: Path(out_dir, "total_glossary.html")
                },
            "wg1_ch1":
                {
                    URL: "https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-1/",
                    XPATH: None,
                    OUTFILE: Path(out_dir, "wg1", "chapter_1.html")
                },
            "wg1_ch2":
                {
                    URL: "https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-2/",
                    XPATH: "//button[contains(@class, 'chapter-expand') and contains(text(), 'Expand section')]",
                    OUTFILE: Path(out_dir, "wg1", "chapter_2.html")
                },
            "wg1_spm":
                {
                    URL: "https://www.ipcc.ch/report/ar6/wg1/chapter/summary-for-policymakers/",
                    XPATH: ["//button[contains(text(), 'Expand all sections')]",
                            "//span[contains(text(), 'Expand')]"],
                    OUTFILE: Path(out_dir, "wg1", "spm.html")
                }
        }

        # driver.execute_instruction_dict(gloss_dict, keys=["wg1_ch1"])
        # driver.execute_instruction_dict(gloss_dict, keys=["wg1_ch2"])
        driver.execute_instruction_dict(gloss_dict, keys=["wg1_spm"])
        driver.quit()

    def test_download_complete_report_wg1(self):
        """
        download material from WG1
        likely to expand as we find more resources in it.
        """

        # Drive wraps all the download functionation , especially a selenium WebDriver
        driver = Driver()
        out_dir = Path("/Users/pm286/projects/semanticClimate/ipcc/ar6/test/wg1")

        # dict of all toplevel resources in WG1
        wg1_dict = {
            "wg1_top":
                {
                    URL: "https://www.ipcc.ch/report/ar6/wg1/",
                    XPATH: None,
                    OUTFILE: Path(out_dir, "toplevel.html")
                }
        }
        driver.execute_instruction_dict(wg1_dict, keys=["wg1_top"])
        root = driver.get_lxml_root_elem()
        assert len(root) == 2  # ???

        """TODO assert chapters """
        chapter_div_xpath = '//section[contains(@class, "chapter") and div/h2="Chapters"]'

        """
        <section class="chapter py-4 homepage"><div class="container"><h2 class="fw-bold color-heading mb-3">Chapters</h2>
        """
        chapter_div = root.xpath(chapter_div_xpath)[0]
        chapters_div = chapter_div.xpath(chapter_div_xpath)
        out_html = Path(out_dir, "raw_chapters.html")
        HtmlUtil.write_html_elem(chapters_div[0], out_html, pretty_print=True)
        assert len(chapters_div) == 1

        driver.quit()

    def test_total_glossary(self):

        "https://apps.ipcc.ch/glossary/"
        driver = Driver()
        out_dir = Path("/Users/pm286/projects/semanticClimate/ipcc/ar6/test/wg1")

        # dict of all toplevel resources in WG1
        wg1_dict = {
            "wg1_top":
                {
                    URL: "https://www.ipcc.ch/report/ar6/wg1/",
                    XPATH: None,
                    OUTFILE: Path(out_dir, "toplevel.html")
                }
        }
        driver.execute_instruction_dict(wg1_dict, keys=["wg1_top"])
        root = driver.get_lxml_root_elem()
        assert len(root) == 2  # ???

        """TODO assert chapters """
        chapter_div_xpath = '//section[contains(@class, "chapter") and div/h2="Chapters"]'

        """
        <section class="chapter py-4 homepage"><div class="container"><h2 class="fw-bold color-heading mb-3">Chapters</h2>
        """
        chapter_div = root.xpath(chapter_div_xpath)[0]
        chapters_div = chapter_div.xpath(chapter_div_xpath)
        out_html = Path(out_dir, "raw_chapters.html")
        HtmlUtil.write_html_elem(chapters_div[0], out_html, pretty_print=True)
        assert len(chapters_div) == 1

        driver.quit()
