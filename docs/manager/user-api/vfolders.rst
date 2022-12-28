Virtual Folders
===============

Virtual folders provide access to shared, persistent, and reused files across
different sessions.

You can mount virtual folders when creating new sessions, and use them
like a plain directory on the local filesystem.
Of course, reads/writes to virtual folder contents may have degraded
performance compared to the main scratch directory (usually ``/home/work`` in
most kernels) as internally it uses a networked file system.

Also, you might share your virtual folders with other users by inviting them
and granting them proper permission. Currently, there are three levels of
permissions: read-only, read-write, read-write-delete. They are represented
by short strings, ``'ro'``, ``'rw'``, ``'wd'``, respectively. The owner of a
virtual folder have read-write-delete permission for the folder.


Listing Virtual Folders
-----------------------

Returns the list of virtual folders created by the current keypair.

* URI: ``/folders``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``all``
     - ``bool``
     - (optional) If this parameter is ``True``, it returns all virtual folders,
       including those that do not belong to the current user. Only available for
       superadmin (default: ``False``).
   * - ``group_id``
     - ``UUID | str``
     - (optional) If this parameter is set, it returns the virtual folders that
       belong to the specified group. Have no effect in user-type virtual folders.

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - (root)
     - ``list[object]``
     - A list of :ref:`vfolder-list-item-object`

Example:

.. code-block:: json

   [
      {
         "name": "myfolder",
         "id": "b4b1b16c-d07f-4f1f-b60e-da9449aa60a6",
         "host": "local:volume1",
         "usage_mode": "general",
         "created_at": "2020-11-28 13:30:30.912056+00",
         "is_owner": "true",
         "permission": "rw",
         "user": "dfa9da54-4b28-432f-be29-c0d680c7a412",
         "group": null,
         "creator": "admin@lablup.com",
         "user_email": "admin@lablup.com",
         "group_name": null,
         "ownership_type": "user",
         "unmanaged_path": null,
         "cloneable": "false",
      }
   ]


Listing Virtual Folder Hosts
----------------------------

Returns the list of available host names where the current keypair can create
new virtual folders.

.. versionadded:: v4.20190315

* URI: ``/folders/_/hosts``
* Method: ``GET``

Parameters
""""""""""

None

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``default``
     - ``str``
     - The default virtual folder host
   * - ``allowed``
     - ``list[str]``
     - The list of available virtual folder hosts

Example:

.. code-block:: json

   {
     "default": "seoul:nfs1",
     "allowed": ["seoul:nfs1", "seoul:nfs2", "seoul:cephfs1"]
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
     - The human-readable name of the virtual folder
   * - ``host``
     - ``str``
     - (optional) The name of the virtual folder host
   * - ``usage_mode``
     - ``str``
     - (optional) The purpose of the virtual folder. Allowed values are
       ``general``, ``model``, and ``data`` (default: ``general``).
   * - ``permission``
     - ``str``
     - (optional) The default share permission of the virtual folder.
       The owner of the virtual folder always have ``wd`` permission regardless of
       this parameter. Allowed values are ``ro``, ``rw``, and ``wd``
       (default: ``rw``).
   * - ``group_id``
     - ``UUID | str``
     - (optional) If this parameter is set, it creates a group-type virtual folder.
       If empty, it creates a user-type virtual folder.
   * - ``quota``
     - ``int``
     - (optional) Set the quota of the virtual folder in bytes. Note, however,
       that the quota is only supported under the xfs filesystems. Other filesystems
       that do not support per-directory quota will ignore this parameter.

Example:

.. code-block:: json

   {
     "name": "My Data",
     "host": "seoul:nfs1"
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
     - The unique folder ID used for later API calls
   * - ``name``
     - ``str``
     - The human-readable name of the created virtual folder
   * - ``host``
     - ``str``
     - The name of the virtual folder host where the new folder is created


Example:

.. code-block:: json

   {
     "id": "aef1691db3354020986d6498340df13c",
     "name": "My Data",
     "host": "nfs1",
     "usage_mode": "general",
     "permission": "rw",
     "creator": "admin@lablup.com",
     "ownership_type": "user",
     "user": "dfa9da54-4b28-432f-be29-c0d680c7a412",
     "group": "",
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
     - The human-readable name of the virtual folder

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
     - :ref:`vfolder-item-object`


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
     - The human-readable name of the virtual folder

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


Rename a Virtual Folder
-----------------------

* URI: ``/folders/:name/rename``
* Method: ``POST``

Rename a virtual folder associated with the current API key.

Parameters
""""""""""

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description

   * - ``:name``
     - ``str``
     - The human-readable name of the virtual folder
   * - ``new_name``
     - ``str``
     - New virtual folder name

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 201 Created
     - The folder is successfully renamed.
   * - 404 Not Found
     - There is no such folder or you may not have proper permission
       to rename the folder.


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
     - The human-readable name of the virtual folder
   * - ``path``
     - ``str``
     - Path inside the virtual folder (default: root)

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


