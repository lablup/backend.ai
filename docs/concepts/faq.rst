FAQ
===

.. rubric:: vs. Notebooks

.. list-table::
   :header-rows: 1

   * - Product
     - Role
     - Value

   * - Apache Zeppelin, Jupyter Notebook
     - Notebook-style document + code *frontends*
     - Familiarity from data scientists and researchers, but hard to avoid insecure host resource sharing

   * - **Backend.AI**
     - Pluggable *backend* to any frontends
     - Built for multi-tenancy: scalable and better isolation

.. rubric:: vs. Orchestration Frameworks

.. list-table::
   :header-rows: 1

   * - Product
     - Target
     - Value

   * - Amazon ECS, Kubernetes
     - Long-running interactive services
     - Load balancing, fault tolerance, incremental deployment

   * - Amazon Lambda, Azure Functions
     - Stateless light-weight, short-lived functions
     - Serverless, zero-management

   * - **Backend.AI**
     - Stateful batch computations mixed with interactive applications
     - Low-cost high-density computation, maximization of hardware potentials

.. rubric:: vs. Big-data and AI Frameworks

.. list-table::
   :header-rows: 1

   * - Product
     - Role
     - Value

   * - TensorFlow, Apache Spark, Apache Hive
     - Computation runtime
     - Difficult to install, configure, and operate at scale

   * - Amazon ML, Azure ML, GCP ML
     - Managed MLaaS
     - Highly scalable but dependent on each platform, still requires system engineering backgrounds

   * - **Backend.AI**
     - Host of computation runtimes
     - Pre-configured, versioned, reproducible, customizable (open-source)


(All product names and trade-marks are the properties of their respective owners.)
