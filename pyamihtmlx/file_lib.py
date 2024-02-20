"""classes and methods to support path operations

"""
import json
from io import StringIO

import chardet
import copy
from enum import Enum, auto
import errno
import glob
#from glob import glob
import logging
import re
import os
from pathlib import Path, PurePath
import shutil

import time

import lxml
import requests
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
from urllib3.exceptions import MaxRetryError
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException

from pyamihtmlx.util import TextUtil

logging.debug("loading file_lib")

py4ami = "pyamihtmlx"
RESOURCES = "resources"

# section keys
_DESC = "_DESC"
PROJ = "PROJ"
TREE = "TREE"
SECTS = "SECTS"
SUBSECT = "SUBSECT"
SUBSUB = "SUBSUB"
FILE = "FILE"
SUFFIX = "SUFFIX"

ALLOWED_SECTS = {_DESC, PROJ, TREE, SECTS, SUBSECT, SUBSUB, FILE, SUFFIX}

# wildcards
STARS = "**"
STAR = "*"

# suffixes
S_PDF = "pdf"
S_PNG = "png"
S_SVG = "pdf"
S_TXT = "txt"
S_XML = "xml"

# markers for processing
_NULL = "_NULL"
_REQD = "_REQD"

# known section names
SVG = "svg"
PDFIMAGES = "pdfimages"
RESULTS = "results"
SECTIONS = "sections"

# subsects
IMAGE_STAR = "image*"

# subsects
OCTREE = "*octree"

# results
SEARCH = "search"
WORD = "word"
EMPTY = "empty"

# files
FULLTEXT_PAGE = "fulltext-page*"
CHANNEL_STAR = "channel*"
RAW = "raw"


# class Globber:
#     """utilities for globbing - may be obsolete
#     glob.glob does most of this
#     """
#
#     def __init__(self, ami_path, recurse=True, cwd=None) -> None:
#
#         self.ami_path = ami_path
#         self.recurse = recurse
#         self.cwd = os.getcwd() if cwd is None else cwd
#
#     def get_globbed_files(self) -> list:
#         """uses the glob_string_list in ami_path to create a path list"""
#         files = []
#         if self.ami_path:
#             glob_list = self.ami_path.get_glob_string_list()
#             for gl_str in glob_list:
#                 files += glob.glob(gl_str, recursive=self.recurse)
#         return files
#

