Compute Session Monitoring
==========================

Full Admin
----------

Query Schema
~~~~~~~~~~~~

.. code-block:: text

   type ComputeSession {
     sess_id: String
     id: UUID
     status: String
     status_info: String
     created_at: DateTime
     terminated_at: DateTime
     agent: String
     container_id: String
     mem_slot: Int
     cpu_slot: Int
     gpu_slot: Int
     num_queries: Int
     cpu_used: Int
     max_mem_bytes: Int
     cur_mem_bytes: Int
     net_rx_bytes: Int
     net_tx_bytes: Int
     io_read_bytes: Int
     io_write_bytes: Int
     lang: String
     workers(status: String): [ComputeWorker]
   }

   type ComputeWorker {
     sess_id: String
     id: UUID
     status: String
     status_info: String
     created_at: DateTime
     terminated_at: DateTime
     agent: String
     container_id: String
     mem_slot: Int
     cpu_slot: Int
     gpu_slot: Int
     num_queries: Int
     cpu_used: Int
     max_mem_bytes: Int
     cur_mem_bytes: Int
     net_rx_bytes: Int
     net_tx_bytes: Int
     io_read_bytes: Int
     io_write_bytes: Int
   }

   type root {
     ...
     compute_sessions(access_key: String, status: String): [ComputeSession]
     compute_workers(sess_id: String!, status: String): [ComputeWorker]
   }


Restricted Owner Access
-----------------------

Query Schema
~~~~~~~~~~~~

It shares the same ``ComputeSession`` and ``ComputeWorker`` type, but with a slightly different root query type:

.. code-block:: text

   type root {
     ...
     compute_sessions(status: String): [ComputeSession]
     compute_workers(sess_id: String!, status: String): [ComputeWorker]
   }
