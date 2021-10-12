# backend.ai Documentation

Build guide for Backend.AI Documentation

## Setup build environment

> 📌 NOTE: You may need a sudo access for a certain command.

### clone docs in `lablup/backend.ai` project
Download `lablup/backend.ai` project using `git clone` and rename it as `meta`.

```console
$ cd ~
$ git clone https://github.com/lablup/backend.ai meta
```
Change current working directory to `docs` directory in meta directory, which you downloaded just now.

```console
$ cd ~/meta/docs
```

### pyenv and pyenv-virtualenv installation

#### MacOS version

Install [pyenv](https://github.com/pyenv/pyenv) using brew.

```console
$ brew install pyenv
```

Set `PYENV_ROOT`, add `pyenv` to `PATH` and execute shell run command file (`.zshrc` or `.bashrc` or etc.).   
For now, we will use `.zshrc` as an example.

```console
$ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
$ echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
$ eval '"(pyenv init --path)"' >> ~/.zshrc
$ source ~/.zshrc
```

Install [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) using brew.   
This is the actual command to create the environment using pyenv.

```console
$ brew install pyenv-virtualenv
```

Add `pyenv-virtualenv` to `PATH` and execute shell run command file (`.zshrc` or `.bashrc` or etc.).

```console
$ eval "$(pyenv virtualenv-init -)"
```

#### Linux (Ubuntu) version

Install [pyenv](https://github.com/pyenv/pyenv) using `git clone`.   

```console
$ git clone https://github.com/pyenv/pyenv.git ~/.pyenv
```

SET `PYENV_ROOT`, add `pyenv` to `PATH` and add `pyenv-virtualenv` to `PATH`.
Execute shell run command file (`.zshrc` or `.bashrc` or etc.).

```console
$ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
$ echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
$ echo -e 'if command -v pyenv 1>/dev/null 2>&1; then\n eval "$(pyenv init --path)"\nfi' >> ~/.bashrc
$ source ~/.bashrc
```

Restart the shell to enable pyenv

```console
$ exec $SHELL
```

Install [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) using `git clone`.   

```console
$ git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv
```

Add `pyenv virtualenv-init` to `$SHELL` to enable auto-activate of virtualenvs.

```console
$ echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
```

Restart the shell to enable pyenv-virtualenv

```console
$ exec $SHELL
```

### install certain version of pyenv

There's no specific restriction about the version of python3 for building documentation of Backend.AI, but
we recommend you to install the version higher than Python 3.8.

> e.g. Install pyenv version: `3.9.6`

```console
$ pyenv install 3.9.6
```

### 

### pyenv activate

> 📌 NOTE: You need to create pyenv first, and then activate/deactivate it.

Create a pyenv with version and a genuine name.
For now, we can use `bai-doc`.

```console
$ pyenv virtualenv 3.9.6 bai-doc
```

Add current directory to automatically activate pyenv.

```console
$ cd ~/meta/docs
$ pyenv local bai-doc
```

### sphinx installation

Install [sphinx](https://www.sphinx-doc.org/en/master/) using [pip](https://pypi.org/project/pip/)

```console
$ pip install sphinx
```

### sphinx-intl installation

Install [sphinx-intl](https://github.com/sphinx-doc/sphinx-intl) using pip.

```console
$ pip install sphinx-intl
```ß

## Build documents
> 📌 NOTE: Please make sure pyenv installation completed and the activation has been enabled before building documents, and current working directory need to be root directory of `docs`.

### Make Default html files
```console
$ make html
```
### Translation

#### Make pot(Portable Object Template) files
```console
$ make gettext
```

#### Make po(Portable Object) files using sphinx-intl
> For now, we use Korean language as an example for translation.

```console
$ sphinx-intl update -p _build/locale/ -l ko_KR
```

#### Make html files with translated version

```console
$ make -e SPHINXOPTS="-D language='ko'" html
```

## 🚧 Build PDF document (WIP) 🚧
 Help wanted!   
Looking for people to help with a short guide for building PDF document based on html files derived from sphinx.

## Advanced Setting

### Managing the hierachy of toctree(Table of Contents) of documentation

When documentation of each file gets too big to contain all things in one topic,   
It should be branched with proper sub-topics.   
The hierarchy of toctree has been managed through `index.rst`.   
Please note that contents in `index.rst` must contain the actual directory tree, unless it will not contain documentation you expected.   

For More Information, Please check out [`index.rst`](https://github.com/lablup/backend.ai/blob/main/docs/index.rst) file.


## References for newcomers

http://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html

