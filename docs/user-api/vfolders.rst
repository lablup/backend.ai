Virtual Folders
===============

Virtual folders provide access to shared, persistent, and reused files across
different kernel sessions.

You can mount virtual folders when creating new kernel sessions, and use them
like a plain directory on the local filesystem.
Of course, reads/writes to virtual folder contents may have degraded
performance compared to the main scratch directory (usually ``/home/work`` in
most kernels) as internally it uses a networked file system.

.. note::

   Currently the total size of a virtual folder is limited to 1 GiB and
   the number of files is limited to 1,000 files during public beta, but these
   limits are subject to change in the future.


Listing Virtual Folders
-----------------------

Retruns the list of virtual folders created by the current keypair.

* URI: ``/v2/folders``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``paging``
     - ``object``
     - :ref:`paging-query-object`.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``paging``
     - ``object``
     - :ref:`paging-info-object`.
   * - ``items``
     - ``list[object]``
     - A list of :ref:`vfolder-item-object`.


Creating a virtual folder
-------------------------

* URI: ``/v2/folders/create``
* Method: ``POST``

Creates a virtual folder associated with the current API key.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description

   * - ``tagName``
     - ``str``
     - The human-readable name of the virtual folder.

Example:

.. code-block:: json

   {
     "tagName": "My Data",
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
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``folderId``
     - ``slug``
     - The unique folder ID used for later API calls.


Example:

.. code-block:: json

   {
     "folderId": "oyU2WOYRYmjCGuKoSkiJ7H2rlN4"
   }


Getting Virtual Folder Information
----------------------------------

* URI: ``/v2/folders/:id``
* Method: ``GET``

Retrieves information about a virtual folder.
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

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``item``
     - ``object``
     - :ref:`vfolder-item-object`.


Deleting Virtual Folder
-----------------------

* URI: ``/v2/folders/:id``
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


Listing Files in Virtual Folder
---------------------------------

Returns the list of files in a virtual folder associated with current keypair.

* URI: ``/v2/folders/:id/files``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The virtual folder ID.
   * - ``path``
     - ``str``
     - Path inside the virtual folder (default: root).

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
   * - 404 Not Found
     - There is no such path.

.. list-table::
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``files``
     - ``str``
     - Stringified json containing list of files.
   * - ``folder_path``
     - ``str``
     - Absolute path inside the virtual folder.


Uploading Files to Virtual Folder
---------------------------------

Upload local files to a virtual folder associated with current keypair.

* URI: ``/v2/folders/:id/upload``
* Method: ``POST``

.. warning::
   If a file with the same name already exists in the virtual folder, it will
   be overwritten without warning.

Parameters
""""""""""

.. list-table::
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The virtual folder ID.
   * - Request content
     - ``list`` of ``aiohttp.web.FileField``_
     - List of file objects to upload.

.. _``aiohttp.web.FileField``: https://docs.aiohttp.org/en/stable/web_reference.html#aiohttp.web.FileField

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 201 Created
     - Success.


Downloading Files from Virtual Folder
-------------------------------------

Download files from a virtual folder associated with the current keypair.

The response contents are streamed as gzipped binaries
(``Content-Encoding: gzip``). Post-processing, such as reading by chunk or
unpacking the binaries, should be handled by the client.

* URI: ``/v2/folders/:id/download``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The virtual folder ID.
   * - ``files``
     - ``list`` of ``str``
     - File paths inside the virtual folder to download.

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
   * - 404 Not Found
     - File not found.


Deleting Files in Virtual Folder
--------------------------------

This deletes files inside a virtual folder.

.. warning::
   There is NO way to get back the files once this API is invoked.

* URI: ``/v2/folders/:id/delete_files``
* Method: ``DELETE``

Parameters
""""""""""

.. list-table::
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:id``
     - ``slug``
     - The virtual folder ID.
   * - ``files``
     - ``list`` of ``str``
     - File paths inside the virtual folder to delete.

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