Uploading a File to Virtual Folder
----------------------------------

Upload a local file to a virtual folder associated with the current keypair.
Internally, the Manager will deligate the upload to a Backend.AI Storage-Proxy
service. JSON web token is used for the authentication of the request.

* URI: ``/folders/:name/request-upload``
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
     - The human-readable name of the virtual folder
   * - ``path``
     - ``str``
     - Path of the local file to upload
   * - ``size``
     - ``int``
     - The total size of the local file to upload

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``token``
     - ``str``
     - JSON web token for the authentication of the upload session to
       Storage-Proxy service.
   * - ``url``
     - ``str``
     - Request url for a Storage-Proxy. Client should use this URL to upload the file.


Creating New Directory in Virtual Folder
----------------------------------------

Create a new directory in the virtual folder associated with current keypair.
this API recursively creates parent directories if they does not exist.

* URI: ``/folders/:name/mkdir``
* Method: ``POST``

.. warning::
   If a directory with the same name already exists in the virtual folder, it may
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
       inside the virtual folder
   * - ``parents``
     - ``bool``
     - If ``True``, the parent directories will be created if they do not exist.
   * - ``exist_ok``
     - ``bool``
     - If a directory with the same name already exists,
       overwrite it without an error.

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


Downloading a File or a Directory from a Virtual Folder
-------------------------------------------------------

Download a file or a directory from a virtual folder associated with the current
keypair. Internally, the Manager will deligate the download to a Backend.AI
Storage-Proxy service. JSON web token is used for the authentication of the
request.

.. versionadded:: v4.20190315

* URI: ``/folders/:name/request-download``
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
     - The human-readable name of the virtual folder
   * - ``path``
     - ``str``
     - The path to a file or a directory inside the virtual folder to download.
   * - ``archive``
     - ``bool``
     - If this parameter is ``True`` and ``path`` is a directory, the directory
       will be archived into a zip file on the fly (default: ``False``).

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
   * - ``token``
     - ``str``
     - JSON web token for the authentication of the download session to
       Storage-Proxy service.
   * - ``url``
     - ``str``
     - Request url for a Storage-Proxy.
       Client should use this URL to download the file.


Deleting Files in Virtual Folder
--------------------------------

This deletes files inside a virtual folder.

.. warning::
   There is NO way to get back the files once this API is invoked.

* URI: ``/folders/:name/delete-files``
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
     - The human-readable name of the virtual folder
   * - ``files``
     - ``list[str]``
     - File paths inside the virtual folder to delete
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


Rename a File in Virtual Folder
-------------------------------

Rename a file inside a virtual folder.

* URI: ``/folders/:name/rename-file``
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
     - The human-readable name of the virtual folder
   * - ``target_path``
     - ``str``
     - The relative path of target file or directory
   * - ``new_name``
     - ``str``
     - The new name of the file or directory
   * - ``is_dir``
     - ``bool``
     - Flag that indicates the ``target_path`` is a directory or not

Response
""""""""

.. list-table::
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 200 OK
     - Success.
   * - 400 Bad Request
     - You tried to rename a directory without setting is_dir option as True.
   * - 404 Not Found
     - There is no such folder or you may not have proper permission
       to rename the file in the folder.

Listing Invitations for Virtual Folder
--------------------------------------

Returns the list of pending invitations that the requested user received.
This will display the invitations sent to me by other users.

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
     - A list of :ref:`vfolder-invitation-object`


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
     - The human-readable name of the virtual folder
   * - ``perm``
     - ``str``
     - The permission to grant to invitee
   * - ``emails``
     - ``list[slug]``
     - A list of user emails to invite

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
     - A list of invited user emails


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
     - The unique invitation ID

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
     - The unique invitation ID

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
     - Detail message for the invitation deletion


Listing Sent Invitations
------------------------

Returns the list of virtual folder invitations the requested user sent.
This does not include the invitations those are already accepted or rejected.

* URI: ``/folders/invitations/list-sent``
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
     - A list of :ref:`vfolder-invitation-object`


Updating an Invitation
----------------------

Update the permission of an already-sent, but not accepted or rejected, invitation.

* URI: ``/folders/invitations/update/:inv_id``
* Method: ``POST``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``:inv_id``
     - ``str``
     - The unique invitation ID
   * - ``perm``
     - ``str``
     - The permission to grant to invitee

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
     - No permission is given.
   * - 404 Not Found
     - There is no invitation.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``msg``
     - ``str``
     - An update message string


Leave an Shared Virtual Folder
------------------------------

Leave a shared virtual folder.

Cannot leave a group vfolder or a vfolder that the requesting user owns.

* URI: ``/folders/:name/leave``
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
     - The human-readable name of the virtual folder

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
     - There is no virtual folder.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``msg``
     - ``str``
     - A result message string


Listing Users Share Virtual Folders
-----------------------------------

Returns the list of users who shares requester's virtual folders.

