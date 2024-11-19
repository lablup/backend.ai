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
  * All fixes must be *first* implemented on the ``main`` branch and then *cherry-picked* back to ``x.y`` branches.

    * When cherry-picking, use the ``-e`` option to edit the commit message.\ :raw-html-m2r:`<br>`
      Append ``Backported-From: main`` and ``Backported-To: X.Y`` lines after one blank line at the end of the existing commit message.

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

Backend.AI uses a PostgreSQL database, an etcd cluster, and a Redis service as containers for its operation.
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
      Redis is also same; its version is now pinned to v7.2 release and we expect only patch releases in the foreseeable future.

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
      cp ./docker-compose.halfstack-${TARGET_VERSION}.yml ${COMPOSE_FILE}
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
