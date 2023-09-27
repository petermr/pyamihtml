from pathlib import Path
from geopy.geocoders import Nominatim

from pyamihtml.file_lib import Driver, URL, XPATH, OUTFILE

from test.test_all import AmiAnyTest


class MiscTest(AmiAnyTest):

    def test_geolocate(self):
        geolocator = Nominatim(timeout=10, user_agent="myGeolocator")
        for location in [
            "Delhi",
            "Mysore",
            "Benares",
            "Mumbai",
            "Bengaluru",
            "Ladakh",
        ]:
            location = geolocator.geocode(location)
            print(location)
            print((location.latitude, location.longitude))

    def test_download_ipcc_syr_longer_report(self):
        driver = Driver()
        url = "https://www.ipcc.ch/report/ar6/syr/longer-report/"
        level = 99
        click_list = [
            '//button[contains(@class, "chapter-expand") and contains(text(), "Expand section")]',
            '//p[contains(@class, "expand-paras") and contains(text(), "Read more...")]'
        ]
        out_dir = "/Users/pm286/projects/semanticClimate/ipcc/ar6/test/"
        html_out = Path(out_dir, f"complete_text_{level}.html")
        driver.download_expand_save(url, click_list, html_out, level=level)
        elem_count = 7566
        assert driver.web_driver.find_elements("//*") == elem_count, f"expected {elem_count}"


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

    def test_download_all_syr_glossaries(self):
        """useful if we can't download the integrated glossarh"""
        driver = Driver()
        print(f"DR {driver}")
        out_dir = Path("/Users/pm286/projects/semanticClimate/ipcc/ar6/test/")
        gloss_dict = {
            "syr" :
                {
                    URL : "https://www.ipcc.ch/report/ar6/syr/annexes-and-index/",
                    XPATH : "//button[contains(@class, 'chapter-expand') and contains(text(), 'Expand section')]",
                    OUTFILE : Path(out_dir, "syr_annexes.html")
                }
            }

        driver.execute_instruction_dict(gloss_dict)

    def test_download_with_dict(self):
        """download single integrated glossary"""
            # "https://apps.ipcc.ch/glossary/"

        """useful if we can't download the integrated glossary"""
        driver = Driver()
        out_dir = Path("/Users/pm286/projects/semanticClimate/ipcc/ar6/test/")
        gloss_dict = {
            "syr" :
                {
                    URL : "https://apps.ipcc.ch/glossary/",
                    XPATH : None, # this skips any button pushes
                    OUTFILE : Path(out_dir, "total_glossary.html")
                },
            "wg1_ch1" :
                {
                    URL : "https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-1/",
                    XPATH : None,
                    OUTFILE : Path(out_dir, "wg1", "chapter_1.html")
                },
            "wg1_ch2" :
                {
                    URL : "https://www.ipcc.ch/report/ar6/wg1/chapter/chapter-2/",
                    XPATH: "//button[contains(@class, 'chapter-expand') and contains(text(), 'Expand section')]",
                    OUTFILE : Path(out_dir, "wg1", "chapter_2.html")
                },
            "wg1_spm" :
                {
                    URL : "https://www.ipcc.ch/report/ar6/wg1/chapter/summary-for-policymakers/",
                    XPATH: ["//button[contains(text(), 'Expand all sections')]",
                            "//span[contains(text(), 'Expand')]"],
                    OUTFILE : Path(out_dir, "wg1", "spm.html")
                }
            }

        # driver.execute_instruction_dict(gloss_dict, keys=["wg1_ch1"])
        # driver.execute_instruction_dict(gloss_dict, keys=["wg1_ch2"])
        driver.execute_instruction_dict(gloss_dict, keys=["wg1_spm"])

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
        """TODO assert chapters """
        """//*[@id="gatsby-focus-wrapper"]/div/div/section/div/div[1]"""