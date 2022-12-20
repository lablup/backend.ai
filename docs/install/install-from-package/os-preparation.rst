Setup OS Environment
====================

Backend.AI and its associated components share common requirements and
configurations for proper operation. This section explains how to configure the
OS environment.

.. note:: This section assumes the installation on Ubuntu 20.04 LTS.


Create a user account for operation
-----------------------------------

We will create a user account ``bai`` to install and operate Backend.AI
services. Set the ``UID`` and ``GID`` to ``1100`` to prevent conflicts with
other users or groups.  ``sudo`` privilege is required so add ``bai`` to
``sudo`` group.

.. code-block:: bash

   # If you do not want to expose your password in the shell history, remove the
   # --disabled-password option and interactively enter your password.
   username="bai"
   password="secure-password"
   sudo adduser --disabled-password --uid 1100 --gecos "" $username
   echo "$username:$password" | sudo chpasswd

   # Add the user to sudo group.
   sudo usermod -aG sudo bai

Login as the ``bai`` user and continue the installation.


Install Docker engine and Compose
---------------------------------

Backend.AI requires Docker Engine to create a compute session with the Docker
container backend. Also, some service components are deployed as containers. So
`installing Docker Engine <https://docs.docker.com/engine/install/ubuntu/>`_ is
required. `Install standalone Compose <https://docs.docker.com/compose/install/other/>`_
as well.

After the installation, add the ``bai`` user to the ``docker`` group not to
issue the ``sudo`` prefix command every time interacting with the Docker engine.

.. code-block:: bash

   sudo usermod -aG docker bai

Logout and login again to apply the group membership change.


Optimize sysctl/ulimit parameters
---------------------------------

This is not essential but the recommended step to optimize the performance and
stability of operating Backend.AI. Refer to the
`guide of the Manager repiository <https://github.com/lablup/backend.ai/blob/main/src/ai/backend/manager/README.md#kernelsystem-configuration>`_
for the details of the kernel parameters and the ulimit settings. Depending on the
Backend.AI services you install, the optimal values may vary. Each service
installation section guide with the values, if needed.

.. note::

   Modern systems may have already set the optimal parameters. In that case, you
   can skip this step.

To cleanly separate the configurations, you may follow the steps below.

- Save the resource limit parameters in ``/etc/security/limits.d/99-backendai.conf``.

  .. code-block:: bash

     root hard nofile 512000
     root soft nofile 512000
     root hard nproc 65536
     root soft nproc 65536
     bai hard nofile 512000
     bai soft nofile 512000
     bai hard nproc 65536
     bai soft nproc 65536

- Logout and login again to apply the resource limit changes.
- Save the kernel parameters in ``/etc/sysctl.d/99-backendai.conf``.

  .. code-block:: bash

     fs.file-max=2048000
     net.core.somaxconn=1024
     net.ipv4.tcp_max_syn_backlog=1024
     net.ipv4.tcp_slow_start_after_idle=0
     net.ipv4.tcp_fin_timeout=10
     net.ipv4.tcp_window_scaling=1
     net.ipv4.tcp_tw_reuse=1
     net.ipv4.tcp_early_retrans=1
     net.ipv4.ip_local_port_range="10000 65000"
     net.core.rmem_max=16777216
     net.core.wmem_max=16777216
     net.ipv4.tcp_rmem=4096 12582912 16777216
     net.ipv4.tcp_wmem=4096 12582912 16777216
     vm.overcommit_memory=1

- Apply the kernel parameters with ``sudo sysctl -p /etc/sysctl.d/99-backendai.conf``.


Prepare required version of Python
----------------------------------

Prepare a Python distribution whose version meets the requirements of the target
package. Backend.AI 22.09, for example, requires Python 3.10. The latest
information on the Python version compability can be found at
`here <https://github.com/lablup/backend.ai#package-installation-guide#python-version-compatibility>`_.

There can be several ways to prepare a specific Python version. Here, we will be
using pyenv and pyenv-virtualenv.


Use pyenv to manually build and select a specific Python version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Install `pyenv <https://github.com/pyenv/pyenv>`_ and
`pyenv-virtualenv <https://github.com/pyenv/pyenv-virtualenv>`_. Then, install
a Python version that are needed:

.. code-block::

   pyenv install $YOUR_PYTHON_VERSION

.. note::

   You may need to install
   `suggested build environment <https://github.com/pyenv/pyenv/wiki#suggested-build-environment>`_
   to build Python from pyenv.

Then, you can create multiple virtual environments per service. To create a
virtual environment for Backend.AI Manager 22.09.x and automatically activate it
under the ``$MANAGER_DIRECTORY``, for example, you may run:

.. code-block::

   cd $MANAGER_DIRECTORY
   pyenv virtualenv $YOUR_PYTHON_VERSION bai-22.09-manager
   pyenv local bai-22.09-manager
   pip install pip setuptools wheel

You also need to make ``pip`` available to the Python installation with the
latest ``wheel`` and ``setuptools`` packages, so that any non-binary extension
packages can be compiled and installed on your system.


Use a standalone static built Python
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

We can `use a standalone static built Python <https://github.com/indygreg/python-build-standalone/releases>`_.

.. warning:: Details will be added later.
