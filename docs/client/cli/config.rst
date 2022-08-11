Configuration
=============

.. note::

   Please consult the detailed usage in the help of each command
   (use ``-h`` or ``--help`` argument to display the manual).

Check out :doc:`the client configuration </gsg/config>` for configurations via environment variables.

Session Mode
------------

When the endpoint type is ``"session"``, you must explicitly login and logout
into/from the console server.

.. code-block:: console

   $ export BACKEND_ENDPOINT=https://my-precious-cluster
   $ unset BACKEND_ACCESS_KEY
   $ unset BACKEND_SECRET_KEY
   $ export BACKEND_ENDPOINT_TYPE=session

   $ backend.ai login
   Username: myaccount@example.com
   Password:
   ✔ Login succeeded.

   $ backend.ai ...  # any commands

   $ backend.ai logout
   ✔ Logout done.


API Mode
--------

After setting up the environment variables, just run any command:

.. code-block:: console

   $ export BACKEND_ACCESS_KEY=AKIA...
   $ export BACKEND_SECRET_KEY=...
   $ export BACKEND_ENDPOINT=https://my-precious-cluster
   $ export BACKEND_ENDPOINT_TYPE=api

   $ backend.ai ...  # any commands


Checking out the current configuration
--------------------------------------

Run the following command to list your current active configurations.

.. code-block:: console

   $ backend.ai config

   # API endpoint: https://my-precious-cluster (mode: session)
   # Client version: 22.06.0b4 (API: v6.20220615)
   # Server version: 22.06.0b4 (API: v6.20220615)
   # Negotiated API version: v6.20220615
   # Domain name: "default"
   # Group name: "default"
   # Signature hash type: sha256
   # Skip SSL certificate validation? False
