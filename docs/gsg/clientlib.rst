Python Client Library
=====================

We provide an official Python client library that abstracts the low-level HTTP REST APIs via a function-based interface.

Requirements
------------

Python 3.6 or higher is required.
You can download `its official installer from python.org <https://www.python.org/downloads/>`_, or use a 3rd-party package/version manager such as `homebrew <http://brew.sh/index_ko.html>`_, `miniconda <http://conda.pydata.org/miniconda.html>`_, or `pyenv <https://github.com/yyuu/pyenv>`_.
It works on Linux, macOS, and Windows.

Installation
------------

We recommend to create a virtual environment for isolated, unobtrusive installation of the library.

.. code-block:: shell

   $ python3 -m venv venv-sorna
   $ source venv-sorna/bin/activate
   (venv-sorna) $

Then install the client library from PyPI.

.. code-block:: shell

   (venv-sorna) $ pip install -U pip wheel setuptools
   (venv-sorna) $ pip install sorna-client

Configuration
-------------

Set your API keypair as environment variables:

.. code-block:: shell

   (venv-sorna) $ export SORNA_ACCESS_KEY=AKIA...
   (venv-sorna) $ export SORNA_SECRET_KEY=...

The run Python in the virtual environment and check if your credentials are valid:

.. code-block:: python

   >>> from sorna.request import Request
   >>> request = Request('GET', '/authorize', {'echo': 'test'})
   >>> request.sign()
   >>> response = request.send()
   >>> response.status
   200
   >>> response.json()
   {'authorized': 'yes', 'echo': 'test'}
