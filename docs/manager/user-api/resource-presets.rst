Resource Presets
================

Resource presets provide a simple storage for pre-configured resource slots
and a dynamic checker for allocatability of given presets before actually
calling the kernel creation API.

To add/modify/delete resource presets, you need to use the admin GraphQL API.

.. versionadded:: v4.20190315


Listing Resource Presets
------------------------

Returns the list of admin-configured resource presets.

* URI: ``/resource/presets``
* Method: ``GET``

Parameters
""""""""""

None.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - The preset list is returned.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``presets``
     - ``list[object]``
     - The list of :ref:`resource-preset-object`


Checking Allocatability of Resource Presets
-------------------------------------------

Returns current keypair and scaling-group's resource limits in addition to the
list of admin-configured resource presets.
It also checks the allocatability of the resource presets and adds ``allocatable``
boolean field to each preset item.

* URI: ``/resource/check-presets``
* Method: ``POST``

Parameters
""""""""""

None.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - The preset list is returned.
   * - 401 Unauthorized
     - The client is not authorized.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``keypair_limits``
     - :ref:`resource-slot-object`
     - The maximum amount of total resource slots allowed for the current access key.
       It may contain infinity values as the string "Infinity".
   * - ``keypair_using``
     - :ref:`resource-slot-object`
     - The amount of total resource slots used by the current access key.
   * - ``keypair_remaining``
     - :ref:`resource-slot-object`
     - The amount of total resource slots remaining for the current access key.
       It may contain infinity values as the string "Infinity".
   * - ``scaling_group_remaining``
     - :ref:`resource-slot-object`
     - The amount of total resource slots remaining for the current scaling group.
       It may contain infinity values as the string "Infinity" if the server is configured
       for auto-scaling.
   * - ``presets``
     - ``list[object]``
     - The list of :ref:`resource-preset-object`, but with an extra boolean field ``allocatable``
       which indicates if the given resource slot is actually allocatable considering
       the keypair's resource limits and the scaling group's current usage.
