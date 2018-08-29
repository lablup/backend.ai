.. Backend.AI documentation master file, created by
   sphinx-quickstart on Tue Mar  1 21:26:20 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Backend.AI Documentation
========================

**Latest API version: v3.20170615** (beta)

Backend.AI is a hassle-free backend for AI programming and service.
It runs arbitrary user codes safely in resource-constrained environments, using Docker and our own sandbox wrapper.

Backend.AI supports various programming languages and runtimes, such as Python 2/3, R, PHP, C/C++, Java, Javascript, Julia, Octave, Haskell, Lua and NodeJS, as well as AI-oriented libraries such as TensorFlow, Keras, Caffe, and MXNet.

FAQ
---

vs. Notebooks
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Product
     - Role
     - Problem and Solution

   * - Apache Zeppelin, Jupyter Notebook
     - Notebook-style document + code *front-ends*
     - Insecure host resource sharing

   * - **Backend.AI**
     - Pluggable *back-end* to any front-ends
     - Built for multi-tenancy: scalable and better isolation

vs. Orchestration Frameworks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Product
     - Target
     - Value

   * - Amazon ECS, Kubernetes
     - Long-running service daemons
     - Laod balancing, fault tolerance, incremental deployment

   * - **Backend.AI**
     - Stateful compute sessions
     - Low-cost high-density computation

   * - Amazon Lambda
     - Stateless, light-weight functions
     - Serverless, zero-management

vs. Big-data and AI Frameworks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Product
     - Role
     - Problem and Solution

   * - TensorFlow, Apache Spark, Apache Hive
     - Computation runtime
     - Difficult to install, configure, and operate

   * - Amazon ML, Azure ML, GCP ML
     - Managed MLaaS
     - Still complicated for scientists, too restrictive for engineers

   * - **Backend.AI**
     - Host of computation runtimes
     - Pre-configured, versioned, reproducible, customizable (open-source)


(All product names and trade-marks are the properties of their respective owners.)

Table of Contents
-----------------

.. _gsg:

.. toctree::
   :maxdepth: 1
   :caption: User Manuals

   gsg/overview
   gsg/clientlib

.. _install:

.. toctree::
   :maxdepth: 1
   :caption: Installation

   install/overview

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
   admin-api/vfolders
   admin-api/stats

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

