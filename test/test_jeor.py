from pathlib import Path

import lxml.etree

from test.resources import Resources
from test.test_all import AmiAnyTest


class JEORTest(AmiAnyTest):
    """
    Tests to read Essential oil table from j. Essential Oil Res.
    and extract profiles
    """

    def test_read_simple_table(self):
        """reads a simple rows*cols table with a compound column and abundance column"""
        table_file = Path(Resources.TEST_RESOURCES_DIR, "plant", "jeor", "10412905_2013_820670.html")
        assert table_file.exists(), f"{table_file} should exist"
        raw_table_elem = lxml.etree.parse(str(table_file))
        assert raw_table_elem is not None

        # extract complete table by HTML tag <table>
        tables = raw_table_elem.xpath('.//table')
        assert len(tables) == 1
        table0 = tables[0]
        assert table0 is not None

        # extract caption
        captions = table0.xpath("caption")
        assert len(captions) == 1
        caption = captions[0]

        # extract caption text
        ps = caption.xpath("div/p")
        assert len(ps) == 1

        p_text = ps[0].text
        p_itertext = self._flatten_html_text_and_normalize_spaces(ps)
        # this contains non-ANSI spaces and also an italic object
        assert p_itertext == "Table 1. Constituents of the essential oil extracted from A. anomala."

        # extract table head
        theads = table0.xpath("thead")
        assert len(theads) == 1
        thead = theads[0]

        # extract column names
        tr0 = thead.xpath("tr")[0]
        ths = tr0.xpath("th")
        assert len(ths) == 5
        col_names = [th.text for th in ths]
        assert len(col_names) == 5
        assert col_names == ['No', 'RT', 'Component', 'RI', 'FID (%)']

        # extract table body
        tbodies = table0.xpath("tbody")
        assert len(tbodies) == 1
        tbody = tbodies[0]

        # extract column_headings


    def _flatten_html_text_and_normalize_spaces(self, ps):
        # itertext includes all descendants
        p_itertext = "".join(ps[0].itertext())
        # convert u2003 to ANSI space
        p_itertext = p_itertext.replace("\u2003", " ")
        # remove newlines
        p_itertext = p_itertext.replace("\n", " ")
        return p_itertext









