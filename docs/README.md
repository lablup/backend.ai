# Backend.AI Documentation

Developer guide for Backend.AI documentation


## Setting up the build environment for docs

### Installing pyenv and pyenv-virtualenv

* Please refer the official docs:
  - https://github.com/pyenv/pyenv#installation
  - https://github.com/pyenv/pyenv-virtualenv#installation

### Setting up the documenting environment

Then, follow the instructions below:

```console
$ pyenv virtualenv $(pyenv latest 3.11) bai-docs
$ git clone https://github.com/lablup/backend.ai bai-dev
$ cd ./bai-dev/docs
$ pyenv local bai-docs
$ pip install -U pip setuptools wheel
$ pip install -U \
    --find-links=https://dist.backend.ai/pypi/simple/grpcio \
    --find-links=https://dist.backend.ai/pypi/simple/grpcio-tools \
    --find-links=https://dist.backend.ai/pypi/simple/hiredis \
    --find-links=https://dist.backend.ai/pypi/simple/psycopg-binary \
    -r requirements.txt
```

## Building API Reference JSON file
```console
$ ./py -m ai.backend.manager.openapi docs/manager/rest-reference/openapi.json
```
This script must be executed on behalf of the virtual environment managed by pants, not by the venv for the sphinx.
Generated OpenAPI JSON file will be located at under `manager/rest-reference/openapi.json`.

## Building HTML document

> 📌 NOTE: Please ensure that you are inside the `docs` directory and the virtualenv is activated.

### Make the html version

```console
$ make html
```

The compiled documentation is under `_build/html/index.html`.
You may serve it for local inspection using `python -m http.server --directory _build/html`.

## Translation

#### Generate/update pot (Portable Object Template) files

```console
$ make gettext
```

#### Build po (Portable Object) files using sphinx-intl

```console
$ sphinx-intl update -p _build/locale/ -l ko
```

The `.po` message files are under `locales/ko/LC_MESSAGES/`.
Edit them by filling missing translations.

#### Build HTML files with translated version

```console
$ sphinx-intl build
$ make -e SPHINXOPTS="-D language='ko'" html
```


## Building PDF document

```console
$ make latexpdf
```

The compiled documentation is under `_build/latex/BackendAIDoc.pdf`.

Building PDF requires following libraries to be present on your system.

* TeX Live 
  - ko.TeX (texlive-lang-korean)
  - latexmk
* ImageMagick
* Font files (All required font files must be installed)

### Installing dependencies on macOS
1. Install MacTeX from [here](https://www.tug.org/mactex/). There are two types of MacTeX distributions; The BasicTeX one is more lightweight and MacTeX contains most of the libraries commonly used.
2. Follow [here](http://wiki.ktug.org/wiki/wiki.php/KtugPrivateRepository) (Korean) to set up KTUG repository.
3. Exceute following command to install missing dependencies.   
```console
sudo tlmgr install latexmk tex-gyre fncychap wrapfig capt-of framed needspace collection-langkorean collection-fontsrecommended tabulary varwidth titlesec
```
4. Install both Pretendard (used for main font) and D2Coding (used to draw monospace characters) fonts on your system.

## Advanced Settings

### Managing the hierarchy of toctree (Table of Contents) of documentation

When documentation of each file gets too big to contain all things in one topic,
It should be branched with proper sub-topics.
The hierarchy of toctree has been managed through `index.rst`.
Please note that contents in `index.rst` must contain the actual directory tree, unless it will not contain documentation you expected.

For More Information, Please check out [`index.rst`](https://github.com/lablup/backend.ai/blob/main/docs/index.rst) file.

### Adding a new language translation

Add a new project in readthedocs.org with the "-xx" suffix
where "xx" is an ISO 639-1 language code, which targets
the same GitHub address to the original project.

Then configure the main project in readthedocs.org to have
the new project as a specific language translation.

Example:

* https://readthedocs.org/projects/sorna
* https://readthedocs.org/projects/sorna-ko

Please ask the docs maintainer for help.

### Previewing built HTML documentation
Simply create a nginx server which serves `_build/html` folder. For example (docker required): 
```bash
docker run --rm -it -v $(pwd)/_build/html:/usr/share/nginx/html -p 8000:80 nginx
```
Executing the command above inside `docs` folder will serve the documentation page on port 8000 (http://localhost:8000).

## References for newcomers

- http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
- https://poedit.net/
