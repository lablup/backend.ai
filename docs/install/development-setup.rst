.. role:: raw-html-m2r(raw)
   :format: html


Development Setup
=================

Currently Backend.AI is developed and tested under only \*NIX-compatible platforms (Linux or macOS).


Installation from Source
------------------------

For the ease of on-boarding developer experience, we provide an automated
script that installs all server-side components in editable states with just
one command.

Prerequisites
~~~~~~~~~~~~~

Install the followings accordingly to your host operating system.

* `Git LFS <https://git-lfs.github.com/>`_

* `pyenv <https://github.com/pyenv/pyenv>`_ and `pyenv-virtualenv <https://github.com/pyenv/pyenv-virtualenv>`_

  - Ensure that you have the Python version specified in ``pants.toml`` on your ``PATH``.

  - Depending on your Linux Distribution, you may have to additionally install a sysmte package that enables Python's `pip` command.

    * Ubuntu

      .. code-block:: console

         $ sudo apt install python3-pip

    * Fedora Core & CentOS

      .. code-block:: console

         $ sudo dnf install python3-pip

* `Docker <https://docs.docker.com/install/>`_

* `Docker Compose <https://docs.docker.com/compose/install/>`_ (v2 required)

* `Rust <https://rustup.rs/>`_ (for bootstrapping Pants)

.. note::

   In some cases, locale conflicts between the terminal client and the remote host
   may cause encoding errors when installing Backend.AI components due to Unicode characters
   in README files.  Please keep correct locale configurations to prevent such errors.

Running the install-dev script
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ git clone https://github.com/lablup/backend.ai bai-dev
   $ cd bai-dev
   $ ./scripts/install-dev.sh

.. note::

   The script requires ``sudo`` to check and install several system packages
   such as ``build-essential``.

This script will bootstrap `Pants <https://pantsbuild.org>`_ and creates the halfstack
containers using ``docker compose`` with fixture population.
At the end of execution, the script will show several command examples about
launching the service daemons such as manager and agent.
You may execute this script multiple times when you encounter prerequisite errors and
resolve them.
Also check out additional options using ``-h`` / ``--help`` option, such as installing
the CUDA mockup plugin together, etc.

.. versionchanged:: 22.09

   We have migrated to per-package repositories to a semi-mono repository that contains
   all Python-based components except plugins.  This has changed the installation
   instruction completely with introduction of Pants.

.. note::

   To install multiple instances/versions of development environments using this script,
   just clone the repository in another location and run ``scripts/install-dev.sh``
   inside that directory.

   It is important to name these working-copy directories *differently* not to confuse
   ``docker compose`` so that it can distinguish the containers for each setup.

   Unless you customize all port numbers by the options of ``scripts/install-dev.sh``,
   you should ``docker compose -f docker-compose.halfstack.current.yml down`` and ``docker compose -f docker-compose.halfstack.current.yml up -d`` when switching
   between multiple working copies.

.. note::

   By default, the script pulls the docker images for our standard Python kernel and
   TensorFlow CPU-only kernel.  To try out other images, you have to pull them
   manually afterwards.

.. tip::

   **Using the agent's cgroup-based statistics without the root privilege (Linux-only)**

   To allow Backend.AI to collect sysfs/cgroup resource usage statistics, the Python executable must have the following Linux capabilities: ``CAP_SYS_ADMIN``, ``CAP_SYS_PTRACE``, and ``CAP_DAC_OVERRIDE``.

   .. code-block:: console

      $ sudo setcap \
      >   cap_sys_ptrace,cap_sys_admin,cap_dac_override+eip \
      >   $(readlink -f $(pyenv which python))


Verifying Installation
~~~~~~~~~~~~~~~~~~~~~~

Refer the instructions displayed after running ``scripts/install-dev.sh``.
We recommend to use `tmux <https://github.com/tmux/tmux/wiki>`_ to open
multiple terminals in a single SSH session.
Your terminal app may provide a tab interface, but when using remote servers,
tmux is more convenient because you don't have to setup a new SSH connection
whenever adding a new terminal.

Ensure the halfstack containers are running:

.. code-block:: console

   $ docker compose -f docker-compose.halfstack.current.yml up -d

Open a terminal for manager and run:

.. code-block:: console

   $ ./backend.ai mgr start-server --debug

Open another terminal for agent and run:

.. code-block:: console

   $ ./backend.ai ag start-server --debug

Open yet another terminal for client and run:

.. code-block:: console

   $ export BACKEND_ENDPOINT=http://127.0.0.1:8081/  # change the port number if customized
   $ export BACKEND_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
   $ export BACKEND_SECRET_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   $ ./backend.ai config
   $ ./backend.ai run python -c 'print("hello world")'
   ∙ Session token prefix: fb05c73953
   ✔ [0] Session fb05c73953 is ready.
   hello world
   ✔ [0] Execution finished. (exit code = 0)
   ✔ [0] Cleaned up the session.
   $ ./backend.ai ps


Resetting the environment
~~~~~~~~~~~~~~~~~~~~~~~~~

Shutdown all docker containers using ``docker compose -f docker-compose.halfstack.current.yml down`` and delete the entire working copy directory.  That's all.

You may need ``sudo`` to remove the directories mounted as halfstack container volumes
because Docker auto-creates them with the root privilege.
