Prepare Config Service
======================

Backend.AI makes use of Etcd as its main config service. Launch the service
using docker compose by generating the file
``$HOME/halfstack/etcd-cluster-default/docker-compose.yaml`` and populating it with the
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
      backendai-halfstack-etcd:
         <<: *base
         image: quay.io/coreos/etcd:v3.4.15
         restart: unless-stopped
         command: >
            /usr/local/bin/etcd
            --name etcd-node01
            --data-dir /etcd-data
            --listen-client-urls http://0.0.0.0:2379
            --advertise-client-urls http://0.0.0.0:8120
            --listen-peer-urls http://0.0.0.0:2380
            --initial-advertise-peer-urls http://0.0.0.0:8320
            --initial-cluster etcd-node01=http://0.0.0.0:8320
            --initial-cluster-token backendai-etcd-token
            --initial-cluster-state new
            --auto-compaction-retention 1
         volumes:
            - "${HOME}/.data/backend.ai/etcd-data:/etcd-data:rw"
         healthcheck:
            test: ["CMD", "etcdctl", "endpoint", "health"]
            interval: 10s
            timeout: 3s
            retries: 10
         ports:
            - "8120:2379"
            # - "8320:2380"  # listen peer (only if required)
         networks:
            - half_stack
         cpu_count: 1
         mem_limit: "1g"

   networks:
      half_stack:

Execute the following command to start the service container. The project
``${USER}`` is added for operational convenience.

.. code-block:: console

   $ cd ${HOME}/halfstack/etcd-cluster-default
   $ docker compose up -d
   $ # -- To terminate the container:
   $ # docker compose down
   $ # -- To see the container logs:
   $ # docker compose logs -f
