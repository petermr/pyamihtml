# Vivliostyle CLI

Vivliostyle CLI is a command line interface for typesetting HTML or Markdown documents.

## Install

You need to install [Node.js](https://nodejs.org/ja/) (v16 or higher) prior to using it.

You can install the Vivliostyle CLI with the following command:

```
npm install -g @vivliostyle/cli
```

## Generate PDF from HTML

When an HTML file is specified with the `vivliostyle build` command, a PDF file will be output as a result of typesetting from the HTML.

```
vivliostyle build index.html
```

The default output PDF file name is "output.pdf".

### Specify the output PDF file

The `-o` (`--output`) option can be used to specify a PDF file name.

```
vivliostyle build book.html -o book.pdf
```

### To view the results without outputting PDF

To view the typesetting results without outputting a PDF, see [Preview the typesetting results](#preview-the-typesetting-results).

### Specify a Web URL

In addition to a local HTML file, you can also specify a Web URL.

```
vivliostyle build https://vivliostyle.github.io/vivliostyle_doc/samples/gutenberg/Alice.html -s A4 -o Alice.pdf
```

### Specifying single HTML document

The default behavior of Vivliostyle CLI is to typeset multi-document publication (webbook or webpub) if the HTML document specified on the command line contains a table of contents with links to other HTML documents, or if it contains links to a publication manifest. The `-d` (`--single-doc`) option changes this behavior so that only a single HTML document can be typeset.

```
vivliostyle build index.html --single-doc
```

## Specifying additional style sheets

To use a style sheet (CSS file) in addition to the style sheets specified in the HTML file, specify the additional style sheet with `--style` option.

```
vivliostyle build example.html --style additional-style.css
```

The style sheet specified in this way is treated as [author style sheet](https://developer.mozilla.org/en-US/docs/Web/CSS/Cascade#author_stylesheets), as if it is specified in the HTML file at very last, and can override styles of other style sheets according to the CSS cascading rules.

### Specifying user style sheets

To use a [user style sheet](https://developer.mozilla.org/en-US/docs/Web/CSS/Cascade#user_stylesheets), specify the style sheet with `--user-style` option. (User style sheet cannot
override styles of author style sheets unless specifying `!important`).

```
vivliostyle build example.html --user-style user-style.css
```

### Specify CSS content directly

The `--css` option allows you to pass the style sheets you wish to add as CSS text directly. This option is useful for setting simple style sheets or CSS variables.

```
vivliostyle build example.html --css "body { background-color: lime; }"
```

### Specify the page size

The `-s` (`--size`) option can be used to specify the page size. The possible sizes are A5, A4, A3, B5, B4, JIS-B5, JIS-B4, letter, legal, ledger, or comma-separated width and height.

```
vivliostyle build paper.html -s A4 -o paper.pdf
vivliostyle build letter.html -s letter -o letter.pdf
vivliostyle build slide.html -s 10in,7.5in -o slide.pdf
```

This option is equivalent to `--css "@page { size: <size>; }"`.

### Setting crop marks

The `-m` (`--crop-marks`) option will add crop marks (markers that indicate where to cut the printed material) to the output PDF.

```
vivliostyle build example.html -m
```

The `--bleed` option can be used to specify the width of the fill when trim marks are added. You can also use the `--crop-offset` option to specify the width outside the bleed line.

```
vivliostyle build example.html -m --bleed 5mm
vivliostyle build example.html -m --crop-offset 20mm
```

This option is equivalent to `--css "@page { marks: crop cross; bleed: <bleed>; crop-offset: <crop-offset>; }"`.

## Generate PDF from EPUB

When an EPUB file is specified with the `vivliostyle build` command, a PDF file will be output as a result of typesetting from the EPUB.

```
vivliostyle build epub-sample.epub -s A5 --user-style epub-style.css -o epub-sample.pdf
```

### Example of user style sheet for EPUB

To typeset EPUB with your preferred page style, you need to [specify a user style sheet](#specifying-user-style-sheets).

Example of user style sheet for EPUB: epub-style.css
```css
@page {
  margin: 10%;
  @top-center {     /* page header */
    writing-mode: horizontal-tb;
    font-size: 75%;
    content: string(title);
  }
  @bottom-center {  /* page footer */
    writing-mode: horizontal-tb;
    font-size: 67%;
    content: counter(page);
  }
}
@page :first {      /* cover page */
  margin: 0;
  @top-center {
    content: none;
  }
  @bottom-center {
    content: none;
  }
}
title {
  string-set: title content();
}
img { /* to fit images in the page */
  max-width: 100vw !important;
  max-height: 100vh !important;
}
```

### Generate PDF from unzipped EPUB

To generate a PDF from an unzipped EPUB, specify the EPUB's OPF file.

```
unzip epub-sample.epub
vivliostyle build item/standard.opf -s A5 --user-style epub-style.css -o epub-sample.pdf
```

## Generate PDF from Markdown

When a Markdown file is specified with the `vivliostyle build` command, a PDF file will be output as a result of typesetting from the Markdown.

```
vivliostyle build manuscript.md -s A4 -o paper.pdf
```

### About the VFM (Vivliostyle Flavored Markdown)

For more information on the Markdown notation available in Vivliostyle CLI, refer to [VFM: Vivliostyle Flavored Markdown](https://vivliostyle.github.io/vfm/#/).

### Specify a theme CSS style sheet

The `-T` (`--theme`) option can be used to specify a CSS file.

```
vivliostyle build manuscript.md --theme my-theme/style.css -o paper.pdf
```

If you cannot prepare your own CSS files, Vivliostyle Themes makes it easy to apply styles. See [About Vivliostyle Themes](#about-vivliostyle-themes) for more information about theme files.

```
vivliostyle build manuscript.md --theme @vivliostyle/theme-techbook -o paper.pdf
```

## Preview the typesetting results

The `vivliostyle preview` command can be used to preview the typesetting results in the browser with [Vivliostyle Viewer](./vivliostyle-viewer.md).

```
vivliostyle preview index.html
vivliostyle preview https://example.com --user-style my-style.css
vivliostyle preview publication.json
vivliostyle preview epub-sample.epub --user-style my-style.css
vivliostyle preview manuscript.md --theme my-theme/style.css
```

### Quick preview for large multi-document publications

To preview quickly a large publication consisting of multiple HTML documents, specify `-q` (`--quick`) option for quick loading using rough page count (page numbers will not be output correctly).

```
vivliostyle preview index.html --quick
vivliostyle preview publication.json --quick
vivliostyle preview epub-sample.epub --quick
```

## About Vivliostyle Themes

- [Vivliostyle Themes](https://vivliostyle.github.io/themes/)

### Find themes

To find the themes published as npm packages, search for the keyword "vivliostyle-theme" in [npm](https://www.npmjs.com/):

- [List of Themes (npm)](https://www.npmjs.com/search?q=keywords%3Avivliostyle-theme)

### Using a theme

The theme is available with the `--theme` option or by specifying `theme` in the configuration file. If the Theme file does not exist locally, it will be installed automatically on the first run.

### Using the Create Book

Create Book makes it easy to create a project with a preset Theme. See [Create Book](create-book).

## Configuration file vivliostyle.config.js

To combine multiple article or chapter files into a single publication, use the configuration file. When running the `vivliostyle build` or `vivliostyle preview` command, the configuration file `vivliostyle.config.js` will be used if it exists in the current directory.

### Create configuration file

You can create a configuration file `vivliostyle.config.js` with the following command:

```
vivliostyle init
```

This will create `vivliostyle.config.js` in the current directory. The configuration file is written in JavaScript, and various settings can be changed by editing it.

### Configuration settings

The configuration settings are explained in the comments (beginning with `//`) in the configuration file.

- **title**: Publication title. Example: `title: 'Principia'`.
- **author**: Author name. Example: `author: 'Isaac Newton'`.
- **language**: Language. Example: `language: 'en'`. If this is specified, it will be reflected in the `lang` attribute of the HTML.
- **size**: Page size. Example: `size: 'A4'`.
- **theme**: Specify a CSS file. Example: `theme: 'style.css'`, or specify a [Vivliostyle Themes](https://vivliostyle.github.io/themes/) package name. Example: `theme: '@vivliostyle/theme-techbook'`.
- **entry**: Specify an array of input Markdown or HTML files.
    ```js
    entry: [
      {
        path: 'about.md',
        title: 'About This Book',
        theme: 'about.css'
      },
      'chapter1.md',
      'chapter2.md',
      'glossary.html'
    ],
    ```
    The entry can be specified as a string or as an object. In the case of object format, the following members can be added:
    - `path`: Specifies the path of the entry. This member is required, but it becomes optional only when `rel: 'contents'` is specified.　For more information on this specification, see [To output the table of contents to a location other than the top of the publication](#to-output-the-table-of-contents-to-a-location-other-than-the-top-of-the-publication).
    - `title`: Specify the title of the entry.
    - `theme`: Specify the CSS file or [Vivliostyle Themes](https://vivliostyle.github.io/themes/) package name to be applied to the entry.
    - `encodingFormat`: Specifies the format of the entry in MIME media type format. If not specified, it is automatically inferred from the file content.
    - `rel`: Specify the property that represents the relationship between the entries. See https://www.w3.org/TR/wpub/#manifest-rel for information on what to set.

- **output**: Output path(s). Example: `output: 'output.pdf'`. The default is `{title}.pdf`. It is also possible to specify multiple outputs as follows:
    ```js
    output: [
      './output.pdf',
      {
        path: './book',
        format: 'webpub',
      },
    ],
    ```
    The output can be specified as a string or an object. In the case of object, the following members can be added:
    - `path`: Specifies the path to the output destination. This member is required.
    - `format`: Specifies the output format (available options: `'pdf'`, `'webpub'`) For the detail of `webpub` output, see [Web Publications (webpub)](#web-publications-webpub).
    - `renderMode`: (Only for `format: 'pdf'`) Specifies the environment in which the output will be generated (available options: `'local'`, `'docker'`) For the detail of generation on Docker, see [Generate using Docker](#generate-using-docker).
    - `preflight`: (Only for `format: 'pdf'`) Specify post-processing for the output PDF (possible options: `'press-ready'`, `'press-ready-local'`) For generating a print-ready PDF using press-ready see [Generate PDF for print (PDF/X-1a format)](#generate-pdf-for-print-pdfx-1a-format).
    - `preflightOption`: (Only for `format: 'pdf'`) Specify the features during PDF post-processing in the form of an array of strings.

- **workspaceDir**: Specify the directory where intermediate files are saved. If this is not specified, the default is the current directory, and the HTML files converted from Markdown will be stored in the same location as the Markdown files. Example: `workspaceDir: '.vivliostyle'`.
- **toc**: If `toc: true` is specified, the HTML file `index.html` containing the table of contents will be output. See [Creating a Table of Contents](#creating-a-table-of-contents) for details.
- **tocTitle**: Specify the title of the automatically generated table of contents file.
- **readingProgression**: Specifies the reading direction of the document (available options: `'ltr'`, `'rtl'`), usually automatically guessed by the CSS horizontal/vertical writing specification (writing-mode), so use only if you want to specify it explicitly.
- **timeout**: Change the time limit (timeout) before the build completes (in milliseconds)
- **vfm**: Specifies transformation options for VFM.
- **image**: Change the Docker image to be used.
- **http**: Start Vivliostyle Viewer in HTTP server mode. This is useful when an external resource requests CORS.
- **viewer**: Change the URL of the Viviliostyle Viewer you want to use. This is useful if you want to use your own Viewer.

Multiple of the above configuration file options can be specified as an array. When set up as an array, it is convenient to handle multiple inputs and outputs at once.
The following example is a configuration file that converts a Markdown file in the `src` directory to a PDF file of the same name.

```js
const fs = require('fs');
const path = require('path');

const inputDir = path.join(__dirname, 'src');
const outputDir = path.join(__dirname, 'output');
const files = fs.readdirSync(inputDir);

const vivliostyleConfig = files
  .filter((name) => name.endsWith('.md'))
  .map((name) => ({
    title: `Article ${path.basename(name, '.md')}`,
    entry: name,
    entryContext: inputDir,
    output: path.join(outputDir, `${path.basename(name, '.md')}.pdf`),
  }));
module.exports = vivliostyleConfig;
```

## Generate PDF for print (PDF/X-1a format)

You can use `vivliostyle build` command with the `--preflight press-ready` option to output in PDF/X-1a format suitable for printing. To use this feature, you need [Docker](https://docs.docker.com/get-docker/) installed.

`--preflight-option` allows additional options for [press-ready](https://github.com/vibranthq/press-ready) to perform this operation.

```
# Grayscale output
vivliostyle build manuscript.md --preflight press-ready --preflight-option gray-scale
# Forces outlined fonts
vivliostyle build manuscript.md --preflight press-ready --preflight-option enforce-outline
```

The option `--preflight press-ready-local` will execute output to PDF/X-1a format in a local environment. However, we usually recommended to run it on a Docker environment.

## Generate using Docker

You can use `vivliostyle build` command with the `--render-mode docker` option to specify Docker as the environment for PDF output (only post-processing is performed on Docker with the above option, this option performs all processing on Docker). Docker can be used to fix the output environment, so you can be sure that the output will be the same on different environments and operating systems.

When using Docker render mode, please note the following:

* Since Docker is isolated from the host environment, it cannot use the fonts installed on the host. There are only a limited number of fonts that can be used as standard in Docker containers, and you usually need to place local font files and specify them with CSS, or use web fonts such as Google font.
* The only file that will be mounted in Docker is _the project workspace directory_ (usually the directory containing vivliostyle.config.js), other files cannot be referenced from inside the Docker container. All files that are referenced in the document, such as images, should be included in the workspace directory.

## Generate PDF Bookmarks

The PDF output from the `vivliostyle build` command will have a table of contents as PDF Bookmarks, which can be used for navigation in PDF viewing software such as Adobe Acrobat.

Bookmark generation is enabled when the publication contains a table of contents. In the case of [Generate PDF from EPUB](#generate-pdf-from-epub), the table of contents in the EPUB will be used. For other cases, see [Creating a Table of Contents](#creating-a-table-of-contents) below.

## Creating a Table of Contents

### Specifying table of contents generation in configuration file

If `toc: true` is specified in the configuration file `vivliostyle.config.js`, a table of contents HTML file `index.html` will be generated and it will be the first file in the publication.

To specify the file name of the table of contents HTML, specify it with `toc:`. Example: `toc: 'toc.html'`

The generated table of contents HTML file will look like the following:

```html
<html>
  <head>
    <title>Book Title</title>
    <link href="publication.json" rel="publication" />
    <link href="style.css" rel="stylesheet" />
  </head>
  <body>
    <h1>Book Title</h1>
    <nav id="toc" role="doc-toc">
      <h2>Table of Contents</h2>
      <ol>
        <li><a href="prologue.html">Prologue</a></li>
        <li><a href="chapter1.html">Chapter 1</a></li>
        <li><a href="chapter2.html">Chapter 2</a></li>
        <li><a href="chapter3.html">Chapter 3</a></li>
        <li><a href="epilogue.html">Epilogue</a></li>
      </ol>
    </nav>
  </body>
</html>
```

### Specifying the title of the table of contents

- The `title` and `h1` elements of the Table of Contents will have the publication title (specified with `title` in the configuration file).
- The title of the table of contents (the content of the heading `h2` element in the `nav` element, "Table of Contents") can be specified with `tocTitle` in the configuration file. Example: `tocTitle: 'Contents'`.

### To output the table of contents to a location other than the top of the publication

If you specify `{ rel: 'contents' }` as an element of the `entry` array in the configuration file `vivliostyle.config.js`, the table of contents HTML file will be generated at that position.

```js
  entry: [
    'titlepage.md',
    { rel: 'contents' },
    'chapter1.md',
    ...
  ],
  toc: 'toc.html',
```

This way, the first HTML file in the publication will be `titlepage.html`, followed by the table of contents HTML file `toc.html`.

### Creating table of contents yourself

To create a table of contents yourself, specify the path to the table of contents file with `rel: 'contents'` in the the `entry` array in the configuration file, as follows:

```js
  entry: [
    'titlepage.md',
    {
      path: 'toc.html',
      rel: 'contents'
    },
    'chapter1.md',
    ...
  ],
```

For information on table of contents structure, please refer to the appendix [Machine-Processable Table of Contents](https://www.w3.org/TR/pub-manifest/#app-toc-structure) of [W3C Publication Manifest](https://www.w3.org/TR/pub-manifest/).

## Web Publications (webpub)

The `vivliostyle build` command with the `-f` (`--format`) option with `webpub` will generate a web publication (webpub). The output destination `-o` (`--output`) option specifies the directory where the webpub will be placed.

(In the example below, we assume that the input Markdown and HTML files are specified in the configuration file `vivliostyle.config.js`.

```
vivliostyle build -o webpub/ -f webpub
```

In the generated webpub directory, there is a publication manifest file, `publication.json`, which contains information about the order in which the content HTML files are loaded. It conforms to the W3C standard specification [Publication Manifest](https://www.w3.org/TR/pub-manifest/).

The webpub can be used to create publications that can be read on the web. You can also generate a PDF from webpub by specifying the `publication.json` file to the `vivliostyle build` command as follows:

```
vivliostyle build webpub/publication.json -o pdfbook.pdf
```

It is also possible to generate both webpub and PDF with a single `vivliostyle build` command, as follows:

```
vivliostyle build -o webpub/ -f webpub -o pdfbook.pdf -f pdf
```

## Other options

You can use the `vivliostyle help` command to display the list of options available in Vivliostyle CLI.

```
vivliostyle help
vivliostyle help init
vivliostyle help build
vivliostyle help preview
```

See also:
- [Vivliostyle CLI (README)](https://github.com/vivliostyle/vivliostyle-cli/blob/main/README.md#readme)
