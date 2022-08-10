Session Management
==================

Here are the API calls to create and manage compute sessions.

.. _create-session-api:

Creating Session
-----------------------

* URI: ``/session`` (``/session/create`` also works for legacy)
* Method: ``POST``

Creates a new session or returns an existing session, depending on the parameters.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description

   * - ``image``
     - ``str``
     - The kernel runtime type in the form of the Docker image name and tag.
       For legacy, the API also recognizes the ``lang`` field when ``image`` is not present.

       .. versionchanged:: v4.20190315

   * - ``architecture``
     - ``str``
     - *(optional)* Set an architecture of agents which run
       the session, such as ``"aarch64"`` or ``"x86_64"``.
       (default: ``"architecture of manager"``)

   * - ``sessionType``
     - ``str``
     - *(optional)* Set the type of session. It can be only ``"interactive"`` or ``"batch"``. (default: ``"interactive"``)

   * - ``clientSessionToken``
     - ``slug``
     - A client-provided session token, which must be unique among the
       currently non-terminated sessions owned by the requesting access key.
       Clients may reuse the token if the previous session with the same token has
       been terminated.

       It may contain ASCII alphabets, numbers, and hyphens in the middle.
       The length must be between 4 to 64 characters inclusively.
       It is useful for aliasing the session with a human-friendly name.

   * - ``enqueueOnly``
     - ``bool``
     - *(optional)* If set true, the API returns immediately after queueing the session creation request to the scheduler.
       Otherwise, the manager will wait until the session gets started actually.
       (default: ``false``)

       .. versionadded:: v4.20190615

   * - ``maxWaitSeconds``
     - ``int``
     - *(optional)* Set the maximum duration to wait until the session starts after queued, in seconds.  If zero,
       the manager will wait indefinitely.
       (default: ``0``)

       .. versionadded:: v4.20190615

   * - ``reuseIfExists``
     - ``bool``
     - *(optional)* If set true, the API returns *without* creating a new session if a session
       with the same ID and the same image already exists and not terminated.
       In this case ``config`` options are *ignored*.
       If set false but a session with the same ID and image exists, the
       manager returns an error: "session already exists".
       (default: ``true``)

       .. versionadded:: v4.20190615

   * - ``group``
     - ``str``
     - *(optional)* The name of a user group (aka "project") to launch the session within.  (default: ``"default"``)

       .. versionadded:: v4.20190615

   * - ``domain``
     - ``str``
     - *(optional)* The name of a domain to launch the session within  (default: ``"default"``)

       .. versionadded:: v4.20190615

   * - ``clusterSize``
     - ``str``
     - *(optional)* Set the number of containers the session spawns.  (default: ``1``)

   * - ``clusterMode``
     - ``str``
     - *(optional)* Set whether the session has a single kernel or multiple kernels.  (default: ``single-node``)

   * - ``config``
     - ``object``
     - *(optional)* A :ref:`creation-config-object` to specify kernel
       configuration including resource requirements.
       If not given, the kernel is created with the minimum required resource slots
       defined by the target image.

   * - ``tag``
     - ``str``
     - *(optional)* A per-session, user-provided tag for administrators to keep track of additional information of each session,
       such as which sessions are from which users.

   * - ``startsAt``
     - ``str``
     - *(optional)* Set the time when the session starts.

   * - ``startupCommand``
     - ``str``
     - *(optional)* A command which the session executes as soon as the session starts.

   * - ``bootstrapScript``
     - ``str``
     - *(optional)* A bootstrap script for the spawned kernels under the session.

   * - ``dependencies``
     - ``str``
     - *(optional)* A list of session IDs which the session depends on.

   * - ``callbackUrl``
     - ``str``
     - *(optional)* Set a callback url to send POST requests whenever the session status changes.

   * - ``owner_access_key``
     - ``str``
     - *(optional)* Set the owner of the session manually.

Example:

