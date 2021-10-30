# backend.ai Documentation

Build guide for Backend.AI Documentation


## Setting up the build environment for docs

> 📌 NOTE: You may need a sudo access for a certain command.

### clone docs in `lablup/backend.ai` project
Download `lablup/backend.ai` project using `git clone` and rename the clone directory as `meta`.

```console
$ cd ~
$ git clone https://github.com/lablup/backend.ai meta
```
Change the current working directory to `meta/docs`.

```console
$ cd ~/meta/docs
```

### pyenv and pyenv-virtualenv installation

#### pyenv installation
Please refer to the [README](https://github.com/pyenv/pyenv#installation) of the official [pyenv](https://github.com/pyenv/pyenv) repository and install it.

#### pyenv-virtualenv installation (optional)
`pyenv-virtualenv` is a `pyenv` plugin.  It is not mandatory to build the Backend.AI docs but highly recommended.   
To install it, please refer to the [README](https://github.com/pyenv/pyenv-virtualenv#installation) of the official [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) repository.

### Sphinx installation

Install [sphinx](https://www.sphinx-doc.org/en/master/) using [pip](https://pypi.org/project/pip/)

```console
$ pip install sphinx
```

### sphinx-intl installation

Install [sphinx-intl](https://github.com/sphinx-doc/sphinx-intl) using pip.

```console
$ pip install sphinx-intl
```


## Building HTML document

> 📌 NOTE: Please make sure pyenv installation completed and the activation has been enabled before building documents, and current working directory need to be root directory of `docs`.

### Make the html version
```console
$ make html
```
### Translation

#### Generate/update pot (Portable Object Template) files
```console
$ make gettext
```

#### Build po (Portable Object) files using sphinx-intl

> In this guide, we use Korean as the target translation language.

```console
$ sphinx-intl update -p _build/locale/ -l ko_KR
```

#### Build HTML files with translated version

```console
$ make -e SPHINXOPTS="-D language='ko'" html
```

## 🚧 Building PDF document (WIP) 🚧

> Help wanted!   

We are looking for people to help with a short guide for building PDF document based on html files derived from sphinx.


## Advanced Settings

### Managing the hierachy of toctree(Table of Contents) of documentation

When documentation of each file gets too big to contain all things in one topic,   
It should be branched with proper sub-topics.   
The hierarchy of toctree has been managed through `index.rst`.   
Please note that contents in `index.rst` must contain the actual directory tree, unless it will not contain documentation you expected.   

For More Information, Please check out [`index.rst`](https://github.com/lablup/backend.ai/blob/main/docs/index.rst) file.


## References for newcomers

http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html

