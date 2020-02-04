Compute Session Monitoring
==========================

Query Schema
------------

.. code-block:: graphql

   type ComputeSession {
     # identity and type
     sess_id: String     # legacy alias to session_name
     sess_type: String   # legacy alias to session_type
     session_name: String
     session_type: String
     id: UUID
     tag: String

     # ownership
     domain_name: String
     group_name: String
     group_id: UUID
     user_email: String
     user_uuid: UUID
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
     scaling_group: String
     service_ports: JSON    # only available in master
     mounts: [String]   # shared by all kernels

     # statistics
     num_queries: BigInt

     # owned kernels
     containers: [ComputeContainer]
   }

   type ComputeContainer {
     # identity
     id: UUID
     role: String   # "master" is reserved, other values are defined by cluster templates
     hostname: String

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
     agent: String   # only available for super-admins
     container_id: String
     occupied_slots: JSON
     resource_opts: JSON

     # statistics
     live_stat: JSON
     last_stat: JSON
   }

   type root {
     compute_sessions(  # deprecated
       access_key: String,
       status: String,
     ): [ComputeSession]

     compute_session_list(
       limit: Int!,
       offset: Int!,
       access_key: String,
       status: String,
     ): PaginatedList[ComputeSession]
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
         session_name
         session_type
         user_email
         status
         status_info
       }
     }
   }

API Parameters
~~~~~~~~~~~~~~

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
           "session_name": "mysession",
           "session_type": "interactive",
           "user_email": "user@lablup.com",
           "status": "RUNNING",
           "status_info": null
         }
       ]
     }
   }

