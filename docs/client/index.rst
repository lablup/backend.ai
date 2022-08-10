Backend.AI Client SDK for Python
================================

Python 3.10.5 or higher is required.

You can download `its official installer from python.org
<https://www.python.org/downloads/>`_, or use a 3rd-party package/version manager
such as `homebrew <http://brew.sh/index_ko.html>`_, `miniconda
<http://conda.pydata.org/miniconda.html>`_, or `pyenv
<https://github.com/pyenv/pyenv>`_.  It works on Linux, macOS, and Windows.

We recommend to create a virtual environment for isolated, unobtrusive installation
of the client SDK library and tools.

.. code-block:: console

   $ python3 -m venv venv-backend-ai
   $ source venv-backend-ai/bin/activate
   (venv-backend-ai) $

Then install the client library from PyPI.

.. code-block:: console

   (venv-backend-ai) $ pip install -U pip setuptools
   (venv-backend-ai) $ pip install backend.ai-client

Set your API keypair as environment variables (Linux, macOS):

.. code-block:: console

   (venv-backend-ai) $ export BACKEND_ACCESS_KEY=AKIA...
   (venv-backend-ai) $ export BACKEND_SECRET_KEY=...
   (venv-backend-ai) $ export BACKEND_ENDPOINT=https://my-precious-cluster
   (venv-backend-ai) $ export BACKEND_ENDPOINT_TYPE=api

On Windows, create a batch file as `my-backend-ai.bat` and run it before using the `backend.ai` command:

.. code-block:: bat

   chcp 65001
   set PYTHONIOENCODING=UTF-8
   set BACKEND_ACCESS_KEY=...
   set BACKEND_SECRET_KEY=...
   set BACKEND_ENDPOINT=https://my-precious-cluster
   set BACKEND_ENDPOINT_TYPE=api

And then try the first commands:

.. code-block:: console

   (venv-backend-ai) $ backend.ai --help
   ...
   (venv-backend-ai) $ backend.ai ps
   ...

Check out more details with the below table of contents.

.. toctree::
   :maxdepth: 2

   gsg/installation
   gsg/config
   cli/index
   dev/index
   func/index
   lowlevel/index
