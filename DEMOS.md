# pyami demos

`pyami` and `pyamihtml` code is often developed as integration tests, run under Python tests. We will systematically move successful tests to our code library and options under `argparse` commandline runner. At present all code requires having Python <= 3.10 installed on your machine. 

## github repo
Check out the latest code from `https://github.com/petermr/pyamihtml`. 

(There is a `PyPI` report for `pyamihtml` but it may not always be uptodate).

We recommend you run the code in an IDE so that individual tests can be located . They can be run from the commandline with
```
pytext -m pytest
````
This requires the Internet and will take several minutes, and there are some uncorrected failures.

## test-based demos

These are contained in `pyamihtml/test`. The main modules used are

* `test_headless` : for scraping web pages 
* `test_html` : for converting to html and and further structuriing or annotating
* `test_integrate` : integration tests
* `test_pdf` : for PDF cnversion and structuring

 
