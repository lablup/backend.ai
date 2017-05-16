JSON Object References
======================

.. _paging-query-object:

Paging Query Object
-------------------

It describes how many items to fetch for object listing APIs.
If ``index`` exceeds the number of pages calculated by the server, an empty list is returned.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``size``
     - ``int``
     - The number of items per page.
   * - ``index``
     - ``int``
     - The page number to show, zero-based.

.. _paging-info-object:

Paging Info Object
------------------

It contains the paging information based on the paging query object in the request.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``pages``
     - ``int``
     - The number of total pages.
   * - ``count``
     - ``int``
     - The number of all items.

.. _keypair-item-object:

KeyPair Item Object
-------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``accessKey``
     - ``slug``
     - The access key part.
   * - ``isActive``
     - ``bool``
     - Indicates if the keypair is active or not.
   * - ``totalQueries``
     - ``int``
     - The number of queries done via this keypair. It may have a stale value.
   * - ``created``
     - ``datetime``
     - The timestamp when the keypair was created.

.. _keypair-props-object:

KeyPair Properties Object
-------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``isActive``
     - ``bool``
     - Indicates if the keypair is activated or not.
       If not activated, all authentication using the keypair returns 401 Unauthorized.
       When changed from ``true`` to ``false``, existing running kernel sessions continue to run but any requests to create new kernel sessions are refused.
       (default: ``true``)
   * - ``concurrecy``
     - ``int``
     - The maximum number of concurrent kernel sessions allowed for this keypair.
       (default: ``5``)
   * - ``ML.clusterSize``
     - ``int``
     - Sets the number of instances clustered together when launching new machine learning kernel sessions. (default: ``1``)
   * - ``ML.instanceMemory``
     - ``int`` (GiB)
     - Sets the memory limit of each instance in the cluster launched for new machine learning kernel sessions. (default: ``8``)

The enterprise edition offers the following additional properties:

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``cost.automatic``
     - ``bool``
     - If set ``true``, enables automatic cost optimization (BETA).
       With supported kernel types, it automatically suspends or resize the kernel sessions not to exceed the configured cost limit per day.
       (default: ``false``)
   * - ``cost.dailyLimit``
     - ``str``
     - The string representation of money amount as decimals.
       The currency is fixed to USD. (default: ``"50.00"``)


.. _session-filter-object:

Session Filter Object
---------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``status``
     - ``enum[str]``
     - Either ``"ongoing"`` or ``"finished"``.
       Note that ``"finished"`` status includes ``"success"`` and ``"error"`` only whereas ``"ongoing"`` includes all other status.

.. _session-item-object:

Session Item Object
---------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``kernelId``
     - ``slug``
     - The kernel session ID.
   * - ``status``
     - ``enum[str]``
     - One of ``"preparing"``, ``"building``", ``"running"``, ``"restarting"``, ``"resizing"``, ``"success"``, ``"error"``, ``"terminating"``, ``"suspended"``.
   * - ``statusInfo``
     - ``str``
     - An optional message related to the current status. (e.g., error information)
   * - ``usedMemory``
     - ``int`` (KiB)
     - The amount of memory currently using. It may show a stale value.
   * - ``cpuUtil``
     - ``int`` (%)
     - The current CPU utilization (sum of all used cores across instances, hence may exceed 100%). It may show a stale value.
   * - ``config.clusterSize``
     - ``int``
     - The configured number of instances bundled for this session.
   * - ``config.instanceMemory``
     - ``int`` (GiB)
     - The configured memory size per instance.

.. _resource-limit-object:

Resource Limit Object
---------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``maxMem``
     - ``int`` (KiB)
     - Maximum memory allowed.
   * - ``execTimeout``
     - ``int`` (msec)
     - Maximum total CPU time.

.. _vfolder-item-object:

Virtual Folder Item Object
--------------------------

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Key
     - Type
     - Description
   * - ``name``
     - ``str``
     - The human readable name set when created.
   * - ``id``
     - ``slug``
     - The unique ID of the folder. Use this when making API requests referring this folder.
   * - ``linked``
     - ``bool``
     - Indicates if this folder is linked to an external service. (enterprise edition only)
   * - ``usedSize``
     - ``int`` (MiB)
     - The sum of the size of files in this folder.
   * - ``numFiles``
     - ``int``
     - The number of files in this folder.
   * - ``maxSize``
     - ``int`` (MiB)
     - The maximum size of this folder.
   * - ``created``
     - ``datetime``
     - The date and time when the folder is created.

