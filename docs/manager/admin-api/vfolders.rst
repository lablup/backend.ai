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
     user_email: String
     group: UUID
     group_name: String
     creator: String        # user email
     unmanaged_path: UUID
     usage_mode: String
     permission: String
     ownership_type: String
     max_files: Int
     max_size: Int
     created_at: DateTime
     last_used: DateTime
     num_files: Int
     cur_size: BigInt
     cloneable: Boolean
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
