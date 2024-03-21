"""classes and methods to support path operations

"""
import json
from io import StringIO

import chardet
# import copy
# from enum import Enum, auto
import errno
import glob
import logging
import re
import os
from pathlib import Path, PurePath, PurePosixPath
import shutil

import time

import lxml.etree as ET
import requests
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webelement import WebElement
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
    def expand_glob_list(cls, file_list):
        """
        :param file_list: list of paths including globs
        :return: flattened globbed list wwith posix names
        """
        if type(file_list) is not list:
            file_list = [file_list]
        files = []
        for file in file_list:
            globbed_files = FileLib.posix_glob(str(file))
            files.extend(globbed_files)
        return cls.convert_files_to_posix(files)

    @classmethod
    def convert_files_to_posix(cls, file_list):
        """converts list of files to posix form (i.e. all files have / not backslash)
        """
        if file_list is None:
            return None
        posix_files = [PurePosixPath(f) for f in file_list]
        return posix_files


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
    def join_dir_and_file_as_posix(cls, indir, input):
        """
        joins indir (directory) and input (descendants) to make a list of full filenames
        if indir or input is null, no action
        if indir is a list no action, returns input unchanged
        if input is absolute (starts with "/") no action

        if input is string, creates PosixPath(indir, input) VIA PosixPath
        if input is list of strings creates:
            f"{indir}/{input1}"
            f"{indir}/{input2}"
            ...
            it skips any input strings starting with "/"
        :param indir: input directory
        :param input: single file or list
        :return: single filke or files AS posix strings
        """
        if not indir or not input:
            return input
        # cannot manage multiple directories (?yet)
        if type(indir) is list and len(indir) > 1:
            return input

        if type(input) is str:
            # single input
            if input[0] != "/":
                output = PurePosixPath(indir, input)
                return str(output)
        elif type(input) is list:
            # list of inputs
            outputs = []
            for input_item in input:
                if input_item[0] != "/":
                    posix = PurePosixPath(indir, input_item)
                    outputs.append(str(posix))
            return outputs

    @classmethod
    def posix_glob(cls, glob_str, recursive = True):
        """expands glob and ensure all output is posix
        :param glob_str: glob or list of globs to expand
        :param recursive: use recursive glob
        :return: list of files in posix format"""
        files = []
        if glob_str is None:
            return files
        if type(glob_str) is str:
            glob_str = [glob_str]
        for globx in glob_str:
            ff = glob.glob(globx, recursive=recursive)
            files.extend(ff)
        files = FileLib.convert_files_to_posix(files)
        return files

    @classmethod
    def assert_exist_size(cls, file, minsize, abort=True):
        """asserts a file exists and is of sufficient size
        :param file: file or path
        :param minsize: minimum size
        """
        path = Path(file)
        try:
            assert path.exists(), f"file {path} must exist"
            assert (s := path.stat().st_size) > minsize, f"file {file} size = {s} must be above {minsize}"
        except AssertionError as e:
            if abort:
                raise e


    @classmethod
    def get_home(cls):
        """
        gets home directory os.path.expanduser("~")
        """
        home = os.path.expanduser("~")
        return home


URL = "url"
XPATH = "xpath"
OUTFILE = "out_file"

EXPAND_SECTION_PARAS = [
    '//button[contains(@class, "chapter-expand") and contains(text(), "Expand section")]',
    '//p[contains(@class, "expand-paras") and contains(text(), "Read more...")]'
]


class AmiDriver:
    """
    create and wrap a Chrome headless browser
    Author Ayush Garg, modified Peter Murray-Rust
    """

    def __init__(self, sleep=3):
        """
        creates a Chrome WebDriver instance with specified options and settings.
        """
        options = webdriver.ChromeOptions()
        options.page_load_strategy = "none"
        chrome_path = ChromeDriverManager().install()
        chrome_service = Service(chrome_path)
        self.web_driver = Chrome(options=options, service=chrome_service)
        self.lxml_root_elem = None
        self.sleep = sleep

    def set_sleep(self, sleep):
        if sleep is None or sleep < 1:
            print(f"sleep must be >= 1")
            return
        if sleep > 20:
            print(f"sleep must be <= 20")
            sleep = 20
        self.sleep = sleep

