Install Backend.AI Manager
==========================

Refer to :ref:`prepare_python_and_venv` to setup Python and virtual environment
for the service.

Install the latest version of Backend.AI Manager for the current Python version:

.. code-block:: console

   $ cd "${HOME}/manager"
   $ # Activate a virtual environment if needed.
   $ pip install -U backend.ai-manager

If you want to install a specific version:

.. code-block:: console

   $ pip install -U backend.ai-manager==${BACKEND_PKG_VERSION}


Local configuration
-------------------

Backend.AI Manager uses a TOML file (``manager.toml``) to configure local
service. Refer to the
`manager.toml sample file <https://github.com/lablup/backend.ai/blob/main/configs/manager/sample.toml>`_
for a detailed description of each section and item. A configuration example
would be:

.. code-block:: toml

   [etcd]
   namespace = "local"
   addr = { host = "bai-m1", port = 8120 }
   user = ""
   password = ""

   [db]
   type = "postgresql"
   addr = { host = "bai-m1", port = 8100 }
   name = "backend"
   user = "postgres"
   password = "develove"

   [manager]
   num-proc = 2
   service-addr = { host = "0.0.0.0", port = 8081 }
   # user = "bai"
   # group = "bai"
   ssl-enabled = false

   heartbeat-timeout = 30.0
   pid-file = "/home/bai/manager/manager.pid"
   disabled-plugins = []
   hide-agents = true
   # event-loop = "asyncio"
   # importer-image = "lablup/importer:manylinux2010"
   distributed-lock = "filelock"

   [docker-registry]
   ssl-verify = false

   [logging]
   level = "INFO"
   drivers = ["console", "file"]

   [logging.pkg-ns]
   "" = "WARNING"
   "aiotools" = "INFO"
   "aiopg" = "WARNING"
   "aiohttp" = "INFO"
   "ai.backend" = "INFO"
   "alembic" = "INFO"

   [logging.console]
   colored = true
   format = "verbose"

   [logging.file]
   path = "./logs"
   filename = "manager.log"
   backup-count = 10
   rotation-size = "10M"

   [debug]
   enabled = false
   enhanced-aiomonitor-task-info = true

Save the contents to ``${HOME}/.config/backend.ai/manager.toml``. Backend.AI
will automatically recognize the location. Adjust each field to conform to your
system.


Global configuration
--------------------

Etcd (cluster) stores globally shared configurations for all nodes. Some of them
should be populated prior to starting the service.

.. note::

   It might be a good idea to create a backup of the current Etcd configuration
   before modifying the values. You can do so by simply executing:

   .. code-block:: console

      $ backend.ai mgr etcd get --prefix "" > ./etcd-config-backup.json

   To restore the backup:

   .. code-block:: console

      $ backend.ai mgr etcd delete --prefix ""
      $ backend.ai mgr etcd put-json "" ./etcd-config-backup.json

The commands below should be executed at ``${HOME}/manager`` directory.

To list a specific key from Etcd, for example, ``config`` key:

.. code-block:: console

   $ backend.ai mgr etcd get --prefix config

Now, configure Redis access information. This should be accessible from all
nodes.

.. code-block:: console

   $ backend.ai mgr etcd put config/redis/addr "bai-m1:8110"
   $ backend.ai mgr etcd put config/redis/password "develove"

Set the container registry. The following is the Lablup's open registry
(cr.backend.ai). You can set your own registry with username and password if
needed.  This can be configured via GUI as well.

.. code-block:: console

   $ backend.ai mgr etcd put config/docker/image/auto_pull "tag"
   $ backend.ai mgr etcd put config/docker/registry/cr.backend.ai "https://cr.backend.ai"
   $ backend.ai mgr etcd put config/docker/registry/cr.backend.ai/type "harbor2"
   $ backend.ai mgr etcd put config/docker/registry/cr.backend.ai/project "stable"
   $ # backend.ai mgr etcd put config/docker/registry/cr.backend.ai/username "bai"
   $ # backend.ai mgr etcd put config/docker/registry/cr.backend.ai/password "secure-password"

Also, populate the Storage Proxy configuration to the Etcd:

.. code-block:: console

   $ # Allow project (group) folders.
   $ backend.ai mgr etcd put volumes/_types/group ""
   $ # Allow user folders.
   $ backend.ai mgr etcd put volumes/_types/user ""
   $ # Default volume host. The name of the volume proxy here is "bai-m1" and volume name is "local".
   $ backend.ai mgr etcd put volumes/default_host "bai-m1:local"
   $ # Set the "bai-m1" proxy information.
   $ # User (browser) facing API endpoint of Storage Proxy.
   $ # Cannot use host alias here. It should be user-accessible URL.
   $ backend.ai mgr etcd put volumes/proxies/bai-m1/client_api "http://10.20.30.10:6021"
   $ # Manager facing internal API endpoint of Storage Proxy.
   $ backend.ai mgr etcd put volumes/proxies/bai-m1/manager_api "http://bai-m1:6022"
   $ # Random secret string which is used by Manager to communicate with Storage Proxy.
   $ backend.ai mgr etcd put volumes/proxies/bai-m1/secret "secure-token-to-authenticate-manager-request"
   $ # Option to disable SSL verification for the Storage Proxy.
   $ backend.ai mgr etcd put volumes/proxies/bai-m1/ssl_verify "false"

