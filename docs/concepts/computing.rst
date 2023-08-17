.. role:: raw-html-m2r(raw)
   :format: html

.. |br| raw:: html

   <br>

Computing
=========

Sessions and kernels
--------------------
:raw-html-m2r:`<span style="background-color:#c1e4f7;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`
:raw-html-m2r:`<span style="background-color:#e5f5ff;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Backend.AI spawns *sessions* to host various kinds of computation with associated computing resources.
Each session may have one or more *kernels*.
We call sessions with multiple kernels as "cluster sessions".

A *kernel* represents an isolated unit of computation such as a container, a virtual machine, a native process, or even a Kubernetes pod,
depending on the Agent's backed implementation and configurations.
The most common form of a kernel is a Docker container.
For container or VM-based kernels, they are also associated with the base images.
The most common form of a base image is `the OCI container images <https://github.com/opencontainers/image-spec/blob/main/spec.md>`_.

Kernel roles in a cluster session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In a cluster session with multiple kernels, each kernel has a role.
By default, the first container takes the "main" role while others takes the "sub" role.
All kernels are given unique hostnames like "main1", "sub1", "sub2", ..., and "subN" (the cluster size is N+1 in this case).
A non-cluster session has one "main1" kernel only.

All interactions with a session are routed to its "main1" kernel,
while the "main1" kernel is allowed to access all other kernels via a private network.

.. seealso::

   :ref:`concept-cluster-networking`

Session templates
-----------------

A session template is a predefined set of parameters to create a session, while they can be overriden by the caller.
It may define additional kernel roles for a cluster session, with different base images and resource specifications.

Session types
-------------

There are several classes of sessions for different purposes having different features.

.. list-table:: Features by the session type
   :header-rows: 1
   :stub-columns: 1

   * - Feature
     - Compute |br| (Interactive)
     - Compute |br| (Batch)
     - Inference
     - System
   * - Code execution
     - ✓
     - ✗
     - ✗
     - ✗
   * - Service port
     - ✓
     - ✓
     - ✓
     - ✓
   * - Dependencies
     - ✗
     - ✓
     - ✗
     - ✗
   * - Session result
     - ✗
     - ✓
     - ✗
     - ✗
   * - Clustering
     - ✓
     - ✓
     - ✓
     - ✓

Compute session is the most generic form of session to host computations.
It has two operation modes: *interactive* and *batch*.

Interactive compute session
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Interactive compute sessions are used to run various interactive applications and development tools,
such as Jupyter Notebooks, web-based terminals, and etc.
It is expected that the users control their lifecycles (e.g., terminating them)
while Backend.AI offers configuration knobs for the administrators to set idle timeouts with various criteria.

There are two major ways to interact with an interactive compute session: *service ports* and *the code execution API*.

Service ports

TODO: port mapping diagram

Code execution

TODO: execution API state diagram

Batch compute session
~~~~~~~~~~~~~~~~~~~~~

Batch compute sessions are used to host a "run-to-completion" script with a finite execution time.
It has two result states: SUCCESS or FAILED, which is defined by whether the main program's exit code is zero or not.

Dependencies between compute sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pipelining

Inference session
~~~~~~~~~~~~~~~~~

Service endpoint and routing

Auto-scaling

System session
~~~~~~~~~~~~~~

SFTP access

.. _concept-scheduler:
Scheduling
----------

Backend.AI keeps track of sessions using a state-machine to represent the various lifecycle stages of them.

TODO: session/kernel state diagram

TODO: two-level scheduler architecture diagram

.. seealso::

   :ref:`concept-resource-group`

Session selection strategy
~~~~~~~~~~~~~~~~~~~~~~~~~~

Heuristic FIFO
^^^^^^^^^^^^^^

The default session selection strategy is the heuristic FIFO.
It mostly works like a FIFO queue to select the oldest pending session,
but offers an option to enable a head-of-line (HoL) blocking avoidance logic.

The HoL blocking problem happens when the oldest pending session requires too much resources so that it cannot be scheduled
while other subsequent pending sessions fit within the available cluster resources.
Those subsequent pending sessions that can be started never have chances until the oldest pending session ("blocker") is either cancelled or more running sessions terminate and release more cluster resources.

When enabled, the HoL blocking avoidance logic keeps track of the retry count of scheduling attempts of each pending session and pushes back the pending sessions whose retry counts exceed a certain threshold.
This option should be explicitly enabled by the administrators or during installation.

Dominant resource fairness (DRF)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Agent selection strategy
~~~~~~~~~~~~~~~~~~~~~~~~

Concentrated
^^^^^^^^^^^^

Dispersed
^^^^^^^^^

Custom
^^^^^^
