.. role:: raw-html-m2r(raw)
   :format: html

Storage Management
------------------

Virtual folders
~~~~~~~~~~~~~~~
:raw-html-m2r:`<span style="background-color:#ffdba9;border:1px solid #ccc;display:inline-block;width:16px;height:16px;margin:0;padding:0;"></span>`

.. _vfolder-concept-diagram:
.. figure:: vfolder-concept.svg

   A conceptual diagram of virtual folders when using two NFS servers as vfolder hosts

As shown in :numref:`vfolder-concept-diagram`, Backend.AI abstracts network storages as "virtual folder", which provides a cloud-like private file storage to individual users.
The users may create their own (one or more) virtual folders to store data files, libraries, and program codes.
Each vfolder (virtual folder) is created under a designated storage mount (called "vfolder hosts").
Virtual folders are mounted into compute session containers at ``/home/work/{name}`` so that user programs have access to the virtual folder contents like a local directory.
As of Backend.AI v18.12, users may also share their own virtual folders with other users in differentiated permissions such as read-only and read-write.

A Backend.AI cluster setup may use any filesystem that provides a local mount point at each node (including the manager and agents) given that the filesystem contents are synchronized across all nodes.
The only requirement is that the local mount-point must be same across all cluster nodes (e.g., ``/mnt/vfroot/mynfs``).
Common setups may use a centralized network storage (served via NFS or SMB), but for more scalability, one might want to use distributed file systems such as CephFS and GlusterFS, or Alluxio that provides fast in-memory cache while backed by another storage server/service such as AWS S3.

For a single-node setup, you may simply use an empty local directory.

User-owned vfolders
^^^^^^^^^^^^^^^^^^^

Project-owned vfolders
^^^^^^^^^^^^^^^^^^^^^^

VFolder invitations and permissions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Volume-level permissions
^^^^^^^^^^^^^^^^^^^^^^^^

Quota scopes
~~~~~~~~~~~~
