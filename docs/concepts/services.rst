.. role:: raw-html-m2r(raw)
   :format: html

Service Components
------------------

Public-facing services
~~~~~~~~~~~~~~~~~~~~~~

Manager and Webserver
^^^^^^^^^^^^^^^^^^^^^
:raw-html-m2r:`<span style="background-color:#fafafa;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Backend.AI manager is the central governor of the cluster.
It accepts user requests, creates/destroys the sessions, and routes code execution requests to appropriate agents and sessions.
It also collects the output of sessions and responds the users with them.

Backend.AI agent is a small daemon installed onto individual worker servers to control them.
It manages and monitors the lifecycle of kernel containers, and also mediates the input/output of sessions.
Each agent also reports the resource capacity and status of its server, so that the manager can assign new sessions on idle servers to load balance.

:raw-html-m2r:`<span style="background-color:#99d5ca;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`
:raw-html-m2r:`<span style="background-color:#202020;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

The primary networking requirements are:

* The manager server (the HTTPS 443 port) should be exposed to the public Internet or the network that your client can access.
* The manager, agents, and all other database/storage servers should reside at the same local private network where any traffic between them are transparently allowed.
* For high-volume big-data processing, you may want to separate the network for the storage using a secondary network interface on each server, such as Infiniband and RoCE adaptors.

App Proxy
^^^^^^^^^

Backend.AI App Proxy is a proxy to mediate the traffic between user applications and clients like browsers.
It provides the central place to set the networking and firewall policy for the user application traffic.

It has two operation modes:

* Port mapping: Individual app instances are mapped with a TCP port taken from a pre-configured range of TCP port range.
* Wildecard subdomain: Individual app instances are mapped with a system-generated subdomain under the given top-level domain.

Depending on the session type and application launch configurations, it may require an authenticated HTTP session for HTTP-based applications.
For instance, you may enforce authentication for interactive development apps like Jupyter while allow anonymous access for AI model service APIs.

Storage Proxy
^^^^^^^^^^^^^

Backend.AI Storage Proxy is a proxy to offload the large file transfers from the manager.
It also provides an abstraction of underlying storage vendor's acceleration APIs since many storage vendors offer vendor-specific APIs for filesystem operations like scanning of directories with millions of files.
Using the storage proxy, we apply our abstraction models for such filesystem operations and quota management specialized to each vendor API.

FastTrack (Enterprise only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Backend.AI FastTrack is an add-on service running on top of the manager that features a slick GUI to design and run pipelines of computation tasks.
It makes it easier to monitor the progress of various MLOps pipelines running concurrently, and allows sharing of such pielines in portable ways.

Resource Management
~~~~~~~~~~~~~~~~~~~

Sokovan Orchestrator
^^^^^^^^^^^^^^^^^^^^

Backend.AI Sokovan is the central cluster-level scheduler running inside the manager.
It monitors the resource usage of agents and assigns new containers from the job queue to the agents.

Each :ref:`resource group <concept-resource-group>` may have separate scheduling policy and options.
The scheduling algorithm may be extended using a common abstract interface.
A scheduler implementation accepts the list of currently running sessions, the list of pending sessions in the job queue, and the current resource usage of target agents.
It then outputs the choice of a pending session to start and the assignment of an agent to host it.

Agent
^^^^^

Backend.AI Agent is a small daemon running at each compute node like a GPU server.
Its main job is to control and monitor the containers via Docker, but also includes an abstraction of various "compute process" backends.
It publishes various types of container-related events so that the manager could react to status updates of containers.

When the manager assigns a new container, the agent decides the device-level resource mappings for the container considering optimal hardware layouts such as NUMA and the PCIe bus locations of accelerator and network devices.

Internal services
~~~~~~~~~~~~~~~~~

Event bus
^^^^^^^^^
:raw-html-m2r:`<span style="background-color:#ffbbb1;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Backend.AI uses Redis to keep track of various real-time information and notify system events to other service components.

Control Panel (Enterprise only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Backend.AI Control Panel is an add-on service to the manager for advanced management and monitoring.
It provides a dedicated superadmin GUI, featuring batch creation and modification of the users, detailed configuration of various resource policies, and etc.

Forklift (Enterprise only)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Backend.AI Forklift is a standalone service that eases building new container images from scratch or importing existing ones that are compatible with Backend.AI.

Reservoir (Enterprise only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Backend.AI Reservoir is an add-on service to provide open source package mirrors for air-gapped setups.

Container Registry
^^^^^^^^^^^^^^^^^^

Backend.AI supports integration with several common container registry solutions, while open source users may also rely on our official registry service with prebuilt images in https://cr.backend.ai:

* `Docker's vanilla open-source registry <https://docs.docker.com/registry/>`_

  - It is simplest to set up but does not provide advanced access controls and namespacing over container images.

* `Harbor v2 <https://goharbor.io/>`_ (recommended)

  - It provides a full-fledged container registry service including ACLs with project/user memberships, cloning from/to remote registries, on-premise and cloud deployments, security analysis, and etc.
