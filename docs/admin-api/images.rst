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

.. code-block:: graphql

   type Query {
     image(reference: String!): Image

     images(
       is_installed: Boolean,
       is_operation: Boolean,
       scaling_group: String,
     ): [Image]
   }

.. versionadded:: v5.20191215

   ``scaling_group`` filter condition is added to the ``images`` root query field.

.. versionchanged:: v5.20191215

   ``images`` query returns the images currently usable by the requesting user,
   checking the allowed scaling groups and whether agents in those scaling groups
   have the image installed, unless the requesting user is not a super-admin.

Mutation Schema
---------------

.. code-block:: graphql

   type RescanImages {
     ok: Boolean
     msg: String
     task_id: String
   }

   type PreloadImage {
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
     preload_image(reference: String!, target_agents: String!): PreloadImage
     unload_image(reference: String!, target_agents: String!): UnloadImage
     forget_image(reference: String!): ForgetImage
     alias_image(alias: String!, target: String!): AliasImage
     dealias_image(alias: String!): DealiasImage
   }

.. versionadded:: v5.20191215

   ``forget_image``, ``preload_image`` and ``unload_image`` are added to the root mutation.
