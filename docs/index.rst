.. Backend.AI documentation master file, created by
   sphinx-quickstart on Tue Mar  1 21:26:20 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Backend.AI API Documentation
============================

**Latest API version: v4.20190315**

Backend.AI is a hassle-free backend for AI programming and service.
It runs arbitrary user codes safely in resource-constrained environments, using Docker and our own sandbox wrapper.

Backend.AI supports various programming languages and runtimes, such as Python 2/3, R, PHP, C/C++, Java, Javascript, Julia, Octave, Haskell, Lua and NodeJS, as well as AI-oriented libraries such as TensorFlow, Keras, Caffe, and MXNet.

Table of Contents
-----------------

.. _gsg:

.. toctree::
   :maxdepth: 1
   :caption: User Manuals

   gsg/overview
   gsg/faq
   gsg/clientlib

.. _install:

.. toctree::
   :maxdepth: 2
   :caption: Cluster Installation

   install/guides
   install/supplementary

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
   user-api/exec-stream
   user-api/exec-query
   user-api/exec-batch
   user-api/vfolders
   user-api/resource-presets

.. _admin_api:

.. toctree::
   :maxdepth: 1
   :caption: Admin API Reference

   admin-api/intro
   admin-api/keypairs
   admin-api/sessions
   admin-api/vfolders
   admin-api/stats

.. _dev:

.. toctree::
   :maxdepth: 1
   :caption: Developer Manuals

   install/development-setup
   dev/repl



Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

