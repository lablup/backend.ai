.. role:: raw-html-m2r(raw)
   :format: html


Development Setup
=================

Currently Backend.AI is developed and tested under only \*NIX-compatible platforms (Linux or macOS).


Method 1: Automatic Installation
--------------------------------

For the ease of on-boarding developer experience, we provide an automated
script that installs all server-side components in editable states with just
one command.

Prerequisites
~~~~~~~~~~~~~

Install the followings accordingly to your host operating system.

* `pyenv <https://github.com/pyenv/pyenv>`_ and `pyenv-virtualenv <https://github.com/pyenv/pyenv-virtualenv>`_

* `docker <https://docs.docker.com/install/>`_

* `docker-compose <https://docs.docker.com/compose/install/>`_

* Correct locale configurations to prevent unexpected errors
  (e.g., resolve mismatches of locales between your terminal client and the remote host)

Running the script
~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ git clone https://github.com/lablup/backend.ai bai-meta
   $ bai-meta/scripts/install-dev.sh

This installs a set of Backend.AI server-side components in the
``backend.ai-dev`` directory under the current working directory.

At the end of execution, the script will show several command examples about
launching the gateway and agent.  There is a unique random key called
"environment ID" to distinguish a particular execution of this script so that
repeated execution does not corrupt your existing setups.

By default, it pulls the docker images for our standard Python kernel and
TensorFlow CPU-only kernel.  To try out other images, you have to pull them
manually afterwards.

Resetting the environment
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ bai-meta/scripts/delete-dev.sh <ENVID>

This will purge all docker resources related to the given environment ID and
the ``backend.ai-dev`` directory under the current working directory.

.. warning::

   Be aware that this script force-removes, without any warning, all contents
   of the ``backend.ai-dev`` directory, which may contain your own
   modifications that is not yet pushed to a remote git repository.


Method 2: Manual Installation
-----------------------------

Requirement packages
~~~~~~~~~~~~~~~~~~~~

* PostgreSQL: 9.6

* etcd: v3.3.9

* redis: latest

Prepare containers for external daemons
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First install an appropriate version of Docker (later than 2017.03 version) and docker-compose (later than 1.21).
Check out the :doc:`Install Docker </install/install-docker>` guide.

.. note::
   In this guide, ``$WORKSPACE`` means the absolute path to an arbitrary working directory in your system.

   To copy-and-paste commands in this guide, set ``WORKSPACE`` environment variable.

   The directory structure would look like after finishing this guide:

   * ``$WORKSPACE``
      * backend.ai
      * backend.ai-manager
      * backend.ai-agent
      * backend.ai-common
      * backend.ai-client-py

.. code-block:: console

   $ cd $WORKSPACE
   $ git clone https://github.com/lablup/backend.ai
   $ cd backend.ai
   $ docker-compose -f docker-compose.halfstack.yml up -d
   $ docker ps  # you should see 3 containers running


.. image:: https://asciinema.org/a/Q2Y3JuwqYoJjG9RB64Ovcpal2.png
   :target: https://asciinema.org/a/Q2Y3JuwqYoJjG9RB64Ovcpal2
   :alt: asciicast


This will create and start PostgreSQL, Redis, and a single-instance etcd containers.
Note that PostgreSQL and Redis uses non-default ports by default (5442 and 6389 instead of 5432 and 6379)
to prevent conflicts with other application development environments.

Prepare Python 3.6+
~~~~~~~~~~~~~~~~~~~

Check out :doc:`Install Python via pyenv <install-python-via-pyenv>` for instructions.

Create the following virtualenvs: ``venv-manager``, ``venv-agent``, ``venv-common``, and ``venv-client``.


.. image:: https://asciinema.org/a/xcMY9g5iATrCchoziCbErwgbG.png
   :target: https://asciinema.org/a/xcMY9g5iATrCchoziCbErwgbG
   :alt: asciicast


Prepare dependent libraries
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Install ``snappy`` (brew on macOS), ``libsnappy-dev`` (Debian-likes), or ``libsnappy-devel`` (RHEL-likes) system package depending on your environment.

Prepare server-side source clones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. image:: https://asciinema.org/a/SKJv19aNu9XKiCTOF0ASXibDq.png
   :target: https://asciinema.org/a/SKJv19aNu9XKiCTOF0ASXibDq
   :alt: asciicast


Clone the Backend.AI source codes.

.. code-block:: console

   $ cd $WORKSPACE
   $ git clone https://github.com/lablup/backend.ai-manager
   $ git clone https://github.com/lablup/backend.ai-agent
   $ git clone https://github.com/lablup/backend.ai-common

Inside each directory, install the sources as editable packages.


