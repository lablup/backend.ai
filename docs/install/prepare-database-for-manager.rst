.. role:: raw-html-m2r(raw)
   :format: html

Prepare Database for Manager
============================


Guide variables
---------------

⚠️ Prepare the values of the following variables before working with this page and replace their occurrences with the values when you follow the guide.



.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - Name
     - Description
   * - ``{NS}``
     - The etcd namespace
   * - ``{ETCDADDR}``
     - The etcd cluster address (``{ETCDHOST}``:``{ETCDPORT}``, ``localhost:8120`` for development setup)
   * - ``{DBADDR}``
     - The PostgreSQL server address (``{DBHOST}``:``{DBPORT}``, ``localhost:8100`` for development setup)
   * - ``{DBUSER}``
     - The database username (e.g., ``postgres`` for development setup)
   * - ``{DBPASS}``
     - The database password (e.g., ``develove`` for development setup)
   * - ``{STRGMOUNT}``
     - The path to a directory that the manager and all agents share together (e.g., a network-shared storage mountpoint). Note that the path must be same across all the nodes that run the manager and agents.
       
       Development setup: Use an arbitrary empty directory where Docker containers can also mount as volumes — e.g., `Docker for Mac requires explicit configuration for mountable parent folders. <https://docs.docker.com/docker-for-mac/#file-sharing>`_


.. image:: https://asciinema.org/a/8vM2cEHEHQzCMaOummV4ruDAm.png
   :target: https://asciinema.org/a/8vM2cEHEHQzCMaOummV4ruDAm
   :alt: asciicast

Database Setup
--------------

Create a new database
^^^^^^^^^^^^^^^^^^^^^

In docker-compose based configurations, you may skip this step.

.. code-block:: console

   $ psql -h {DBHOST} -p {DBPORT} -U {DBUSER}

.. code-block:: console

   postgres=# CREATE DATABASE backend;
   postgres=# \q

Install database schema
^^^^^^^^^^^^^^^^^^^^^^^

Backend.AI uses `alembic <http://alembic.zzzcomputing.com/en/latest/>`_ to manage database schema and its migration during version upgrades.
First, localize the sample config:

.. code-block:: console

   $ cp alembic.ini.sample alembic.ini

Modify the line where ``sqlalchemy.url`` is set.
You may use the following shell command:
(ensure that special characters in your password are properly escaped)

.. code-block:: console

   $ sed -i'' -e 's!^sqlalchemy.url = .*$!sqlalchemy.url = postgresql://{DBUSER}:{DBPASS}@{DBHOST}:{DBPORT}/backend!' alembic.ini

.. code-block:: console

   $ ./backend.ai mgr schema oneshot

example execution result

.. code-block:: console

   201x-xx-xx xx:xx:xx INFO alembic.runtime.migration [MainProcess] Context impl PostgresqlImpl.
   201x-xx-xx xx:xx:xx INFO alembic.runtime.migration [MainProcess] Will assume transactional DDL.
   201x-xx-xx xx:xx:xx INFO ai.backend.manager.cli.dbschema [MainProcess] Detected a fresh new database.
   201x-xx-xx xx:xx:xx INFO ai.backend.manager.cli.dbschema [MainProcess] Creating tables...
   201x-xx-xx xx:xx:xx INFO ai.backend.manager.cli.dbschema [MainProcess] Stamping alembic version to head...
   INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
   INFO  [alembic.runtime.migration] Will assume transactional DDL.
   INFO  [alembic.runtime.migration] Running stamp_revision  -> f9971fbb34d9

NOTE: All sub-commands under "schema" uses alembic.ini to establish database connections.

Load initial fixtures
^^^^^^^^^^^^^^^^^^^^^

The file ``fixtures/manager/example-keypairs.json`` , is example of admin keypair json file.
If you want to change a randomized admin keypair, copy the ``fixtures/manager/example-keypairs.json`` to create and modify the ``example_keypair.json`` .
so that you can edit & apply admin keypair using ``example_keypair.json`` file.

Database information is located on ``manager.toml`` file.

Then pour it to the database:

.. code-block:: console

   $ ./backend.ai mgr fixture populate \
   >   fixture populate example_keypair.json

example execution result

.. code-block:: console

   202x-xx-xx xx:xx:xx INFO ai.backend.manager.cli.fixture [MainProcess] Populating fixture 'example_keypair' ...
   202x-xx-xx xx:xx:xx INFO ai.backend.manager.cli.fixture [MainProcess] Done
