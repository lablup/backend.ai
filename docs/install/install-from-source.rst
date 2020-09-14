Install from Source
===================

This is the recommended way to install on most setups, for both development and production.

.. note::

   For production deployments, we also recommend pinning specific releases when cloning or updating source repositories.


Setting Up Manager and Agent (single node)
------------------------------------------

Prerequisites
^^^^^^^^^^^^^

For a standard installation:

* Ubuntu 16.04+ / CentOS 7.4+ / macOS 10.12+

  - For Linux: ``sudo`` with access to the package manager (``apt-get`` or ``yum``)
  - For macOS: `homebrew <https://brew.sh>`_ with the latest Xcode Command Line tools.

* bash
* git

To enable CUDA (only supported in Ubuntu or CentOS):

* CUDA 8.0 or later (with compatible NVIDIA driver)
* nvidia-docker 1.0 or 2.0


Running the Installer
^^^^^^^^^^^^^^^^^^^^^

Clone `the meta repository <https://github.com/lablup/backend.ai>`_ first.
For the best result, clone the branch of this repo that matches with the target server branch you want to install.
Inside the cloned working copy, ``scripts/install-dev.sh`` is the automatic single-node installation script.

It provides the following options (check with ``--help``):

* ``--python-version``: The Python version to install.
* ``--install-path``: The target directory where individual Backend.AI components are installed together as subdirectories.
* ``--server-branch``: The branch/tag used for the manager, agent, and common components.
* ``--client-branch``: The branch/tag used for the client-py component.
* ``--enable-cuda``: If specified, the installer will install the open-source version of CUDA plugin for the agent.
* ``--cuda-branch``: The branch/tag used for the CUDA plugin.

With default options, the script will install a source-based single-node Backend.AI cluster as follows:

* The installer tries to install pyenv, the designated Python version, docker-compose, and a few libraries (e.g., libsnappy) automatically
  after checking their availability.  If it encounters an error during installation, it will show manual instructions and stop.
* It creates a set of Docker containers for Redis 5, PostgreSQL 9.6, and etcd 3.3 via docker-compose, with the default credentials:
  The Redis and etcd is configured without authentication and PostgreSQL uses ``postgres`` / ``develove``.
  We call these containers as "halfstack".
* ``./backend.ai-dev/{component}`` where components are manager, agent, common, client, and a few others, using separate virtualenvs.
  They are all installed as "editable" so modifying the cloned sources takes effects immediately.
* For convenience, when ``cd``-ing into individual component directories, pyenv will activate the virtualenv automatically for supported shells.
  This is configured via ``pyenv local`` command during installation.
* The default vfolder mount point is ``./backend.ai/vfolder`` and the default vfolder host is ``local``.
* The installer automatically populates the example fixtures (in the ``sample-configs`` directory of `the manager
  repository <https://github.com/lablup/backend.ai-manager>`_) for during the database initialization.
* It automatically updates the list of available Backend.AI kernel images from the public Docker Hub.
  It also pulls a few frequently used images such as the base Python image.
* The manager and agent are *NOT* daemonized. You must run them by running
  ``scripts/run-with-halfstack.sh python -m ...`` inside each component's source clones.
  Those wrapper scripts configure environment variables suitable for the default halfstack containers.


Verifying the Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the manager and agent as follows in their respective component directories:

* manager:

  .. code-block:: console

     $ cd backend.ai-dev/manager
     $ scripts/run-with-halfstack.sh python -m ai.backend.gateway.server

  By default, it listens on the localhost's 8080 port using the plain-text HTTP.

* agent:

  .. code-block:: console

     $ cd backend.ai-dev/agent
     $ scripts/run-with-halfstack.sh python -m ai.backend.agent.server \
           --scratch-root=$(pwd)/scratches

.. note::

   The manager and agent may be executed without the root privilege on both Linux and macOS.
   In Linux, the installer sets extra capability bits to the Python executable so that
   the agent can manage cgroups and access the Docker daemon.

If all is well, they will say "started" or "serving at ...".
You can also check their CLI options using ``--help`` option to change service IP and ports or enable the debug mode.

To run a "hello world" example, you first need to configure the client using the following script:

.. code-block:: shell

   # env-local-admin.sh
   export BACKEND_ENDPOINT=http://127.0.0.1:8080
   export BACKEND_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
   export BACKEND_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

And then run the following inside the client directory.
If you see similar console logs, your installation is now working:

.. code-block:: console

   $ cd backend.ai-dev/client-py
   $ source env-local-admin.sh
   $ backend.ai run --rm -c 'print("hello world")' python:3.6-ubuntu18.04
   ∙ Session token prefix: fb05c73953
   ✔ [0] Session fb05c73953 is ready.
   hello world
   ✔ [0] Execution finished. (exit code = 0)
   ✔ [0] Cleaned up the session.

Setting Up Additional Agents (multi-node)
-----------------------------------------

Updating Manager Configuration for Multi-Nodes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Verifying the Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^


