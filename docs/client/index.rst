Backend.AI Client SDK for Python
================================

This is the documentation for the Python Client SDK which implements
:doc:`the Backend.AI API <backendai:index>`.

Quickstart
----------

Python 3.8 or higher is required.

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

Set your API keypair as environment variables:

.. code-block:: console

   (venv-backend-ai) $ export BACKEND_ACCESS_KEY=AKIA...
   (venv-backend-ai) $ export BACKEND_SECRET_KEY=...

And then try the first commands:

.. code-block:: console

   (venv-backend-ai) $ backend.ai --help
   ...
   (venv-backend-ai) $ backend.ai ps
   ...

Check out more details about :doc:`client configuration <gsg/config>`, the command-line
examples, and :doc:`SDK code examples <dev/examples>`.

Getting Started
---------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   gsg/installation
   gsg/config

Command-line Interface
----------------------

.. toctree::
   :maxdepth: 2
   :caption: CLI

   cli/config
   cli/sessions
   cli/apps
   cli/storage
   cli/code-execution
   cli/session-templates

Developer Reference
-------------------
.. toctree::
   :maxdepth: 2
   :caption: Development

   dev/index
   func/index
   lowlevel/index
