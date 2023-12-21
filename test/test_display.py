from pathlib import Path

from pyamihtml.display import VIVLIO_APP
from pyamihtml.un import UNFCCC
from pyamihtml.xml_lib import HtmlLib
from test.test_all import AmiAnyTest
from test.test_un import UNFCCC_TEMP_DOC_DIR


class TestVivlio(AmiAnyTest):
    pass

    def test_create_vivlio_from_final_html(self):
        """extracts final HTML documents and creates a VIVLIO bundle to ingest and publish
        """
        session = "CMA_3"
        sub_repo = Path(UNFCCC_TEMP_DOC_DIR, session)
        assert sub_repo.exists(), f"sub_repo {sub_repo} should exist"
        print (f"sub_repo {sub_repo}")
        decision_dirs = [f for f in sub_repo.glob(f"Decision*{session}/")]
        print (f"decision_files {len(decision_dirs)}")
        for decision_dir in sorted(decision_dirs):
            decision_html = HtmlLib.parse_html(Path(decision_dir, "final.html"))
            title = UNFCCC.get_title_from_decision_file(decision_html)
            # print(f"{decision_dir.stem}: {title}")

    """to display VIVLIO
    https://vivliostyle.vercel.app/#src=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/publication.json&style=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/css/appaloosa-rq.css
    """
    def test_display_vivlio(self):
        """creates VIVLIO display string"""
        test_json = "https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/publication.json"
        test_css = "https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/css/appaloosa-rq.css"
        display_str = self.create_vivlio_url(test_css, test_json)
        print(f"{display_str}")

    def create_vivlio_url(self, test_css, test_json):
        display_str = f"{VIVLIO_APP}/#src={test_json}&style={test_css}"
        return display_str

