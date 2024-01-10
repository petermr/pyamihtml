import json
from datetime import datetime
from pathlib import Path

import lxml
import lxml.etree

from pyamihtmlx.xml_lib import HtmlLib


class VivlioManifest:

    @classmethod
    def add_biblio_meta(cls, pub_dict, name, author):
        """
            "name": "Report of the Conference of the Parties serving as the meeting of the Parties to the Paris Agreement on its third session, held in Glasgow from 31 October to 13 November 2021",
            "author": "United Nations Framework Convention on Climate Change (UNFCCC)",
        """
        pub_dict["name"] = name
        pub_dict["author"] = author

    @classmethod
    def add_general(cls, pub_dict, type="Book", inLanguage="en"):
        """
            "type": "Book",
            "inLanguage": "en",
        """
        pub_dict["type"] = type
        pub_dict["inLanguage"] = inLanguage

    @classmethod
    def add_w3c(cls, pub_dict):
        """            "@context": [
              "https://schema.org",
              "https://www.w3.org/ns/pub-context"
            ],
            "conformsTo": "https://www.w3.org/TR/pub-manifest/",
        """
        pub_dict["@context"] = [
            "https://schema.org",
            "https://www.w3.org/ns/pub-context"
        ]
        pub_dict["conformsTo"] = "https://www.w3.org/TR/pub-manifest/"

    @classmethod
    def add_resource(cls, resource_list, resource):
        """
            {
            "type": [
                "LinkedResource"
            ],
            "url": "css/appaloosa.css"
        },

        """
        resource_dict = dict()
        resource_dict["type"] = ["LinkedResource"]
        resource_dict["url"] = resource
        resource_list.append(resource_dict)

    @classmethod
    def create_session_manifest_json(cls, decision_dirs, lead_dirs=None, title="no title", get_title=None, out_dir=None,
                                     html_inname="final.html", outname="publication.json", debug=False):
        """{
            "@context": [
              "https://schema.org",
              "https://www.w3.org/ns/pub-context"
            ],
            "conformsTo": "https://www.w3.org/TR/pub-manifest/",
            "type": "Book",
            "name": "Report of the Conference of the Parties serving as the meeting of the Parties to the Paris Agreement on its third session, held in Glasgow from 31 October to 13 November 2021",
            "author": "United Nations Framework Convention on Climate Change (UNFCCC)",
            "inLanguage": "en",
            "readingOrder": [
              {
                "url": "LEAD/split.html",
                "rel": "contents"
              },
              "Decision_1_CMA_3/split.html",
              "Decision_2_CMA_3/split.html",
              "Decision_3_CMA_3/split.html",
              "Decision_4_CMA_3/split.html"
            ],
            "resources": [
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
          }"""

        pub_dict = dict()
        cls.add_w3c(pub_dict)
        cls.add_general(pub_dict)
        cls.add_biblio_meta(pub_dict, name="Report of the Conference of the Parties...", author="UNFCCC")
        cls.add_reading_order(pub_dict, decision_dirs)

        cls.add_resources(pub_dict)
        if out_dir and outname:
            path = str(Path(out_dir, outname))
            with open(path, "w") as f:
                json.dump(path, f, indent=4)
            if debug:
                print(f"wrote manifest {path}")

        return pub_dict

    @classmethod
    def add_resources(cls, pub_dict):
        APPALOOSA = "css/appaloosa.css"
        MATHLIVE = "css/mathlive.css"
        BOOK = "css/book.css"
        resource_list = []
        pub_dict["resources"] = resource_list
        for resource in [
            APPALOOSA,
            MATHLIVE,
            BOOK,
        ]:
            cls.add_resource(resource_list, resource)

    @classmethod
    def add_reading_order(cls, pub_dict, decision_dirs):
        """
        "readingOrder": [
              {
                "url": "LEAD/split.html",
                "rel": "contents"
              },
              "Decision_1_CMA_3/split.html",
              "Decision_2_CMA_3/split.html",
              "Decision_3_CMA_3/split.html",
              "Decision_4_CMA_3/split.html"
            ],

        """
        readings = []
        pub_dict["readingOrder"] = readings
        lead_dict = dict()
        lead_dict["url"] = "LEAD"
        lead_dict["rel"] = "contents"
        readings.append(lead_dict)
        for decision_dir in decision_dirs:
            readings.append(str(Path(decision_dir.stem, f"{Vivlio.FINAL}.html")))


