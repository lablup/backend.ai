Group Management
=================

Query Schema
------------

.. code-block:: graphql

   type Group {
     id: UUID
     name: String
     description: String
     is_active: Boolean
     created_at: DateTime
     modified_at: DateTime
     domain_name: String
     total_resource_slots: JSONString  # ResourceSlot
     allowed_vfolder_hosts: [String]
     integration_id: String
     scaling_groups: [String]
   }

   type Query {
     group(id: String!): Group
     groups(domain_name: String, is_active: Boolean): [Group]
   }

Mutation Schema
---------------

.. code-block:: graphql

   input GroupInput {
     description: String
     is_active: Boolean
     domain_name: String!
     total_resource_slots: JSONString  # ResourceSlot
     allowed_vfolder_hosts: [String]
     integration_id: String
   }

   input ModifyGroupInput {
     name: String
     description: String
     is_active: Boolean
     domain_name: String
     total_resource_slots: JSONString  # ResourceSlot
     user_update_mode: String
     user_uuids: [String]
     allowed_vfolder_hosts: [String]
     integration_id: String
   }

   type CreateGroup {
     ok: Boolean
     msg: String
     keypair: KeyPair
   }

   type ModifyGroup {
     ok: Boolean
     msg: String
   }

   type DeleteGroup {
     ok: Boolean
     msg: String
   }

   type Mutation {
     create_group(name: String!, props: GroupInput!): CreateGroup
     modify_group(name: String!, props: ModifyGroupInput!): ModifyGroup
     delete_group(name: String!): DeleteGroup
   }
