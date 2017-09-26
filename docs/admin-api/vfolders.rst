Virtual Folder Management
=========================

Full Admin
----------

Query Schema
~~~~~~~~~~~~

.. code-block:: text

   type VirtualFolder {
     id: UUID
     host: String
     name: String
     max_files: Int
     max_size: Int
     created_at: DateTime
     last_used: DateTime
     num_files: Int
     cur_size: Int
   }

   type rootQuery {
     ...
     vfolders(access_key: String): [VirtualFolder]
   }


Restricted Owner Access
-----------------------

Query Schema
~~~~~~~~~~~~

It shares the same ``VirtualFolder`` type, but you cannot use ``access_key`` argument in the root query.

.. code-block:: text

   type root {
     ...
     vfolders(): [VirtualFolder]
   }
