.. role:: raw-html-m2r(raw)
   :format: html

.. include:: <isonum.txt>

Version Numbering
=================

* Version numbering uses ``x.y.z`` format (where ``x``\ , ``y``\ , ``z`` are integers).
* Mostly, we follow `the calendar versioning scheme <https://calver.org/>`_.
* ``x.y`` is a release branch name (major releases per 6 months).

  * When ``y`` is smaller than 10, we prepend a zero sign like ``05`` in the version numbers (e.g., ``20.09.0``).
  * When referring the version in other Python packages as requirements, you need to strip the leading zeros (e.g., ``20.9.0`` instead of ``20.09.0``) because Python setuptools normalizes the version integers.

* ``x.y.z`` is a release tag name (patch releases).
* When releasing ``x.y.0``:

  * Create a new ``x.y`` branch, do all bugfix/hotfix there, and make ``x.y.z`` releases there.
  * Register ``x.y`` in ``.github/maintained-versions.yml`` so that it starts receiving backports.
  * All fixes must be *first* implemented on the ``main`` branch and then *cherry-picked* back to ``x.y`` branches.

    * The cherry-pick is automated.  See `Backporting`_ below.

  * Change the version number of ``main`` to ``x.(y+1).0.dev0``
  * There is no strict rules about alpha/beta/rc builds yet. We will elaborate as we scale up.\ :raw-html-m2r:`<br>`
    Once used, alpha versions will have ``aN`` suffixes, beta versions ``bN`` suffixes, and RC versions ``rcN`` suffixes where ``N`` is an integer.

* New development should go on the ``main`` branch.

  * ``main``: commit here directly if your changes are a self-complete one as a single commit.
  * Use both short-lived and long-running feature branches freely, but ensure there names differ from release branches and tags.

* The major/minor (\ ``x.y``\ ) version of Backend.AI subprojects will go together to indicate compatibility.  Currently manager/agent/common versions progress this way, while client SDKs have their own version numbers and the API specification has a different ``vN.yyyymmdd`` version format.

  * Generally ``backend.ai-manager 1.2.p`` is compatible with ``backend.ai-agent 1.2.q`` (where ``p`` and ``q`` are same or different integers)

    * As of 22.09, this won't be guaranteed anymore.  All server-side core component versions should **exactly match** with others, as we release them at once from the mono-repo, even for those who do not have any code changes.

  * The client is guaranteed to be backward-compatible with the server they share the same API specification version.


Backporting
===========

Every change lands on ``main`` first.
When it is merged, the ``backport`` workflow cherry-picks it to each target
release branch and opens a backport pull request there, so backporting is not
a manual step.

Maintained versions
-------------------

``.github/maintained-versions.yml`` is the single source of truth for the
release branches that are still maintained.

.. code-block:: yaml

   versions:
     - version: "26.8"
     - version: "26.4"
       lts: true

Every entry must have a release branch of the same name.
A version that is not listed here receives no backport at all, so removing a
version from the list is how a release goes out of maintenance.

``lts`` marks a long-term support line, and is left out otherwise.
Besides the backport targets below, the release workflow reads the file to
point the installer download links at a release: the newest maintained version
drives the ``edge`` link, and the newest LTS one the ``stable`` link that
``scripts/install.sh`` follows.

Entries come and go with the release lines. ``scripts/release.sh`` calls
``.github/scripts/update-maintained-versions.sh`` on every release, which
registers a line only when the target is the ``X.Y.0rc1`` that cuts it, so no
release has to be classified by hand.  Whether the line is LTS is the one thing
that cannot be read off the version, and is given explicitly:

.. code-block:: console

   $ scripts/release.sh --lts 26.9.0rc1

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Line
     - Retired
   * - LTS
     - Once ``retire_after`` has passed.  Registering an LTS line records the end
       of the same month one year on, counted from the rc that cuts it; correct
       the date by hand if the rc period ran long.
   * - regular
     - As soon as any newer line is registered, LTS or not.  A regular line
       exists to get new features out quickly, so it lives only while it is the
       newest line there is.

Whether a line is LTS is a support commitment and is given on the command line,
never inferred.

How the targets are decided
---------------------------

