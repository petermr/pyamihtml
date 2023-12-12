import argparse
import ast
import codecs
import logging
import os
import sys
import csv
import re
from enum import Enum
from abc import ABC, abstractmethod
from collections import Counter

import pandas as pd
import pyvis
from lxml import html
from pathlib import Path
import time
import requests
import json
import base64

logger = logging.getLogger(__file__)

HREF = "href"


class Util:
    """Utilities, mainly staticmethod or classmethod and not tightly linked to AMI"""

    @classmethod
    def set_logger(cls, module,
                   ch_level=logging.INFO, fh_level=logging.DEBUG,
                   log_file=None, logger_level=logging.WARNING):
        """create console and stream loggers

        taken from https://docs.python.org/3/howto/logging-cookbook.html#logging-cookbook

        :param module: module to create logger for
        :param ch_level:
        :param fh_level:
        :param log_file:
        :param logger_level:
        :returns: singleton logger for module
        :rtype logger:

        """
        _logger = logging.getLogger(module)
        _logger.setLevel(logger_level)
        # create path handler

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        if log_file is not None:
            fh = logging.FileHandler(log_file)
            fh.setLevel(fh_level)
            fh.setFormatter(formatter)
            _logger.addHandler(fh)

        # create console handler
        ch = logging.StreamHandler()
        ch.setLevel(ch_level)
        ch.setFormatter(formatter)
        _logger.addHandler(ch)

        _logger.debug(f"PyAMI {_logger.level}{_logger.name}")
        return _logger

    @staticmethod
    def find_unique_keystart(keys, start):
        """finds keys that start with 'start'
        return a list, empty if none found or null args
        """
        return [] if keys is None or start is None else [k for k in keys if k.startswith(start)]

    @staticmethod
    def find_unique_dict_entry(the_dict, start):
        """
        return None if 0 or >= keys found
        """
        keys = Util.find_unique_keystart(the_dict, start)
        if len(keys) == 1:
            return the_dict[keys[0]]
        print("matching keys:", keys)
        return None

    @classmethod
    def read_pydict_from_json(cls, file):
        with open(file, "r") as f:
            contents = f.read()
            dictionary = ast.literal_eval(contents)
            return dictionary

    @classmethod
    def normalize_whitespace(cls, text):
        """normalize spaces in string to single space
        :param text: text to normalize"""
        return " ".join(text.split())

    @classmethod
    def is_whitespace(cls, text):
        text = cls.normalize_whitespace(text)
        return text == " " or text == ""

    @classmethod
    def basename(cls, file):
        """returns basename of file
        convenience (e.g. in debug statements
        :param file:
        :return: basename"""
        return os.path.basename(file) if file else None

    @classmethod
    def add_sys_argv_str(cls, argstr):
        """splits argstr and adds (extends) sys.argv
        simulates a commandline
        e.g. Util.add_sys_argv_str("foo bar")
        creates sys.argv as [<progname>, "foo", "bar"]
        Fails if len(sys.argv) != 1 (traps repeats)
        :param argstr: argument string spoce separated
        :return:None
        """
        cls.add_sys_argv(argstr.split())

    @classmethod
    def add_sys_argv(cls, args):
        """adds (extends) sys.argv
        simulates a commandline
        e.g. Util.add_sys_argv_str(["foo", "bar"])
        creates sys.argv as [<progname>, "foo", "bar"]
        Fails if len(sys.argv) != 1 (traps repeats)
        :param args: arguments
        :return:None
        """
        if not args:
            logger.warning(f"empty args, ignored")
            return
        if len(sys.argv) != 1:
            print(f"should only extend default sys.argv (len=1), found {sys.argv}")
        sys.argv.extend(args)

    @classmethod
    def create_name_value(cls, arg: str, delim: str = "=") -> tuple:
        """create name-value from argument
        if arg is simple string, set value to True
        if arg contains delimeter (e.g. "=") split at that
        :param arg: argument (with 0 or 1 delimiters
        :param delim: delimiter (default "=", cannot be whitespace
        :return: name, value , or name, True or None
        """
        if not arg:
            return None
        if not delim:
            raise ValueError(f"delimiter cannot be None")
        if arg.isspace():
            raise ValueError(f"arg cannot be whitespace")
        if len(arg) == 0:
            raise ValueError(f"arg cannot be empty")
        if len(arg.split()) > 1:
            raise ValueError(f"arg [{arg}] may not contain whitespace")

        if delim.isspace():
            raise ValueError(f"cannot use whitespace delimiter")

        ss = arg.split(delim)
        if len(ss) == 1:
            return arg, True
        if len(ss) > 2:
            raise ValueError(f"too many delimiters in {arg}")
        # convert words to booleans
        try:
            ss[1] = ast.literal_eval(ss[1])
        except Exception:
            pass
        return ss[0], ss[1]

    @classmethod
    def extract_csv_fields(cls, csv_file, name, selector, typex):
        """select fields in CSV file by selector value"""
        values = []
        with open(str(csv_file), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                if row[selector] == typex:
                    values.append(row[name])
        return values

    SINGLE_BRACKET_RE = re.compile(r"""
                    (?P<pre>[^(]*)
                    [(]
                    (?P<body>
                    [^)]*
                    )
                    [)]
                    (?P<post>.*)
                    """, re.VERBOSE)  # finds a bracket pair in running text, crude

    @classmethod
    def range_list_contains_int(cls, value, range_list):
        """Is an in in a list of ranges
        :param value: int to test
        :param range_list: list of ranges (or single range)"""
        if range_list is None:
            return False
        # might be a single range
        if type(range_list) is range:
            return value in range_list
        for rangex in range_list:
            if value in rangex:
                return True
        return False

    @staticmethod
    def matches_regex_list(string, regex_list):
        """
        iterate through list and break at first match
        :param string: to match
        :param regex_list: list of regexes
        :return: regex of first match, else None
        """
        for regex in regex_list:
            if re.match(regex, string):
                return regex
        return None

    @classmethod
    def make_translate_mask_to_char(cls, orig, rep):
        """
        make mask to replace all characters in orig with rep character
        :param orig: string of replaceable characters
        :param rep: character to replac e them
        :returns: dict mapping (see str.translate and str.make
        """
        if not orig or not rep:
            return None
        if len(rep) != 1:
            logging.warning(f"rep should be single char, found {rep}")
            return None
        if len(orig) == 0:
            logging.warning(f"orig should be len > 0")
            return None
        return str.maketrans(orig, rep * len(orig))

    @classmethod
    def print_stacktrace(cls, ex):
        """
        prints traceback
        :param ex: the exception
        """
        if ex:
            traceback = ex.__traceback__
            while traceback:
                print(f"{traceback.tb_frame.f_code.co_filename}: {traceback.tb_lineno}")
                traceback = traceback.tb_next

    @classmethod
    def get_urls_from_webpage(cls, suffixes, weburl):

        page = requests.get(weburl)
        tree = html.fromstring(page.content)
        ahrefs = tree.xpath(f".//a[@{HREF}]")
        urls = []
        for sf in suffixes:
            sf_ = [ahref.attrib[HREF] for ahref in ahrefs if ahref.attrib[HREF].endswith(f".{sf}")]
            urls.extend(sf_)
        return urls

    @classmethod
    def download_urls(cls, urls=None, target_dir=None, maxsave=100, printfile=True, skip_exists=True, sleep=5):
        """
        download list of urls
        :param urls: urls to download
        :param target_dir: directry to receive urls
        :param maxsave: maximum number to download (note: can be used tyo dowwnload in batches) default = 100
        :param printfile: prints download or skip (default = True)
        :param skip_exists: If true does not overwrite existuing file (default = True)
        :param sleep: seconds to wait  between downloads (default = 5)
        """
        if urls is None:
            print(f"no url list to download")
            return None
        if type(urls) is not list:
            urls = [urls]
        if target_dir is None:
            print(f"no traget_dir to download into")
            return None
        for url in urls[:maxsave]:
            stem = url.split("/")[-1]
            target_dir.mkdir(exist_ok=True)
            path = Path(target_dir, stem)
            if skip_exists and path.exists():
                if printfile:
                    print(f"file exists, skipped {path}")
            else:
                try:
                    content = requests.get(url).content
                except Exception as e:
                    print(f"cannot get content from url {url}")
                    continue
                with open(path, "wb") as f:
                    if printfile:
                        print(f"wrote url: {path}")
                    f.write(content)
                time.sleep(sleep)
        return None

    @classmethod
    def get_file_from_url(cls, url):
        """
        takes last slash-separated field in url as pseudo filename
        url to parse of form https://foo.nar/plugh/bloop.xml
        :param url: url to parse
        :return: file after last slash (i.e. bloop.xml) or None
        """
        if url is None:
            return None
        rindex = url.rfind('/')
        if rindex == -1:
            return None
        return url[rindex + 1:]

    @classmethod
    def create_string_separated_list(cls, listx):
        """
        create string separated list , e.g. [1,2,3] => "1 2 3"
        :param listx: list of objects
        :return" space-separaated list
        """
        return " ".join(list(map(str, listx))) if listx else ""

    @classmethod
    def open_write_utf8(cls, outpath):
        """
        opens file for writing as UTF-8
        (with open(outpath,"w" as f
        may fail if there are problem characters)
        :param outpath: file to write to
        :return: StreamReaderWriter
        """
        if not outpath:
            return None
        return codecs.open(str(outpath), "w", "UTF-8")

    @classmethod
    def open_read_utf8(cls, inpath):
        """
        opens file for reading as UTF-8
        (with open(inpath,"r" as f
        may fail if there are problem characters)
        :param inpath: file to read
        :return: StreamReaderWriter
        """
        return codecs.open(inpath, "r", "UTF-8")

    @classmethod
    def is_base64(cls, s):
        """
        tests if string is base64 by encoding and decoding
        :param s: string to test
        :return: True if successful , Exception creates False
        """
        try:
            return base64.b64encode(base64.b64decode(s)) == s
        except Exception:
            print(f"not b64: {s}")
            return False

    @classmethod
    def create_pyviz_graph(cls, incsv, anchor="anchor", target="target", outpath=None):
        """creates network graph from CSV file
        :param incsv: csv filename
        :param anchor: name of anchor column (def 'anchor')
        :param target: name of target column (def 'target')
        :param outpath: file to draw graph to (def None)
        uses pyvis_graph.force_atlas_2based() for layout (will give moer options later
        """
        try:
            with open(str(incsv), "r") as f:
                data = pd.read_csv(f)
        except Exception as e:
            logger.error(f"cannot read {incsv} because {e}")
            return
        anchors = cls.get_column(data, anchor, incsv)
        targets = cls.get_column(data, target, incsv)
        if anchors is None or targets is None:
            logger.error(f"Cannot find anchors/targets in CSV {incsv}")
            return None
        pyvis_graph = pyvis.network.Network(notebook=True)
        for a, t in zip(anchors, targets):
            pyvis_graph.add_node(a, label=a)  # also color, size
            pyvis_graph.add_node(t, label=t)
            pyvis_graph.add_edge(a, t)  # also color
        pyvis_graph.force_atlas_2based()
        if outpath:
            try:
                pyvis_graph.show(str(outpath))
            except Exception as e:
                logger.error(f"Cannot write pyviz graph to {outpath} because {e}")

    @classmethod
    def get_column(cls, data, colname, csvname=None):
        col = data.get(colname)
        if col is None:
            logger.error(f"Cannot find column {colname} in CSV {csvname}")
        return col

    @classmethod
    def should_make(cls, target, source):
        """
        return True if target does not exist or is older than source
        :param target: file to make
        :param source: file to create from
        :return:
        """
        if not source:
            raise ValueError("source is None")
        if not target:
            raise ValueError("target is None")
        source_path = Path(source)
        target_path = Path(target)
        if not source_path.exists():
            raise FileNotFoundError("{source} does not exist")
        if not target_path.exists():
            return True
        # modification times (the smaller the older)
        target_mod = os.path.getmtime(target)
        source_mod = os.path.getmtime(source)
        return target_mod < source_mod


class GithubDownloader:
    """Note: Github uses the old 'master' name but we have changed it to 'main'"""

    def __init__(self, owner=None, repo=None, sleep=3, max_level=1):
        """if sleep is too small, Github semds 403"""
        self.owner = owner
        self.repo = repo
        self.main_url = None
        self.sleep = sleep
        self.max_level = max_level

        """
        7
https://stackoverflow.com/questions/50601081/github-how-to-get-file-list-under-directory-on-github-pages

Inspired by octotree (a chrome plugin for github),
send API GET https://api.github.com/repos/{owner}/{repo}/git/trees/master to get root folder structure and recursively visit children of "type": "tree".

As github API has rate limit of 5000 requests / hour, this might not be good for deep and wide tree.
{
  "sha": "8b991099652468e1c3c801f5600d37ec483be07f",
  "url": "https://api.github.com/repos/petermr/CEVOpen/git/trees/8b991099652468e1c3c801f5600d37ec483be07f",
  "tree": [
    {
      "path": ".gitignore",
      "mode": "100644",
      "type": "blob",
      "sha": "22c4e9d412e97ebbeceb6d7b922970ba115db9ac",
      "size": 323,
      "url": "https://api.github.com/repos/petermr/CEVOpen/git/blobs/22c4e9d412e97ebbeceb6d7b922970ba115db9ac"
    },
    {
      "path": "BJOC",
      "mode": "040000",
      "type": "tree",
      "sha": "68866e1c37b63e4699b75cae8dc6923ef04fb898",
      "url": "https://api.github.com/repos/petermr/CEVOpen/git/trees/68866e1c37b63e4699b75cae8dc6923ef04fb898"
    },
        """

    def make_get_main_url(self):
        if not self.main_url and self.owner and self.repo:
            self.main_url = f"https://api.github.com/repos/{self.owner}/{self.repo}/git/trees/master"
        return self.main_url

    def load_page(self, url, level=1, page=None, last_path=None):
        if level >= self.max_level:
            print(f"maximum tree levels exceeded {level} >= {self.max_level}\n")
            return
        time.sleep(self.sleep)
        response = requests.get(url)
        if str(response.status_code) != '200':
            print(f"page response {response} {response.status_code} {response.content}")
            return None
        page_dict_str = response.content.decode("UTF-8")
        json_page = json.loads(page_dict_str)
        print(f"json page {json_page.keys()}")
        path = json_page["path"] if "path" in json_page else last_path
        if "tree" in json_page:
            links = json_page['tree']
            for link in links:
                print(f"link: {link.items()} ")
                typex = link["type"]
                path = link["path"]  # relative (child) pathname
                child_url = link["url"]
                if typex == 'blob':
                    self.load_page(child_url, level=level, last_path=path)
                elif typex == 'tree':
                    print(f"\n============={path}===========")
                    self.load_page(child_url, level=level + 1)
        elif "content" in json_page:
            content_str = json_page["content"]
            encoding = json_page["encoding"]
            if encoding == "base64":
                content = base64.b64decode(content_str).decode("UTF-8")
                print(f"\n===={path}====\n{content[:100]} ...\n")
        else:
            print(f"unknown type {json_page.keys()}")

    @classmethod
    def make_translate_mask_to_char(cls, punct, charx):
        """
        makes mask to translate all chars to a sigle replacmeny
        uses str,maketrans()

        Use:
        mask = Util.make_translate_mask_to_char("=]%", "_""):
        str1 = str0.translate(mask)
        str1 is same length as str0
        :param punct: string containing unwanted chars
        :param charx: their single character replacement.
        """
        punct_mask = str.maketrans(punct, charx * len(punct))
        return punct_mask


class AmiArgParseException(Exception):
    """
    to capture error messages from AmiArgparser
    """
    pass


class AmiArgParser(argparse.ArgumentParser):
    """
    subclasses ArgumentParser and overrides error()
    """

    def error(self, message):
        """
        raises self.exit(2, error_message) so can be caught
        """
        raise AmiArgParseException(message)


class AbstractArgs(ABC):

    def __init__(self):
        self.parser = None
        self.parsed_args = None
        self.ref_counter = Counter()
        self.arg_dict = self.create_default_arg_dict()

    def create_arg_dict(self, args=None):
        if args:
            self.parsed_args = args
        # print(f"PARSED_ARGS {type(self.parsed_args)} {self.parsed_args}")
        if not self.parsed_args:
            return None
        try:
            arg_vars = vars(self.parsed_args)
        except TypeError:
            # print(f" type args {type(self.parsed_args)} {self.parsed_args}")
            arg_vars = self.parsed_args
        self.arg_dict = dict()
        for item in arg_vars.items():
            key = item[0]
            if item[1] is None:
                pass
            elif type(item[1]) is list and len(item[1]) == 1:
                self.arg_dict[key] = item[1][0]
            else:
                self.arg_dict[key] = item[1]

        return self.arg_dict

    def parse_and_process(self):
        """Parse args after program name.
        If running in IDE there may be 2 names.
        All names should contain name of module (e.g. ami_dict)

        '/Applications/PyCharm CE.app/Contents/plugins/python-ce/helpers/pycharm/_jb_pytest_runner.py', 'ami_dict.py::test_process_args']
        or
        '/Users/pm286/workspace/pyami/pyamihtml/ami_dict.py', '--dict', 'foo', '--words', 'bar'

        """
        # strip all tokens including ".py" (will proably fail on some m/c)
        print(f"module_stem: {self.module_stem}\n sys.argv {sys.argv}")
        args_store = sys.argv.copy()
        while len(sys.argv) > 0 and self.module_stem not in str(sys.argv[0]):
            print(f"trimming sys.argv {sys.argv}")
            sys.argv = sys.argv[1:]
        if len(sys.argv) == 0:  # must have name of prog
            sys.argv = args_store.copy()
        try:
            self.add_arguments()
        except Exception as e:
            print(f"failed to add args {e}")
            # if "list index out of range" == str(e):
            #     print(f"trying to fix args {sys.argv}")
            #     sys.argv = args_store.copy()
            #     print(f"original args {sys.argv}")
            # else:
            raise e
        logger.warning(f"AbstractArgs ADDED ARGS {sys.argv}")
        # print(f"argv {sys.argv}")
        if len(sys.argv) == 1:  # no args, print help
            self.parser.print_help()
        else:
            logging.warning(f"sys.argv {sys.argv}")
            argv_ = sys.argv[1:]
            print(f"argv: {argv_}")
            self.parse_and_process1(argv_)

    def parse_and_process1(self, argv_):
        logging.debug(f"********** args for parse_and_process1 {argv_}")
        self.parsed_args = argv_ if self.parser is None else self.parser.parse_args(argv_)
        #        logging.warning(f"ARG DICTYY {self.arg_dict}")
        self.arg_dict = self.create_arg_dict()
        self.process_args()

    @property
    # @abstractmethod  # I don't know why this doesn't work
    def subparser_name(self):
        pass

    # @abstractmethod
    def add_argumants(self):
        pass

    @abstractmethod
    def process_args(self):
        pass

    @abstractmethod
    def create_default_arg_dict(self):
        pass

    @property
    def subparser_arg(self):
        """extracts suparser arg (e.g. 'DICT',(base) pm286macbook:pyami pm286$ python -m pyamihtml.pyamix DICT --dict /Users/pm286/projects/semanticClimate/ipcc//ar6/wg3/Chapter02/dict/emissions.xml --valid
===========LOGGING 30 .. 10
WARNING:pyami:
============== running pyami main ===============
['DICT', '--dict', '/Users/pm286/projects/semanticClimate/ipcc//ar6/wg3/Chapter02/dict/emissions.xml', '--valid']
 COMMAND: DICT
reading /Users/pm286/projects/semanticClimate/ipcc//ar6/wg3/Chapter02/dict/emissions.xml as dictionary
dictionary.entries 33
entry_by_term 33
title emissions
VALIDATING <pyamihtml.ami_dict.AmiDictionary object at 0x7fcfb34981f0>
forbidden child synonym ; allowed = {'entry', 'desc'}
forbidden child synonym ; allowed = {'entry', 'desc'}
forbidden child synonym ; allowed = {'entry', 'desc'}
forbidden child synonym ; allowed = {'entry', 'desc'}
forbidden child synonym ; allowed = {'entry', 'desc'}
(base) pm286macbook:pyami pm286$
 """
        stem = self.module_stem.replace("ami_", "")
        return stem.upper()

    def make_run_func(self):
        """probably obsolete"""
        func_name = self.module_stem.replace("ami_", "run_")
        print(f"run_func_name {func_name}")
        return func_name

    def make_sub_parser(self, subparsers):
        """make subparser from subparsers
        requires self.subparser_arg (probably should be argument
        ALSO adds arguments through `self.add_arguments`
        :param subparsers: subparser generator
        :return: new subparser"""
        self.parser = subparsers.add_parser(self.subparser_arg)
        subparser_arg = self.parser.prog.split()[1]
        self.add_arguments()
        return self.parser


class ArgParseBuilder:
    ARG_LIST = "arg_list"
    DESCRIPTION = "description"

    def __init__(self):
        self.parser = None

    def create_arg_parse(self, arg_dict=None, arg_dict_file=None):
        # arg_dict_file takes precedence
        if arg_dict_file and arg_dict_file.exists():
            with open(arg_dict_file, 'r') as f:
                data = f.read()
                arg_dict = json.loads(data)
                print(f"arg_dict {arg_dict}")

        if arg_dict is not None:
            desc = f'{arg_dict.get(self.DESCRIPTION)}'
            print(f"\ndesc: '{desc}'")
            self.parser = argparse.ArgumentParser(description=desc)
            arg_list = arg_dict.get(self.ARG_LIST)
            if arg_list is None:
                raise ValueError(f"must give arg_list to ArgParseBuilder")
            for arg_dict in arg_list:
                if not type(arg_dict) is dict:
                    raise ValueError(f"arg_list_dict {arg_dict} is not a dict")
                args = arg_dict.keys()
                for arg in args:
                    print(f"\n{arg}:")
                    param_dict = arg_dict.get(arg)
                    self.process_params(param_dict)
                # self.parser.add_argument(f"--{ProjectArgs.PROJECT}", type=str, nargs=1, help="project directory")

    """https://stackoverflow.com/questions/28348117/using-argparse-and-json-together"""

    def process_params(self, param_dict):
        for param, param_val in param_dict.items():
            print(f"  {param}='{param_val}'")


"!\"#$%&'()*+,/:;<=>?@[\]^`{|}~"


class AmiLogger:
    """wrapper for logger to limit or condense voluminous output

    adds a dictionary of counts for each log level
    """

    def __init__(self, loggerx, initial=10, routine=100):
        """create from an existing logger"""
        self.logger = loggerx
        self.func_dict = {
            "debug": self.logger.debug,
            "info": self.logger.info,
            "warning": self.logger.warning,
            "error": self.logger.error,

        }
        self.initial = initial
        self.routine = routine
        self.count = {
        }
        self.reset_counts()

    def reset_counts(self):
        for level in self.func_dict.keys():
            self.count[level] = 0

    # these will be called instead of logger
    def debug(self, msg):
        self._print_count(msg, "debug")

    def info(self, msg):
        self._print_count(msg, "info")

    def warning(self, msg):
        self._print_count(msg, "warning")

    def error(self, msg):
        self._print_count(msg, "error")

    # =======

    def _print_count(self, msg, level):
        """called by the wrapper"""
        logger_func = self.func_dict[level]
        if level not in self.count:
            self.count[level] = 0
        if self.count[level] <= self.initial or self.count[level] % self.routine == 1:
            logger_func(f"{self.count[level]}: {msg}")
        else:
            print(".", end="")
        self.count[level] += 1

    @classmethod
    def create_named_logger(cls, file):
        return logging.getLogger(os.path.basename(file))


GENERATE = "_GENERATE"  # should we generate IDREF?


class EnhancedRegex:
    """parses regex and uses them to transform"""

    STYLES = [
        (".class0", [("color", "red;")]),
        (".class1", [("background", "#ccccff;")]),
        (".class2", [("color", "#00cc00;")]),
    ]

    # class EnhancedRegex:

    def __init__(self, regex=None, components=None):
        self.regex = regex
        self.components = components
        if regex and not components:
            self.components = self.make_components_from_regex(self.regex)
        if components and not regex:
            self.regex = self.make_regex_with_capture_groups(self.components)

    # class EnhancedRegex:
    def make_components_from_regex(self, regex):
        """splits regex into components
        regex must contain alternating sequence of capture/non_capture groups"""
        # split = "(\(\?P<[^\)]*]\))"
        split = "(\([^\)]*\))"
        self.components = None
        if regex is not None:
            # print(f"regex {regex}")
            self.components = re.split(split, regex)
        return self.components

    # class EnhancedRegex:

    def make_id(self, target):
        """assumes self.regex or self.components has been loaded
        """
        return None if not self.regex else self.make_id_with_regex(self.regex, target)

    def make_id_with_regex(self, regex, target, sep="_"):
        """makes ids from strings using list of sub-regexes
        :param regex: regex with cpature groups ...
        :param target: string to generate id from
        :param sep: separator
        see make_regex_with_capture_groups
        at present separator is "_" ; TODO expand this
        """
        if regex is None or target is None:
            return None
        components = self.make_components_from_regex(regex)
        id = self.make_id_with_regex_components(components, target)
        return id

    # class EnhancedRegex:

    def make_id_with_regex_components(self, components, target, sep="_"):
        """makes ids from strings using list of sub-regexes
        :param components: list of regex components of form (name, regex) separator ...
        :param target: string to generate id from
        :param sep: separator
        see make_regex_with_capture_groups
        at present separator is "_" ; TODO expand this
        """

        def make_list_of_names_in_capture_groups(capturegroup_name, components, debug=False):
            names = []
            for comp in components:
                # extract capture_group name from regex
                match1 = re.match(capturegroup_name, comp)
                if match1:
                    names.append(match1.group(1))
            return names

        if self.regex is None:
            return None
        capturegroup_name_regex = ".*\(\?P<(.*)>.*"

        names = make_list_of_names_in_capture_groups(capturegroup_name_regex, components)
        match = re.match(self.regex, target)
        # print(f">>match {match}")
        # SEP = "_"
        id = None
        if match:
            id = ""
            for i, name in enumerate(names):
                if i > 0:
                    id += sep
                id += match.group(name)

        return id

    # class EnhancedRegex:

    def make_regex_with_capture_groups(self, components):
        """make regex with capture groups
        takes components list of alternating strings and tuples (of form name, regex)
        :param components: list [str] (tuple) str (tuple) str (tuple) ... [str]
        from
        components = ["", ("decision", "\d+"), "/", ("type", "CP|CMA|CMP"), "\.", ("session", "\d+"), ""]
        :return: a regex of form:
        (?P<decision>\d+)/(?P<type>CP|CMA|CMP)\.(?P<session>\d+)
        """
        last_t = None
        regex = ""
        for component in components:
            # t = type(component)
            # if isinstance(component, str) and (last_t is None or isinstance(last_t, tuple)):
            #     regex += component
            # elif isinstance(component, tuple) and (last_t is None or isinstance(last_t, str)):
            #     regex += f"(?P<{component[0]}>{component[1]})"
            # else:
            #     print(f"bad component [{component}] in {components}")
            last_t = component
        return regex

    # class EnhancedRegex:

    def make_components_from_regex(self, regex):
        """splits regex into components
        regex must contain alternating sequence of capture/non_capture groups"""
        split = "(\(\?P<[^\)]*]\))"
        split = "(\([^\)]*\))"
        raw_comps = None
        if regex is not None:
            # print(f"...regex {regex}")
            raw_comps = re.split(split, str(regex))
        return raw_comps

    # class EnhancedRegex:

    def get_href(self, href, text=None):
        """generates href/idref from matched string
        """
        from pyamihtml.util import GENERATE

        if href == GENERATE:
            idref = self.make_id_with_regex(self.regex, text)
            return idref
        else:
            return href

class Templater:
    """
    inserts strings into templates
    uses format, not f-strings
    """
    def __init__(self, template=None, regex=None):
        self.template = template
        self.regex = regex

    def match_template(self, strng):
        return Templater.get_matched_template()

    @classmethod
    def get_matched_templates(cls, regex, strings, template):
        matched_templates = []
        for strng in strings:
            matched_template = cls.get_matched_template(regex, strng, template)
            matched_templates.append(matched_template)
        return matched_templates

    @classmethod
    def get_matched_template(cls, regex, strng, template):
        """
        matches strng with regex-named-capture-groups and extracts matches into template
        :parem regex: with named captures
        :param strng: to match
        :param template: final string with named groups in {} to substitute
        :return substituted strng

        Simple Examaple
        template = "{DecRes}_{decision}_{type}_{session}"
        regex = "(?P<DecRes>Decision|Resolution)\\s(?P<decision>\\d+)/(?P<type>CMA|CMP|CP)\\.(?P<session>\\d+)"
        strng = "Decision 12/CMP.5"
        returns 'Decision_12_CMP_5'

        but more complex templates can include repeats. However these are NOT f-strings and do not use eval()
        """
        match = re.search(regex, strng)
        if not match:
            matched_template = None
        else:
            template_values = match.groupdict()
            matched_template = template.format(**template_values)
        return matched_template

    @classmethod
    def create_template(cls, template, regex):
        templater = Templater()
        templater.regex = regex
        templater.template = template
        return templater


# sub/Super

class SScript(Enum):
    SUB = 1
    SUP = 2
