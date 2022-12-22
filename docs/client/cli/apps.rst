Container Applications
======================

.. note::

   Please consult the detailed usage in the help of each command
   (use ``-h`` or ``--help`` argument to display the manual).


Starting a session and connecting to its Jupyter Notebook
---------------------------------------------------------

The following command first spawns a Python session named "mysession"
without running any code immediately, and then executes a local proxy which
connects to the "jupyter" service running inside the session via the local
TCP port 9900.
The ``start`` command shows application services provided by the created
compute session so that you can choose one in the subsequent ``app``
command.
In the ``start`` command, you can specify detailed resource options using
``-r`` and storage mounts using ``-m`` parameter.

.. code-block:: shell

  backend.ai start -t mysession python
  backend.ai app -b 9900 mysession jupyter

Once executed, the ``app`` command waits for the user to open the displayed
address using appropriate application.
For the jupyter service, use your favorite web browser just like the
way you use Jupyter Notebooks.
To stop the ``app`` command, press ``Ctrl+C`` or send the ``SIGINT`` signal.

Accessing sessions via a web terminal
-------------------------------------

All Backend.AI sessions expose an intrinsic application named ``"ttyd"``.
It is an web application that embeds xterm.js-based full-screen terminal
that runs on web browsers.

.. code-block:: shell

   backend.ai start -t mysession ...
   backend.ai app -b 9900 mysession ttyd

Then open ``http://localhost:9900`` to access the shell in a fully
functional web terminal using browsers.
The default shell is ``/bin/bash`` for Ubuntu/CentOS-based images and
``/bin/ash`` for Alpine-based images with a fallback to ``/bin/sh``.

.. note::

   This shell access does *NOT* grant your root access.
   All compute session processes are executed as the user privilege.


Accessing sessions via native SSH/SFTP
--------------------------------------

Backend.AI offers direct access to compute sessions (containers) via SSH
and SFTP, by auto-generating host identity and user keypairs for all
sessions.
All Baceknd.AI sessions expose an intrinsic application named ``"sshd"``
like ``"ttyd"``.

To connect your sessions with SSH, first prepare your session and download
an auto-generated SSH keypair named ``id_container``.
Then start the service port proxy ("app" command) to open a local TCP port
that proxies the SSH/SFTP traffic to the compute sessions:

.. code-block:: console

  $ backend.ai start -t mysess ...
  $ backend.ai session download mysess id_container
  $ mv id_container ~/.ssh
  $ backend.ai app mysess sshd -b 9922

In another terminal on the same PC, run your ssh client like:

.. code-block:: console

  $ ssh -o StrictHostKeyChecking=no \
  >     -o UserKnownHostsFile=/dev/null \
  >     -i ~/.ssh/id_container \
  >     work@localhost -p 9922
  Warning: Permanently added '[127.0.0.1]:9922' (RSA) to the list of known hosts.
  f310e8dbce83:~$

This SSH port is also compatible with SFTP to browse the container's
filesystem and to upload/download large-sized files.

You could add the following to your ``~/.ssh/config`` to avoid type
extra options every time.

.. code-block:: text

  Host localhost
    User work
    IdentityFile ~/.ssh/id_container
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

.. code-block:: console

  $ ssh localhost -p 9922

.. warning::

   Since the SSH keypair is auto-generated every time when your launch a
   new compute session, you need to download and keep it separately for
   each session.

To use your own SSH private key across all your sessions without
downloading the auto-generated one every time, create a vfolder named
``.ssh`` and put the ``authorized_keys`` file that includes the public key.
The keypair and ``.ssh`` directory permissions will be automatically
updated by Backend.AI when the session launches.

.. code-block:: console

  $ ssh-keygen -t rsa -b 2048 -f id_container
  $ cat id_container.pub > authorized_keys
  $ backend.ai vfolder create .ssh
  $ backend.ai vfolder upload .ssh authorized_keys
