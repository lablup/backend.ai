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


Storage Proxy
^^^^^^^^^^^^^


FastTrack
^^^^^^^^^


Resource controller
~~~~~~~~~~~~~~~~~~~

Agent
^^^^^


Internal services
~~~~~~~~~~~~~~~~~

Event bus
^^^^^^^^^
:raw-html-m2r:`<span style="background-color:#ffbbb1;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Backend.AI uses Redis to keep track of various real-time information and notify system events to other service components.

Forklift
^^^^^^^^

Reservoir
^^^^^^^^^

Container Registry
^^^^^^^^^^^^^^^^^^

About Harbor


