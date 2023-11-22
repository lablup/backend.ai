.. include:: <isonum.txt>

Environment specifics: WSL v2
=============================

Backend.AI supports running on WSL (Windows Subsystem for Linux) version 2.
However, you need to configure some special options so that the WSL distribution can interact with the Docker Desktop service.

Configuration of Docker Desktop for Windows
-------------------------------------------

Turn on WSL Integration on Settings |rarr| Resources |rarr| WSL INTEGRATION.
For the most cases, this should be already configured when you install Docker Desktop for Windows.

.. seealso::

   https://docs.docker.com/desktop/wsl/

Configuration of WSL
--------------------

1. Create or modify ``/etc/wsl.conf`` using ``sudo`` in the WSL shell.

2. Write down this and save.

   .. code-block:: dosini

      [automount]
      root = /
      options = "metadata"

3. Run ``wsl --shutdown`` in a PowerShell prompt to restart the WSL distribution to ensure your ``wsl.conf`` updates applied.

4. Enter the WSL shell again. If it is applied, your path must appears like ``/c/some/path`` instead of ``/mnt/c/some/path``.

5. Run ``sudo mount --make-rshared /`` in the WSL shell. Otherwise, your container creation from Backend.AI will fail with an error message like ``aiodocker.exceptions.DockerError: DockerError(500, 'path is mounted on /d but it is not a shared mount.')``.

Installation of Backend.AI
--------------------------

Now you may run the installer in the WSL shell.
