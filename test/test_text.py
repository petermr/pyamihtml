import unittest

from pyamihtmlx.util import TextUtil


class TestHtml(unittest.TestCase):
    """ test text_lib (not juch in yet) and other text packages
    """

    def setUp(self) -> None:
        pass


    def test_phrase_extraction(self):
        """https://stackoverflow.com/questions/58023920/n-grams-based-on-pos-tags-spacy"""
        pass

    def test_replace_chars(self):
        """"""
        text = """ax!@£$%bg^&*()zq"""
        non_file_punct = '\t \n{}!@#$%^&*()[]:;\'",|\\~+=/`'
        result = TextUtil.replace_chars(text, non_file_punct, "_")
        assert result == 'ax__£__bg_____zq'



