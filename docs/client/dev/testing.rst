Testing
=======

Unit Tests
----------

Unit tests perform function-by-function tests to ensure their individual
functionality.  This test suite runs without depending on the server-side
and thus it is executed in Travis CI for every push.

How to run
~~~~~~~~~~

.. code-block:: console

   $ python -m pytest -m 'not integration' tests


Integration Tests
-----------------

Integration tests combine multiple invocations of high-level interfaces to make underlying API requests
to a running gateway server to test the full functionality of the client as well as the manager.

They are marked as "integration" using the ``@pytest.mark.integration`` decorator
to each test case.

.. warning::

   The integration tests actually make changes to the target gateway server and agents.
   If some tests fail, those changes may remain in an inconsistent state and requires a manual recovery
   such as resetting the database and populating fixtures again, though the test suite tries to clean
   up them properly.

   So, DO NOT RUN it against your production server.

Prerequisite
~~~~~~~~~~~~

Please refer the README of the manager and agent repositories to set up them.
To avoid an indefinite waiting time for pulling Docker images:

* (manager) ``python -m ai.backend.manager.cli image rescan``

* (agent) ``docker pull``

  - ``lablup/python:3.6-ubuntu18.04``

  - ``lablup/lua:5.3-alpine3.8``

The manager must also have at least the following active suerp-admin account
in the ``default`` domain and the ``default`` group.

* Example super-admin account:

  - User ID: ``admin@lablup.com``

  - Password ``wJalrXUt``

  - Access key: ``AKIAIOSFODNN7EXAMPLE``

  - Secret key: ``wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY``

One or more ``testing-XXXX`` domain, one or more ``testing-XXXX`` groups, and one ore more dummy users
are created and used during the tests and destroyed after running tests.  ``XXXX`` will be filled with
random identifiers.


.. tip::

   The *halfstack* configuration and the ``example-users.json``, ``example-keypairs.json``, ``example-set-user-main-access-keys.json`` fixture is compatible with this
   integration test suite.


How to run
~~~~~~~~~~

Execute the gateway and at least one agent in their respective virtualenvs and hosts:

.. code-block:: console

   $ python -m ai.backend.client.gateway.server
   $ python -m ai.backend.client.agent.server
   $ python -m ai.backend.client.agent.watcher

Then run the tests:

.. code-block:: console

   $ export BACKEND_ENDPOINT=...
   $ python -m pytest -m 'integration' tests
