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

      $ pants [GLOBAL_OPTS] GOAL [GOAL_OPTS] [TARGET ...]

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

      $ pants list ::

  - This list includes the full enumeration of individual targets auto-generated
    by collective targets (e.g., ``python_sources()`` generates multiple
    ``python_source()`` targets by globbing the ``sources`` pattern)

* Display all dependencies of a specific target (i.e., all targets required to
  build this target)

  .. code-block:: console

      $ pants dependencies --transitive src/ai/backend/common:src

* Display all dependees of a specific target (i.e., all targets affected when
  this target is changed)

  .. code-block:: console

      $ pants dependees --transitive src/ai/backend/common:src

.. note::

   Pants statically analyzes the source files to enumerate all its imports
   and determine the dependencies automatically.  In most cases this works well,
   but sometimes you may need to manually declare explicit dependencies in
   ``BUILD`` files.

Running lint and check
----------------------

Run lint/check for all targets:

.. code-block:: console

    $ pants lint ::
    $ pants check ::

To run lint/check for a specific target or a set of targets:

.. code-block:: console

    $ pants lint src/ai/backend/common:: tests/common::
    $ pants check src/ai/backend/manager::

Currently running mypy with pants is slow because mypy cannot utilize its own cache as pants invokes mypy per file due to its own dependency management scheme.
(e.g., Checking all sources takes more than 1 minutes!)
This performance issue is being tracked by `pantsbuild/pants#10864
<https://github.com/pantsbuild/pants/issues/10864>`_.  For now, try using a
smaller target of files that you work on and `use an option to select the
targets only changed
<https://www.pantsbuild.org/docs/advanced-target-selection#running-over-changed-files-with---changed-since>`_ (``--changed-since``).

Running formatters
------------------

If you encounter failure from ``ruff``, you may run the following to automatically fix the import ordering issues.

.. code-block:: console

   $ pants fix ::

If you encounter failure from ``black``, you may run the following to automatically fix the code style issues.

.. code-block:: console

   $ pants fmt ::

Running unit tests
------------------

Here are various methods to run tests:

.. code-block:: console

    $ pants test ::
    $ pants test tests/manager/test_scheduler.py::
    $ pants test tests/manager/test_scheduler.py:: -- -k test_scheduler_configs
    $ pants test tests/common::            # Run common/**/test_*.py
    $ pants test tests/common:tests        # Run common/test_*.py
    $ pants test tests/common/redis::      # Run common/redis/**/test_*.py
    $ pants test tests/common/redis:tests  # Run common/redis/test_*.py

You may also try ``--changed-since`` option like ``lint`` and ``check``.

To specify extra environment variables for tests, use the ``--test-extra-env-vars``
option:

.. code-block:: console

    $ pants test \
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

    $ pants \
    >   --tag="wheel" \
    >   package \
    >   src/ai/backend/common:dist
    $ ls -l dist/*.whl

If the package content varies by the target platform, use:

.. code-block:: console

    $ pants \
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
This is very useful when you use IDEs and editors.

To (re-)generate the virtualenv(s), run:

.. code-block:: console

    $ pants export --resolve=RESOLVE_NAME  # you may add multiple --resolve options

You may display the available resolve names by (the command works with Python 3.12 or later):

.. code-block:: console

    $ python -c 'import tomllib,pathlib;print("\n".join(tomllib.loads(pathlib.Path("pants.toml").read_text())["python"]["resolves"].keys()))'

Similarly, you can export all virtualenvs at once:

.. code-block:: console

    $ python -c 'import tomllib,pathlib;print("\n".join(tomllib.loads(pathlib.Path("pants.toml").read_text())["python"]["resolves"].keys()))' | sed 's/^/--resolve=/' | xargs pants export

Then configure your IDEs/editors to use
``dist/export/python/virtualenvs/python-default/PYTHON_VERSION/bin/python`` as the
interpreter for your code, where ``PYTHON_VERSION`` is the interpreter version
specified in ``pants.toml``.

As of Pants 2.16, you must export the virtualenvs by the individual lockfiles
using the ``--resolve`` option, as all tools are unified to use the same custom resolve subsystem of Pants and the ``::`` target no longer works properly, like:

.. code-block:: console

    $ pants export --resolve=python-default --resolve=mypy

To make LSP (language server protocol) services like PyLance to detect our source packages correctly,
you should also configure ``PYTHONPATH`` to include the repository root's ``src`` directory and
``plugins/*/`` directories if you have added Backend.AI plugin checkouts.

