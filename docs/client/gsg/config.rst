Client Configuration
====================

The configuration for Backend.AI API includes the endpoint URL prefix, API
keypairs (access and secret keys), and a few others.

There are two ways to set the configuration:

1. Setting environment variables before running your program that uses this SDK.
   This applies to the command-line interface as well.

.. code-block:: console

   # Linux, macOS
   $ export BACKEND_ACCESS_KEY=AKIA...
   $ export BACKEND_SECRET_KEY=...
   $ export BACKEND_ENDPOINT=https://my-precious-cluster
   $ export BACKEND_ENDPOINT_TYPE=api

   # Windows
   > chcp 65001
   > set BACKEND_ACCESS_KEY=AKIA...
   > set BACKEND_SECRET_KEY=...
   > set BACKEND_ENDPOINT=https://my-precious-cluster
   > set BACKEND_ENDPOINT_TYPE=api

2. Manually creating :class:`~ai.backend.client.config.APIConfig` instance and creating sessions with it.

.. code-block:: python

   from ai.backend.client.config import APIConfig, set_config
   config = APIConfig(
      access_key="AKIA...",
      secret_key="...",
      endpoint="https://my-precious-cluster",
      endpoint_type="api",
      vfolder_mounts=None,
   )
   set_config(config)

The list of configurable environment variables are:

* ``BACKEND_ENDPOINT``
* ``BACKEND_ENDPOINT_TYPE``
* ``BACKEND_ACCESS_KEY``
* ``BACKEND_SECRET_KEY``
* ``BACKEND_VFOLDER_MOUNTS``

Please refer the parameter descriptions of :class:`~ai.backend.client.config.APIConfig`'s constructor
for what each environment variable means and what value format should be used.
