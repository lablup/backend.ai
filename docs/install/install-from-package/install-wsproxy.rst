Install Backend.AI WSProxy
=========================

Refer to :ref:`prepare_python_and_venv` to setup Python and virtual environment
for the service.

Install the latest version of Backend.AI WSProxy for the current Python
version:

.. code-block:: console

   $ cd "${HOME}/wsproxy"
   $ # Activate a virtual environment if needed.
   $ pip install -U backend.ai-wsproxy

If you want to install a specific version:

.. code-block:: console

   $ pip install -U backend.ai-wsproxy==${BACKEND_PKG_VERSION}


Local configuration
-------------------

Backend.AI WSProxy uses a config file (``wsproxy.conf``) to configure
local service. Refer to the
`wsproxy.conf sample file <https://github.com/lablup/backend.ai/blob/main/configs/wsproxy/sample.toml>`_
for a detailed description of each section and item. A configuration example
would be:

.. code-block:: toml

   [wsproxy]
   bind_host = "127.0.0.1"
   advertised_host = "127.0.0.1"

   bind_api_port = 5050
   advertised_api_port = 5050

   # replace these values with your passphrase
   jwt_encrypt_key = "50M3G00DL00KING53CR3T"
   permit_hash_key = "50M3G00DL00KING53CR3T"
   api_secret = "v625xZLOgbMHhl0s49VuqQ"


Save the contents to ``${HOME}/.config/backend.ai/wsproxy.toml``.

Run Backend.AI WSProxy service
------------------------------

You can run the service by specifying the config file path with ``-f`` option:

.. code-block:: console

   $ cd "${HOME}/wsproxy"
   $ python -m ai.backend.wsproxy.server -f ${HOME}/.config/backend.ai/wsproxy.toml

Press ``Ctrl+C`` to stop both services.


Register systemd service
------------------------

The service can be registered as a systemd daemon. It is recommended to
automatically run the service after rebooting the host machine, although this is
entirely optional.

First, create a runner script at ``${HOME}/bin/run-wsproxy.sh``:

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
      exec python -m ai.backend.wsproxy.server -f ${HOME}/.config/backend.ai/wsproxy.toml
   else
      exec "$@"
   fi

Make the scripts executable:

.. code-block:: console

   $ chmod +x "${HOME}/bin/run-wsproxy.sh"

Then, create a systemd service file at
``/etc/systemd/system/backendai-wsproxy.service``:

.. code-block:: dosini

   [Unit]
   Description= Backend.AI WSProxy
   Requires=network.target
   After=network.target remote-fs.target

   [Service]
   Type=simple
   ExecStart=/home/bai/bin/run-wsproxy.sh
   PIDFile=/home/bai/wsproxy/wsproxy.pid
   WorkingDirectory=/home/bai/wsproxy
   User=1100
   Group=1100
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
   $ sudo systemctl enable --now backendai-wsproxy

   $ # To check the service status
   $ sudo systemctl status backendai-wsproxy
   $ # To restart the service
   $ sudo systemctl restart backendai-wsproxy
   $ # To stop the service
   $ sudo systemctl stop backendai-wsproxy
   $ # To check the service log and follow
   $ sudo journalctl --output cat -u backendai-wsproxy -f
