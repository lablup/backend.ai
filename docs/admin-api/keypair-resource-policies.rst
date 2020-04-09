KeyPair Resource Policy Management
==================================

Query Schema
------------

.. code-block:: graphql

   type KeyPairResourcePolicy {
     name: String
     created_at: DateTime
     default_for_unspecified: String
     total_resource_slots: JSONString  # ResourceSlot
     max_concurrent_sessions: Int
     max_containers_per_session: Int
     idle_timeout: BigInt
     max_vfolder_count: Int
     max_vfolder_size: BigInt
     allowed_vfolder_hosts: [String]
   }

   type Query {
     keypair_resource_policy(name: String): KeyPairResourcePolicy
     keypair_resource_policies(): [KeyPairResourcePolicy]
   }

Mutation Schema
---------------

.. code-block:: graphql

   input CreateKeyPairResourcePolicyInput {
     default_for_unspecified: String!
     total_resource_slots: JSONString!
     max_concurrent_sessions: Int!
     max_containers_per_session: Int!
     idle_timeout: BigInt!
     max_vfolder_count: Int!
     max_vfolder_size: BigInt!
     allowed_vfolder_hosts: [String]
   }

   input ModifyKeyPairResourcePolicyInput {
     default_for_unspecified: String
     total_resource_slots: JSONString
     max_concurrent_sessions: Int
     max_containers_per_session: Int
     idle_timeout: BigInt
     max_vfolder_count: Int
     max_vfolder_size: BigInt
     allowed_vfolder_hosts: [String]
   }

   type CreateKeyPairResourcePolicy {
     ok: Boolean
     msg: String
     resource_policy: KeyPairResourcePolicy
   }

   type ModifyKeyPairResourcePolicy {
     ok: Boolean
     msg: String
   }

   type DeleteKeyPairResourcePolicy {
     ok: Boolean
     msg: String
   }

   type Mutation {
     create_keypair_resource_policy(name: String!, props: CreateKeyPairResourcePolicyInput!): CreateKeyPairResourcePolicy
     modify_keypair_resource_policy(name: String!, props: ModifyKeyPairResourcePolicyInput!): ModifyKeyPairResourcePolicy
     delete_keypair_resource_policy(name: String!): DeleteKeyPairResourcePolicy
   }
