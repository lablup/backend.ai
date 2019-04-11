Virtual Folders
===============

Virtual folders provide access to shared, persistent, and reused files across
different kernel sessions.

You can mount virtual folders when creating new kernel sessions, and use them
like a plain directory on the local filesystem.
Of course, reads/writes to virtual folder contents may have degraded
performance compared to the main scratch directory (usually ``/home/work`` in
most kernels) as internally it uses a networked file system.

Also, you might share your virtual folders with other users by inviting them
and granting them proper permission. Currently, there are three levels of
permissions: read-only, read-write, read-write-delete. They are represented
by short strings, ``'ro'``, ``'rw'``, ``'rd'``, respectively. The owner of a
virtual folder have read-write-delete permission for the folder.

.. note::

   Currently the total size of a virtual folder is limited to 1 GiB and
   the number of files is limited to 1,000 files during public beta, but these
   limits are subject to change in the future.


Listing Virtual Folders
-----------------------

Returns the list of virtual folders created by the current keypair.

* URI: ``/folders``
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
     - Success.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - (root)
     - ``list[object]``
     - A list of :ref:`vfolder-list-item-object`.

Example:

.. code-block:: json

   [
     { "name": "mydata", "id": "5da5f8e163dd4b86826d6b4db2b7b71a", "...": "..." },
     { "name": "sample01", "id": "0ecfab9e608c478f98d1734b02a54774", "...": "..." },
   ]


Listing Virtual Folder Hosts
----------------------------

Returns the list of available host names where the current keypair can create new virtual folders.

.. versionadded:: v4.20190315

* URI: ``/folders/_/hosts``
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
     - Success.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``default``
     - ``str``
     - The default virtual folder host.
   * - ``allowed``
     - ``list[str]``
     - The list of available virtual folder hosts.

Example:

.. code-block:: json

   {
     "default": "nfs1",
     "allowed": ["nfs1", "nfs2", "cephfs1"]
   }

Creating a Virtual Folder
-------------------------

* URI: ``/folders``
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

   * - ``name``
     - ``str``
     - The human-readable name of the virtual folder.
   * - ``host``
     - ``str``
     - (optional) The name of the virtual folder host.

Example:

