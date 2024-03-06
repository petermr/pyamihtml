from pathlib import Path
from pprint import pprint

from pyamihtmlx.display import Vivlio, VivlioManifest
from pyamihtmlx.file_lib import FileLib
from pyamihtmlx.un import UNFCCC
from test.test_all import AmiAnyTest
from test.test_un import UNFCCC_TEMP_DOC_DIR


class TestVivlio(AmiAnyTest):

    def test_create_vivlio_from_final_html(self):
        """extracts final HTML documents and creates a VIVLIO bundle to ingest and publish
        """
        session = "CMA_3"

        sub_repo = Path(UNFCCC_TEMP_DOC_DIR, session)
        out_dir = Path(UNFCCC_TEMP_DOC_DIR, "html", session)
        decision_dirs = [f for f in sub_repo.glob(f"Decision*{session}/")]
        decision_dirs = FileLib.convert_files_to_posix(decision_dirs)
        decision_dirs.sort(key=lambda fname: int(str(fname).split('_')[2]))  # bit tacky but works; splits on Decision number
        print(f"decision_dirs {decision_dirs}")
        html_elem = Vivlio.create_toc_html(decision_dirs, out_dir=out_dir,
                                           get_title=UNFCCC.get_title_from_decision_file)
        assert html_elem is not None
        assert len(html_elem.xpath("//*")) > 0


    """to display VIVLIO
    https://vivliostyle.vercel.app/#src=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/publication.json&style=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/css/appaloosa-rq.css
    """

    def test_create_vivlio_from_many_sessions(self):
        """
        """
        debug = True
        cma_list = [
            "CMA_1",
            "CMA_2",
            "CMA_3",
            "CMA_4",
        ]
        self.analyze_write_session(cma_list, debug=debug)

        cmp_list = [
            "CMP_1",
            # "CMP_2",
            "CMP_3",
            "CMP_4",
            # "CMP_5",
            # "CMP_6",
            # "CMP_7",
            # "CMP_8",
            # "CMP_9",
            "CMP_10",
            "CMP_11",
            # "CMP_12",
            # "CMP_13",
            "CMP_14",
            "CMP_15",
            "CMP_16",
            "CMP_17",
        ]
        self.analyze_write_session(cmp_list, debug=debug)

        cp_list = [
            "CP_1",
            "CP_2",
            "CP_3",
            # "CP_4",
            # "CP_5",
            "CP_6",
            "CP_7",
            "CP_8",
            # "CP_9",
            # "CP_10",
            "CP_11",
            # "CP_12",
            "CP_13",
            "CP_14",
            "CP_15",
            "CP_16",
            "CP_17",
            "CP_18",
            "CP_19",
            "CP_20",
            "CP_21",
            # "CP_22",
            "CP_23",
            "CP_24",
            "CP_25",
            "CP_26",
            "CP_27",
        ]
        self.analyze_write_session(cp_list, debug=debug)

    def analyze_write_session(self, sessions, debug=False):
        for session in sessions:
            sub_repo = Path(UNFCCC_TEMP_DOC_DIR, session)
            out_dir = Path(UNFCCC_TEMP_DOC_DIR, "html", session)
            lead_dirs = [f for f in sub_repo.glob(f"*{session}*LEAD/")]
            lead_dirs = FileLib.convert_files_to_posix(lead_dirs)
            decision_dirs = [f for f in sub_repo.glob(f"Decision*{session}/")]
            decision_dirs = FileLib.convert_files_to_posix(decision_dirs)
            decision_dirs.sort(key=lambda fname: int(str(fname).split('_')[2]))  # bit tacky but works
            print(f"decision_dirs {session} : {len(decision_dirs)}")
            html_elem = Vivlio.create_toc_html(decision_dirs, lead_dirs=lead_dirs, title=session, out_dir=out_dir,
                                               get_title=UNFCCC.get_title_from_decision_file, debug=True)
            session_dict = VivlioManifest.create_session_manifest_json (
                decision_dirs, out_dir=out_dir, outname="publication.json", debug=debug)
            if debug:
                pprint(f"session_dict {session_dict}")

    """to display VIVLIO
    https://vivliostyle.vercel.app/#src=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/publication.json&style=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/css/appaloosa-rq.css
    """

    def test_display_vivlio(self):
        """creates VIVLIO display string"""
        test_json = "https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/publication.json"
        test_css = "https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/css/appaloosa-rq.css"
        display_str = Vivlio.create_vivlio_url(test_css, test_json)
        assert display_str == "https://vivliostyle.vercel.app/#src=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/publication.json&style=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/css/appaloosa-rq.css"
