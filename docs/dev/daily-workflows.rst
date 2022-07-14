Daily Development Workflows
===========================

About Pants
-----------

Since 22.09, we have migrated to `Pants <https://pantsbuild.org>`_ as our
primary build system and dependency manager for the mono-repository of Python
components.

Pants is a graph-based async-parallel task executor written in Rust and Python.
It is tailored to building programs with explicit and auto-inferred
dependency checks and aggressive caching.

Key concepts
~~~~~~~~~~~~

* The command pattern:

  .. code-block:: console

      $ ./pants [GLOBAL_OPTS] GOAL [GOAL_OPTS] [TARGET ...]

  .. warning::

      If your ``scripts/install-dev.sh`` says that you need to use
      ``./pants-local`` instead of ``./pants``, replace all ``./pants``
      in the following command examples with ``./pants-local``.

* Goal: an action to execute

  - You may think this as the root node of the task graph executed by Pants.

* Target: objectives for the action, usually expressed as ``path/to/dir:name``

  - The targets are declared/defined by ``path/to/dir/BUILD`` files.

* The global configuration is at ``pants.toml``.

* Recommended reading: https://www.pantsbuild.org/docs/concepts

Inspecting build configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Display all targets

  .. code-block:: console

      $ ./pants list ::

  - This list includes the full enumeration of individual targets auto-generated
    by collective targets (e.g., ``python_sources()`` generates multiple
    ``python_source()`` targets by globbing the ``sources`` pattern)

* Display all dependencies of a specific target (i.e., all targets required to
  build this target)

  .. code-block:: console

      $ ./pants dependencies --transitive src/ai/backend/common:lib

* Display all dependees of a specific target (i.e., all targets affected when
  this target is changed)

  .. code-block:: console

      $ ./pants dependees --transitive src/ai/backend/common:lib

.. note::

   Pants statically analyzes the source files to enumerate all its imports
   and determine the dependencies automatically.  In most cases this works well,
   but sometimes you may need to manually declare explicit dependencies in
   ``BUILD`` files.

Running lint and check
----------------------

Run lint/check for all targets:

.. code-block:: console

    $ ./pants lint ::
    $ ./pants check ::

To run lint/check for a specific target or a set of targets:

.. code-block:: console

    $ ./pants lint src/ai/backend/common:: tests/common::
    $ ./pants check src/ai/backend/manager::

Currently running mypy with pants is slow because mypy cannot utilize its own cache as pants invokes mypy per file due to its own dependency management scheme.
(e.g., Checking all sources takes more than 1 minutes!)
This performance issue is being tracked by `pantsbuild/pants#10864
<https://github.com/pantsbuild/pants/issues/10864>`_.  For now, try using a
smaller target of files that you work on and `use an option to select the
targets only changed
<https://www.pantsbuild.org/docs/advanced-target-selection#running-over-changed-files-with---changed-since>`_ (``--changed-since``).

Running formatters
------------------

If you encounter failure from ``isort``, you may run the formatter to automatically fix the import ordering issues.

.. code-block:: console

   $ ./pants fmt ::
   $ ./pants fmt src/ai/backend/common::

Running unit tests
------------------

Here are various methods to run tests:

.. code-block:: console

    $ ./pants test ::
    $ ./pants test tests/manager/test_scheduler.py::
    $ ./pants test tests/manager/test_scheduler.py:: -- -k test_scheduler_configs

You may also try ``--changed-since`` option like ``lint`` and ``check``.

To specify extra environment variables for tests, use the ``--test-extra-env-vars``
option:

.. code-block:: console

    $ ./pants test \
    >   --test-extra-env-vars=MYVARIABLE=MYVALUE \
    >   tests/common:tests

Running integration tests
-------------------------

.. code-block:: console

    $ ./backend.ai test run-cli user,admin

Building wheel packages
-----------------------

To build a specific package:

