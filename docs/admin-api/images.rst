Image Management
================

Query Schema
------------

.. code-block:: graphql

   type Image {
     name: String
     humanized_name: String
     tag: String
     registry: String
     digest: String
     labels: [KVPair]
     aliases: [String]
     size_bytes: BigInt
     resource_limits: [ResourceLimit]
     supported_accelerators: [String]
     installed: Boolean
     installed_agents: [String]
   }

   type Query {
     image(reference: String!): Image

     images(
       is_installed: Boolean,
       is_operation: Boolean,
     ): [Image]
   }

Mutation Schema
---------------

.. code-block:: graphql

   type RescanImages {
     ok: Boolean
     msg: String
     task_id: String
   }

   type ForgetImage {
     ok: Boolean
     msg: String
     task_id: String
   }

   type AliasImage {
     ok: Boolean
     msg: String
   }

   type DealiasImage {
     ok: Boolean
     msg: String
   }

   type Mutation {
     rescan_images(registry: String!): RescanImages
     alias_image(alias: String!, target: String!): AliasImage
     dealias_image(alias: String!): DealiasImage
   }
