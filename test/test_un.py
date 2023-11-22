import glob
import os
from pathlib import Path

from pyamihtml.ami_integrate import HtmlGenerator
from pyamihtml.xml_lib import HtmlLib
from test.resources import Resources
from test.test_all import AmiAnyTest
from test.test_pdf import UNFCCC_DIR, Unfccc

UNFCCC_DIR = Path(Resources.TEST_RESOURCES_DIR, "unfccc")
UNFCCC_TEMP_DIR = Path(Resources.TEMP_DIR, "unfccc")


class TestUN(AmiAnyTest):
    """Tests high level operations relating to UN content (currently UNFCCC and UN/IPCC)
    """

    def test_markup_unfccc_doc(self):
        """
        convert single UN PDF to HTML and add sections.
        """
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
        pdf_files = glob.glob(str(input_dir) + pdf_glob)
        assert len(pdf_files) > 0

        for pdf_infile in pdf_files[:999]:
            html_elem = HtmlGenerator.convert_to_html("foo", pdf_infile, section_regexes="") # section_regexes forces styles
            stem = Path(pdf_infile).stem
            HtmlLib.write_html_file(html_elem, Path(UNFCCC_TEMP_DIR, "html", stem, f"{stem}.html"), debug=True)
            # html_infile = Path(input_dir, "1_CMA_3_section target.html")
            # Unfccc.parse_unfccc_doc(html_infile, debug=True)



