Kernel Session Monitoring
=========================

Listing Kernel Sessions
-----------------------

* URI: ``/v2/admin/sessions/:access_key``
* Method: ``REPORT``

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:access_key``
     - ``slug``
     - The access key.
   * - ``filter``
     - ``object``
     - :ref:`session-filter-object`
   * - ``paging``
     - ``object``
     - :ref:`paging-query-object`

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - The list of kernel sessions is being returned.


.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``paging``
     - ``object``
     - :ref:`paging-info-object`
   * - ``items``
     - ``object``
     - A list of :ref:`session-item-object`
