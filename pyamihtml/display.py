from datetime import datetime
from pathlib import Path

import lxml

from pyamihtml.un import UNFCCC
from pyamihtml.xml_lib import HtmlLib


class Vivlio:

    """to display VIVLIO
    https://vivliostyle.vercel.app/#src=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/publication.json&style=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/css/appaloosa-rq.css
    """
    VIVLIO_APP = "https://vivliostyle.vercel.app"

    V_BACK = {
            "filename" : "back_ccver.html",
            "content" : f"""
<html>
  <head>
    <meta charset="UTF-8">
  </head>
  <body class="user-contents">
    <div class="backcover backmatter">
      <h4 class="bookversion">Version Alpha 1.0 DOI: 10.1000/100 SHA-256: {datetime.today()}
  </body>
</html>
"""
        }

    V_FRONT = {
        "filename": "front_cover.html",
        "content": f"""
<html>
  <head>
    <meta charset="UTF-8">
  </head>
<body class="user-contents">
    <div class="titlepage frontmatter">
      <h1 class="booktitle">{{TITLE}}</h1>
      <h2 class="booksubtitle">{{FRONT_SUBTITLE}}</h2>
      <h3 class="bookauthor">by Team #semanticClimate</h3>
      <h4 class="bookversion">Version Alpha 1.0 DOI: 10.1000/100 SHA-256: #0000000 UTC: 0000-00-00T00:00:00Z</h4>
    </div>
</body></html>""",
        }

    V_IMPRINT = f"""<html>
    <head>
        <meta charset="UTF-8">
    </head>
    <body class="user-contents">
      <div class="copyrightpage frontmatter">
        <p>{{TITLE}}</p>
      <p>Version: Alpha 1.0 (work in progress)</p>
        <p>Last updated: f'{{date.today():%Y-%m-%d}}'</p>
      <p>GitHub source: <a href="{{GITHUB_SOURCE}}">{{GITHUB_SOURCE}}</a></p>
      <p>SHA-256: <a href="https://www.w3.org/TR/wpub/#example-60-a-resource-with-a-sha-256-hashing-of-its-content">W3C Web Publications support integrity checks: A resource with a SHA-256 hashing of its content</a></p>
        </div>
    </body>
</html>""",

    VIVLIO_JSON = f"""{{
        "filename": "publication.json",
        "content":     {{
    "@context": [
      "https://schema.org",
      "https://www.w3.org/ns/pub-context"
    ],
    "conformsTo": "https://www.w3.org/TR/pub-manifest/",
    "type": "Book",
    "name": f"{{TITLE}}",
    "author": f"{{AUTHOR}}",
    "inLanguage": "en",
    "readingOrder": [
      "front_cover.html",
      "imprint.html",
      "toc_ses_dec_res.html",
      f"{{TEMP_REPO}}/CMA_4/12_24_CMA_4_section%20target.html",
      "toc_dec_res_13_20_CMA_1.html",
      f"{{TEMP_REPO}}/{{SESSION}}/{{DECISION}}/final.html",
      # f"{{TEMP_REPO}}/CMA_3/1_4_CMA_3_section%20target.html",
      "back_cover.html"
    ]
    }},
        }}
            """


    resources = [
      {
        "type": "LinkedResource",
        "url": "toc_toplevel_sum_ses.html",
        "rel": "contents"
      },
        {
            "type": [
                "LinkedResource"
            ],
            "url": "css/appaloosa.css"
        },
        {
          "type": [
              "LinkedResource"
          ],
          "url": "css/mathlive.css"
      },
        {
            "type": [
                "LinkedResource"
            ],
            "url": "css/book.css"
        }
      ]

    @classmethod
    def create_vivlio_url(cls, css, json):
        display_str = f"{Vivlio.VIVLIO_APP}/#src={json}&style={css}"
        return display_str

    @classmethod
    def create_toc_html(cls, decision_dirs, get_title=None, out_dir=None, html_inname="final.html", outname="toc.html", debug=False):
        html_elem = HtmlLib.create_html_with_empty_head_body()
        body_elem = HtmlLib.get_body(html_elem)
        for decision_dir in decision_dirs:
            ul_elem = lxml.etree.SubElement(body_elem, "ul")
            decision_html = HtmlLib.parse_html(Path(decision_dir, html_inname))
            title = "dummy" if get_title is None else get_title(decision_html)
            li_elem = lxml.etree.SubElement(ul_elem, "li")
            p_elem = lxml.etree.SubElement(li_elem, "p")
            a_elem = lxml.etree.SubElement(p_elem, "a")
            a_elem.text = f"{title}"
            a_elem = lxml.etree.SubElement(p_elem, "br")
            a_elem = lxml.etree.SubElement(p_elem, "a")
            a_elem.text = f"{decision_dir.stem}"
            a_elem.attrib["href"] = str(Path(decision_dir, html_inname))
            if debug:
                print(f"{decision_dir.stem}: {title}")
            if out_dir and outname:
                path = Path(out_dir, outname)
                HtmlLib.write_html_file(html_elem, path)
                if debug:
                    print(f"wrote {path}")
        return html_elem