.. code-block:: console

    $ ./pants \
    >   --tag="wheel" \
    >   package \
    >   src/ai/backend/common:dist
    $ ls -l dist/*.whl

If the package content varies by the target platform, use:

.. code-block:: console

    $ ./pants \
    >   --tag="wheel" \
    >   --tag="+platform-specific" \
    >   --platform-specific-resources-target=linux_arm64 \
    >   package \
    >   src/ai/backend/runner:dist
    $ ls -l dist/*.whl

Using IDEs and editors
----------------------

Pants has an ``export`` goal to auto-generate a virtualenv that contains all
external dependencies installed in a single place.
This is very useful when you work with IDEs and editors.

To (re-)generate the virtualenv, run:

.. code-block:: console

    $ ./pants export ::

Then configure your IDEs/editors to use
``dist/export/python/virtualenvs/python-default/VERSION/bin/python`` as the
interpreter for your code, where ``VERSION`` is the interpreter version
specified in ``pants.toml``.

To make LSP (language server protocol) services like PyLance to detect our source packages correctly,
you should also configure ``PYTHONPATH`` to include the repository root's ``src`` directory and
``plugins/*/`` directories if you have added Backend.AI plugin checkouts.

.. tip::

   To activate flake8/mypy checks (in Vim) and get proper intelli-sense support
   for pytest (in VSCode), just install them in the exported venv as follows.
   (You need to repeat this when you re-export!)

   .. code-block:: console

      $ ./py -m pip install flake8 mypy pytest

   For Vim, you also need to explicitly activate the exported venv.

Switching between branches
~~~~~~~~~~~~~~~~~~~~~~~~~~

When each branch has different external package requirements, you should run ``./pants export ::``
before running codes after ``git switch``-ing between such branches.

Sometimes, you may experience bogus "glob" warning from pants because it sees a stale cache.
In that case, run ``killall -r pantsd`` and it will be fine.

Running entrypoints
-------------------

To run a Python program within the unified virtualenv, use the ``./py`` helper
script.  It automatically passes additional arguments transparently to the
Python executable of the unified virtualenv.

``./backend.ai`` is an alias of ``./py -m ai.backend.cli``.

Examples:

.. code-block:: console

    $ ./py -m ai.backend.storage.server
    $ ./backend.ai mgr start-server
    $ ./backend.ai ps

Working with plugins
--------------------

To develop Backend.AI plugins together, the repository offers a special location
``./plugins`` where you can clone plugin repositories and a shortcut script
``scripts/install-plugin.sh`` that does this for you.

.. code-block:: console

    $ scripts/install-plugin.sh lablup/backend.ai-accelerator-cuda-mock

This is equivalent to:

.. code-block:: console

    $ git clone \
    >   https://github.com/lablup/backend.ai-accelerator-cuda-mock \
    >   plugins/backend.ai-accelerator-cuda-mock

These plugins are auto-detected by scanning ``setup.cfg`` of plugin subdirectories
by the ``ai.backend.plugin.entrypoint`` module, even without explicit editable installations.

Writing test cases
------------------

Mostly it is just same as before: use the standard pytest practices.
Though, there are a few key differences:

- Tests are executed **in parallel** in the unit of test modules.

- Therefore, session-level fixtures may be executed *multiple* times during a
  single run of ``./pants test``.

.. warning::

  If you *interrupt* (Ctrl+C, SIGINT) a run of ``./pants test``, it will
  immediately kill all pytest processes without fixture cleanup. This may
  accumulate unused Docker containers in your system, so it is a good practice
  to run ``docker ps -a`` periodically and clean up dangling containers.

  To interactively run tests, see :ref:`debugging-tests`.

Here are considerations for writing Pants-friendly tests:

* Ensure that it runs in an isolated/mocked environment and minimize external dependency.

