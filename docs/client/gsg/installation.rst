Installation
============

Linux/macOS
-----------

We recommend using `pyenv <https://github.com/pyenv/pyenv>`_ to manage your Python
versions and virtual environments to avoid conflicts with other Python applications.

Create a new virtual environment (Python 3.6 or higher) and activate it on your
shell.  Then run the following commands:

.. code-block:: sh

  pip install -U pip setuptools
  pip install -U backend.ai-client-py

Create a shell script ``my-backendai-env.sh`` like:

.. code-block:: sh

  export BACKEND_ACCESS_KEY=...
  export BACKEND_SECRET_KEY=...
  export BACKEND_ENDPOINT=https://my-precious-cluster
  export BACKEND_ENDPOINT_TYPE=api

Run this shell script before using ``backend.ai`` command.

.. note::

   The console-server users should set ``BACKEND_ENDPOINT_TYPE`` to ``session``.
   For details, check out :doc:`the client configuration document <config>`.

Windows
-------

We recommend using `the Anaconda Navigator <https://www.anaconda.com/download/>`_ to
manage your Python environments with a slick GUI app.

Create a new environment (Python 3.6 or higher) and launch a terminal (command
prompt).  Then run the following commands:

.. code-block:: bat

  python -m pip install -U pip setuptools
  python -m pip install -U backend.ai-client-py

Create a batch file ``my-backendai-env.bat`` like:

.. code-block:: bat

  chcp 65001
  set PYTHONIOENCODING=UTF-8
  set BACKEND_ACCESS_KEY=...
  set BACKEND_SECRET_KEY=...
  set BACKEND_ENDPOINT=https://my-precious-cluster
  set BACKEND_ENDPOINT_TYPE=api

Run this batch file before using ``backend.ai`` command.

Note that this batch file switches your command prompt to use the UTF-8 codepage
for correct display of special characters in the console logs.

Verification
------------

Run ``backend.ai ps`` command and check if it says "there is no compute sessions
running" or something similar.

If you encounter error messages about "ACCESS_KEY", then check if your batch/shell
scripts have the correct environment variable names.

If you encounter network connection error messages, check if the endpoint server is
configured correctly and accessible.
