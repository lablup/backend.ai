.. role:: raw-html-m2r(raw)
   :format: html

Install Docker
==============


.. image:: https://asciinema.org/a/dCkoIy27EwVvO6sVVXNaAWcCp.png
   :target: https://asciinema.org/a/dCkoIy27EwVvO6sVVXNaAWcCp
   :alt: asciicast


For platform-specific instructions, please consult `the docker official documentation <https://docs.docker.com/engine/installation/>`_.

Alternative way of docker installation on Linux (Ubuntu, CentOS, ...)

.. code-block:: console

   $ curl -fsSL https://get.docker.io | sh

type your password to install docker. 

Run docker commands without sudo (required)
-------------------------------------------

By default, you need sudo to execute docker commands.\ :raw-html-m2r:`<br>`
To do so without sudo, add yourself to the system ``docker`` group.

.. code-block:: console

   $ sudo usermod -aG docker $USER

It will work after restarting your login session.

Install docker-compose (only for development/single-server setup)
-----------------------------------------------------------------

You need to install docker-compose separately.\ :raw-html-m2r:`<br>`
Check out `the official documentation <https://docs.docker.com/compose/install/>`_.

Install nvidia-docker (only for GPU-enabled agents)
---------------------------------------------------

Check out `the official repository <https://github.com/NVIDIA/nvidia-docker>`_ for instructions.