# class AmiPath:
#     """holds a (keyed) scheme for generating lists of path globs
#     The scheme has several segments which can be set to create a glob expr.
#     """
#     # keys for path scheme templates
#     T_FIGURES = "fig_captions"
#     T_OCTREE = "octree"
#     T_PDFIMAGES = "pdfimages"
#     T_RESULTS = "results"
#     T_SECTIONS = "sections"
#     T_SVG = "climate10_"
#
#     logger = logging.getLogger("ami_path")
#     # dict
#
#     def __init__(self, scheme=None):
#         self.scheme = scheme
#
#     def print_scheme(self):
#         """for debugging and enlightenment"""
#         if self.scheme is not None:
#             for key in self.scheme:
#                 print("key ", key, "=", self.scheme[key])
#             print("")
#
#     @classmethod
#     def create_ami_path_from_templates(cls, key, edit_dict=None):
#         """creates a new AmiPath object from selected template
#         key: to template
#         edit_dict: dictionary with values to edit in
#         """
#         """Doesn't look right!"""
#         key = key.lower()
#         if key is None or key not in TEMPLATES:
#             cls.logger.error(f"cannot find key {key}")
#             cls.logger.error("no scheme for: ", key,
#                              "expected", TEMPLATES.keys())
#         ami_path = AmiPath()
#         # start with default template values
#         ami_path.scheme = copy.deepcopy(TEMPLATES[key])
#         if edit_dict:
#             ami_path.edit_scheme(edit_dict)
#         return ami_path
#
#     def edit_scheme(self, edit_dict):
#         """edits values in self.scheme using edit_dict"""
#         for k, v in edit_dict.items():
#             self.scheme[k] = v
#
#     def permute_sets(self):
#         self.scheme_list = []
#         self.scheme_list.append(self.scheme)
#         # if scheme has sets, expand them
#         change = True
#         while change:
#             change = self.expand_set_lists()
#
#     def expand_set_lists(self):
#         """expands the sets in a scheme
#         note: sets are held as lists in JSON
#
#         a scheme with 2 sets of size n and m is
#         expanded to n*m schemes covering all permutations
#         of the set values
#
#         self.scheme_list contains all the schemes
#
#         returns True if any sets are expanded
#
#         """
#         change = False
#         for scheme in self.scheme_list:
#             for sect, value in scheme.items():
#                 if type(value) == list:
#                     change = True
#                     # delete scheme with set, replace by copies
#                     self.scheme_list.remove(scheme)
#                     for set_value in value:
#                         scheme_copy = copy.deepcopy(scheme)
#                         self.scheme_list.append(scheme_copy)
#                         scheme_copy[sect] = set_value  # poke in set value
#                     break  # after each set processed
#
#         return change
#
#     def get_glob_string_list(self):
#         """expand sets in AmiPath
#         creates m*n... glob strings for sets with len n and m
#         """
#         self.permute_sets()
#         self.glob_string_list = []
#         for scheme in self.scheme_list:
#             glob_string = AmiPath.create_glob_string(scheme)
#             self.glob_string_list.append(glob_string)
#         return self.glob_string_list
#
#     @classmethod
#     def create_glob_string(cls, scheme):
#         globx = ""
#         for sect, value in scheme.items():
#             cls.logger.debug(sect, type(value), value)
#             if sect not in ALLOWED_SECTS:
#                 cls.logger.error(f"unknown sect: {sect}")
#             elif _DESC == sect:
#                 pass
#             elif _REQD == value:
#                 cls.logger.error("must set ", sect)
#                 globx += _REQD + "/"
#             elif _NULL == value:
#                 pass
#             elif FILE == sect:
#                 globx += AmiPath.convert_to_glob(value)
#             elif STAR in value:
#                 globx += AmiPath.convert_to_glob(value) + "/"
#             elif SUFFIX == sect:
#                 globx += "." + AmiPath.convert_to_glob(value)
#             else:
#                 globx += AmiPath.convert_to_glob(value) + "/"
#         cls.logger.debug("glob", scheme, "=>", globx)
#         return globx
#
#     @classmethod
#     def convert_to_glob(cls, value):
#         valuex = value
#         if type(value) == list:
#             # tacky. string quotes and add commas and parens
#             valuex = "("
#             for v in value:
#                 valuex += v + ","
#             valuex = valuex[:-1] + ")"
#         return valuex
#
#     def get_globbed_files(self):
#         files = Globber(self).get_globbed_files()
#         self.logger.debug("files", len(files))
#         return files