* If required, use the environment variable ``BACKEND_TEST_EXEC_SLOT`` (an integer
  value) to uniquely define TCP port numbers and other resource identifiers to
  allow parallel execution.
  `Refer the Pants docs <https://www.pantsbuild.org/docs/reference-pytest#section-execution-slot-var](https://www.pantsbuild.org/docs/reference-pytest#section-execution-slot-var>`_.

* Use ``ai.backend.testutils.bootstrap`` to populate a single-node
  Redis/etcd/Postgres container as fixtures of your test cases.
  Import the fixture and use it like a plain pytest fixture.

  - These fixtures create those containers with **OS-assigned public port
    numbers** and give you a tuple of container ID and a
    ``ai.backend.common.types.HostPortPair`` for use in test codes. In manager and
    agent tests, you could just refer ``local_config`` to get a pre-populated
    local configurations with those port numbers.

  - In this case, you may encounter ``flake8`` complaining about unused imports
    and redefinition. Use ``# noqa: F401`` and ``# noqa: F811`` respectively for now.

.. warning::

   **About using /tmp in tests**

   If your Docker service is installed using **Snap** (e.g., Ubuntu 20.04 or
   later), it cannot access the system ``/tmp`` directory because Snap applies a
   private "virtualized" tmp directory to the Docker service.

   You should use other locations under the user's home directory (or
   preferably ``.tmp`` in the working copy directory) to avoid mount failures
   for the developers/users in such platforms.

   It is okay to use the system ``/tmp`` directory if they are not mounted inside
   any containers.

Writing documentation
---------------------

* Create a new pyenv virtualenv based on Python 3.10.

  .. code-block:: console

     $ pyenv virtualenv 3.10.4 venv-bai-docs

* Activate the virtualenv and run:

  .. code-block:: console

     $ pyenv activate venv-bai-docs
     $ pip install -U pip setuptools wheel
     $ pip install -U -r docs/requirements.txt

* You can build the docs as follows:

  .. code-block:: console

     $ cd docs
     $ pyenv activate venv-bai-docs
     $ make html

* To locally serve the docs:

  .. code-block:: console

     $ cd docs
     $ python -m http.server --directory=_build/html