.. code-block:: json

   {
     "name": "My Data",
     "host": "nfs1"
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
   * - ``id``
     - ``slug``
     - The unique folder ID used for later API calls.
   * - ``name``
     - ``str``
     - The human-readable name of the created virtual folder.
   * - ``host``
     - ``str``
     - The name of the virtual folder host where the new folder is created.


Example:

.. code-block:: json

   {
     "id": "aef1691db3354020986d6498340df13c",
     "name": "My Data",
     "host": "nfs1"
   }


Getting Virtual Folder Information
----------------------------------

* URI: ``/folders/:name``
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
   * - ``name``
     - ``str``
     - The human-readable name of the virtual folder.

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
     - There is no such folder or you may not have proper permission
       to access the folder.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - (root)
     - ``object``
     - :ref:`vfolder-item-object`.


Deleting Virtual Folder
-----------------------

* URI: ``/folders/:name``
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
   * - ``name``
     - The human-readable name of the virtual folder.

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
     - There is no such folder or you may not have proper permission
       to delete the folder.


Listing Files in Virtual Folder
---------------------------------

Returns the list of files in a virtual folder associated with current keypair.

* URI: ``/folders/:name/files``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:name``
     - ``str``
     - The human-readable name of the virtual folder.
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
     - There is no such path or you may not have proper permission
       to access the folder.

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``files``
     - ``list[object]``
     - List of :ref:`vfolder-file-object`


Uploading Multiple Files to Virtual Folder
------------------------------------------

Upload local files to a virtual folder associated with current keypair.

* URI: ``/folders/:name/upload``
* Method: ``POST``

.. warning::
   If a file with the same name already exists in the virtual folder, it will
   be overwritten without warning.

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:name``
     - ``str``
     - The human-readable name of the virtual folder.
   * - (body)
     - ``multipart``
     - A multi-part encoded file data which is composed of multiple occurrences
       of ``src`` field.  Each part must contain a valid filename and the content
       type is always assumed as ``application/octet-stream``.

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 201 Created
     - Success.
   * - 400 Bad Request
     - There already exists a file with duplicated name
       that cannot be overwritten in the virtual folder.
   * - 404 Not Found
     - There is no such folder or you may not have proper permission
       to write into folder.


Creating New Directory in Virtual Folder
----------------------------------------

Create a new directory in the virtual folder associated with current keypair.
this API recursively creates parent directories if they does not exist.

* URI: ``/folders/:name/mkdir``
* Method: ``POST``

.. warning::
   If a directory with the same name already exists in the virtual folder, it will
   be overwritten without warning.

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:name``
     - ``str``
     - The human-readable name of the virtual folder.
   * - ``path``
     - ``str``
     - The relative path of a new folder to create
       inside the virtual folder.

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 201 Created
     - Success.
   * - 400 Bad Request
     - There already exists a file, not a directory, with duplicated name.
   * - 404 Not Found
     - There is no such folder or you may not have proper permission
       to write into folder.


Downloading Single File from Virtual Folder
-------------------------------------------

Download a single file from a virtual folder associated with the current keypair.
This API does not perform any encoding or compression but just outputs the raw
file content as the response body, for simpler client-side implementation.

.. versionadded:: v4.20190315

* URI: ``/folders/:name/download_single``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:name``
     - ``str``
     - The human-readable name of the virtual folder.
   * - ``file``
     - ``str``
     - A file path inside the virtual folder to download.

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
   * - 404 Not Found
     - File not found or you may not have proper permission
       to access the folder.

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - (body)
     - ``bytes``
     - The content of file.

Downloading Multiple Files from Virtual Folder
----------------------------------------------

Download files from a virtual folder associated with the current keypair.

The response contents are streamed as gzipped binaries
(``Content-Encoding: gzip``) in a multi-part message format.
Clients may detect the total download size using ``X-TOTAL-PAYLOADS-LENGTH``
(all upper case) HTTP header of the response in prior to reading/parsing the
response body.

* URI: ``/folders/:name/download``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:name``
     - ``str``
     - The human-readable name of the virtual folder.
   * - ``files``
     - ``list[str]``
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
     - File not found or you may not have proper permission
       to access the folder.

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - (body)
     - ``multipart``
     - The gzipped content of files in the mixed multipart format.


Deleting Files in Virtual Folder
--------------------------------

This deletes files inside a virtual folder.

.. warning::
   There is NO way to get back the files once this API is invoked.

* URI: ``/folders/:name/delete_files``
* Method: ``DELETE``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:name``
     - ``str``
     - The human-readable name of the virtual folder.
   * - ``files``
     - ``list[str]``
     - File paths inside the virtual folder to delete.
   * - ``recursive``
     - ``bool``
     - Recursive option to delete folders if set to True. The default is False.

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
   * - 400 Bad Request
     - You tried to delete a folder without setting recursive option as True.
   * - 404 Not Found
     - There is no such folder or you may not have proper permission
       to delete the file in the folder.


Listing Invitations for Virtual Folder
--------------------------------------

Returns the list of pending invitations that requested user received.

* URI: ``/folders/invitations/list``
* Method: ``GET``

Parameters
""""""""""

This API does not need any parameter.

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
   * - ``invitations``
     - ``list[object]``
     - A list of :ref:`vfolder-invitation-object`.


Creating an Invitation
----------------------

Invite other users to share a virtual folder with proper permissions.
If a user is already invited, then this API does not create a new invitation
or update the permission of the existing invitation.

* URI: ``/folders/:name/invite``
* Method: ``POST``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:name``
     - ``str``
     - The human-readable name of the virtual folder.
   * - ``perm``
     - ``str``
     - The permission to grant to invitee.
   * - ``user_ids``
     - ``list[slug]``
     - A list of user IDs to invite.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
   * - 400 Bad Request
     - No invitee is given.
   * - 404 Not Found
     - There is no invitation.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``invited_ids``
     - ``list[slug]``
     - A list of invited user IDs.


Accepting an Invitation
-----------------------

Accept an invitation and receive permission to a virtual folder as in the invitation.

* URI: ``/folders/invitations/accept``
* Method: ``POST``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``inv_id``
     - ``slug``
     - The unique invitation ID.
   * - ``inv_ak``
     - ``bool``
     - The access key of invitee.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
   * - 400 Bad Request
     - The name of the target virtual folder is duplicate with
       your existing virtual folders.
   * - 404 Not Found
     - There is no such invitation.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``msg``
     - ``str``
     - Detail message for the invitation acceptance.

Rejecting an Invitation
-----------------------

Reject an invitation.

* URI: ``/folders/invitations/delete``
* Method: ``DELETE``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``inv_id``
     - ``slug``
     - The unique invitation ID.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
   * - 404 Not Found
     - There is no such invitation.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``msg``
     - ``str``
     - Detail message for the invitation deletion.
