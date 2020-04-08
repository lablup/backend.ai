Agent Monitoring
================

Query Schema
------------

.. code-block:: graphql

   type Agent {
     id: ID
     status: String
     status_changed: DateTime
     region: String
     scaling_group: String
     available_slots: JSONString
     occupied_slots: JSONString
     addr: String
     first_contact: DateTime
     lost_at: DateTime
     live_stat: JSONString
     version: String
     compute_plugins: JSONString
     mem_slots: Int
     cpu_slots: Float
     gpu_slots: Float
     tpu_slots: Float
     used_mem_slots: Int
     used_cpu_slots: Float
     used_gpu_slots: Float
     used_tpu_slots: Float
     cpu_cur_pct: Float
     mem_cur_bytes: Float
     computations(status: String): [Computation]
   }

   type Query {
     agent_list(
      limit: Int!,
      offset: Int!
      order_key: String,
      order_asc: Boolean,
      scaling_group: String,
      status: String,
    ): PaginatedList[Agent]
   }