For linters and formatters, configure the tool executable paths to indicate
``dist/export/python/virtualenvs/RESOLVE_NAME/PYTHON_VERSION/bin/EXECUTABLE``.
For example, ruff's executable path is
``dist/export/python/virtualenvs/ruff/3.12.4/bin/ruff``.

Currently we have the following Python tools to configure in this way:

* ``ruff``: Provides a fast linting (combining pylint, flake8, and isort)
  fixing (auto-fix for some linting rules and isort) and formatting (black)

* ``mypy``: Validates the type annotations and performs a static analysis

  .. tip::

     For a long list of arguments or list/tuple items, you could explicitly add a
     trailing comma to force Ruff/Black to insert line-breaks after every item even when
     the line length does not exceed the limit (100 characters).

  .. tip::

     You may disable auto-formatting on a specific region of code using ``# fmt: off``
     and ``# fmt: on`` comments, though this is strongly discouraged except when
     manual formatting gives better readability, such as numpy matrix declarations.

* ``pytest``: The unit test runner framework.

* ``coverage-py``: Generates reports about which source lines were visited during execution of a pytest session.

* ``towncrier``: Generates the changelog from news fragments in the ``changes`` directory when making a new release.

VSCode
~~~~~~

Install the following extensions:

   * Python (``ms-python.python``)
   * Pylance (``ms-python.vscode-pylance``) (optional but recommended)
   * Mypy (``ms-python.mypy-type-checker``)
   * Ruff (``charliermarsh.ruff``)
   * For other standard Python extensions like Flake8, isort, and Black,
     *disable* them for the Backend.AI workspace only to prevent interference
     with Ruff's own linting, fixing and formatting.

Set the workspace settings for the Python extension for code navigation and auto-completion:

.. list-table::
   :header-rows: 1

   * - Setting ID
     - Recommended value
   * - ``python.analysis.autoSearchPaths``
     - true
   * - ``python.analysis.extraPaths``
     - ``["dist/export/python/virtualenvs/python-default/3.12.4/lib/python3.12/site-packages"]``
   * - ``python.analysis.importFormat``
     - ``"relative"``
   * - ``editor.formatOnSave``
     - ``true``
   * - ``editor.codeActionsOnSave``
     - ``{"source.fixAll": true}``

Set the following keys in the workspace settings to configure Python tools:

.. list-table::
   :header-rows: 1

   * - Setting ID
     - Example value
   * - ``mypy-type-checker.interpreter``
     - ``["dist/export/python/virtualenvs/mypy/3.12.4/bin/python"]``
   * - ``mypy-type-checker.importStrategy``
     - ``"fromEnvironment"``
   * - ``ruff.interpreter``
     - ``["dist/export/python/virtualenvs/ruff/3.12.4/bin/python"]``
   * - ``ruff.importStrategy``
     - ``"fromEnvironment"``

.. note:: **Changed in July 2023**

   After applying `the VSCode Python Tool migration <https://github.com/microsoft/vscode-python/wiki/Migration-to-Python-Tools-Extensions>`_,
   we no longer recommend to configure ``python.linting.*Path`` and ``python.formatting.*Path`` keys.

Vim/NeoVim
~~~~~~~~~~

There are a large variety of plugins and usually heavy Vimmers should know what to do.

We recommend using `ALE <https://github.com/dense-analysis/ale>`_ or
`CoC <https://github.com/neoclide/coc.nvim>`_ plugins to have automatic lint highlights,
auto-formatting on save, and auto-completion support with code navigation via LSP backends.

.. warning::

   Note that it is recommended to enable only one linter/formatter at a time (either ALE or CoC)
   with proper configurations, to avoid duplicate suggestions and error reports.

When using ALE, it is recommended to have a directory-local vimrc as follows.
First, add ``set exrc`` in your user-level vimrc.
Then put the followings in ``.vimrc`` (or ``.nvimrc`` for NeoVim) in the build root directory:

.. code-block:: vim

   let s:cwd = getcwd()
   let g:ale_python_mypy_executable = s:cwd . '/dist/export/python/virtualenvs/mypy/3.12.4/bin/mypy'
   let g:ale_python_ruff_executable = s:cwd . '/dist/export/python/virtualenvs/ruff/3.12.4/bin/ruff'
   let g:ale_linters = { "python": ['ruff', 'mypy'] }
   let g:ale_fixers = {'python': ['ruff']}
   let g:ale_fix_on_save = 1

