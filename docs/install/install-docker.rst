Install from Docker Containers
==============================

This guide explains how to run Backend.AI components using Docker containers built from the monorepo.
All six components are covered: manager, agent, webserver, storage-proxy, appproxy-coordinator, and appproxy-worker.

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

4. Register storage-proxy volumes in etcd:

   .. code-block:: bash

      docker exec backendai-backendai-half-etcd-1 etcdctl put /sorna/local/volumes '{"default:volume1": {"backend": "vfs", "path": "/vfroot/volume1"}}'

   Adjust the volume name and path as needed. The ``path`` must match what the storage-proxy
   container mounts (see the storage-proxy configuration below).

5. Set AppProxy address in the scaling group:

   .. code-block:: bash

      docker exec backendai-backendai-half-db-1 psql -U postgres -d backend -c \
        "UPDATE scaling_groups SET wsproxy_addr = 'http://backend-ai-appproxy-coordinator:10200' WHERE name = 'default';"

   This tells the manager to reach the AppProxy coordinator via the Docker network name.
   The ``advertised_addr`` in the AppProxy coordinator config controls what the browser sees.

Building Docker Images
----------------------

Build the Docker images:

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

   # Build agent image
   docker build -f docker/backend.ai-agent.dockerfile \
     -t backend.ai/agent:${PKGVER} \
     --build-arg PYTHON_VERSION=3.13 \
     --build-arg PKGVER=${PKGVER} \
     .

   # Build storage-proxy image
   docker build -f docker/backend.ai-storage-proxy.dockerfile \
     -t backend.ai/storage-proxy:${PKGVER} \
     --build-arg PYTHON_VERSION=3.13 \
     --build-arg PKGVER=${PKGVER} \
     .

   # Build appproxy-coordinator image
   docker build -f docker/backend.ai-appproxy-coordinator.dockerfile \
     -t backend.ai/appproxy-coordinator:${PKGVER} \
     --build-arg PYTHON_VERSION=3.13 \
     --build-arg PKGVER=${PKGVER} \
     .

   # Build appproxy-worker image
   docker build -f docker/backend.ai-appproxy-worker.dockerfile \
     -t backend.ai/appproxy-worker:${PKGVER} \
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

Agent Configuration
~~~~~~~~~~~~~~~~~~~

Create ``agent.toml`` with the following content:

.. code-block:: toml

   # Backend.AI Agent configuration for Docker containers (DooD mode)

   [etcd]
   namespace = "local"
   addr = { host = "host.docker.internal", port = 8121 }
   user = ""
   password = ""

   [agent]
   mode = "docker"
   rpc-listen-addr = { host = "0.0.0.0", port = 6001 }
   advertised-rpc-addr = { host = "backend-ai-agent", port = 6001 }
   service-addr = { host = "0.0.0.0", port = 6003 }
   agent-sock-port = 6007
   scaling-group = "default"
   ipc-base-path = "/tmp/backend.ai/ipc"
   var-base-path = "/var/lib/backend.ai"
   image-commit-path = "/tmp/backend.ai/commit/"

   [container]
   port-range = [30000, 31000]
   bind-host = "host.docker.internal"
   advertised-host = "host.docker.internal"
   sandbox-type = "docker"
   scratch-type = "hostdir"
   scratch-root = "/tmp/scratches"
   scratch-size = "1G"

   [resource]
   reserved-cpu = 1
   reserved-mem = "1G"
   reserved-disk = "8G"

   [logging]
   level = "INFO"
   drivers = ["console"]

   [logging.console]
   colored = true
   format = "verbose"

   [debug]
   enabled = true

The agent runs in DooD (Docker-out-of-Docker) mode, using the host's Docker daemon
via the mounted ``/var/run/docker.sock``. Key configuration points:

- ``agent.advertised-rpc-addr`` must use the container service name (``backend-ai-agent``)
  so the manager can reach the agent via the Docker network
- ``container.bind-host`` and ``container.advertised-host`` must be ``host.docker.internal``
  so session containers (created on the host Docker daemon) can reach the agent
