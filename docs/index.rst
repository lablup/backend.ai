Backend.AI Documentation
========================

**Latest API version: v6.20220615**

Backend.AI is an enterprise-grade development and service backend for a wide range of AI-powered applications.
Its core technology is tailored for operating high density computing clusters including GPUs and heterogeneous accelerators.

From the user's perspective, Backend.AI is a cloud-like GPU powered HPC/DL application host ("Google Colab on your machine").
It runs arbitrary user codes safely in resource-constrained containers.
It hosts various programming languages and runtimes, such as Python 2/3, R, PHP, C/C++, Java, JavaScript, Julia, Octave, Haskell, Lua and Node.js, as well as AI-oriented libraries such as TensorFlow, Keras, Caffe, and MXNet.

From the admin's perspective, Backend.AI streamlines the process of assigning computing nodes, GPUs, and storage space to individual research team members.
With detailed policy-based idle checks and resource limits, you no longer have to worry about exceeding the capacity of the cluster when there are high demands.

Using the plugin architecture, Backend.AI also offers more advanced features such as fractional sharing of GPUs and site-specific SSO integrations, etc. for various-sized enterprise customers.

.. toctree::
   :maxdepth: 2

   concepts/index
   install/index
   user/index
   dev/index
   migration/index
   manager/index
   agent/index
   storage-proxy/index
   client/index



Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