.. code-block:: json

   {
     "image": "python:3.6-ubuntu18.04",
     "clientSessionToken": "mysession-01",
     "enqueueOnly": false,
     "maxWaitSeconds": 0,
     "reuseIfExists": true,
     "domain": "default",
     "group": "default",
     "config": {
       "clusterSize": 1,
       "environ": {
         "MYCONFIG": "XXX",
       },
       "mounts": ["mydata", "mypkgs"],
       "resources": {
         "cpu": "2",
         "mem": "4g",
         "cuda.devices": "1",
       }
     },
     "tag": "example-tag"
   }


Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - The session is already running and you are okay to reuse it.
   * - 201 Created
     - The session is successfully created.
   * - 401 Invalid API parameters
     - There are invalid or malformed values in the API parameters.
   * - 406 Not acceptable
     - The requested resource limits exceed the server's own limits.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``sessId``
     - ``str``
     - The session ID used for later API calls. This is a random-generated UUID type string.
   * - ``sessionName``
     - ``slug``
     - The name of the session, which is same to the value of ``clientSessionToken``.
       The session name can be used for later API calls.
   * - ``status``
     - ``str``
     - The status of the created kernel. This is always ``"PENDING"`` if ``enqueueOnly`` is set true.
       In other cases, it may be either ``"RUNNING"`` (normal case),
       ``"ERROR"``, or even ``"TERMINATED"`` depending on what happens during
       session startup.

       .. versionadded:: v4.20190615

   * - ``servicePorts``
     - ``list[object]``
     - The list of :ref:`service-port-object`.
       This field becomes an empty list if ``enqueueOnly`` is set true, because the final service ports
       are determined when the session becomes ready after scheduling.

       .. note::

          In most cases the service ports are same to what specified in the image metadata, but the agent
          may add shared services for all sessions.

       .. versionchanged:: v4.20190615

   * - ``created``
     - ``bool``
     - True if the session is freshly created.


Example:

.. code-block:: json

   {
     "sessId": "7dab-1aa9-4451-a094-f0aba",
     "sessionName": "mysession-01",
     "status": "RUNNING",
     "servicePorts": [
       {"name": "jupyter", "protocol": "http"},
       {"name": "tensorboard", "protocol": "http"}
     ],
     "created": true
   }


Getting Session Information
---------------------------

* URI: ``/session/:id``
* Method: ``GET``

Retrieves information about a session.
For performance reasons, the returned information may not be real-time; usually
they are updated every a few seconds in the server-side.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The session ID or the session name.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - The information is successfully returned.
   * - 404 Not Found
     - There is no such session.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``domainName``
     - ``str``
     - The domain name, which the session belongs to.
   * - ``groupId``
     - ``str``
     - The group ID, which the session belongs to.
   * - ``userId``
     - ``str``
     - The user ID, which owns the session.
   * - ``image``
     - ``str``
     - The kernel's image.
   * - ``lang``
     - ``str``
     - (Legacy) The kernel's programming language.
       The value is identical to ``image``.
   * - ``architecture``
     - ``str``
     - The architecture of the node which runs the session.
   * - ``registry``
     - ``str``
     - The registry of the image used to spawn the session's kernels.
   * - ``tag``
     - ``str``
     - The tag of the session.
   * - ``containerId``
     - ``str``
     - The containerId of the session's main kernel.
   * - ``occupiedSlots``
     - ``str``
     - The resource slots the session is occupying.
   * - ``occupiedShares``
     - ``str``
     - The shared resource slots of the session.
   * - ``environ``
     - ``str``
     - The environment variables of the session.
   * - ``status``
     - ``str``
     - The status of the session.
   * - ``statusInfo``
     - ``str``
     - The reason of latest status change.
   * - ``statusData``
     - ``object``
     - The detail session status data which contains
       statuses of kernels and session, or error messages.
   * - ``age``
     - ``int`` (msec)
     - The time elapsed since the kernel has started.
   * - ``creationTime``
     - ``str``
     - The time session creates.
   * - ``terminationTime``
     - ``str``
     - The time session terminates.
   * - ``numQueriesExecuted``
     - ``int``
     - The number of times the kernel has been accessed.
   * - ``lastStat``
     - ``object``
     - The :ref:`container-stats-object` of the kernel.


Destroying Session
-------------------------

* URI: ``/session/:id``
* Method: ``DELETE``

Terminates a session.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The session ID.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 204 No Content
     - The session is successfully destroyed.
   * - 404 Not Found
     - There is no such session.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``stats``
     - ``object``
     - The :ref:`container-stats-object` of the kernel when deleted.


Restarting Session
-------------------------

* URI: ``/session/:id``
* Method: ``PATCH``

Restarts a session.
The idle time of the session will be reset, but other properties such as the age and CPU credit will continue to accumulate.
All global states such as global variables and modules imports are also reset.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The session ID.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 204 No Content
     - The session is successfully restarted.
   * - 404 Not Found
     - There is no such session.