- ``container.scratch-root`` must be a **host-accessible path** (e.g. ``/tmp/scratches``).
  In DooD mode, the agent tells Docker to bind-mount scratch directories into session containers,
  and Docker resolves these paths on the **host** filesystem, not inside the agent container
- The agent entrypoint script automatically sets up krunner file sharing for DooD.
  It copies ``runner``, ``kernel``, and ``helpers`` packages to ``/tmp/backend-ai-krunner/``
  and creates symlinks so Docker can find them on the host

Webserver Configuration
~~~~~~~~~~~~~~~~~~~~~~~

Create ``webserver.conf`` with the following content:

.. code-block:: toml

   # Backend.AI Web Server configuration for Docker containers

   [service]
   ip = "0.0.0.0"
   port = 8090
   wsproxy.url = "http://localhost:10200"
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

   [api]
   domain = "default"
   # Multiple endpoints: first for container-to-container communication, second for browser access
   endpoint = "http://backend-ai-manager:8091,http://127.0.0.1:8091"
   text = "Backend.AI Cloud"
   ssl_verify = false
   auth_token_name = 'sToken'

   [session]

   [session.redis]
   addr = "host.docker.internal:8111"

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

   [debug]
   enabled = true

   [otel]
   enabled = true
   log-level = "INFO"
   endpoint = "http://host.docker.internal:4317"

   [apollo-router]
   enabled = true
   endpoint = "http://host.docker.internal:4000"