The backport targets of a merged pull request come from its title prefix, its
description and its labels.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Signal
     - Targets
   * - ``Backport:`` trailer
     - Exactly the versions it names, whatever the prefix would have chosen.
       ``Backport: none`` means no target at all.
   * - ``fix:`` title prefix, with no trailer
     - Every version in ``.github/maintained-versions.yml``.
   * - any other title prefix, with no trailer
     - None.

The prefix picks the default and the trailer replaces it, so one line in the
description covers every case: a ``feat:`` that has to reach a release branch, a
``fix:`` that applies to only some of them, and a ``fix:`` that must not be
backported at all.

.. code-block:: text

   Backport: 26.8, 26.4

The versions may be separated by commas or spaces.
A trailer that names a version outside the registry backports nothing and fails
the job with a comment on the pull request, rather than quietly dropping that
target; comment ``/backport <version>`` once the line is right.

Requesting a backport after the merge
-------------------------------------

If a target turns out to be missing after the pull request is merged, comment
on it:

.. code-block:: text

   /backport 26.4

The comment is accepted from the repository owners, members and collaborators,
and only on a merged pull request.
Any other case is answered with a comment stating the reason.

The backport pull request
-------------------------

The generated pull request keeps the original title, so its ``(#N)`` suffix
stays as the link back to the pull request the change came from, and it is set
to auto-merge.
When the cherry-pick conflicts the workflow stops and leaves a comment on the
original pull request: the conflict is resolved by hand rather than by
overwriting the release branch.


Upgrading
=========

Local packages
--------------

.. note::

   Before doing branch switches or package upgrades, stop all Backend.AI services first.
   For most minor upgrades, you may keep the session containers running, but whenever possible, it is strongly recommended to terminate them first.
   When there are changes in the agent and kernel runner, it may break up the running containers.

   For specific configurations or advanced setups, refer to the version-specific upgrade guide or contact the support.

Development Setup
~~~~~~~~~~~~~~~~~

It is advised to clone a new working copy and perform a clean install to work on a different *release* branch.
You may keep multiple clones by stopping and starting compose stacks for each working copy for testing.

The following guide is for switching *topic* branches.
Again, if the target topic branch involves complex database/configuration migration, it is better to make a new clone with a clean install.
To save the GitHub bandwidth, consider local filesystem clones like ``git clone /path/to/existing/copy /path/to/new/copy`` or minimizing the fetch depth like ``git clone --depth=10 https://github.com/lablup/backend.ai bai-topic``.

1. Run ``./py -m alembic downgrade -N`` if the current topic branch has *N* database migrations.
   For example, if it has only one migration, say ``-1``.
   You may check the ``require:db-migration`` label in the GitHub PR to see if the branch has database migrations.

2. Switch to the target topic branch using ``git switch``.

3. Run ``pants export --resolve=python-default --resolve=python-kernel --resolve=mypy --resolve=ruff`` to repopulate the virtualenvs for local execution.
   This resolve arguments are the minimum-required sets for editor/IDE configuration.

4. Run ``./py -m alembic upgrade head`` if the new topic branch has database migrations.

5. Check if there are any additional TOML and etcd configuration updates required.

Package Setup
~~~~~~~~~~~~~

If you want to perform a release upgrade (e.g., 23.09 |rarr| 24.03), please consult the specific version's upgrade guides.

For a minor patch update, follow the steps:

1. Upgrade the Backend.AI wheel packages in the virtualenv.

2. Run ``alembic upgrade head`` in the virtualenv.

3. Check if there are TOML and etcd configuration updates required.


Halfstack Containers
--------------------

Backend.AI uses a PostgreSQL database, an etcd cluster, and a Valkey (Redis-compatible) service as containers for its operation.
We call this set of containers as *"halfstack"*.
When making a new major release of Backend.AI or to address upstream issues, we update the versions of halfstack containers.

A development setup or an all-in-one package setup uses a docker-compose stack, which can be upgraded relatively easily in-place.
Still, it is advised to do a clean install on a new clone for new major releases.

First, review your current configuration variables used in this guide.
A typical development setup uses the following values:

- ``${COMPOSE_PROJECT_NAME}``: the name of directory where ``scripts/install-dev.sh`` resides in.
- ``${COMPOSE_FILE}``: ``docker-compose.halfstack.current.yml``
- ``${DB_SERVICE_NAME}``: ``backendai-half-db``
- ``${DB_USER}``: ``postgres``
- ``${DB_NAME}``: ``backend``
- ``${DB_BACKUP_FILE}``: set as you want (e.g., ``./db-backup.sql``)
- ``${POSTGRES_DATA_DIR}``: ``volumes/postgres-data``

Here is the step-by-step guide to upgrade the halfstack containers.

1. Terminate all existing sessions and stop all Backend.AI services first.

2. Backup the current PostgreSQL database content:

   .. code-block:: shell

      docker compose -p ${COMPOSE_PROJECT_NAME} -f ${COMPOSE_FILE} exec -T ${DB_SERVICE_NAME} pg_dump -U ${DB_USER} ${DB_NAME} > ${DB_BACKUP_FILE}

   .. note::

      Currently, etcd is staying at the v3.5 release for multiple years and it is not anticipated to see its major upgrade in the foreseeable future.
      When it happens, refer to the official upgrade document like https://etcd.io/docs/v3.5/upgrades/upgrade_3_5/.
      Valkey is also same; its version is now pinned to the v9.1 release and we expect only patch releases in the foreseeable future.

      You may *skip* the PostgreSQL-related steps if the postgres' major version did not change in the target verion's compose configuration.
      In that case, you may just do the step 3, 5, 6, and 8 only.

3. Stop all halfstack containers:

   .. code-block:: shell

      docker compose -p ${DOCKER_PROJECT_NAME} -f ${COMPOSE_FILE} down

4. Delete the PostgreSQL database volume with an additional volume backup for the emergency like when the new postgres container cannot read the dump file.
   If that happens, you could mount the copied directory to a postgres container pinned to the previous version to access the data.

   .. code-block:: shell

      # sudo required as postgres runs as the non-user uid
      sudo cp -Rp ${POSTGRES_DATA_DIR} ./postgres-volume-backup
      sudo rm -rf ${POSTGRES_DATA_DIR}

   .. warning::

      This step will *delete* all Backend.AI database!
      Make sure all backups are verified for integrity before starting the upgrade process.
      Verify your command twice before running.

5. Overwrite the *current* halfstack compose configuration.
   The target version depends on your choice, usually in the form of ``yymm`` like ``2309`` or ``2403``.
   You may also create a new configuration with updated halfstack container versions.

   .. code-block:: shell

      # save the port numbers
      MY_DB_PORT=$(yq -r '.services.backendai-half-db.ports[0]' docker-compose.halfstack.current.yml|cut -d: -f1)
      MY_REDIS_PORT=$(yq -r '.services.backendai-half-redis.ports[0]' docker-compose.halfstack.current.yml|cut -d: -f1)
      MY_ETCD_PORT=$(yq -r '.services.backendai-half-etcd.ports[0]' docker-compose.halfstack.current.yml|cut -d: -f1)
      # overwrite the compose config
      cp ./docker-compose.halfstack-main.yml ${COMPOSE_FILE}
      # restore the port numbers
      yq eval --inplace '.services.backendai-half-db.ports[0] = "'$MY_DB_PORT':5432"' docker-compose.halfstack.current.yml
      yq eval --inplace '.services.backendai-half-redis.ports[0] = "'$MY_REDIS_PORT':6379"' docker-compose.halfstack.current.yml
      yq eval --inplace '.services.backendai-half-etcd.ports[0] = "'$MY_ETCD_PORT':2379"' docker-compose.halfstack.current.yml

   .. tip::

      Install the ``yq`` utility to read and manipulate the YAML files easily on the shell.
      Refer to https://mikefarah.gitbook.io/yq.

6. Start the halfstack with the new compose configuration:

   .. code-block:: shell

      docker compose -p ${COMPOSE_PROJECT_NAME} -f ${COMPOSE_FILE} up -d

7. Restore the PostgreSQL database content:

   .. code-block:: shell

      docker compose -p ${COMPOSE_PROJECT_NAME} -f ${COMPOSE_FILE} exec -T ${DB_SERVICE_NAME} psql -U ${DB_USER} -d ${DB_NAME} < ${DB_BACKUP_FILE}

8. Start the Backend.AI services and test.
   If it successfully runs, remove the volume backup directory so that ``pants`` does not get confused with unreadable directories due to the different uid ownership.

   .. code-block:: shell

      sudo rm -rf ./postgres-volume-backup  # if copied in the step 4
      rm ${DB_BACKUP_FILE}