class FileLib:

    logger = logging.getLogger("file_lib")

    @classmethod
    def force_mkdir(cls, dirx):
        """ensure dirx and its parents exist

        :dirx: directory
        """
        path = Path(dirx)
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                assert (f := path).exists(), f"dir {path} should now exist"
            except Exception as e:
                cls.logger.error(f"cannot make dirx {dirx} , {e}")
                print(f"cannot make dirx {dirx}, {e}")



    @classmethod
    def force_mkparent(cls, file):
        """ensure parent directory exists

        :path: whose parent directory is to be created if absent
        """
        if file is not None:
            cls.force_mkdir(cls.get_parent_dir(file))

    @classmethod
    def force_write(cls, file, data, overwrite=True):
        """:write path, creating directory if necessary
        :path: path to write to
        :data: str data to write
        :overwrite: force write if path exists

        may throw exception from write
        """
        if file is not None:
            if os.path.exists(file) and not overwrite:
                logging.warning(f"not overwriting existsnt path {file}")
            else:
                cls.force_mkparent(file)
                with open(file, "w", encoding="utf-8") as f:
                    f.write(data)

    @classmethod
    def copy_file_or_directory(cls, dest_path, src_path, overwrite):
        if dest_path.exists():
            if not overwrite:
                file_type = "dirx" if dest_path.is_dir() else "path"
                raise TypeError(
                    str(dest_path), f"cannot overwrite existing {file_type} (str({dest_path})")

        else:
            # assume directory
            cls.logger.warning(f"create directory {dest_path}")
            dest_path.mkdir(parents=True, exist_ok=True)
            cls.logger.info(f"created directory {dest_path}")
        if src_path.is_dir():
            if os.path.exists(dest_path):
                shutil.rmtree(dest_path)
            shutil.copytree(src_path, dest_path)
            cls.logger.info(f"copied directory {src_path} to {dest_path}")
        else:
            try:
                shutil.copy(src_path, dest_path)  # will overwrite
                cls.logger.info(f"copied path {src_path} to {dest_path}")
            except Exception as e:
                cls.logger.fatal(f"Cannot copy direcctory {src_path} to {dest_path} because {e}")

    @staticmethod
    def create_absolute_name(file):
        """create absolute/relative name for a path relative to pyamihtmlx

        TODO this is messy
        """
        absolute_file = None
        if file is not None:
            file_dir = FileLib.get_parent_dir(__file__)
            absolute_file = os.path.join(os.path.join(file_dir, file))
        return absolute_file

    @classmethod
    def get_py4ami(cls):
        """ gets paymi_m pathname

        """
        return Path(__file__).parent.resolve()

    @classmethod
    def get_pyami_root(cls):
        """ gets paymi root pathname

        """
        return Path(__file__).parent.parent.resolve()

    @classmethod
    def get_pyami_resources(cls):
        """ gets paymi root pathname

        """
        return Path(cls.get_py4ami(), RESOURCES)

    @classmethod
    def get_parent_dir(cls, file):
        return None if file is None else PurePath(file).parent

    @classmethod
    def read_pydictionary(cls, file):
        """read a JSON path into a python dictionary
        :param file: JSON file to read
        :return: JSON dictionary (created by ast.literal_eval)
        """
        import ast
        with open(file, "r") as f:
            pydict = ast.literal_eval(f.read())
        return pydict

    @classmethod
    def punct2underscore(cls, text):
        """ replace all ASCII punctuation except '.' , '-', '_' by '_'

        usually used for filenames
        :param text: input string
        :return: substituted string

        """
        # this is non-trivial https://stackoverflow.com/questions/10017147/removing-a-list-of-characters-in-string

        non_file_punct = '\t \n{}!@#$%^&*()[]:;\'",|\\~+=/`'
        # [unicode(x.strip()) if x is not None else '' for x in row]

        text0 = TextUtil.replace_chars(text, non_file_punct, "_")
        return text0

    @classmethod
    def get_suffix(cls, file):
        """get suffix of filename
        :param file: filename
        :return: suffix including the '.'

        """
        _suffix = None if file is None else Path(file).suffix
        return _suffix

    @staticmethod
    def check_exists(file):
        """
        raise exception on null value or non-existent path
        """
        if file is None:
            raise Exception("null path")

        if os.path.isdir(file):
            # print(path, "is directory")
            pass
        elif os.path.isfile(file):
            # print(path, "is path")
            pass
        else:
            try:
                f = open(file, "r")
                print("tried to open", file)
                f.close()
            except Exception:
                raise FileNotFoundError(str(file) + " should exist")

    @classmethod
    def copyanything(cls, src, dst):
        """copy file or directory
        (from StackOverflow)
        :param src: source file/directory
        :param dst: destination
        """
        try:
            shutil.copytree(src, dst)
        except OSError as exc:  # python >2.5
            if exc.errno in (errno.ENOTDIR, errno.EINVAL):
                shutil.copy(src, dst)
            else:
                raise exc

    @classmethod
    def copy_file(cls, file, src, dst):
        """
        :param file: filename in src dir
        :param src: source directory
        :oaram dst: destinatiom diecrtory
        """
        FileLib.copyanything(Path(src, file), Path(dst, file))

    @classmethod
    def delete_directory_contents(cls, dirx, delete_directory=False):
        """
        deletes directories recursively using shutil.rmtree
        :param dirx: directory tree to delete
        :param delete_directory: If True, delete dirx
        :return None:
        """
        if not dirx or not Path(dirx).exists():
            print (f"no directory given or found {dirx}")
            return
        if delete_directory:
            shutil.rmtree(dirx)
        else:
            for path in Path(dirx).glob("**/*"):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path)

    @classmethod
    def delete_files(cls, dirx, globstr):
        """
        delete files in directory
        :param dirx: directory containing files
        :param globstr: glob string, e.g. "*.html"
        :return: list of deleted files (Paths)

        """
        files = []
        for path in Path(dirx).glob(globstr):
            if path.is_file():
                path.unlink()
                files.append(path)
        return files

    @classmethod
    def list_files(cls, dirx, globstr):
        """
        list files in directory
        :param dirx: directory containing files
        :param globstr: glob string, e.g. "*.html"
        :return: list of files (Paths)
        """
        return [path for path in Path(dirx).glob(globstr) if path.is_file()]

    @classmethod
    def size(cls, file):
        """
        get size of file
        :param file:
        :return: file size bytes else None if not exist
        """
        return None if file is None or not file.exists() else os.path.getsize(file)

    @classmethod
    def get_encoding(cls, file):
        """tries to guess (text) encoding
        :param file: to read
        :return: {'encoding': Guess, 'confidence': d.d, 'language': Lang}"""
        with open(file, "rb") as f:
            rawdata = f.read()
            return cls.get_encoding_from_bytes(rawdata)

    @classmethod
    def get_encoding_from_bytes(cls, rawdata):
        chardet.detect(rawdata)
        encode = chardet.UniversalDetector()
        encode.close()
        return encode.result

    @classmethod
    def expand_glob_list(self, pdf_list):
        """
        :param pdf_list: list of paths including globs
        :return: flattened globbed list
        """
        if type(pdf_list) is not list:
            pdf_list = [pdf_list]
        input_pdfs = []
        for input_pdf in pdf_list:
            globbed_files = glob.glob(str(input_pdf))
            input_pdfs.extend(globbed_files)
        return input_pdfs

    @classmethod
    def delete_file(cls, file):
        """delete file (uses unlink) and asserts it has worked
        ;param file: to delete"""
        if file.exists():
            file.unlink()
        assert not file.exists()

    @classmethod
    def write_dict(cls, dikt, path, debug=False, indent=2):
        """write dictionary as JSON object
        :param dikt: python dictionary
        :param path: path to write to
        :param debug:
        :param indent:
        """

        with open(str(path), "w") as f:
            json.dump(dikt, f, indent=indent)
        if debug:
            print(f"wrote dictionary to {path}")

    @classmethod
    def read_string_with_user_agent(self, url, user_agent='my-app/0.0.1', encoding="UTF-8", encoding_scheme="chardet", debug=False):
        """
        allows request.get() to use a user_agent
        :param url: url to read
        :param encoding_scheme: id "chardet uses chardet else response.appenent_encoding
        :return: decoded string
        """
        if not url:
            return None
        if debug:
            print(f"reading {url}")
        response = requests.get(url, headers={'user-agent': user_agent})
        if debug:
            print(f"response: {response} content: {response.content[:400]}")
        content = response.content
        if debug:
            print(f"apparent encoding: {response.apparent_encoding}")
        if encoding is None:
            encoding = chardet.detect(content)['encoding'] if encoding_scheme == "chardet" else response.apparent_encoding
        content = content.decode(encoding)
        return content, encoding

    @classmethod
    def join_dir_and_file(cls, indir, input):
        """joins indir (directory) and input (descendants) to make a list of full filenames
        if indir or input is null, no action
        if indir is a list no action, returns input unchanged
        if input is absolute (starts with "/") no action

        if input is string, creates f"{indir}/{input}"
        if input is list of strings creates:
            f"{indir}/{input1}"
            f"{indir}/{input2}"
            ...
            it skips any input strings starting with "/"
        """
        if not indir or not input:
            return input
        # cannot manage multiple directories (?yet)
        if type(indir) is list and len(indir) > 1:
            return input

        if type(input) is str:
            # single input
            if input[0] != "/":
                input = f"{indir}/{input}"
        elif type(input) is list:
            # list of inputs
            all_inputs = []
            for input_item in input:
                if input_item[0] != "/":
                    all_inputs.append(f"{indir}/{input_item}")
            input = all_inputs
        return input



