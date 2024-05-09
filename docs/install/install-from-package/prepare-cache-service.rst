Prepare Cache Service
=====================

Backend.AI makes use of Redis as its main cache service. Launch the service
using docker compose by generating the file
``$HOME/halfstack/redis-cluster-default/docker-compose.yaml`` and populating it with the
following YAML. Feel free to adjust the volume paths and port settings. Please
refer
`the latest configuration <https://github.com/lablup/backend.ai/blob/main/docker-compose.halfstack-main.yml>`_
(it's a symbolic link so follow the filename in it) if needed.

.. code-block:: yaml

   x-base: &base
      logging:
         driver: "json-file"
         options:
            max-file: "5"
            max-size: "10m"

   services:
      backendai-halfstack-redis:
         <<: *base
         image: redis:6.2-alpine
         restart: unless-stopped
         command: >
            redis-server
            --requirepass develove
            --appendonly yes
         volumes:
            - "${HOME}/.data/backend.ai/redis-data:/data:rw"
         healthcheck:
            test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
            interval: 10s
            timeout: 3s
            retries: 10
         ports:
            - "8110:6379"
         networks:
            - half_stack
         cpu_count: 1
         mem_limit: "2g"

   networks:
      half_stack:

Execute the following command to start the service container. The project
``${USER}`` is added for operational convenience.

.. code-block:: console

   $ cd ${HOME}/halfstack/redis-cluster-default
   $ docker compose up -d
   $ # -- To terminate the container:
   $ # docker compose down
   $ # -- To see the container logs:
   $ # docker compose logs -f
