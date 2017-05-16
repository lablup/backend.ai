Statistics
==========

Per-keypair Usage Counter
-------------------------

* URI: ``/v2/admin/usage/:access_key``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:access_key``
     - The access key of the keypair.
   * - ``keys``
     - The comman-separated key list of desired statistic values.

       Available keys are:

       * storage

Response
""""""""

Per-keypair Billing Calculator
------------------------------

* URI: ``/v2/admin/bill/:access_key``
* Method: ``GET``

