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
$ pyenv virtualenv 3.10.8 venv-bai-docs
$ git clone https://github.com/lablup/backend.ai backend.ai
$ cd ~/backend.ai/docs
$ pyenv local venv-bai-docs
$ pip install -U pip setuptools wheel
$ pip install -U -r requirements.txt   # docs/requirements.txt
```

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


## 🚧 Building PDF document (WIP) 🚧

> Help wanted!

We are looking for people to help with a short guide for building PDF document based on html files derived from sphinx.


## Advanced Settings

### Managing the hierachy of toctree (Table of Contents) of documentation

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


## References for newcomers

- http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
- https://poedit.net/
