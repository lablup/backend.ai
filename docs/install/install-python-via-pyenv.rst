.. role:: raw-html-m2r(raw)
   :format: html


We highly recommend `pyenv <https://github.com/pyenv/pyenv>`_ to install multiple Python versions side-by-side,
which does not interfere with system-default Pythons.


.. image:: https://asciinema.org/a/ow9AdNDqjGnkN5ky2dyxMaQmQ.png
   :target: https://asciinema.org/a/ow9AdNDqjGnkN5ky2dyxMaQmQ
   :alt: asciicast


Install dependencies for building Python
----------------------------------------

Ubuntu / Debian
^^^^^^

.. code-block:: console

   $ sudo apt-get update -y
   $ sudo apt-get dist-upgrade -y
   $ sudo apt-get install -y \
   > build-essential git-core                                     # for generic C/C++ builds
   > libreadline-dev libsqlite3-dev libssl-dev libbz2-dev tk-dev  # for Python builds
   > libzmq3-dev libsnappy-dev                                      # for Backend.AI dependency builds

CentOS / RHEL
^^^^^^^^^^^^^

.. code-block:: console

   $ sudo yum clean expire-cache  # next yum invocation will update package metadata cache
   $ sudo yum install -y git jq gcc make gcc-c++ \ # generic C/C++ builds
   > openssl-devel readline-devel gdbm-devel zlib-devel
   > bzip2-devel sqlite-devel libffi-devel xz-devel # for Python builds
   > snappy-devel                                   # for Backend.AI dependency builds

Install pyenv & pyenv-virtualenv plugin
-------------

**NOTE:** Change ``~/.profile`` accroding to your shell/system (e.g., ``~/.bashrc``\ , ``~/.bash_profile``\ , ``~/.zshrc``\ , ...) -- whichever loaded at startup of your shell! 

.. code-block:: console

   $ curl https://pyenv.run | bash
   ...
   $ echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.profile
   $ echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.profile
   $ echo 'eval "$(pyenv init --path)"' >> ~/.profile
   $ echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.profile
   $ exec $SHELL -l
   $ pyenv  # check installation
   pyenv 2.3.3
   Usage: pyenv <command> [<args>]

   Some useful pyenv commands are:
      ...

   $ pyenv virtualenv  # check installation
   pyenv-virtualenv: no virtualenv name given.

Install Python via pyenv
------------------------

Install Python 3.10 latest version.\ :raw-html-m2r:`<br>`

.. warning::
   According to `PEP-644 <https://peps.python.org/pep-0644/>`_ , Python 3.10 requires openssl 1.1.1 or newer

.. code-block:: console

   $ pyenv install 3.10.5

Create a virtualenv using a specific Python version
---------------------------------------------------

Change ``myvenv`` to specific names required in other guide pages.

.. code-block:: console

   $ pyenv virtualenv 3.10.5 myvenv

Activate the virtualenv for the current shell
---------------------------------------------

.. code-block:: console

   $ pyenv shell myvenv

Activate the virtualenv when your shell goes into a directory
-------------------------------------------------------------

.. code-block:: console

   $ cd some-directory
   $ pyenv local myvenv


.. note::

   `pyenv local` creates a hidden `.python-version` file at each directory specifying the Python version/virtualenv recongnized by pyenv.
   Any pyenv-enabled shells will automagically activate/deactivate this version/virtualenv when going in/out such directories.