.. note::
   Editable packages makes Python to apply any changes of the source code in git clones immediately when importing the installed packages.


.. code-block:: console

   $ cd $WORKSPACE/backend.ai-manager
   $ pyenv local venv-manager
   $ pip install -U -r requirements-dev.txt

.. code-block:: console

   $ cd $WORKSPACE/backend.ai-agent
   $ pyenv local venv-agent
   $ pip install -U -r requirements-dev.txt

.. code-block:: console

   $ cd $WORKSPACE/backend.ai-common
   $ pyenv local venv-common
   $ pip install -U -r requirements-dev.txt

(Optional) Symlink backend.ai-common in the manager and agent directories to the cloned source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you do this, your changes in the source code of the backend.ai-common directory will be reflected immediately to the manager and agent.
You should install backend.ai-common dependencies into ``venv-manager`` and ``venv-agent`` as well, but this is already done in the previous step.

.. code-block:: console

   $ cd "$(pyenv prefix venv-manager)/src"
   $ mv backend.ai-common backend.ai-common-backup
   $ ln -s "$WORKSPACE/backend.ai-common" backend.ai-common

.. code-block:: console

   $ cd "$(pyenv prefix venv-agent)/src"
   $ mv backend.ai-common backend.ai-common-backup
   $ ln -s "$WORKSPACE/backend.ai-common" backend.ai-common

Initialize databases and load fixtures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check out the :doc:`Prepare Databases for Manager </install/prepare-database-for-manager>` guide.

Prepare Kernel Images
~~~~~~~~~~~~~~~~~~~~~

You need to pull the kernel container images first to actually spawn compute sessions.\ :raw-html-m2r:`<br>`
The kernel images here must have the tags specified in image-metadata.yml file.

.. code-block:: console

   $ docker pull lablup/kernel-python:3.6-debian

For the full list of publicly available kernels, `check out the kernels repository. <https://github.com/lablup/backend.ai-kernels>`_

**NOTE:** You need to restart your agent if you pull images after starting the agent.

Setting Linux capabilities to Python (Linux-only)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To allow Backend.AI to collect sysfs/cgroup resource usage statistics, the Python executable must have the following Linux capabilities (to run without "root"): ``CAP_SYS_ADMIN``, ``CAP_SYS_PTRACE``, and ``CAP_DAC_OVERRIDE``.
You may use the following command to set them to the current virtualenv's Python executable.

.. code-block:: console

   $ sudo setcap cap_sys_ptrace,cap_sys_admin,cap_dac_override+eip $(readlink -f $(pyenv which python))

Running daemons from cloned sources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ cd $WORKSPACE/backend.ai-manager
   $ ./scripts/run-with-halfstack.sh python -m ai.backend.gateway.server --service-port=8081 --debug

Note that through options, PostgreSQL and Redis ports set above for development environment are used. You may change other options to match your environment and personal configurations. (Check out ``-h`` / ``--help``)

.. code-block:: console

   $ cd $WORKSPACE/backend.ai-agent
   $ mkdir -p scratches  # used as in-container scratch "home" directories
   $ ./scripts/run-with-halfstack.sh python -m ai.backend.agent.server --scratch-root=`pwd`/scratches --debug --idle-timeout 30

※ The role of ``run-with-halfstack.sh`` script is to set appropriate environment variables so that the manager/agent daemons use the halfstack docker containers.

Prepare client-side source clones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


.. image:: https://asciinema.org/a/dJQKPrcmIliVkCX4ldSg3rPki.png
   :target: https://asciinema.org/a/dJQKPrcmIliVkCX4ldSg3rPki
   :alt: asciicast


.. code-block:: console

   $ cd $WORKSPACE
   $ git clone https://github.com/lablup/backend.ai-client-py

.. code-block:: console

   $ cd $WORKSPACE/backend.ai-client-py
   $ pyenv local venv-client
   $ pip install -U -r requirements-dev.txt

Inside ``venv-client``\ , now you can use the ``backend.ai`` command for testing and debugging.


Verifying Installation
----------------------

Write a shell script (e.g., ``env_local.sh``) like below to easily switch the API endpoint and credentials for testing:

.. code-block:: sh

   #! /bin/sh
   export BACKEND_ENDPOINT=http://127.0.0.1:8081/
   export BACKEND_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
   export BACKEND_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

Load this script (e.g., ``source env_local.sh``) before you run the client against your server-side installation.

Now you can do ``backend.ai ps`` to confirm if there are no sessions running and run the hello-world:

.. code-block:: sh

   $ cd $WORKSPACE/backend.ai-client-py
   $ source env_local.sh  # check above
   $ backend.ai run python -c 'print("hello")'
