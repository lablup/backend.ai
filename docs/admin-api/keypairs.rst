KeyPair Management
==================

Listing KeyPairs
----------------

* URI: ``/v2/admin/keypairs/:user``
* Method: ``REPORT``

Returns the list of keypairs associated with the given user UUID.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:user``
     - ``str``
     - The associated user ID.
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
     - The list of keypair is being returned.

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
     - ``list[object]``
     - A list of :ref:`keypair-item-object`

Creating KeyPair
----------------

* URI: ``/v2/admin/keypairs/:user/create``
* Method: ``POST``

Creates a new keypair associated with the given user UUID.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:user``
     - ``str``
     - The associated user ID.
       The exact format would depend on your user management system.
   * - ``isActive``
     - ``bool``
     - If specified, set the key's initial activation status after creation.
       (optional, default: ``true``)

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - A new keypair is being returned.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``accessKey``
     - ``str``
     - The access key part.
   * - ``secretKey``
     - ``str``
     - The secret key part.

Getting KeyPair Properties
--------------------------

* URI: ``/v2/admin/keypairs/:user/:accessKey``
* Method: ``GET``

Retrieves the current values of the given list of properties.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:user``
     - ``str``
     - The associated user ID.
   * - ``:accessKey``
     - ``slug``
     - The access key of the keypair.
   * - ``keys``
     - ``list[str]``
     - The list of the property names available in :ref:`keypair-props-object`.

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
     - There is no such keypair.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``values``
     - ``list[*]``
     - The values of the request properties, in the same order of the request.

Updating KeyPair Properties
---------------------------

* URI: ``/v2/admin/keypairs/:user/:accessKey``
* Method: ``PATCH``

Updates the given list of properties to the given values.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:user``
     - ``str``
     - The associated user ID.
   * - ``:accessKey``
     - ``slug``
     - The access key of the keypair.
   * - ``props``
     - ``object``
     - A part of :ref:`keypair-props-object` containing only modified properties.

Deleting KeyPair
----------------

* URI: ``/v2/admin/keypairs/:user/:accessKey``
* Method: ``DELETE``

Delete a keypair. This is not a reversible operation, and only intended for use in database clean-ups.
In most cases when you need to delete a keypair, deactivate it instead using the property change API above.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:user``
     - ``str``
     - The associated user ID.
   * - ``:accessKey``
     - ``slug``
     - The access key of the keypair.
