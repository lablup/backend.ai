
Demo Setup
==========

`This meta-repository <https://github.com/lablup/backend.ai>`_ provides a docker-compose configuration to fire up a single-node Backend.AI cluster running on your PC (http://localhost:8081).  

Prerequisites
-------------


* All: `install Docker 17.06 or later <https://docs.docker.com/install/>`_ with `docker-compose v1.21 or later <https://docs.docker.com/compose/install/>`_
* Linux users: change "docker.for.mac.localhost" in docker-compose.yml to "172.17.0.1"

* intstall docker-ce at Centos 7.5
.. code-block:: console  
   $ sudo curl -fsSL https://get.docker.io | sh
   $ sudo usermod -aG docker your-user

* install pre-requirement package
.. code-block:: console
   $ sudo yum install gcc zlib-devel bzip2 bzip2-devel readline readline-devel sqlite sqlite-devel openssl openssl-devel git

* install pyenv that support enviroment for Python
.. code-block:: console
   $ git clone https://github.com/pyenv/pyenv.git ~/.pyenv
   $ echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bash_profile
   $ echo 'eval "$(pyenv init -)"' >> ~/.bash_profile
   $ source ~/.bash_profile
   $ exec $SHELL -l

* install pyenv that support virtual enviroment for Python
.. code-block:: console
   $ git clone https://github.com/yyuu/pyenv-virtualenv.git ~/.pyenv/plugins/pyenv-virtualenv
   $ echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bash_profile
   $ exec $SHELL -l

* install python 3.6.x to run backend.ai
.. code-block:: console
   $ pyenv install 3.6.7
   $ pyenv virtualenv 3.6.7 backend.ai

* install requirement packer of python and docker
  * Clone the repository
  * Check out the prerequisites above    
.. code-block:: console
   $ git clone https://github.com/lablup/backend.ai.git
   $ cd backend.ai
   $ pyenv local backend.ai
   $ pip install -U pip setuptools
   $ pip install docker-compose
   
Notes
^^^^^

* This demo setup does *not* support GPUs.

All you have to do
------------------

* ``docker-compose up -d``

* Pull some kernel images to try out

Pulling kernel images
^^^^^^^^^^^^^^^^^^^^^

Pull the images on your host Docker daemon like:

.. code-block:: console

   $ docker pull lablup/kernel-python:latest
   $ docker pull lablup/kernel-python-tensorflow:latest-dense
   $ docker pull lablup/kernel-c:latest

By default this demo cluster already has metadata/alias information for `all publicly available Backend.AI kernels <https://github.com/lablup/backend.ai-kernels>`_\ , so you don't have to manually register the pulled kernel information to the cluster but only have to *pull* those you want to try out.

Using Clients
^^^^^^^^^^^^^

To access this local cluster, set the following configurations to your favoriate Backend.AI client:

.. code-block:: console

   $ export BACKEND_ENDPOINT="http://localhost:8081"
   $ export BACKEND_ACCESS_KEY="AKIAIOSFODNN7EXAMPLE"
   $ export BACKEND_SECRET_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

With `our official Python client <http://pypi.python.org/pypi/backend.ai-client>`_\ , you can do:

.. code-block:: console

   $ backend.ai run python -c "print('hello world')"
   ✔ Session 9c737d84724173354fa10445d0b35fe0 is ready.
   hello world
   ✔ Finished. (exit code = 0)

   $ backend.ai run python-tensorflow:latest-dense -c "import tensorflow as tf; print(tf.__version__)"
   ✔ Session 950713741d5ed43a191704f2cd375ff0 is ready.
   1.5.0
   ✔ Finished. (exit code = 0)

WARNING: This demo configuration is highly insecure. DO NOT USE in production!

FAQ
---


* When launching a kernel, it says "Service Unavailable"!

  * Each image has different default resource requirements and your Docker daemon may have a too small amount of resources. For example, TensorFlow images require 8 GiB or more RAM for your Docker daemon.
  * Or, you might have launched 30 kernel sessions already, which is the default limit for this demo setup.

* What does the "dense" tag mean in the TensorFlow kernel images?

  * Images with "dense" tags are optimized for shared multi-tenancy environments. There is no difference in functionalities.
