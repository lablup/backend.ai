.. role:: raw-html-m2r(raw)
   :format: html

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
while the "main1" kernel is allowed to access all other kernels via a private network (see **Cluster Networking**).

Session templates
-----------------

A session template is a predefined set of parameters to create a session, while they can be overriden by the caller.
It may define additional kernel roles for a cluster session, with different base images and resource specifications.

Session types
-------------

There are several classes of sessions for different purposes having different features.

Compute Session
~~~~~~~~~~~~~~~

Compute session is the most generic form of session to host computations.
It has two operation modes: *interactive* and *batch*.

Interactive compute session
^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
^^^^^^^^^^^^^^^^^^^^^

Batch compute sessions are used to host a "run-to-completion" script with a finite execution time.
It has two result states: SUCCESS or FAILED, which is defined by whether the main program's exit code is zero or not.

Dependencies between compute sessions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Pipelining

Inference Session
~~~~~~~~~~~~~~~~~

Service endpoint and routing

Auto-scaling

System Session
~~~~~~~~~~~~~~

SFTP access

Scheduling
----------

Backend.AI keeps track of sessions using a state-machine to represent the various lifecycle stages of them.

TODO: session/kernel state diagram

TODO: two-level scheduler architecture diagram

Session selection policy
~~~~~~~~~~~~~~~~~~~~~~~~

Heuristic FIFO
^^^^^^^^^^^^^^

Dominant resource fairness (DRF)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Agent selection policy
~~~~~~~~~~~~~~~~~~~~~~

Concentrated
^^^^^^^^^^^^

Dispersed
^^^^^^^^^

Custom
^^^^^^
