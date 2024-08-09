Prepare Database
================

Backend.AI makes use of PostgreSQL as its main database. Launch the service
using docker compose by generating the file
``$HOME/halfstack/postgres-cluster-default/docker-compose.yaml`` and populating it with the
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
      backendai-pg-active:
         <<: *base
         image: postgres:16.3-alpine
         restart: unless-stopped
         command: >
            postgres
            -c "max_connections=256"
            -c "max_worker_processes=4"
            -c "deadlock_timeout=10s"
            -c "lock_timeout=60000"
            -c "idle_in_transaction_session_timeout=60000"
         environment:
            - POSTGRES_USER=postgres
            - POSTGRES_PASSWORD=develove
            - POSTGRES_DB=backend
            - POSTGRES_INITDB_ARGS="--data-checksums"
         healthcheck:
            test: ["CMD", "pg_isready", "-U", "postgres"]
            interval: 10s
            timeout: 3s
            retries: 10
         volumes:
            - "${HOME}/.data/backend.ai/postgres-data/active:/var/lib/postgresql/data:rw"
         ports:
            - "8100:5432"
         networks:
            half_stack:
         cpu_count: 4
         mem_limit: "4g"

   networks:
       half_stack:

Execute the following command to start the service container. The project
``${USER}`` is added for operational convenience.

.. code-block:: console

   $ cd ${HOME}/halfstack/postgres-cluster-default
   $ docker compose up -d
   $ # -- To terminate the container:
   $ # docker compose down
   $ # -- To see the container logs:
   $ # docker compose logs -f
