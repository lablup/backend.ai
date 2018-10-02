We highly recommend [pyenv](https://github.com/pyenv/pyenv) to install multiple Python versions side-by-side,
which does not interfere with system-default Pythons.

[![asciicast](https://asciinema.org/a/ow9AdNDqjGnkN5ky2dyxMaQmQ.png)](https://asciinema.org/a/ow9AdNDqjGnkN5ky2dyxMaQmQ)

## Install dependencies for building Python

### Ubuntu

```console
$ sudo apt-get update -y
$ sudo apt-get dist-upgrade -y
$ sudo apt-get install -y \
> build-essential git-core \                                     # for generic C/C++ builds
> libreadline-dev libsqlite3-dev libssl-dev libbz2-dev tk-dev \  # for Python builds
> libzmq3-dev libsnappy-dev                                      # for Backend.AI dependency builds
```

### CentOS / RHEL

(TODO)

## Install pyenv

**NOTE:** Change `~/.profile` accroding to your shell/system (e.g., `~/.bashrc`, `~/.bash_profile`, `~/.zshrc`, ...) -- whichever loaded at startup of your shell! 

```console
$ git clone https://github.com/pyenv/pyenv.git ~/.pyenv
...
$ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
$ echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
$ echo 'eval "$(pyenv init -)"' >> ~/.profile
$ exec $SHELL -l
$ pyenv  # check installation
pyenv 1.2.0-6-g9619e6b
Usage: pyenv <command> [<args>]

Some useful pyenv commands are:
   ...
```

## Install pyenv's virtualenv plugin

```console
$ git clone https://github.com/pyenv/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
...
$ echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.profile
$ exec $SHELL -l
$ pyenv virtualenv  # check installation
pyenv-virtualenv: no virtualenv name given.
```

## Install Python via pyenv
Install Python 3.6 latest version.  
**NOTE:** Currently Python 3.7 is not supported yet.

```console
$ pyenv install 3.6.6
```

## Create a virtualenv using a specific Python version

Change `myvenv` to specific names required in other guide pages.

```console
$ pyenv virtualenv 3.6.6 myvenv
```

## Activate the virtualenv for the current shell

```console
$ pyenv shell myvenv
```

## Activate the virtualenv when your shell goes into a directory

```console
$ cd some-directory
$ pyenv local myvenv
```

<table><tr><td>💡</td><td>

`pyenv local` creates a hidden `.python-version` file at each directory specifying the Python version/virtualenv recongnized by pyenv.
Any pyenv-enabled shells will automagically activate/deactivate this version/virtualenv when going in/out such directories.

</td></tr></table>