#    class AmiDriver:

    def quit(self):
        """quite the web_driver"""
        print("Quitting the driver...")
        self.web_driver.quit()
        print("DONE")

    def safe_click_element(self, element):
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
            WebDriverWait(self, self.sleep).until(
                EC.element_to_be_clickable((By.XPATH, element.get_attribute("outerHTML")))
            )
            print(f"waiting... {self.sleep}")
            element.click()
        except ElementClickInterceptedException:
            # If the element is not clickable, scroll to it and try again
            self.web_driver.execute_script("arguments[0].scrollIntoView();", element)
            element.click()
        except Exception:
            # If it still doesn't work, use JavaScript to click on the element
            self.web_driver.execute_script("arguments[0].click();", element)

    #    class AmiDriver:

    def get_page_source(self, url):
        """
        returns the page source code.

        :param url: The URL of the webpage you want to retrieve the source code from
        :param sleep: sleep time
        :return: the page source of the website after the driver navigates to the specified URL.
        """
        print(f"Fetching page source from URL: {url}")
        self.web_driver.get(url)
        time.sleep(self.sleep)
        return self.web_driver.page_source

    def click_xpath_list(self, xpath_list):
        if not xpath_list or type(xpath_list) is not list:
            print(f"no xpath_list {xpath_list}")
            return
        print(f"Clicking xpaths...{xpath_list}")
        for xpath in xpath_list:
            print(f"xpath: {xpath}")
            self.click_xpath(xpath)

    #    class AmiDriver:

    def click_xpath(self, xpath):
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
            print(f"sleep {self.sleep}")
            time.sleep(self.sleep)  # Wait for the section to expand
        print(f"<<<<element count after = {self.get_lxml_element_count()}")

    def get_lxml_element_count(self):
        elements = self.get_lxml_root_elem().xpath("//*")
        return len(elements)

    #    class AmiDriver:

    def download_expand_save(self, url, xpath_list, html_out, level=99, sleep=3, pretty_print=True):
        """
        Toplevel convenience class

        :param url: to download
        :param xpath_list: ordered list of Xpaths to click
        :param html_out: file to write
        :param level: number of levels to desend (default = 99)
        :param sleep: seconds to sleep between download (default 3)
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

    #    class AmiDriver:

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
        ss = ET.tostring(html_elem, pretty_print=pretty_print)
        if debug:
            print(f"writing {html_out}")

        Path(html_out).parent.mkdir(exist_ok=True, parents=True)
        with open(html_out, 'wb') as f:
            f.write(ss)

    #    class AmiDriver:

    def execute_instruction_dict(self, gloss_dict, keys=None):
        keys = gloss_dict.keys() if not keys else keys
        for key in keys:
            _dict = gloss_dict.get(key)
            if _dict is None:
                print(f"cannot find key {key}")
                continue
            self.download_expand_save(_dict.get(URL), _dict.get(XPATH), _dict.get(OUTFILE))

    #    class AmiDriver:

    def get_lxml_root_elem(self):
        """Convenience method to query the web_driver DOM
        :param xpath: to query the dom
        :return: elements in Dom satisfying xpath (may be empty list)
        """
        if self.lxml_root_elem is None:
            data = self.web_driver.page_source
            doc = ET.parse(StringIO(data), ET.HTMLParser())
            self.lxml_root_elem = doc.xpath("/*")[0]
            print(f"elements in lxml_root: {len(self.lxml_root_elem.xpath('//*'))}")
        return self.lxml_root_elem

    #    class AmiDriver:

    def run_from_dict(self, outfile, dikt, declutter=None, keys=None, debug=True):
        """
        reads doc names from dict and creates HTML

        :param outfile: file to write
        :param control: control dict
        :param declutter: elements to remove (default DECLUTTER_BASIC)
        :param keys: list of control keys (default = all)

        """
        self.execute_instruction_dict(dikt, keys=keys)
        root = self.get_lxml_root_elem()
        self.write_html(outfile, pretty_print=True, debug=debug)
        assert Path(outfile).exists(), f"{outfile} should exist"

    #    class AmiDriver:

    def download_and_save(self, outfile, chap, wg, wg_url):
        ch_url = wg_url + f"chapter/{chap}"
        wg_dict = {
            f"wg{wg}_{chap}":
                {
                    URL: ch_url,
                    XPATH: None,  # no expansiom
                    # OUTFILE: spm_outfile_gatsby2 # dont think this gets written
                },
        }
        keys = wg_dict.keys()
        self.run_from_dict(outfile, wg_dict)
        root_elem = self.lxml_root_elem
        self.quit()
        return root_elem




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
