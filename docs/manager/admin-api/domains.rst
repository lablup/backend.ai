Domain Management
=================

Query Schema
------------

.. code-block:: graphql

   type Domain {
     name: String
     description: String
     is_active: Boolean
     created_at: DateTime
     modified_at: DateTime
     total_resource_slots: JSONString  # ResourceSlot
     allowed_vfolder_hosts: [String]
     allowed_docker_registries: [String]
     integration_id: String
     scaling_groups: [String]
   }

   type Query {
     domain(name: String): Domain
     domains(is_active: Boolean): [Domain]
   }

Mutation Schema
---------------

.. code-block:: graphql

   input DomainInput {
     description: String
     is_active: Boolean
     total_resource_slots: JSONString  # ResourceSlot
     allowed_vfolder_hosts: [String]
     allowed_docker_registries: [String]
     integration_id: String
   }

   input ModifyDomainInput {
     name: String
     description: String
     is_active: Boolean
     total_resource_slots: JSONString  # ResourceSlot
     allowed_vfolder_hosts: [String]
     allowed_docker_registries: [String]
     integration_id: String
   }

   type CreateDomain {
     ok: Boolean
     msg: String
     keypair: KeyPair
   }

   type ModifyDomain {
     ok: Boolean
     msg: String
   }

   type DeleteDomain {
     ok: Boolean
     msg: String
   }

   type Mutation {
     create_domain(name: String!, props: DomainInput!): CreateDomain
     modify_domain(name: String!, props: ModifyDomainInput!): ModifyDomain
     delete_domain(name: String!): DeleteDomain
   }
