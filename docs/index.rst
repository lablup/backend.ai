.. Sorna API Library documentation master file, created by
   sphinx-quickstart on Tue Mar  1 21:26:20 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Sorna Documentation
===================

**Latest API version: v3.20170615** (beta)

Sorna is an online code execution service that runs arbitrary user codes
safely in resource-constrained environments, using Docker and our own sandbox
wrapper.
It currently supports Python 2/3, R, PHP, Javascript, Julia, Octave, Haskell, Lua and NodeJS for general programming language, and TensorFlow, Keras, Theano for Deep-learning environments (more being added).
Sorna's primary target is to provide a zero-configuration evaluation tool for
short-running programs used in education and scientific researches, such as
problem solving and plotting.

FAQ
---

The idea of a code (or function) execution service has existed for years, but no one ever reached the comfort offered by Sorna.
Here we describe key differences to existing products and software with similar purposes.

* What is the difference to AWS Lambda?

  * *On-the-fly execution of code snippets:* AWS Lambda mandates its users to package their own programs with libraries as a series of zip files and explicitly deploy them to run.  Meanwhile, Sorna provides a variety of pre-configured sandbox containers and its users pass the code snippets on-the-fly at runtime as individual API requests.
  * *Long-running large-scale computing sessions:* You can run even large-scale machine-learning training sessions with no time limits [1]_.  Sorna automatically bundles of multiple different servers for distributed, paralllel computation.
  * *On-premise deployability:* AWS Lambda is a strictly cloud-only service which requires Internet connections always, while Sorna can be deployed on your on-premise machines and portable PCs such as Intel NUC devices for use in off-line lecture rooms.

* What is the difference to Jupyter/IPython Notebook?

  * *Horizontal scalability:* Jupyter Notebook is designed for a single-user PC. JupyterHub supports multi-user scenarios but for only modest-sized, semi-trusted user groups. Sorna is designed for multiple arbitrary users and multiple servers to scale out from the very beginning.
  * *Additional security:* Sorna adds a sandbox layer using Docker containers and a custom system call filter to safely execute malicious, unpredictable user inputs without breaking the system and other users.


.. [1] On the public cloud service, we apply different limits depending on the subscription levels.


Table of Contents
-----------------

.. _gsg:

.. toctree::
   :maxdepth: 1
   :caption: User Manuals

   gsg/overview
   gsg/clientlib

.. _common_api:

.. toctree::
   :maxdepth: 1
   :caption: API Common Reference

   common-api/convention
   common-api/auth
   common-api/ratelimit
   common-api/objects

.. _user_api:

.. toctree::
   :maxdepth: 1
   :caption: User API Reference

   user-api/intro
   user-api/kernels
   user-api/exec-query
   user-api/exec-stream
   user-api/exec-batch
   user-api/vfolders

.. _admin_api:

.. toctree::
   :maxdepth: 1
   :caption: Admin API Reference

   admin-api/intro
   admin-api/keypairs
   admin-api/sessions

.. _dev:

.. toctree::
   :maxdepth: 1
   :caption: Developer Manuals

   dev/repl



Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

