User Management
===============

Query Schema
------------

.. code-block:: graphql

   type User {
     uuid: UUID
     username: String
     email: String
     password: String
     need_password_change: Boolean
     full_name: String
     description: String
     is_active: Boolean
     created_at: DateTime
     domain_name: String
     role: String
     groups: [UserGroup]
   }

   type UserGroup {  # shorthand reference to Group
     id: UUID
     name: String
   }

   type Query {
     keypair(domain_name: String, access_key: String): KeyPair
     keypairs(domain_name: String, email: String, is_active: Boolean): [KeyPair]
   }

Mutation Schema
---------------

.. code-block:: graphql

   input UserInput {
     username: String!
     password: String!
     need_password_change: Boolean!
     full_name: String
     description: String
     is_active: Boolean
     domain_name: String!
     role: String
     group_ids: [String]
   }

   input ModifyUserInput {
     username: String
     password: String
     need_password_change: Boolean
     full_name: String
     description: String
     is_active: Boolean
     domain_name: String
     role: String
     group_ids: [String]
   }

   type CreateKeyPair {
     ok: Boolean
     msg: String
     keypair: KeyPair
   }

   type ModifyUser {
     ok: Boolean
     msg: String
     user: User
   }

   type DeleteUser {
     ok: Boolean
     msg: String
   }

   type Mutation {
     create_user(email: String!, props: UserInput!): CreateUser
     modify_user(email: String!, props: ModifyUserInput!): ModifyUser
     delete_user(email: String!): DeleteUser
   }