When using CoC, run ``:CocInstall coc-pyright @yaegassy/coc-ruff`` and ``:CocLocalConfig`` after opening a file
in the local working copy to initialize Pyright functionalities.
In the local configuration file (``.vim/coc-settings.json``), you may put the linter/formatter configurations
just like VSCode (see `the official reference <https://www.npmjs.com/package/coc-pyright>`_).

.. code-block:: json

   {
     "coc.preferences.formatOnType": false,
     "coc.preferences.willSaveHandlerTimeout": 5000,
     "ruff.enabled": true,
     "ruff.autoFixOnSave": true,
     "ruff.useDetectRuffCommand": false,
     "ruff.builtin.pythonPath": "dist/export/python/virtualenvs/ruff/3.12.4/bin/python",
     "ruff.serverPath": "dist/export/python/virtualenvs/ruff/3.12.4/bin/ruff-lsp",
     "python.pythonPath": "dist/export/python/virtualenvs/python-default/3.12.4/bin/python",
     "python.linting.mypyEnabled": true,
     "python.linting.mypyPath": "dist/export/python/virtualenvs/mypy/3.12.4/bin/mypy",
   }

To activate Ruff (a Python linter and fixer), run ``:CocCommand ruff.builtin.installServer``
after opening any Python source file to install the ``ruff-lsp`` server.

Switching between branches
~~~~~~~~~~~~~~~~~~~~~~~~~~

When each branch has different external package requirements, you should run ``pants export``
before running codes after ``git switch``-ing between such branches.

Sometimes, you may experience bogus "glob" warning from pants because it sees a stale cache.
In that case, run ``pgrep pantsd | xargs kill`` and it will be fine.

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
  single run of ``pants test``.

.. warning::

  If you *interrupt* (Ctrl+C, SIGINT) a run of ``pants test``, it will
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

     $ pyenv virtualenv 3.10.9 venv-bai-docs

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

     $ pants generate-lockfiles
     $ pants export

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
   $ pants generate-lockfiles --resolve=python-default
   $ git add python.lock
   $ git commit

Resetting Pants
~~~~~~~~~~~~~~~

If Pants behaves strangely, you could simply reset all its runtime-generated files by:

