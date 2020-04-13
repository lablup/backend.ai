Virtual Folder Management
=========================

Query Schema
------------

.. code-block:: graphql

   type VirtualFolder {
     id: UUID
     host: String
     name: String
     user: UUID
     group: UUID
     unmanaged_path: UUID
     max_files: Int
     max_size: Int
     created_at: DateTime
     last_used: DateTime
     num_files: Int
     cur_size: BigInt
   }

   type Query {
     vfolder_list(
       limit: Int!,
       offset: Int!,
       order_key: String,
       order_asc: Boolean,
       domain_name: String,
       group_id: String,
       access_key: String,
     ): PaginatedList[VirtualFolder]
   }
