KeyPair Management
==================

Full Admin
----------

Query Schema
~~~~~~~~~~~~

.. code-block:: text

   type KeyPair {
     access_key: String
     secret_key: String
     is_active: Boolean
     is_admin: Boolean
     resource_policy: String
     created_at: DateTime
     last_used: DateTime
     concurrency_limit: Int
     concurrency_used: Int
     rate_limit: Int
     num_queries: Int
     vfolders: [VirtualFolder]
     compute_sessions(status: String): [ComputeSession]
   }

   type root {
     ...
     keypairs(user_id: Int!, is_active: Boolean): [KeyPair]
   }

Mutation Schema
~~~~~~~~~~~~~~~

.. code-block:: text

   input KeyPairInput {
     is_active: Boolean
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

   type root {
     ...
     create_keypair(user_id: Int!, props: KeyPairInput!): CreateKeyPair
     modify_keypair(access_key: String!, props: KeyPairInput!): ModifyKeyPair
     delete_keypair(access_key: String!): DeleteKeyPair
   }


Restricted Owner Access
-----------------------

Query Schema
~~~~~~~~~~~~

It shares the same ``KeyPair`` type, but you cannot use ``user_id`` argument in the root query
because the client can only query the keypair that is being used to make this API query.
Also the returned value is always a single object.

.. code-block:: text

   type root {
     ...
     keypair(): KeyPair
   }

Mutation Schema
~~~~~~~~~~~~~~~

There is no mutations available.
