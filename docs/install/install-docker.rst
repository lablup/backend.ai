Install from Docker Containers
==============================

This guide explains how to run Backend.AI components (manager, webserver) using Docker containers built from the monorepo.

Prerequisites
-------------

1. Build the wheel packages:

   .. code-block:: bash

      ./scripts/build-wheels.sh

2. Start the halfstack infrastructure (PostgreSQL, Redis, etcd):

   .. code-block:: bash

      docker compose -f docker-compose.halfstack-ha.yml up -d

3. Configure etcd for Redis connection:

   .. code-block:: bash

      docker exec backendai-backendai-half-etcd-1 etcdctl put /sorna/local/config/redis/addr "host.docker.internal:8110"

Building Docker Images
----------------------

Build the manager and webserver Docker images:

.. code-block:: bash

   # Get the current version
   PKGVER=$(./py -c "import packaging.version,pathlib; print(str(packaging.version.Version(pathlib.Path('VERSION').read_text())))")

   # Build webserver image
   docker build -f docker/backend.ai-webserver.dockerfile \
     -t backend.ai/webserver:${PKGVER} \
     --build-arg PYTHON_VERSION=3.13 \
     --build-arg PKGVER=${PKGVER} \
     .

   # Build manager image
   docker build -f docker/backend.ai-manager.Dockerfile \
     -t backend.ai/manager:${PKGVER} \
     --build-arg PYTHON_VERSION=3.13 \
     --build-arg PKGVER=${PKGVER} \
     .

Configuration Files
-------------------

Create the configuration files before running the containers.

Manager Configuration
~~~~~~~~~~~~~~~~~~~~~

Create ``manager.toml`` with the following content:

.. code-block:: toml

   # Backend.AI Manager configuration for Docker containers

   [etcd]
   namespace = "local"
   addr = { host = "host.docker.internal", port = 8220 }
   user = ""
   password = ""

   [db]
   type = "postgresql"
   addr = { host = "host.docker.internal", port = 8100 }
   name = "backend"
   user = "postgres"
   password = "develove"
   pool-size = 8
   pool-recycle = -1
   pool-pre-ping = true

   [manager]
   num-proc = 4
   distributed-lock = "filelock"
   service-addr = { host = "0.0.0.0", port = 8091 }
   heartbeat-timeout = 5.0
   secret = "some-secret-private-for-signing-manager-api-requests"
   hide-agents = true
   importer-image = "lablup/backend.ai-importer:manylinux2014"
   use_sokovan = true

   [docker-registry]
   enabled = false

   [logging]
   level = "INFO"
   drivers = ["console"]

   [logging.console]
   colored = true
   format = "verbose"

   [debug]
   enabled = true

   [otel]
   enabled = true
   log-level = "INFO"
   endpoint = "http://host.docker.internal:4317"

Webserver Configuration
~~~~~~~~~~~~~~~~~~~~~~~

Create ``webserver.conf`` with the following content:

.. code-block:: toml

   # Backend.AI Web Server configuration for Docker containers

   [service]
   ip = "0.0.0.0"
   port = 8090
   wsproxy.url = ""
   mode = "webui"
   enable_signup = false
   allow_anonymous_change_password = false
   allow_project_resource_monitor = false
   allow_change_signin_mode = false
   allow_manual_image_name_for_session = false
   allow_signup_without_confirmation = false
   always_enqueue_compute_session = false
   webui_debug = true
   mask_user_info = false
   enable_2FA = false
   force_2FA = false
   directory_based_usage = false
   enable_reservoir = false

   [resources]
   open_port_to_public = false
   allow_non_auth_tcp = false
   allow_preferred_port = false
   max_cpu_cores_per_container = 64
   max_memory_per_container = 64
   max_cuda_devices_per_container = 16
   max_cuda_shares_per_container = 16
   max_shm_per_container = 2
   max_file_upload_size = 4294967296

   [security]
   request_policies = ["reject_metadata_local_link_policy", "reject_access_for_unsafe_file_policy"]
   response_policies = ["set_content_type_nosniff_policy"]

   [environments]

   [plugin]

   [pipeline]
   endpoint = "http://127.0.0.1:9500"
   frontend-endpoint = "http://127.0.0.1:3000"

   [ui]
   menu_blocklist = "pipeline"
   menu_inactivelist = "statistics"

   [api]
   domain = "default"
   # Multiple endpoints: first for container-to-container communication, second for browser access
   endpoint = "http://backend-ai-manager:8091,http://127.0.0.1:8091"
   text = "Backend.AI Cloud"
   ssl_verify = false
   auth_token_name = 'sToken'

   [session]

   [session.redis]
   # Use the halfstack Redis service name for container networking
   addr = "backendai-half-redis-node01:8110"

   [session.redis.redis_helper_config]
   socket_timeout = 5.0
   socket_connect_timeout = 2.0
   reconnect_poll_timeout = 0.3

   [webserver]

   [logging]
   level = "INFO"
   drivers = ["console"]

   [logging.console]
   colored = true
   format = "verbose"

   [logging.pkg-ns]
   "" = "WARNING"
   "aiotools" = "INFO"
   "aiohttp" = "INFO"
   "ai.backend" = "INFO"

   [debug]
   enabled = true

   [otel]
   enabled = true
   log-level = "INFO"
   endpoint = "http://host.docker.internal:4317"

   [apollo-router]
   enabled = true
   endpoint = "http://host.docker.internal:4000"