.. code-block:: console

   $ pgrep pantsd | xargs -r kill
   $ rm -r /tmp/*-pants/ .pants.d .pids ~/.cache/pants

After this, re-running any Pants command will automatically reinitialize itself and
all cached data as necessary.

Note that you may find out the concrete path inside ``/tmp`` from ``.pants.rc``'s
``local_execution_root_dir`` option set by ``install-dev.sh``.

.. warning::

   If you have run ``pants`` or the installation script with ``sudo``, some of the above directories
   may be owned by root and running ``pants`` as the user privilege would not work.
   In such cases, remove the directories with ``sudo`` and retry.

Resolve the error message 'Pants is not abailable for your platform', When installing Backend.AI with pants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When installing Backend.AI, you may find the following error message saying 'Pants is not available for your platform' if you have installed Pants 2.17 or older with prior versions of Backend.AI.

.. code-block:: text

   [INFO] Bootstrapping the Pants build system...
   Pants system command is already installed.
   Failed to fetch https://binaries.pantsbuild.org/tags/pantsbuild.pants/release_2.19.0: [22] HTTP response code said error (The requested URL returned error: 404)
   Bootstrapping Pants 2.19.0 using cpython 3.9.15
   Installing pantsbuild.pants==2.19.0 into a virtual environment at /home/aaa/.cache/nce/bad1ad5b44f41a6ca9c99a135f9af8849a3b93ec5a018c7b2d13acaf0a969e3a/bindings/venvs/2.19.0
       ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 65.4/65.4 KB 3.3 MB/s eta 0:00:00
   ERROR: Could not find a version that satisfies the requirement pantsbuild.pants==2.19.0 (from versions: 0.0.17, 0.0.18, 0.0.20, 0.0.21, 0.0.22, ... (a long list of versions) ..., 2.17.0,
   2.17.1rc0, 2.17.1rc1, 2.17.1rc2, 2.17.1rc3, 2.17.1, 2.18.0.dev0, 2.18.0.dev1, 2.18.0.dev3, 2.18.0.dev4, 2.18.0.dev5, 2.18.0.dev6, 2.18.0.dev7, 2.18.0a0)
   ERROR: No matching distribution found for pantsbuild.pants==2.19.0
   Install failed: Command '['/home/aaa/.cache/nce/bad1ad5b44f41a6ca9c99a135f9af8849a3b93ec5a018c7b2d13acaf0a969e3a/bindings/venvs/2.19.0/bin/python', '-sE', '-m', 'pip', '--disable-pip-versi
   on-check', '--no-python-version-warning', '--log', PosixPath('/home/aaa/.cache/nce/bad1ad5b44f41a6ca9c99a135f9af8849a3b93ec5a018c7b2d13acaf0a969e3a/bindings/venvs/2.19.0/pants-install.log'
   ), 'install', '--quiet', '--find-links', 'file:///home/aaa/.cache/nce/bad1ad5b44f41a6ca9c99a135f9af8849a3b93ec5a018c7b2d13acaf0a969e3a/bindings/find_links/2.19.0/e430175b/index.html', '--p
   rogress-bar', 'off', 'pantsbuild.pants==2.19.0']' returned non-zero exit status 1.
   More information can be found in the log at: /home/aaa/.cache/nce/bad1ad5b44f41a6ca9c99a135f9af8849a3b93ec5a018c7b2d13acaf0a969e3a/bindings/logs/install.log

   Error: Isolates your Pants from the elements.

   Please select from the following boot commands:

   <default>: Detects the current Pants installation and launches it.
   bootstrap-tools: Introspection tools for the Pants bootstrap process.
   pants: Runs a hermetic Pants installation.
   pants-debug: Runs a hermetic Pants installation with a debug server for debugging Pants code.
   update: Update scie-pants.

   You can select a boot command by passing it as the 1st argument or else by setting the SCIE_BOOT environment variable.

   ERROR: Failed to establish atomic directory /home/aaa/.cache/nce/bad1ad5b44f41a6ca9c99a135f9af8849a3b93ec5a018c7b2d13acaf0a969e3a/locks/install-a4f15e2d2c97473883ec33b4ee0f9d11f99dcf5bee63
   8b1cc7a0270d55d0ec8d. Population of work directory failed: Boot binding command failed: exit status: 1

   [ERROR] Cannot proceed the installation because Pants is not available for your platform!

To resolve this error, `reinstall or upgrade Pants <https://www.pantsbuild.org/2.19/docs/getting-started/installing-pants>`_.
As of the Pants 2.18.0 release, they no longer use the Python Package Index but GitHub releases to distribute the binary builds.


Resolving missing directories error when running Pants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   ValueError: Failed to create temporary directory for immutable inputs: No such file or directory (os error 2) at path "/tmp/bai-dev-PN4fpRLB2u2xL.j6-pants/immutable_inputsvIpaoN"

If you encounter errors like above when running daily Pants commands like ``lint``,
you may manually create the directory one step higher.
For the above example, run:

.. code-block:: shell

   mkdir -p /tmp/bai-dev-PN4fpRLB2u2xL.j6-pants/

If this workaround does not work, backup your current working files and
reinstall by running ``scripts/delete-dev.sh`` and ``scripts/install-dev.sh``
serially.

Changing or updating the Python runtime for Pants
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you run ``scripts/install-dev.sh``, it automatically creates ``.pants.bootstrap``
to explicitly set a specific pyenv Python version to run Pants.

If you have removed/upgraded this specific Python version from pyenv, you also need to
update ``.pants.bootstrap`` accordingly.

.. _debugging-tests:

Debugging test cases (or interactively running test cases)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When your tests *hang*, you can try adding the ``--debug`` flag to the ``pants test`` command:

.. code-block:: console

   $ pants test --debug ...

so that Pants runs the designated test targets **serially and interactively**.
This means that you can directly observe the console output and Ctrl+C to
gracefully shutdown the tests  with fixture cleanup. You can also apply
additional pytest options such as ``--fulltrace``, ``-s``, etc. by passing them
after target arguments and ``--`` when executing ``pants test`` command.

Installing a subset of mono-repo packages in the editable mode for other projects
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, you need to editable-install a subset of packages into other project's directories.
For instance you could mount the client SDK and its internal dependencies for a Docker container for development.

In this case, we recommend to do it as follows:

1. Run the following command to build a wheel from the current mono-repo source:

   .. code-block:: console

      $ pants --tag=wheel package src/ai/backend/client:dist

   This will generate ``dist/backend.ai_client-{VERSION}-py3-none-any.whl``.

2. Run ``pip install -U {MONOREPO_PATH}/dist/{WHEEL_FILE}`` in the target environment.

   This will populate the package metadata and install its external dependencies.
   The target environment may be one of a separate virtualenv or a container being built.
   For container builds, you need to first ``COPY`` the wheel file and install it.

3. Check the internal dependency directories to link by running the following command:

   .. code-block:: console

      $ pants dependencies --transitive src/ai/backend/client:src \
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
  (Running ``pants test ::`` consumes about 2GB.)

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
    actually modifying the filesystem.

  - (WIP: `lablup/backend.ai#427 <https://github.com/lablup/backend.ai/pull/427>`_).

* Make a new git commit with the commit message: "release: <version>".

* Make an annotated tag to the commit with the message: "Release v<version>"
  or "Pre-release v<version>" depending on the release version.

* Push the commit and tag.  The GitHub Actions workflow will build the packages
  and publish them to PyPI.

* When making a new major release, snapshot of prior release's final DB migration history
  should be dumped. This will later help to fill out missing gaps of DB revisions when
  upgrading outdated cluster. The output then should be committed to **next** major release.

  .. code-block:: console

      $ ./backend.ai mgr schema dump-history > src/ai/backend/manager/models/alembic/revision_history/<version>.json

  Suppose you are trying to create both fresh baked 24.09.0 and good old 24.03.10 releases.
  In such cases you should first make a release of version 24.03.10, move back to latest branch, and then
  execute code snippet above with `<version>` set as `24.03.10`, and release 24.09.0 including the dump.

  To make workflow above effective, be aware that backporting DB revisions to older major releases will no longer
  be permitted after major release version is switched.

Making a new release branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example shows the case when the current release is 24.03 and the next upcoming release is 24.09.
It makes the main branch to stand for the upcoming release 24.09, by branching out the current release 24.03.

* Make a new git branch for the current release in the ``YY.MM`` format (like ``24.03``) from the main branch.

* Update ``./VERSION`` file to indicate the next development version (like ``24.09.0dev0``).

* Create a new halfstack compose configuration for the next release by copying and updating the halfstack config of the current release.

  .. code-block:: console

     $ cp docker-compose.halfstack-2403.yml docker-compose.halfstack-2409.yml
     $ edit docker-compose.halfstack-2409.yml  # update the container versions
     $ rm docker-compose.halfstack-main.yml
     $ ln -s docker-compose.halfstack-2409.yml docker-compose.halfstack-main.yml
     $ git add docker-compose.*.yml

Backporting to legacy per-pkg repositories
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Use ``git diff`` and ``git apply`` instead of ``git cherry-pick``.

  - To perform a three-way merge for conflicts, add ``-3`` option to the ``git apply`` command.

  - You may need to rewrite some codes as the package structure differs. (The
    new mono repository has more fine-grained first party packages divided from
    the ``backend.ai-common`` package.)

* When referring the PR/issue numbers in the commit for per-pkg repositories,
  update them like ``lablup/backend.ai#NNN`` instead of ``#NNN``.

Writing down new REST API
~~~~~~~~~~~~~~~~~~~~~~~~~

Be advised that starting from 24.03, every new and updated REST APIs should adapt pydantic as its request and response validator. For starters our `service` API implementations can be a good boilerplate.

.. note::
   Do not adapt legacy trafaret-based approach for fresh new REST APIs! This approach is deprecated.

Use ``ai.backend.manager.api.utils.pydantic_response_api_handler()``` as a function decorator for API handlers without request body or queryparam to consume. Otherwise adapt ``ai.backend.manager.utils.pydantic_params_api_handler()``.
Every response data model should inherit ``ai.backend.manager.api.utils.BaseResponseModel`` as its parent class. To use arbitrary HTTP response status code other than 200, fill in ``status`` value of ``BaseResponseModel``.

Here are some examples:

* `list_serve() <https://github.com/lablup/backend.ai/blob/main/src/ai/backend/manager/api/service.py#L147-L152>`_
* `get_info() <https://github.com/lablup/backend.ai/blob/main/src/ai/backend/manager/api/service.py#L221-L224>`_
