Virtual Folders
===============

Virtual folders provide access to shared, persistent, and reused files across different kernel sessions.

You can mount virtual folders when creating new kernel sessions, and use them
like a plain directory on the local filesystem.
Of course, reads/writes to virtual folder contents may have degraded
performance compared to the main scratch directory (usually ``/home/work`` in
most kernels) as internally it uses a networked file system.

.. note::

   Currently the total size of a virtual folder is limited to 1 GiB and
   the number of files is limited to 1,000 files during public beta, but these
   limits are subject to change in the future.


Creating a virtual folder
-------------------------

* URI: ``/v2/folder/create``
* Method: ``POST``

Creates a virtual folder associated with the current API key.

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description

   * - ``name``
     - The human-readable name of the virtual folder.
       Only ASCII alpha-numeric characters, hyphens, and underscores are allowed.
       The name must start with alpha-numeric characters.

Example:

.. code-block:: json

   {
     "name": "mydata",
   }


Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 201 Created
     - The kernel is successfully created.
   * - 400 Bad Request
     - The name is malformed or duplicate with your existing
       virtual folders.
   * - 406 Not acceptable
     - You have exceeded internal limits of virtual folders.
       (e.g., the maximum number of folders you can have.)

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Fields
     - Values
   * - ``folderId``
     - The unique folder ID used for later API calls.


Example:

.. code-block:: json

   {
     "kernelId": "oyU2WOYRYmjCGuKoSkiJ7H2rlN4"
   }


Getting virtual folder information
----------------------------------

* URI: ``/v2/folder/:id``
* Method: ``GET``

Retrieves information about a virtual folder.
For performance reasons, the returned information may not be real-time; usually
they are updated every a few seconds in the server-side.

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
     - The virtual folder ID.

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
     - There is no such folder.

(TODO)


Deleting a virtual folder
-------------------------

* URI: ``/v2/folder/:id``
* Method: ``DELETE``

This immediately deletes all contents of the given virtual folder and makes the
folder unavailable for future mounts.

.. danger::

   If there are running kernels that have mounted the deleted virtual folder,
   those kernels are likely to break!

.. warning::

   There is NO way to get back the contents once this API is invoked.

Parameters
""""""""""

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - Parameter
     - Description
   * - ``:id``
     - The virtual folder ID.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 204 No Content
     - The folder is successfully destroyed.
   * - 404 Not Found
     - There is no such folder.

Acessing virtual folders via WebDAV
-----------------------------------

(TODO)