URL = "url"
XPATH = "xpath"
OUTFILE = "out_file"

class AmiDriver:
    """
    create and wrap a Chrome headless browser
    Author Ayush Garg, modified Peter Murray-Rust
    """

    def __init__(self):
        """
        creates a Chrome WebDriver instance with specified options and settings.
        """
        options = webdriver.ChromeOptions()
        options.page_load_strategy = "none"
        chrome_path = ChromeDriverManager().install()
        chrome_service = Service(chrome_path)
        self.web_driver = Chrome(options=options, service=chrome_service)
        self.lxml_root_elem = None

    def quit(self):
        """quite the web_driver"""
        print("Quitting the driver...")
        self.web_driver.quit()
        print("DONE")

    def safe_click_element(self, element, sleep=3):
        """
        attempt to click on a web element
        in a safe manner, handling potential exceptions and using different strategies if necessary.

        a web browser. It allows you to navigate to web pages, interact with elements on the page, and
        perform various actions
        :param element: the web element to click on. It can be any
        valid web element object, such as an instance of `WebElement` class in Selenium
        :param sleep: time to wait
        """
        assert type(element) is WebElement, f"should be WebElement found {type(element)}"
        try:
            # Wait for the element to be clickable
            WebDriverWait(self, sleep).until(
                EC.element_to_be_clickable((By.XPATH, element.get_attribute("outerHTML")))
            )
            element.click()
        except ElementClickInterceptedException:
            # If the element is not clickable, scroll to it and try again
            self.web_driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()
        except Exception:
            # If it still doesn't work, use JavaScript to click on the element
            self.web_driver.execute_script("arguments[0].click();", element)

    def get_page_source(self, url, sleep=3):
        """
        returns the page source code.

        :param url: The URL of the webpage you want to retrieve the source code from
        :param sleep: sleep time
        :return: the page source of the website after the driver navigates to the specified URL.
        """
        print(f"Fetching page source from URL: {url}")
        self.web_driver.get(url)
        time.sleep(sleep)
        return self.web_driver.page_source

    def click_xpath_list(self, xpath_list):
        if not xpath_list or type(xpath_list) is not list:
            print(f"no xpath_list {xpath_list}")
            return
        print(f"Clicking xpaths...{xpath_list}")
        for xpath in xpath_list:
            print(f"xpath: {xpath}")
            self.click_xpath(xpath)

    def click_xpath(self, xpath, sleep=3):
        """
        find clickable elemnts by xpath and click them
        :param xpath: xpath to click
        :param sleep: wait until click has been executed
        """
        print(f">>>>before click {xpath} => {self.get_lxml_element_count()}")
        # elements = self.get_lxml_root().xpath(xpath)
        elements = self.web_driver.find_elements(
            By.XPATH,
            xpath,
        )
        print(f"click found WebElements {len(elements)}")
        for element in elements:
            self.safe_click_element(element)
            print(f"sleep {sleep}")
            time.sleep(sleep)  # Wait for the section to expand
        print(f"<<<<after {self.get_lxml_element_count()}")

    def get_lxml_element_count(self):
        # elements = self.web_driver.find_elements(
        #     By.XPATH,
        #     "//*",
        # )
        elements = self.get_lxml_root_elem().xpath("//*")
        return len(elements)

    def download_expand_save(self, url, xpath_list, html_out, level=99, pretty_print=True):
        """
        Toplevel convenience class

        :param url: to download
        :param xpath_list: ordered list of Xpaths to click
        :param html_out: file to write
        :param level: number of levels to desend (default = 99)
        """
        if url is None:
            print(f"no url given")
            return
        html_source = self.get_page_source(url)
        if xpath_list is None:
            print(f"no xpath_list specified")
        else:
            self.click_xpath_list(xpath_list[:level])

        if html_out is None:
            print(f"no output html")
            return
        print(f"writing ... {html_out}")

        # Path(html_out).parent.mkdir(parents=True, exist_ok=True)
        # roots = self.web_driver.find_elements(By.XPATH, "/*")
        # assert len(roots) == 1
        # print(f"wrote HTML {html_out}")
        # AmiDriver.write_html(roots[0], html_out)


    def write_html(self, html_out, html_elem=None, pretty_print=True, debug=False):
        """
        convenience method to write HTML
        :param out_html: output file
        :param html_elem: elem to write, if none uses driver.root_elem
        :param pretty_print: pretty_print (default True)
        :param debug: writes name of file
        """
        if html_elem is None:
            html_elem = self.get_lxml_root_elem()
        ss = lxml.etree.tostring(html_elem, pretty_print=pretty_print)
        if debug:
            print(f"writing {html_out}")

        Path(html_out).parent.mkdir(exist_ok=True, parents=True)
        with open(html_out, 'wb') as f:
            f.write(ss)


    def execute_instruction_dict(self, gloss_dict, keys=None):
        keys = gloss_dict.keys() if not keys else keys
        for key in keys:
            _dict = gloss_dict.get(key)
            if _dict is None:
                print(f"cannot find key {key}")
                continue
            self.download_expand_save(_dict.get(URL), _dict.get(XPATH), _dict.get(OUTFILE))

    def get_lxml_root_elem(self):
        """Convenience method to query the web_driver DOM
        :param xpath: to query the dom
        :return: elements in Dom satisfying xpath (may be empty list)
        """
        if self.lxml_root_elem is None:
            data = self.web_driver.page_source
            doc = lxml.etree.parse(StringIO(data), lxml.etree.HTMLParser())
            self.lxml_root_elem = doc.xpath("/*")[0]
            print(f"elements in lxml_root: {len(self.lxml_root_elem.xpath('//*'))}")
        return self.lxml_root_elem


# see https://realpython.com/python-pathlib/

def main():
    print("started file_lib")
    # test_templates()

    print("finished file_lib")


if __name__ == "__main__":
    print("running file_lib main")
    main()
else:
    #    print("running file_lib main anyway")
    #    main()
    pass

# examples of regex for filenames


def glob_re(pattern, strings):
    return filter(re.compile(pattern).match, strings)


filenames = glob_re(r'.*(abc|123|a1b).*\.txt', os.listdir())