* URI: ``/folders/_/shared``
* Method: ``GET``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``vfolder_id``
     - ``str``
     - (Optional) The unique virtual folder ID to list shared users. If not
       specified, all users who shares any virtual folders the requester created.

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
   * - ``shared``
     - ``list[object]``
     - A list of information about shared users.

Example:

.. code-block:: json

   [
      {
         "vfolder_id": "aef1691db3354020986d6498340df13c",
         "vfolder_name": "My Data",
         "shared_by": "admin@lablup.com",
         "shared-to": {
            "uuid": "dfa9da54-4b28-432f-be29-c0d680c7a412",
            "email": "user@lablup.com"
         },
         "perm": "ro"
      }
   ]


Updating the permission of a shared virtual folder
--------------------------------------------------

Update the permission of a user for a shared virtual folder.

* URI: ``/folders/_/shared``
* Method: ``POST``

Parameters
""""""""""

.. list-table::
   :widths: 15 10 80
   :header-rows: 1

   * - Parameter
     - Type
     - Description
   * - ``vfolder``
     - ``UUID``
     - The unique virtual folder ID
   * - ``user``
     - ``UUID``
     - The unique user ID
   * - ``perm``
     - ``str``
     - The permission to update for the ``user`` on ``vfolder``

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
     - No permission or user is given.
   * - 404 Not Found
     - There is no virtual folder.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``msg``
     - ``str``
     - An update message string


Share a Group Virtual Folder to an Individual Users
---------------------------------------------------

Share a group virtual folder to users with overriding permission.

This will create vfolder_permission(s) relation directly without creating
invitation(s). Only group virtual folders are allowed to be shared directly.

This API can be useful when you want to share a group virtual folder to every
group members with read-only permission, but allows some users read-write
permission.

NOTE: This API is only available for group virtual folders.

* URI: ``/folders/:name/share``
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
     - The human-readable name of the virtual folder
   * - ``permission``
     - ``str``
     - Overriding permission to share the group virtual folder
   * - ``emails``
     - ``list[str]``
     - A list of user emails to share

Response
""""""""

.. list-table::
   :widths: 25 75
   :header-rows: 1

   * - HTTP Status Code
     - Description
   * - 201 Created
     - Success.
   * - 400 Bad Request
     - No permission or email is given.
   * - 404 Not Found
     - There is no virtual folder.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``shared_emails``
     - ``list[str]``
     - A list of user emails those are successfully shared the virtual folder


Unshare a Group Virtual Folder from Users
-----------------------------------------

Unshare a group virtual folder from users

NOTE: This API is only available for group virtual folders.

* URI: ``/folders/:name/unshare``
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
     - The human-readable name of the virtual folder
   * - ``emails``
     - ``list[str]``
     - A list of user emails to unshare

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
     - No email is given.
   * - 404 Not Found
     - There is no virtual folder.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``unshared_emails``
     - ``list[str]``
     - A list of user emails those are successfully unshared the virtual folder


Clone a Virtual Folder
----------------------

Clone a virtual folder

* URI: ``/folders/:name/clone``
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
     - The human-readable name of the virtual folder
   * - ``cloneable``
     - ``bool``
     - If ``True``, cloned virtual folder will be cloneable again.
   * - ``target_name``
     - ``str``
     - The name of the new virtual folder
   * - ``target_host``
     - ``str``
     - The targe host volume of the new virtual folder
   * - ``usage_mode``
     - ``str``
     - (optional) The purpose of the new virtual folder. Allowed values are
       ``general``, ``model``, and ``data`` (default: ``general``).
   * - ``permission``
     - ``str``
     - (optional) The default share permission of the new virtual folder.
       The owner of the virtual folder always have ``wd`` permission regardless of
       this parameter. Allowed values are ``ro``, ``rw``, and ``wd``
       (default: ``rw``).

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
     - No target name, target host, or no permission.
   * - 403 Forbidden
     - The source virtual folder is not permitted to be cloned.
   * - 404 Not Found
     - There is no virtual folder.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - ``unshared_emails``
     - ``list[str]``
     - A list of user emails those are successfully unshared the virtual folder.

.. list-table::
   :widths: 15 5 80
   :header-rows: 1

   * - Fields
     - Type
     - Values
   * - (root)
     - ``list[object]``
     - :ref:`vfolder-list-item-object`

Example:

.. code-block:: json

   {
      "name": "my cloned folder",
      "id": "b4b1b16c-d07f-4f1f-b60e-da9449aa60a6",
      "host": "local:volume1",
      "usage_mode": "general",
      "created_at": "2020-11-28 13:30:30.912056+00",
      "is_owner": "true",
      "permission": "rw",
      "user": "dfa9da54-4b28-432f-be29-c0d680c7a412",
      "group": null,
      "creator": "admin@lablup.com",
      "user_email": "admin@lablup.com",
      "group_name": null,
      "ownership_type": "user",
      "unmanaged_path": null,
      "cloneable": "false"
   }