Check if the configuration is properly populated:

.. code-block:: console

   $ backend.ai mgr etcd get --prefix volumes

Note that you have to change the secret to a unique random string for secure
communication between the manager and Storage Proxy. The most recent set of
parameters can be found from
`sample.etcd.volumes.json <https://github.com/lablup/backend.ai/blob/main/configs/manager/sample.etcd.volumes.json>`_.

To enable access to the volumes defined by the Storage Proxy from every user,
you need to update the ``allowed_vfolder_hosts`` column of the ``domains`` table
to hold the storage volume reference (e.g., ``bai-m1:local``). You can do this by
issuing SQL statement directly inside the PostgreSQL container:

.. code-block:: console

   $ vfolder_host_val='{"bai-m1:local": ["create-vfolder", "modify-vfolder", "delete-vfolder", "mount-in-session", "upload-file", "download-file", "invite-others", "set-user-specific-permission"]}'
   $ docker exec -it bai-backendai-pg-active-1 psql -U postgres -d backend \
         -c "UPDATE domains SET allowed_vfolder_hosts = '${vfolder_host_val}' WHERE name = 'default';"


Populate the database with initial fixtures
-------------------------------------------

You need to prepare ``alembic.ini`` file under ``${HOME}/manager`` to manage
the database schema. Copy the sample
`halfstack.alembic.ini <https://github.com/lablup/backend.ai/blob/main/configs/manager/halfstack.alembic.ini>`_
and save it as ``${HOME}/manager/alembic.ini``. Adjust the ``sqlalchemy.url``
field if database connection information is different from the default one. You
may need to change ``localhost`` to ``bai-m1``.

Populate the database schema and initial fixtures. Copy the example JSON files
(`example-keypairs.json <https://github.com/lablup/backend.ai/blob/main/fixtures/manager/example-keypairs.json>`_
and
`example-resource-presets.json <https://github.com/lablup/backend.ai/blob/main/fixtures/manager/example-resource-presets.json>`_)
as ``keypairs.json`` and ``resource-presets.json``, save them under
``${HOME}/manager/``. Customize them to have unique keypairs and passwords for
your initial superadmin and sample user accounts for security.

.. code-block:: console

   $ backend.ai mgr schema oneshot
   $ backend.ai mgr fixture populate ./keypairs.json
   $ backend.ai mgr fixture populate ./resource-presets.json


Sync the information of container registry
------------------------------------------

You need to scan the image catalog and metadata from the container registry to
the Manager. This is required to display the list of compute environments in the
user web GUI (Web UI). You can run the following command to sync the
information with Lablup's public container registry:

.. code-block:: console

   $ backend.ai mgr image rescan cr.backend.ai


Run Backend.AI Manager service
------------------------------

You can run the service:

.. code-block:: console

   $ cd "${HOME}/manager"
   $ python -m ai.backend.manager.server

Check if the service is running. The default Manager API port is 8081, but it
can be configured from ``manager.toml``:

.. code-block:: console

   $ curl bai-m1:8081
   {"version": "v6.20220615", "manager": "22.09.6"}

Press ``Ctrl-C`` to stop the service.


Register systemd service
------------------------

The service can be registered as a systemd daemon. It is recommended to
automatically run the service after rebooting the host machine, although this is
entirely optional.

First, create a runner script at ``${HOME}/bin/run-manager.sh``:

.. code-block:: bash

   #! /bin/bash
   set -e

   if [ -z "$HOME" ]; then
      export HOME="/home/bai"
   fi

   # -- If you have installed using static python --
   source .venv/bin/activate

   # -- If you have installed using pyenv --
   if [ -z "$PYENV_ROOT" ]; then
      export PYENV_ROOT="$HOME/.pyenv"
      export PATH="$PYENV_ROOT/bin:$PATH"
   fi
   eval "$(pyenv init --path)"
   eval "$(pyenv virtualenv-init -)"

   if [ "$#" -eq 0 ]; then
      exec python -m ai.backend.manager.server
   else
      exec "$@"
   fi

Make the script executable:

.. code-block:: console

   $ chmod +x "${HOME}/bin/run-manager.sh"

Then, create a systemd service file at
``/etc/systemd/system/backendai-manager.service``:

.. code-block:: dosini

   [Unit]
   Description= Backend.AI Manager
   Requires=network.target
   After=network.target remote-fs.target

   [Service]
   Type=simple
   ExecStart=/home/bai/bin/run-manager.sh
   PIDFile=/home/bai/manager/manager.pid
   User=1100
   Group=1100
   WorkingDirectory=/home/bai/manager
   TimeoutStopSec=5
   KillMode=process
   KillSignal=SIGTERM
   PrivateTmp=false
   Restart=on-failure
   RestartSec=10
   LimitNOFILE=5242880
   LimitNPROC=131072

   [Install]
   WantedBy=multi-user.target

Finally, enable and start the service:

.. code-block:: console

   $ sudo systemctl daemon-reload
   $ sudo systemctl enable --now backendai-manager

   $ # To check the service status
   $ sudo systemctl status backendai-manager
   $ # To restart the service
   $ sudo systemctl restart backendai-manager
   $ # To stop the service
   $ sudo systemctl stop backendai-manager
   $ # To check the service log and follow
   $ sudo journalctl --output cat -u backendai-manager -f
