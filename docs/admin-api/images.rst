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
     installed_agents: [String]  # super-admin only
   }

.. code-block:: graphql

   type Query {
     image(reference: String!): Image

     images(
       is_installed: Boolean,
       is_operation: Boolean,
       domain: String,         # only settable by super-admins
       group: String,
       scaling_group: String,  # null to take union of all agents from allowed scaling groups
     ): [Image]
   }

The image list is automatically filtered by:
1) the allowed docker registries of the current user's domain,
2) whether at least one agent in the union of all agents from the allowed scaling groups for the current user's group has the image or not.
The second condition applies only when the value of ``group`` is given explicitly.
If ``scaling_group`` is not ``null``, then only the agents in the given scaling group are checked for image availability instead of taking the union of all agents from the allowed scaling groups.

If the requesting user is a super-admin, clients may set the filter conditions as they want.
If the filter conditions are not specified by the super-admin, clients work like v19.09 and prior versions

.. versionadded:: v5.20191215

   ``domain``, ``group``, and ``scaling_group`` filters are added to the ``images`` root query field.

.. versionchanged:: v5.20191215

   ``images`` query returns the images currently usable by the requesting user as described above.
   Previously, it returned all etcd-registered images.

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

   type UnloadImage {
     ok: Boolean
     msg: String
     task_id: String
   }

   type ForgetImage {
     ok: Boolean
     msg: String
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

All these mutations are only allowed for super-admins.

The query parameter ``target_agents`` takes a special expression to indicate a set of agents.

The mutations that returns ``task_id`` may take an arbitrarily long time to complete.
This means that getting the response does not necessarily mean that the requested task is complete.
To monitor the progress and actual completion, clients should use :ref:`the background task API <bgtask-progress-events>` using the ``task_id`` value.

.. versionadded:: v5.20191215

   ``forget_image``, ``preload_image`` and ``unload_image`` are added to the root mutation.

.. versionchanged:: v5.20191215

   ``rescan_images`` now returns immediately and its completion must be monitored using the new background task API.
