API Overview
============

Backend.AI API v3 consists of two parts: User APIs and Admin APIs.

.. warning::

   APIv3 breaks backward compatibility a lot, and we will primarily support v3 after June 2017.
   Please upgrade your clients immediately.

API KeyPair Registration
------------------------

For managed, best-experience service, you may register to our cloud version of Backend.AI API service instead of installing it to your own machines.
Simply create an account at `cloud.backend.ai <https://cloud.backend.ai>`_ and generate a new API keypair.
You may also use social accounts for log-ins such as Twitter, Facebook, and GitHub.

An API keypair is composed of a 20-characters access key (``AKIA...``) and a 40-characters secret key, in a similar form to AWS access keys.

Currently, the service is BETA: it is free of charge but each user is limited to have only one keypair and have up to 5 concurrent sessions for a given keypair.
Keep you eyes on further announcements for upgraded paid plans.

Accessing Admin APIs
--------------------

The admin APIs require a special keypair with the admin privilege:

* The public cloud service (``api.backend.ai``): It currently does *not* offer any admin privileges to the end-users, as its functionality is already available via our management console at `cloud.backend.ai <https://cloud.backend.ai>`_.
* On-premise installation: You will get an auto-generated admin keypair during installation.
