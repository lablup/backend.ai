Compute Session Monitoring
==========================

As of Backend.AI v20.03, compute sessions are composed of one or more containers, while interactions with sessions only occur with the *master* container when using REST APIs.
The GraphQL API allows users and admins to check details of sessions and their belonging containers.

.. versionchanged:: v5.20191215

Query Schema
------------

``ComputeSession`` provides information about the whole session, including user-requested parameters when creating sessions.

.. code-block:: graphql

   type ComputeSession {
     # identity and type
     id: UUID
     name: String
     type: String
     id: UUID
     tag: String

     # image
     image: String
     registry: String
     cluster_template: String  # reserved for future release

     # ownership
     domain_name: String
     group_name: String
     group_id: UUID
     user_email: String
     user_id: UUID
     access_key: String
     created_user_email: String  # reserved for future release
     created_user_uuid: UUID     # reserved for future release

     # status
     status: String
     status_changed: DateTime
     status_info: String
     created_at: DateTime
     terminated_at: DateTime
     startup_command: String
     result: String

     # resources
     resource_opts: JSONString
     scaling_group: String
     service_ports: JSONString   # only available in master
     mounts: List[String]            # shared by all kernels
     occupied_slots: JSONString  # ResourceSlot; sum of belonging containers

     # statistics
     num_queries: BigInt

     # owned containers (aka kernels)
     containers: List[ComputeContainer]  # full list of owned containers

     # pipeline relations
     dependencies: List[ComputeSession]  # full list of dependency sessions
   }

The sessions may be queried one by one using ``compute_session`` field on the root query schema,
or as a paginated list using ``compute_session_list``.

.. code-block:: graphql

   type Query {
     compute_session(
       id: UUID!,
     ): ComputeSession

     compute_session_list(
       limit: Int!,
       offset: Int!,
       order_key: String,
       order_asc: Boolean,
       domain_name: String,  # super-admin can query sessions in any domain
       group_id: String,     # domain-admins can query sessions in any group
       access_key: String,   # admins can query sessions of other users
       status: String,
     ): PaginatedList[ComputeSession]
   }

``ComputeContainer`` provides information about individual containers that belongs to the given session.
Note that the client must assume that ``id`` is different from ``container_id``, because agents may be configured to use non-Docker backends.

.. note::

   The container ID in the GraphQL queries and REST APIs are *different* from the actual Docker container ID.
   The Docker container IDs can be queried using ``container_id`` field of ``ComputeContainer`` objects.
   If the agents are configured to using non-Docker-based backends, then ``container_id`` may also be completely arbitrary identifiers.

.. code-block:: graphql

   type ComputeContainer {
     # identity
     id: UUID
     role: String      # "master" is reserved, other values are defined by cluster templates
     hostname: String  # used by sibling containers in the same session
     session_id: UUID

     # image
     image: String
     registry: String

     # status
     status: String
     status_changed: DateTime
     status_info: String
     created_at: DateTime
     terminated_at: DateTime

     # resources
     agent: String               # super-admin only
     container_id: String
     resource_opts: JSONString
     # NOTE: mounts are same in all containers of the same session.
     occupied_slots: JSONString  # ResourceSlot

     # statistics
     live_stat: JSONString
     last_stat: JSONString
   }

In the same way, the containers may be queried one by one using ``compute_container`` field on the root query schema, or as a paginated list using ``compute_container_list`` for a single session.

.. note::

   The container ID of the master container of each session is same to the session ID.

.. code-block:: graphql

   type Query {
     compute_container(
       id: UUID!,
     ): ComputeContainer

     compute_container_list(
       limit: Int!,
       offset: Int!,
       session_id: UUID!,
       role: String,
     ): PaginatedList[ComputeContainer]
   }

Query Example
-------------

.. code-block:: graphql

   query(
     $limit: Int!,
     $offset: Int!,
     $ak: String,
     $status: String,
   ) {
     compute_session_list(
       limit: $limit,
       offset: $offset,
       access_key: $ak,
       status: $status,
     ) {
       total_count
       items {
         id
         name
         type
         user_email
         status
         status_info
         status_updated
         containers {
           id
           role
           agent
         }
       }
     }
   }

API Parameters
~~~~~~~~~~~~~~

Using the above GraphQL query, clients may send the following JSON object as the request:

.. code-block:: json

   {
     "query": "...",
     "variables": {
       "limit": 10,
       "offset": 0,
       "ak": "AKIA....",
       "status": "RUNNING"
     }
   }

API Response
~~~~~~~~~~~~

.. code-block:: json

   {
     "compute_session_list": {
       "total_count": 1,
       "items": [
         {
           "id": "12c45b55-ce3c-418d-9c58-223bbba307f1",
           "name": "mysession",
           "type": "interactive",
           "user_email": "user@lablup.com",
           "status": "RUNNING",
           "status_info": null,
           "status_updated": "2020-02-16T15:47:28.997335+00:00",
           "containers": [
             {
               "id": "12c45b55-ce3c-418d-9c58-223bbba307f1",
               "role": "master",
               "agent": "i-agent01"
             },
             {
               "id": "12c45b55-ce3c-418d-9c58-223bbba307f2",
               "role": "slave",
               "agent": "i-agent02"
             },
             {
               "id": "12c45b55-ce3c-418d-9c58-223bbba307f3",
               "role": "slave",
               "agent": "i-agent03"
             }
           ]
         }
       ]
     }
   }