Key configuration points for Docker containers:

- Use ``host.docker.internal`` to access services on the host machine (etcd, PostgreSQL, OTEL)
- Use container service names for inter-container communication (``backend-ai-manager``, ``backendai-half-redis-node01``)
- The webserver endpoint uses multiple values: first for container-to-container, second for browser access

Running with Docker Compose
----------------------------

The easiest way to run the components is using docker-compose.

The ``docker-compose.monorepo.yml`` file includes both manager and webserver:

.. code-block:: yaml

   version: "3.8"

   services:
     backend-ai-manager:
       image: backend.ai/manager:26.1.0rc1
       container_name: backend-ai-manager
       networks:
         - half
       ports:
         - "8091:8091"
       volumes:
         - ./fixtures:/app/fixtures:ro
         - ./manager.toml:/etc/backend.ai/manager.toml:ro
         - ./logs:/var/log/backend.ai
         - /tmp/backend.ai/ipc:/tmp/backend.ai/ipc
         - /var/run/docker.sock:/var/run/docker.sock
       environment:
         - PYTHONUNBUFFERED=1
       extra_hosts:
         - "host.docker.internal:host-gateway"
       restart: unless-stopped

     backend-ai-webserver:
       image: backend.ai/webserver:26.1.0rc1
       container_name: backend-ai-webserver
       networks:
         - half
       ports:
         - "8090:8090"
       volumes:
         - ./webserver.conf:/etc/backend.ai/webserver.conf:ro
       extra_hosts:
         - "host.docker.internal:host-gateway"
       restart: unless-stopped
       depends_on:
         - backend-ai-manager

   networks:
     half:
       external: true
       name: backendai_half

Start the services:

.. code-block:: bash

   docker compose -f docker-compose.monorepo.yml up -d

Running Manually
----------------

Alternatively, you can run the containers manually:

**Manager:**

.. code-block:: bash

   docker run -d \
     --name backend-ai-manager \
     --network backendai_half \
     --add-host host.docker.internal:host-gateway \
     -p 8091:8091 \
     -v $(pwd)/fixtures:/app/fixtures:ro \
     -v $(pwd)/manager.toml:/etc/backend.ai/manager.toml:ro \
     -v $(pwd)/logs:/var/log/backend.ai \
     -v /tmp/backend.ai/ipc:/tmp/backend.ai/ipc \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -e PYTHONUNBUFFERED=1 \
     --restart unless-stopped \
     backend.ai/manager:26.1.0rc1

**Webserver:**

.. code-block:: bash

   docker run -d \
     --name backend-ai-webserver \
     --network backendai_half \
     --add-host host.docker.internal:host-gateway \
     -p 8090:8090 \
     -v $(pwd)/webserver.conf:/etc/backend.ai/webserver.conf:ro \
     --restart unless-stopped \
     backend.ai/webserver:26.1.0rc1

Accessing the Services
----------------------

After starting the containers:

- Web UI: http://localhost:8090
- Manager API: http://localhost:8091
- Default credentials: ``admin@lablup.com`` / ``wJalrXUt``

Troubleshooting
---------------

Container fails to start
~~~~~~~~~~~~~~~~~~~~~~~~

Check logs:

.. code-block:: bash

   docker logs backend-ai-manager
   docker logs backend-ai-webserver

Connection issues
~~~~~~~~~~~~~~~~~

Ensure all halfstack services are running:

.. code-block:: bash

   docker compose -f docker-compose.halfstack-ha.yml ps

pycares version mismatch
~~~~~~~~~~~~~~~~~~~~~~~~~

The Dockerfile has been updated to respect ``requirements.txt`` version constraints.
If you encounter DNS resolution errors, verify the pycares version:

.. code-block:: bash

   docker run --rm backend.ai/webserver:26.1.0rc1 pip list | grep pycares

It should show version 4.11.0.

Stopping Services
-----------------

Using docker-compose:

.. code-block:: bash

   docker compose -f docker-compose.monorepo.yml down

Or manually:

.. code-block:: bash

   docker stop backend-ai-manager backend-ai-webserver
   docker rm backend-ai-manager backend-ai-webserver
