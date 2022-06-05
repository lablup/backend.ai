Backend.AI Documentation
========================

**Latest API version: v5.20191215**

Backend.AI is an enterprise-grade development and service backend for a wide range of AI-powered applications.
Its core technology is tailored for operating high density computing clusters including GPUs and heterogeneous accelerators.

From the user's perspective, Backend.AI is a cloud-like GPU powered HPC/DL application host ("Google Collab on your machine").
It runs arbitrary user codes safely in resource-constrained containers.
It hosts various programming languages and runtimes, such as Python 2/3, R, PHP, C/C++, Java, Javascript, Julia, Octave, Haskell, Lua and NodeJS, as well as AI-oriented libraries such as TensorFlow, Keras, Caffe, and MXNet.

From the admin's perspecetive, Backend.AI streamlines the process of assigning computing nodes, GPUs, and storage space to individual research team members.
With detailed policy-based idle checks and resource limits, you no longer have to worry about exceeding the capacity of the cluster when there are high demands.

Using the plugin architecture, Backend.AI also offers more advanced features such as fractional sharing of GPUs and site-specific SSO integrations, etc. for various-sized enterprise customers.

Table of Contents
-----------------

.. _concepts:

.. toctree::
   :maxdepth: 2
   :caption: Concepts

   concepts/key-concepts
   concepts/api-overview
   concepts/faq

.. _install:

.. toctree::
   :maxdepth: 2
   :caption: Cluster Installation

   install/guides
   install/supplementary
   install/configure-autoscaling

.. _migration:

.. toctree::
   :maxdepth: 2
   :caption: Migration Guides

   migration/2003-to-2009
   migration/docker-hub-to-backendai-cr

.. _clients:

.. toctree::
   :maxdepth: 1
   :caption: Client SDK

   client/index

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
   user-api/sessions
   user-api/service-ports
   user-api/exec-stream
   user-api/exec-query
   user-api/exec-batch
   user-api/events
   user-api/vfolders
   user-api/resource-presets

.. _admin_api:

.. toctree::
   :maxdepth: 1
   :caption: Admin API Reference

   admin-api/intro
   admin-api/agents
   admin-api/scaling-groups
   admin-api/domains
   admin-api/groups
   admin-api/users
   admin-api/images
   admin-api/sessions
   admin-api/vfolders
   admin-api/keypairs
   admin-api/keypair-resource-policies
   admin-api/resource-presets

.. _dev:

.. toctree::
   :maxdepth: 1
   :caption: Developer Manuals

   install/development-setup
   dev/daily-workflows
   dev/adding-kernels



Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

