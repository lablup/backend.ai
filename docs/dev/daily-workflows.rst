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

* Goal: an action to execute

  - You may think this as the root node of the task graph executed by Pants.

* Target: objectives for the action, usually expressed as ``path/to/dir:name``

  - The targets are declared/defined by ``path/to/dir/BUILD`` files.

* The global configuration is at ``pants.toml``.

Inspecting build configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

   If your ``scripts/install-dev.sh`` says that you need to use
   ``./pants-local`` instead of ``./pants``, replace all ``./pants``
   in the following command examples with ``./pants-local``.

* See all targets

  .. code-block:: console

     $ ./pants list ::

  - This list includes the full enumeration of individual targets auto-generated
    by collective targets (e.g., ``python_sources()`` generates multiple
    ``python_source()`` targets by globbing the ``sources`` pattern)

* See all dependencies of a specific target (i.e., all targets required to
  build this target)

  .. code-block:: console

     $ ./pants dependencies --transitive src/ai/backend/common:lib

* See all dependees of a specific target (i.e., all targets affected when
  this target is changed)

  .. code-block:: console

     $ ./pants dependees --transitive src/ai/backend/common:lib

Running lint and check
----------------------

Run lint/check for all targets:

.. code-block:: console

   $ ./pants lint ::
   $ ./pants check ::

To run lint/check for a specific project:

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

Running unit tests
------------------

Here are various methods to run tests:

.. code-block:: console

    $ ./pants test ::
    $ ./pants test tests/manager/test_scheduler.py::
    $ ./pants test tests/manager/test_scheduler.py:: -- -k test_scheduler_configs

You may also try ``--changed-since`` option like ``lint`` and ``check``.

Running integration tests
-------------------------

.. code-block:: console

    $ ./backend.ai test run-cli user,admin


Building wheel packages
-----------------------

To build a specific package:

.. code-block:: console

    $ ./pants package src/ai/backend/common:dist

To specify extra environment variables for tests:

.. code-block:: console

    $ ./pants test \
    >   --test-extra-env-vars=BACKEND_ETCD_ADDR=localhost:8121 \
    >   tests/common:tests

Adding new external dependencies
--------------------------------

* Add the version requirements to ``./requirements.txt``.

* Run:

  .. code-block:: console

     $ ./pants generate-lockfiles

Using IDEs and editors
----------------------

To use an IDE/VSCode/etc. with a unified virtual environment, ``./pants export ::`` and configure your editors to use ``dist/export/python/virtualenvs/python-default``.

    - If you encounter errors like the following, set the Python version explicitly using `PY` environment variable by copy-and-pasting `./pants` to `./pants-local` and editing `./pants-local` to have `export PY=$(pyenv prefix 3.10.4)/bin/python`

    .. code-block:: text

        pex.environment.ResolveError: A distribution for pyyaml could not be resolved in this environment.Found 1 distribution for pyyaml that do not apply:
        1.) The wheel tags for PyYAML 5.4.1 are cp310-cp310-linux_aarch64 which do not match the supported tags of /usr/bin/python3.8:

    - To activate flake8/mypy checks (in Vim) and get proper intelli-sense support for pytest (in VSCode), just install them in the exported venv as follows. (You need to repeat this when you re-export!)
    ``./py -m pip install flake8 mypy pytest``

        - For Vim, you also need to explicitly activate the exported venv.

### Writing test cases for Pants

- Mostly it is just same as before: use the standard pytest practices.
- The key differences
    - Tests are executed ***in parallel*** in the unit of test modules.
    - Therefore, session-level fixtures may be executed *multiple* times during a single run of `./pants test`.

    <aside>
    ⚠️ If you *interrupt* (Ctrl+C, SIGINT) a run of `./pants test`, it will immediately kill all pytest processes without fixture cleanup. This may accumulate unused Docker containers in your system, so it is a good practice to run `docker ps -a` periodically.

    </aside>

- Writing Pants-friendly tests
    - Ensure that it runs in an isolated/mocked environment and minimize external dependency.
    - If required, use the environment variable `BACKEND_TEST_EXEC_SLOT` (an integer value) to uniquely define TCP port numbers and other resource identifiers to allow parallel execution.
    (ref: [https://www.pantsbuild.org/docs/reference-pytest#section-execution-slot-var](https://www.pantsbuild.org/docs/reference-pytest#section-execution-slot-var))
    - Use `ai.backend.testutils.bootstrap` to use a single-node Redis/etcd/Postgres container in test cases. Import the fixture and use it like a plain pytest fixture.
        - These fixtures create those containers with **OS-assigned public port numbers** and give you a tuple of container ID and a `ai.backend.common.types.HostPortPair` for use in test codes. In manager and agent tests, you could just refer `local_config` to get a pre-populated local configurations with those port numbers.
        - In this case, you may encounter `flake8` complaining about unused imports and redefinition. Use `# noqa: F401` and `# noqa: F811` respectively for now.
- Debugging tests
    - When your tests *hang*, you can try `./pants test --debug ...` so that Pants runs the designated test targets ***serially and interactively***. This means that you can directly observe the console output and Ctrl+C to gracefully shutdown the tests  with fixture cleanup. You can also apply additional pytest options such as `--fulltrace`, `-s`, etc. by passing them after target arguments and `--` when executing `./pants test` command.
- Mounting `/tmp` directories to a container
    - If your Docker service is installed using **Snap** (e.g., Ubuntu), it cannot access the system `/tmp` directory because Snap applies a private tmp directory to the Docker service. You should use other locations to avoid mount failures for the developers/users in such platforms.

Tips
----

- To boost the performance of pants, you could make the `.tmp` directory under the repository root a tmpfs partition:
`sudo mount -t tmpfs -o size=4G tmpfs .tmp`
    - To make this persistent across reboots, add the following line to `/etc/fstab`:
    `tmpfs /path/to/dir/.tmp tmpfs defaults,size=4G 0 0`
    - The size should be at least 2G but more than 3G is recommended.
    (Running `./pants test ::` consumes about 2GB.)
    - To change the size, you could simply remount it with a new size option:
    `sudo mount -t tmpfs -o remount,size=8G tmpfs .tmp`

Backporting to legacy per-pkg repositories
------------------------------------------

- Use `git diff` and `git apply` instead of `git cherry-pick`.
    - To perform a three-way merge for conflicts, add `-3` option to the `git apply` command.
- When referring the PR/issue numbers in the commit for per-pkg repositories, update them like `lablup/backend.ai#NNN` instead of `#NNN`.