- ``wsproxy.url`` must point to the AppProxy coordinator URL **as seen by the browser**
  (``http://localhost:10200``), not the container-to-container address

Storage-Proxy Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``storage-proxy.toml`` with the following content:

.. code-block:: toml

   # Backend.AI Storage Proxy configuration for Docker containers

   [etcd]
   namespace = "local"
   addr = { host = "host.docker.internal", port = 8121 }
   user = ""
   password = ""

   [storage-proxy]
   node-id = "i-storage-proxy-01"
   num-proc = 2
   pid-file = "/var/log/backend.ai/storage-proxy.pid"
   event-loop = "uvloop"
   scandir-limit = 1000
   max-upload-size = "100g"
   secret = "some-secret-shared-with-manager"

   [storage-proxy.client]
   service-addr = { host = "0.0.0.0", port = 6021 }

   [storage-proxy.manager]
   service-addr = { host = "0.0.0.0", port = 6022 }
   ipc-base-path = "/tmp/backend.ai/ipc"

   [volume.volume1]
   backend = "vfs"
   path = "/vfroot/volume1"

   [logging]
   level = "INFO"
   drivers = ["console"]

   [logging.console]
   colored = true
   format = "verbose"

   [debug]
   enabled = true

The ``[volume.volume1]`` section must match the etcd volumes configuration from the prerequisites.

AppProxy Coordinator Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``proxy-coordinator.toml`` with the following content:

.. code-block:: toml

   # Backend.AI AppProxy Coordinator configuration for Docker containers

   [db]
   type = "postgresql"
   name = "appproxy"
   user = "appproxy"
   password = "develove"
   pool_size = 8
   max_overflow = 64
   addr = { host = "host.docker.internal", port = 8101 }

   [redis]
   addr = { host = "host.docker.internal", port = 8111 }

   [proxy_coordinator]
   tls_listen = false
   tls_advertised = false
   allow_unauthorized_configure_request = true

   [proxy_coordinator.bind_addr]
   host = "0.0.0.0"
   port = 10200

   [proxy_coordinator.advertised_addr]
   host = "localhost"
   port = 10200

   [secrets]
   api_secret = "some_api_secret"
   jwt_secret = "some_jwt_secret"

   [permit_hash]
   secret = "some_permit_hash_secret"

   [logging]
   level = "INFO"
   drivers = ["console"]

   [logging.console]
   colored = true
   format = "verbose"

   [debug]
   enabled = true
   log-events = true

- ``proxy_coordinator.advertised_addr`` must use ``localhost`` because this address is sent
  to the browser for direct AppProxy connections
- ``proxy_coordinator.bind_addr`` uses ``0.0.0.0`` to accept connections from both the
  manager container and the host network

AppProxy Worker Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``proxy-worker.toml`` with the following content:

.. code-block:: toml

   # Backend.AI AppProxy Worker configuration for Docker containers

   [redis]
   addr = { host = "host.docker.internal", port = 8111 }

   [proxy_worker]
   coordinator_endpoint = "http://backend-ai-appproxy-coordinator:10200"
   authority = "worker-1"
   tls_listen = false
   tls_advertised = false
   frontend_mode = "port"
   protocol = "http"
   accepted_traffics = ["inference", "interactive"]
   api_bind_addr = { host = "0.0.0.0", port = 10201 }
   api_advertised_addr = { host = "localhost", port = 10201 }

   [proxy_worker.port_proxy]
   bind_host = "0.0.0.0"
   advertised_host = "localhost"
   bind_port_range = [10205, 10300]

   [secrets]
   api_secret = "some_api_secret"
   jwt_secret = "some_jwt_secret"

   [permit_hash]
   secret = "some_permit_hash_secret"

   [logging]
   level = "INFO"
   drivers = ["console"]

   [logging.console]
   colored = true
   format = "verbose"

   [debug]
   enabled = true
   log-events = true

- ``coordinator_endpoint`` uses the container name for inter-container communication
- ``api_advertised_addr`` and ``port_proxy.advertised_host`` must use ``localhost``
  because these addresses are sent to the browser

Address Configuration Summary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a Docker environment, each address serves a different audience. Use the correct hostname
for each:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Purpose
     - Hostname
     - Why
   * - Container-to-container (e.g. manager to agent RPC, worker to coordinator)
     - Docker service name (e.g. ``backend-ai-agent``)
     - Resolved via Docker DNS on the shared network
   * - Container-to-halfstack (e.g. to etcd, PostgreSQL, Redis)
     - ``host.docker.internal``
     - Halfstack ports are mapped on the host
   * - Browser-facing (e.g. AppProxy advertised addresses, ``wsproxy.url``)
     - ``localhost``
     - Browser runs on the host machine
   * - Scaling group ``wsproxy_addr`` (manager to AppProxy)
     - ``backend-ai-appproxy-coordinator``
     - Manager container calls AppProxy coordinator container

Running with Docker Compose
----------------------------

The easiest way to run all components is using docker-compose.

The ``docker-compose.monorepo.yml`` file includes all six services: manager, agent,
webserver, storage-proxy, appproxy-coordinator, and appproxy-worker.

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
     backend.ai/manager:${PKGVER}

**Agent (DooD):**

.. code-block:: bash

   docker run -d \
     --name backend-ai-agent \
     --network backendai_half \
     --add-host host.docker.internal:host-gateway \
     -p 6001:6001 -p 6003:6003 \
     -v $(pwd)/agent.toml:/etc/backend.ai/agent.toml:ro \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v /tmp/backend.ai/ipc:/tmp/backend.ai/ipc \
     -v /tmp/scratches:/tmp/scratches \
     -v /tmp/backend-ai-krunner:/tmp/backend-ai-krunner \
     -e PYTHONUNBUFFERED=1 \
     --restart unless-stopped \
     backend.ai/agent:${PKGVER}

.. note::

   Do **not** map ports 30000-31000 to the agent container. In DooD mode, session containers
   bind these ports directly on the host Docker daemon. Mapping them to the agent container
   would cause port conflicts.

**Webserver:**

.. code-block:: bash

   docker run -d \
     --name backend-ai-webserver \
     --network backendai_half \
     --add-host host.docker.internal:host-gateway \
     -p 8090:8090 \
     -v $(pwd)/webserver.conf:/etc/backend.ai/webserver.conf:ro \
     --restart unless-stopped \
     backend.ai/webserver:${PKGVER}

**Storage-Proxy:**

.. code-block:: bash

   docker run -d \
     --name backend-ai-storage-proxy \
     --network backendai_half \
     --add-host host.docker.internal:host-gateway \
     -p 6021:6021 -p 6022:6022 \
     -v $(pwd)/storage-proxy.toml:/etc/backend.ai/storage-proxy.toml:ro \
     -v $(pwd)/vfroot:/vfroot \
     --restart unless-stopped \
     backend.ai/storage-proxy:${PKGVER}

**AppProxy Coordinator:**

.. code-block:: bash

   docker run -d \
     --name backend-ai-appproxy-coordinator \
     --network backendai_half \
     --add-host host.docker.internal:host-gateway \
     -p 10200:10200 \
     -v $(pwd)/proxy-coordinator.toml:/etc/backend.ai/proxy-coordinator.toml:ro \
     --restart unless-stopped \
     backend.ai/appproxy-coordinator:${PKGVER}

**AppProxy Worker:**

.. code-block:: bash

   docker run -d \
     --name backend-ai-appproxy-worker \
     --network backendai_half \
     --add-host host.docker.internal:host-gateway \
     -p 10201:10201 -p 10205-10300:10205-10300 \
     -v $(pwd)/proxy-worker.toml:/etc/backend.ai/proxy-worker.toml:ro \
     --restart unless-stopped \
     backend.ai/appproxy-worker:${PKGVER}

Accessing the Services
----------------------

After starting the containers:

- Web UI: http://localhost:8090
- Manager API: http://localhost:8091
- AppProxy: http://localhost:10200
- Default credentials: ``admin@lablup.com`` / ``wJalrXUt``

Troubleshooting
---------------

Container fails to start
~~~~~~~~~~~~~~~~~~~~~~~~~

Check logs:

.. code-block:: bash

   docker logs backend-ai-manager
   docker logs backend-ai-agent
   docker logs backend-ai-webserver
   docker logs backend-ai-storage-proxy
   docker logs backend-ai-appproxy-coordinator
   docker logs backend-ai-appproxy-worker

Connection issues
~~~~~~~~~~~~~~~~~

Ensure all halfstack services are running:

.. code-block:: bash

   docker compose -f docker-compose.halfstack-ha.yml ps

AppProxy 503 / "Failed to fetch"
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the browser shows "Failed to connect to AppProxy" or "Failed to fetch" when opening
session apps:

1. Verify the scaling group has the correct ``wsproxy_addr``:

   .. code-block:: bash

      docker exec backendai-backendai-half-db-1 psql -U postgres -d backend -c \
        "SELECT wsproxy_addr FROM scaling_groups WHERE name = 'default';"

   It should show ``http://backend-ai-appproxy-coordinator:10200``.

2. Verify AppProxy advertised addresses use ``localhost``:

   .. code-block:: bash

      curl -s http://localhost:10200/status | python3 -m json.tool

   The ``advertise_address`` should be ``http://localhost:10200``.

3. Verify the webserver ``wsproxy.url`` is set to ``http://localhost:10200``.

DooD agent: session creation fails
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If session containers fail to start with "bind source path does not exist":

- Ensure ``/tmp/backend-ai-krunner`` is mounted as a volume to the agent container.
  The entrypoint script populates this directory with krunner files on first start.
- Ensure ``scratch-root`` in the agent config uses a host-accessible path
  (e.g. ``/tmp/scratches``, not ``/app/scratches``).

pycares version mismatch
~~~~~~~~~~~~~~~~~~~~~~~~~

The Dockerfile has been updated to respect ``requirements.txt`` version constraints.
If you encounter DNS resolution errors, verify the pycares version:

.. code-block:: bash

   docker run --rm backend.ai/webserver:${PKGVER} pip list | grep pycares

It should show version 4.11.0.

Stopping Services
-----------------

Using docker-compose:

.. code-block:: bash

   docker compose -f docker-compose.monorepo.yml down

Or manually:

.. code-block:: bash

   docker stop backend-ai-manager backend-ai-agent backend-ai-webserver \
     backend-ai-storage-proxy backend-ai-appproxy-coordinator backend-ai-appproxy-worker
   docker rm backend-ai-manager backend-ai-agent backend-ai-webserver \
     backend-ai-storage-proxy backend-ai-appproxy-coordinator backend-ai-appproxy-worker