(TODO: Use Pants' own Sphinx support when `pantsbuild/pants#15512 <https://github.com/pantsbuild/pants/pull/15512>`_ is released.)


Advanced Topics
---------------

Adding new external dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Add the package version requirements to the unified requirements file (``./requirements.txt``).

* Update the ``module_mapping`` field in the root build configuration (``./BUILD``)
  if the package name and its import name differs.

* Update the ``type_stubs_module_mapping`` field in the root build configuration
  if the package provides a type stubs package separately.

* Run:

  .. code-block:: console

     $ ./pants generate-lockfiles
     $ ./pants export ::

Merging lockfile conflicts
~~~~~~~~~~~~~~~~~~~~~~~~~~

When you work on a branch that adds a new external dependency and the main branch has also
another external dependency addition, merging the main branch into your branch is likely to
make a merge conflict on ``python.lock`` file.

In this case, you can just do the followings since we can just *regenerate* the lockfile
after merging ``requirements.txt`` and ``BUILD`` files.

.. code-block:: console

   $ git merge main
   ... it says a conflict on python.lock ...
   $ git checkout --theirs python.lock
   $ ./pants generate-lockfiles --resolve=python-default
   $ git add python.lock
   $ git commit

Resetting Pants
~~~~~~~~~~~~~~~

If Pants behaves strangely, you could simply reset all its runtime-generated files by:

.. code-block:: console

   $ killall -r pantsd
   $ rm -r .tmp .pants.d ~/.cache/pants

After this, re-running any Pants command will automatically reinitialize itself and
all cached data as necessary.

.. _debugging-tests:

Debugging test cases (or interactively running test cases)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When your tests *hang*, you can try adding the ``--debug`` flag to the ``./pants test`` command:

.. code-block:: console

   $ ./pants test --debug ...

so that Pants runs the designated test targets **serially and interactively**.
This means that you can directly observe the console output and Ctrl+C to
gracefully shutdown the tests  with fixture cleanup. You can also apply
additional pytest options such as ``--fulltrace``, ``-s``, etc. by passing them
after target arguments and ``--`` when executing ``./pants test`` command.

Installing a subset of mono-repo packages in the editable mode for other projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, you need to editable-install a subset of packages into other project's directories.
For instance you could mount the client SDK and its internal dependencies for a Docker container for development.

In this case, we recommend to do it as follows:

1. Run the following command to build a wheel from the current mono-repo source:

   .. code-block:: console

      $ ./pants --tag=wheel package src/ai/backend/client:dist

   This will generate ``dist/backend.ai_client-{VERSION}-py3-none-any.whl``.

2. Run ``pip install -U {MONOREPO_PATH}/dist/{WHEEL_FILE}`` in the target environment.

   This will populate the package metadata and install its external dependencies.
   The target environment may be one of a separate virtualenv or a container being built.
   For container builds, you need to first ``COPY`` the wheel file and install it.

3. Check the internal dependency directories to link by running the following command:

   .. code-block:: console

      $ ./pants dependencies --transitive src/ai/backend/client:lib \
      >   | grep src/ai/backend | grep -v ':version' | cut -d/ -f4 | uniq
      cli
      client
      plugin

4. Link these directories in the target environment.

   For example, if it is a Docker container, you could add
   ``-v {MONOREPO_PATH}/src/ai/backend/{COMPONENT}:/usr/local/lib/python3.10/site-packages/ai/backend/{COMPONENT}``
   to the ``docker create`` or ``docker run`` commands for all the component
   directories found in the previous step.

   If it is a local checkout with a pyenv-based virtualenv, you could replace
   ``$(pyenv prefix)/lib/python3.10/site-packages/ai/backend/{COMPONENT}`` directories
   with symbolic links to the mono-repo's component source directories.

Boosting the performance of Pants commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since Pants uses temporary directories for aggressive caching, you could make
the ``.tmp`` directory under the working copy root a tmpfs partition:

.. code-block:: console

   $ sudo mount -t tmpfs -o size=4G tmpfs .tmp

* To make this persistent across reboots, add the following line to ``/etc/fstab``:

  .. code-block:: text

     tmpfs /path/to/dir/.tmp tmpfs defaults,size=4G 0 0

* The size should be more than 3GB.
  (Running ``./pants test ::`` consumes about 2GB.)

* To change the size at runtime, you could simply remount it with a new size option:

  .. code-block:: console

     $ sudo mount -t tmpfs -o remount,size=8G tmpfs .tmp

Making a new release
~~~~~~~~~~~~~~~~~~~~

* Update ``./VERSION`` file to set a new version number. (Remove the ending new
  line, e.g., using ``set noeol`` in Vim.  This is also configured in
  ``./editorconfig``)

* Run ``LOCKSET=tools/towncrier ./py -m towncrier`` to auto-generate the changelog.

  - You may append ``--draft`` to see a preview of the changelog update without
    actually modifying the filesytem.

  - (WIP: `lablup/backend.ai#427 <https://github.com/lablup/backend.ai/pull/427>`_).

* Make a new git commit with the commit message: "release: <version>".

* Make an annotated tag to the commit with the message: "Release v<version>"
  or "Pre-release v<version>" depending on the release version.

* Push the commit and tag.  The GitHub Actions workflow will build the packages
  and publish them to PyPI.

Backporting to legacy per-pkg repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Use ``git diff`` and ``git apply`` instead of ``git cherry-pick``.

  - To perform a three-way merge for conflicts, add ``-3`` option to the ``git apply`` command.

  - You may need to rewrite some codes as the package structure differs. (The
    new mono repository has more fine-grained first party packages divided from
    the ``backend.ai-common`` package.)

* When referring the PR/issue numbers in the commit for per-pkg repositories,
  update them like ``lablup/backend.ai#NNN`` instead of ``#NNN``.