class Vivlio:
    """to display VIVLIO
    https://vivliostyle.vercel.app/#src=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/publication.json&style=https://raw.githubusercontent.com/semanticClimate/cma3-test/main/CMA_3/css/appaloosa-rq.css
    """
    VIVLIO_APP = "https://vivliostyle.vercel.app"
    FINAL = "final"

    V_BACK = {
        "filename": "back_ccver.html",
        "content": f"""
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

    # resources = [
    #   {
    #     "type": "LinkedResource",
    #     "url": "toc_toplevel_sum_ses.html",
    #     "rel": "contents"
    #   },
    #     {
    #         "type": [
    #             "LinkedResource"
    #         ],
    #         "url": "css/appaloosa.css"
    #     },
    #     {
    #       "type": [
    #           "LinkedResource"
    #       ],
    #       "url": "css/mathlive.css"
    #   },
    #     {
    #         "type": [
    #             "LinkedResource"
    #         ],
    #         "url": "css/book.css"
    #     }
    #   ]

    @classmethod
    def create_vivlio_url(cls, css, json):
        display_str = f"{Vivlio.VIVLIO_APP}/#src={json}&style={css}"
        return display_str

    """{
        "@context": [
          "https://schema.org",
          "https://www.w3.org/ns/pub-context"
        ],
        "conformsTo": "https://www.w3.org/TR/pub-manifest/",
        "type": "Book",
        "name": "Report of the Conference of the Parties serving as the meeting of the Parties to the Paris Agreement on its third session, held in Glasgow from 31 October to 13 November 2021",
        "author": "United Nations Framework Convention on Climate Change (UNFCCC)",
        "inLanguage": "en",
        "readingOrder": [ 
          {
            "url": "LEAD/split.html",
            "rel": "contents"
          },
          "Decision_1_CMA_3/split.html",
          "Decision_2_CMA_3/split.html",
          "Decision_3_CMA_3/split.html",
          "Decision_4_CMA_3/split.html"
        ],
        "resources": [
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
      }
    """

    @classmethod
    def create_toc_html(cls, decision_dirs, lead_dirs=None, title="no title", get_title=None, out_dir=None,
                        html_inname="final.html", outname="toc.html", debug=False):
        '''
<nav id="toc-sessions" role="doc-toc">
  <ul>
    <li><div class="title"><a href="LEAD/">CMA 3: FCCC/PA/CMA/2021/10/Add.1</a></div><div class="description">Report of the Conference of the Parties serving as the meeting of the Parties to the Paris Agreement on its third session, held in Glasgow from 31 October to 13 November 2021</div></li>
    <ul>
     <li><div class="title"><a href="Decision_1_CMA_3/split.html">Decision 1/CMA.3</a></div>
      <div class="description">Glasgow Climate Pact</div></li>
'''
        FINAL = "final"
        html_elem = HtmlLib.create_html_with_empty_head_body()
        body_elem = HtmlLib.get_body(html_elem)

        nav_elem = lxml.etree.SubElement(body_elem, "nav")
        nav_elem.attrib["id"] = "toc-sessions"
        nav_elem.attrib["role"] = "doc-top"

        """    
        <ul>
            <li>
              <div class="title"><a href="LEAD/">CMA 3: FCCC/PA/CMA/2021/10/Add.1</a></div>
              <div class="description">Report of the Conference of the Parti...rom 31 October to 13 November 2021</div>
            </li>"""
        lead_ul_elem = lxml.etree.SubElement(nav_elem, "ul")
        lead_li_elem = lxml.etree.SubElement(lead_ul_elem, "li")

        lead_title_div_elem = lxml.etree.SubElement(lead_li_elem, "div")
        lead_title_div_elem.attrib["class"] = "title"
        lead_title_a_elem = lxml.etree.SubElement(lead_title_div_elem, "a")
        if lead_dirs:
            lead_title_a_elem.attrib["href"] = str(Path(lead_dirs[0], f"{FINAL}.html"))
        lead_title_a_elem.text = f"{title}"

        lead_desc_div_elem = lxml.etree.SubElement(lead_li_elem, "div")
        lead_desc_div_elem.attrib["class"] = "description"
        lead_html = HtmlLib.parse_html(Path(lead_dirs[0], f"{FINAL}.html")) if lead_dirs else None
        lead_desc_div_elem.text = "no lead" if lead_html is None else get_title(lead_html)

        for decision_dir in decision_dirs:
            ul_elem = lxml.etree.SubElement(lead_li_elem, "ul")
            decision_html = HtmlLib.parse_html(Path(decision_dir, html_inname))
            title = "dummy" if get_title is None else get_title(decision_html)
            li_elem = lxml.etree.SubElement(ul_elem, "li")
            p_elem = lxml.etree.SubElement(li_elem, "p")
            a_elem = lxml.etree.SubElement(p_elem, "a")
            a_elem.text = f"{title}"
            br_elem = lxml.etree.SubElement(p_elem, "br")
            a_elem = lxml.etree.SubElement(p_elem, "a")
            a_elem.text = f"{decision_dir.stem}"
            # strip local dir
            href_str = str(Path(decision_dir.stem, html_inname))
            a_elem.attrib["href"] = href_str
            # print(f"href: {href_str}")
            if debug:
                print(f"{decision_dir.stem}: {title}")
        if out_dir and outname:
            path = Path(out_dir, outname)
            HtmlLib.write_html_file(html_elem, path, debug=debug)
        return html_elem
