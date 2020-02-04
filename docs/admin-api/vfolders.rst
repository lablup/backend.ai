Virtual Folder Management
=========================

Query Schema
------------

.. code-block:: graphql

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
     vfolders(access_key: String): List[VirtualFolder]
   }
