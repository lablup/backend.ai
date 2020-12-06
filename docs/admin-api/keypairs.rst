KeyPair Management
==================

Query Schema
------------

.. code-block:: graphql

   type KeyPair {
     user_id: String
     access_key: String
     secret_key: String
     is_active: Boolean
     is_admin: Boolean
     resource_policy: String
     created_at: DateTime
     last_used: DateTime
     concurrency_used: Int
     rate_limit: Int
     num_queries: Int
     user: UUID
     ssh_public_key: String
     vfolders: [VirtualFolder]
     compute_sessions(status: String): [ComputeSession]
   }

   type Query {
     keypair(domain_name: String, access_key: String): KeyPair
     keypairs(domain_name: String, email: String, is_active: Boolean): [KeyPair]
   }

Mutation Schema
---------------

.. code-block:: graphql

   input KeyPairInput {
     is_active: Boolean
     resource_policy: String
     concurrency_limit: Int
     rate_limit: Int
   }

   input ModifyKeyPairInput {
     is_active: Boolean
     is_admin: Boolean
     resource_policy: String
     concurrency_limit: Int
     rate_limit: Int
   }

   type CreateKeyPair {
     ok: Boolean
     msg: String
     keypair: KeyPair
   }

   type ModifyKeyPair {
     ok: Boolean
     msg: String
   }

   type DeleteKeyPair {
     ok: Boolean
     msg: String
   }

   type Mutation {
     create_keypair(props: KeyPairInput!, user_id: String!): CreateKeyPair
     modify_keypair(access_key: String!, props: ModifyKeyPairInput!): ModifyKeyPair
     delete_keypair(access_key: String!): DeleteKeyPair
   }
