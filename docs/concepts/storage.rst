.. role:: raw-html-m2r(raw)
   :format: html

Storage Management
------------------

Virtual folders
~~~~~~~~~~~~~~~
:raw-html-m2r:`<span style="background-color:#ffdba9;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

Backend.AI abstracts network storages as a set of "virtual folders" (aka "vfolders"), which provides a persistent file storage to users and projects.

When creating a new session, users may connect vfolders to it with read-only or read-write permissions.
If the shared vfolder has limited the permission to read-only, then the user may connect it with the read-only permission only.
Virtual folders are mounted into compute session containers at ``/home/work/{name}`` so that user programs have access to the virtual folder contents like a local directory.
The mounted path inside containers may be customized (e.g., ``/workspace``) for compatibility with existing scripts and codes.
Currently it is not possible to unmount or delete a vfolder when there are any running session connected to it.
For cluster sessions having multiple kernels (containers), the connected vfolders are mounted to all kernels using the same location and the permission.

For a multi-node setup, the storage volume mounts must be synchronized across all Agent nodes and the Storage Proxy node(s) using the same mount path (e.g., ``/mnt`` or ``/vfroot``).
For a single-node setup, you may simply use an empty local directory, like our ``install-dev.sh`` script (`link <https://github.com/lablup/backend.ai/blob/main/scripts/install-dev.sh>`_) does.

From the perspective of the storage, all vfolders from different Backend.AI users and projects share a single same UID and GID.
This allows a flexible permission sharing between users and projects, while keeping the Linux ownership of the files and directories consistent when they are accessed by multiple different Backend.AI users.

User-owned vfolders
^^^^^^^^^^^^^^^^^^^

The users may create their own one or more virtual folders to store data files, libraries, and program codes.
The superadmins may limit the maximum number of vfolders owned by a user.

Project-owned vfolders
^^^^^^^^^^^^^^^^^^^^^^

The project admins and superadmins may create a vfolder that is automatically shared to all members of the project,
with a specific read-only or read-write permission.

.. note::

   If allowed, users and projects may create and access vfolders in multiple different storage volumes,
   but the vfolder names must be unique in all storage volumes, for each user and project.

VFolder invitations and permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Users and project administrators may invite other users to collaborate on a vfolder.
Once the invitee accepts the request, he/she gets the designated read-only or read-write permission on the shared vfolder.

Volume-level permissions
^^^^^^^^^^^^^^^^^^^^^^^^

The superadmin may set additional action privileges to each storage volume,
such as whether to allow or block mounting the vfolders in compute sessions, cloning the vfolders, etc.

Auto-mount vfolders
^^^^^^^^^^^^^^^^^^^

If a user-owned vfolder's name starts with a dot, it is automatically mounted at ``/home/work`` for all sessions created by the user.
A good usecase is ``.config`` and ``.local`` directories to keep your local configurations and user-installed packages (e.g., ``pip install --user``) persistent across all your sessions.


Quota scopes
~~~~~~~~~~~~

.. versionadded:: 23.03

Quota scopes implement per-user and per-project storage usage limits.
Currently it supports the hard limits specified in bytes.
There are two main schemes to set up this feature.

Storage with per-directory quota
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _vfolder-dir-quota:
.. figure:: vfolder-dir-quota.svg
   :width: 80%
   :align: center

   Quota scopes and vfolders with storage solutions supporting per-directry quota

For each storage volume, each user and project has their own dedicated quota scope directories as shown in :numref:`vfolder-dir-quota`.
The storage solution must support per-directory quota, at least for a single-level (like NetApp's QTree).
We recommend this configuration for filesystems like CephFS, Weka.io, or custom-built storage servers using ZFS or XFS where Backend.AI Storage Proxy can be installed directly onto the storage servers.

Storage with per-volume quota
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _vfolder-volume-quota:
.. figure:: vfolder-volume-quota.svg
   :width: 72%
   :align: center

   Quota scopes and vfolders with storage solutions supporting per-volume quota

Unfortunately, there are many cases that we cannot rely on per-directory quota support in storage solutions,
due to limitation of the underlying filesystem implementation or having no direct access to the storage vendor APIs.

For this case, we may assign dedicated storage volumes to each user and project like :numref:`vfolder-volume-quota`,
which *naturally* limits the space usage by the volume size.
Another option is not to configure quota limits, but we don't recommend this option in production setups.

The shortcoming is that we may need to frequently mount/unmount the network volumes when we create or remove users and projects, which may cause unexpected system failures due to stale file descriptors.

.. note::

   For shared vfolders, the quota usage is accounted for the original owner of the vfolder, either a user or a project.

.. warning::

   For both schemes, the administrator should take care of the storage solution's system limits such as the maximum number of volumes and quota sets
   because such limits may impose a hidden limit to the maximum number of users and projects in Backend.AI.
