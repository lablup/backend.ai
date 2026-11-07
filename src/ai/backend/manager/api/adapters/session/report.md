## session

[background](/src/ai/backend/manager/api/adapters/session/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/session/adapter.py)

Scenario: incomplete 2 / 30

- built from ops (7)
  - batch_load_kernel_group_environs_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_kernel_group_resource_slots_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_kernel_groups_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_main_kernel_groups: representative success ✓ · representative rejection ✓
  - scoped_search_kernel_group_environs: representative success ✓ · representative rejection ✓
  - scoped_search_kernel_group_resource_slots: representative success ✓ · representative rejection ✓
  - scoped_search_kernel_groups: representative success ✓ · representative rejection ✓
- ops + direct implementation (10)
  - admin_search: success present 3 · rejection present 1 (global_searcher_ops, partial_bulk)
  - admin_search_kernels: success present 1 · rejection present 1 (atomic_bulk_field, global_searcher_ops)
  - batch_load_by_ids: success present 1 · rejection present 1 (partial_bulk, partial_bulk_get_ops)
  - batch_load_kernels_by_ids: success present 1 · rejection present 1 (atomic_bulk_field, partial_bulk_get_ops)
  - gql_search_by_project: success present 1 · rejection present 1 (partial_bulk, scoped_search_ops)
  - project_search: success present 1 · rejection present 1 (partial_bulk, scoped_search_ops)
  - scoped_search: success present 1 · rejection present 1 (partial_bulk, scoped_search_ops)
  - search_kernels_by_agent: success present 1 · rejection present 1 (atomic_bulk_field, global_searcher_ops)
  - search_kernels_by_session: success present 1 · rejection present 1 (atomic_bulk_field, atomic_bulk_scoped_search_ops)
  - search_sessions_by_agent: success present 1 · rejection present 1 (global_searcher_ops, partial_bulk)
- direct implementation (13)
  - batch_resource_allocation_by_kernel: success present 1 · rejection present 1 (atomic_bulk_field)
  - batch_resource_allocation_by_session: success present 1 · rejection present 1 (partial_bulk)
  - compute_schedule: success present 1 · rejection present 2 (single_entity)
  - enqueue: success present 1 · rejection present 1 (partial_bulk, scope)
  - exclude_idle_checks: success present 2 · rejection present 1 (legacy_partial_bulk)
  - get: success present 1 · rejection present 1 (partial_bulk, single_entity)
  - get_logs: success present 1 · rejection present 1 (single_entity)
  - include_idle_checks: success present 2 · rejection present 1 (legacy_partial_bulk)
  - partial_bulk_terminate: success present 3 · rejection absent (partial_bulk): SCENARIO-GAP
  - shutdown_service: success present 1 · rejection present 1 (single_entity)
  - start_service: success absent · rejection present 2 (single_entity): SCENARIO-GAP
  - terminate: success present 1 · rejection present 1 (partial_bulk)
  - update: success present 1 · rejection present 2 (partial_bulk, single_entity)

**batch_load_kernel_group_environs_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project loads a kernel group environ by id, it comes back exactly as it was stored](#reading-a-kernel-group-environ-is-batch-loaded-by-id-project) | answered |
| [when a user granted nothing loads a kernel group environ by id, the call is rejected for lack of permission](#reading-a-kernel-group-environ-is-batch-loaded-by-id-nothing) | rejected |

**batch_load_kernel_group_resource_slots_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project loads a kernel group resource slot by id, it comes back exactly as it was stored](#reading-a-kernel-group-resource-slot-is-batch-loaded-by-id-project) | answered |
| [when a user granted nothing loads a kernel group resource slot by id, the call is rejected for lack of permission](#reading-a-kernel-group-resource-slot-is-batch-loaded-by-id-nothing) | rejected |

**batch_load_kernel_groups_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project loads a kernel group by id, it comes back exactly as it was stored](#reading-a-kernel-group-is-batch-loaded-by-id-project) | answered |
| [when a user granted nothing loads a kernel group by id, the call is rejected for lack of permission](#reading-a-kernel-group-is-batch-loaded-by-id-nothing) | rejected |

**batch_load_main_kernel_groups**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project loads the main kernel group of a session, it comes back exactly as it was stored](#reading-a-main-kernel-group-is-batch-loaded-by-session-id-project) | answered |
| [when a user granted nothing loads the main kernel group of a session, the call is rejected for lack of permission](#reading-a-main-kernel-group-is-batch-loaded-by-session-id-nothing) | rejected |

**scoped_search_kernel_group_environs**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project searches the environment variables of a session's kernel groups, the stored environment variable comes back](#searching-the-kernel-group-environs-of-a-session-project) | answered |
| [when a user granted nothing searches the environment variables of a session's kernel groups, the call is rejected for lack of permission](#searching-the-kernel-group-environs-of-a-session-nothing) | rejected |

**scoped_search_kernel_group_resource_slots**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project searches the resource slots of a session's kernel groups, the stored resource slot comes back](#searching-the-kernel-group-resource-slots-of-a-session-project) | answered |
| [when a user granted nothing searches the resource slots of a session's kernel groups, the call is rejected for lack of permission](#searching-the-kernel-group-resource-slots-of-a-session-nothing) | rejected |

**scoped_search_kernel_groups**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project searches the kernel groups of a session, the stored kernel group comes back](#searching-the-kernel-groups-of-a-session-project) | answered |
| [when a user granted nothing searches the kernel groups of a session, the call is rejected for lack of permission](#searching-the-kernel-groups-of-a-session-nothing) | rejected |

**admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches with no session seeded, the answer is empty](#session-a-scenario-that-laid-no-session-finds-none) | answered |
| [when the superadmin reads the set session scheduling conditions, they are kept with the existing session information](#searching_details-session-scheduling-conditions-are-preserved-when-configured) | answered |
| [when the superadmin reads the unset session scheduling conditions, they are kept with the existing session information](#searching_details-session-scheduling-conditions-are-preserved-when-unset) | answered |
| [an unfiltered search is open only to the superadmin role, so a user granted nothing is rejected for lacking the role](#session-a-user-granted-nothing-may-not-search-sessions) | rejected |

**admin_search_kernels**

| scenario | verdict |
|---|---|
| [when a superadmin holding no permission searches every kernel, the stored kernel comes back; a role checks this operation, so the requesting user is a superadmin](#searching-superadmin-searches-every-kernel) | answered |
| [when a user who is not a superadmin searches every kernel, the role rejects it](#searching-a-user-who-is-not-a-superadmin-searches-every-kernel) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project loads a session by id, it comes back exactly as it was stored](#reading-a-session-is-batch-loaded-by-id-project) | answered |
| [when a user granted nothing loads a session by id, the call is rejected for lack of permission](#reading-a-session-is-batch-loaded-by-id-nothing) | rejected |

**batch_load_kernels_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project loads a kernel by id, it comes back exactly as it was stored](#reading-a-kernel-is-batch-loaded-by-id-project) | answered |
| [when a user granted nothing loads a kernel by id, the call is rejected for lack of permission](#reading-a-kernel-is-batch-loaded-by-id-nothing) | rejected |

**gql_search_by_project**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project searches sessions in that project's scope, the stored session comes back](#searching-gql_search_by_project-project) | answered |
| [when a user granted nothing searches sessions in a project scope, the call is rejected for lack of permission](#searching-gql_search_by_project-nothing) | rejected |

**project_search**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project searches sessions in that project's scope, the stored session comes back](#searching-project_search-project) | answered |
| [when a user granted nothing searches sessions in a project scope, the call is rejected for lack of permission](#searching-project_search-nothing) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project searches sessions in that project's scope, the stored session comes back](#searching-scoped_search-project) | answered |
| [when a user granted nothing searches sessions in a project scope, the call is rejected for lack of permission](#searching-scoped_search-nothing) | rejected |

**search_kernels_by_agent**

| scenario | verdict |
|---|---|
| [when the kernels are searched for an agent that runs none, the answer is empty; a role checks this operation, so the requesting user is a superadmin](#agent_searching-an-agent-that-runs-no-kernel-superadmin) | answered |
| [when a user who is not a superadmin searches the kernels of an agent, the role rejects it](#agent_searching-an-agent-that-runs-no-kernel-a-user-who-is-not-a-superadmin) | rejected |

**search_kernels_by_session**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project searches the kernels of a session, the stored kernel comes back](#searching-the-kernels-of-a-session-project) | answered |
| [when a user granted nothing searches the kernels of a session, the call is rejected for lack of permission](#searching-the-kernels-of-a-session-nothing) | rejected |

**search_sessions_by_agent**

| scenario | verdict |
|---|---|
| [when the sessions are searched for an agent that runs none, the answer is empty; a role checks this operation, so the requesting user is a superadmin](#agent_searching-an-agent-that-runs-no-session-superadmin) | answered |
| [when a user who is not a superadmin searches the sessions of an agent, the role rejects it](#agent_searching-an-agent-that-runs-no-session-a-user-who-is-not-a-superadmin) | rejected |

**batch_resource_allocation_by_kernel**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project loads the resource allocation of a kernel, the allocation it asked for comes back](#loading_allocations-a-kernel-allocation-is-batch-loaded-project) | answered |
| [when a user granted nothing loads the resource allocation of a kernel, the call is rejected for lack of permission](#loading_allocations-a-kernel-allocation-is-batch-loaded-nothing) | rejected |

**batch_resource_allocation_by_session**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project loads the resource allocation of a session, the allocation it asked for comes back](#loading_allocations-a-session-allocation-is-batch-loaded-project) | answered |
| [when a user granted nothing loads the resource allocation of a session, the call succeeds but that entry is rejected for lack of permission](#loading_allocations-a-session-allocation-is-batch-loaded-nothing) | rejected |

**compute_schedule**

| scenario | verdict |
|---|---|
| [when a user who can read the resource group computes a kernel against a group whose agent holds enough of the slot, the kernel is answered as fitting](#computing_schedule-computing-whether-a-kernel-fits-granted-with-an-agent) | answered |
| [when a user who may not read the resource group computes whether a kernel fits, the call is rejected for lack of permission](#computing_schedule-computing-whether-a-kernel-fits-granted-nothing-with-an-agent) | rejected |
| [when a user who can read the resource group computes a kernel against a group with no agent, the call is rejected because no agent is there](#computing_schedule-computing-whether-a-kernel-fits-granted-without-an-agent) | rejected |

**enqueue**

| scenario | verdict |
|---|---|
| [when a user who may create sessions in the project creates one, the whole pending session comes back](#enqueueing-creating-a-session-granted) | answered |
| [when a user granted nothing creates a session in a project, the call is rejected for lack of permission](#enqueueing-creating-a-session-granted-nothing) | rejected |

**exclude_idle_checks**

| scenario | verdict |
|---|---|
| [when a user granted session update in the project excludes a session with a checker the catalog does not hold, that pair comes back in the failed list](#idle_checking-excluding-a-pair-from-idle-checks-granted-a-checker-that-is-not-there) | answered |
| [when a user granted session update in the project excludes one session and checker pair, that pair comes back excluded](#idle_checking-excluding-a-pair-from-idle-checks-granted-the-laid-pair) | answered |
| [when a user granted nothing excludes a session from idle checks, the call is rejected for lack of permission](#idle_checking-excluding-a-pair-from-idle-checks-granted-nothing-the-laid-pair) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project reads a session by id, it comes back exactly as it was stored](#reading-a-session-is-read-by-id-project) | answered |
| [when a user granted nothing reads a session by id, the call is rejected for lack of permission](#reading-a-session-is-read-by-id-nothing) | rejected |

**get_logs**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project reads the container log of a session, the log the agent answered comes back](#logs_and_services-the-container-log-of-a-session-project) | answered |
| [when a user granted nothing reads the container log of a session, the call is rejected for lack of permission](#logs_and_services-the-container-log-of-a-session-nothing) | rejected |

**include_idle_checks**

| scenario | verdict |
|---|---|
| [when a user granted session update in the project includes a session with a checker the catalog does not hold, that pair comes back in the failed list](#idle_checking-including-a-pair-in-idle-checks-granted-a-checker-that-is-not-there) | answered |
| [when a user granted session update in the project includes one session and checker pair again, that pair comes back included](#idle_checking-including-a-pair-in-idle-checks-granted-the-laid-pair) | answered |
| [when a user granted nothing includes a session in idle checks again, the call is rejected for lack of permission](#idle_checking-including-a-pair-in-idle-checks-granted-nothing-the-laid-pair) | rejected |

**partial_bulk_terminate**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to terminate a pending session, none is terminated and it comes back in the failed list for lack of permission](#partial_bulk_terminating-a-user-granted-nothing-terminates-none) | answered |
| [when a user granted session soft delete in the project scope terminates the pending session of that project, it comes back as cancelled in the processed list](#partial_bulk_terminating-a-user-granted-session-soft-delete-in-the-project-terminates-its-session) | answered |
| [when the superadmin terminates a pending session and a missing id in one call, the pending session comes back as cancelled and the missing id as skipped in the processed list](#partial_bulk_terminating-terminating-several-skips-the-missing-one) | answered |

**shutdown_service**

| scenario | verdict |
|---|---|
| [when a user granted session soft delete in the project shuts a service of a session down, the call answers nothing](#logs_and_services-shutting-down-a-service-granted) | answered |
| [when a user granted nothing shuts a service of a session down, the call is rejected for lack of permission](#logs_and_services-shutting-down-a-service-granted-nothing) | rejected |

**start_service**

| scenario | verdict |
|---|---|
| [when a user granted session create in the project starts a service of a session whose resource group has no proxy address, the call is rejected as unavailable](#logs_and_services-starting-a-service-granted) | rejected |
| [when a user granted nothing starts a service of a session, the call is rejected for lack of permission](#logs_and_services-starting-a-service-granted-nothing) | rejected |

**terminate**

| scenario | verdict |
|---|---|
| [when the superadmin terminates a pending session, it comes back in the cancelled list](#terminating-a-superadmin-terminates-a-pending-session) | answered |
| [when a user granted nothing tries to terminate a pending session, the whole call is rejected](#terminating-a-user-granted-nothing-may-not-terminate) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted session read in the project updates a session with no value to change, the current session comes back](#updating-a-session-update-with-no-field-project) | answered |
| [when a user granted nothing updates a session with no value to change, the call is rejected for lack of permission](#updating-a-session-update-with-no-field-nothing) | rejected |
| [when a user granted session update in the project renames a session that is not running, the call is rejected because of its state](#updating-renaming-a-session-that-is-not-running-is-refused) | rejected |

### batch_load_kernel_group_environs_by_ids

<a id="reading-a-kernel-group-environ-is-batch-loaded-by-id-project"></a>

#### [a-kernel-group-environ-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted session read in the project loads a kernel group environ by id, it comes back exactly as it was stored

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.batch_load_kernel_group_environs_by_ids: user-2 loads an environment variable of the session session-1's kernel group by id

Then

- the environment variable comes back as one entry as it was stored
  - length = 1
  - [0]: same as the whole information of the stored environment variable row

<a id="reading-a-kernel-group-environ-is-batch-loaded-by-id-nothing"></a>

#### [a-kernel-group-environ-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted nothing loads a kernel group environ by id, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.batch_load_kernel_group_environs_by_ids: user-2 loads an environment variable of the session session-1's kernel group by id

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### batch_load_kernel_group_resource_slots_by_ids

<a id="reading-a-kernel-group-resource-slot-is-batch-loaded-by-id-project"></a>

#### [a-kernel-group-resource-slot-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted session read in the project loads a kernel group resource slot by id, it comes back exactly as it was stored

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.batch_load_kernel_group_resource_slots_by_ids: user-2 loads a resource slot of the session session-1's kernel group by id

Then

- the resource slot row comes back as one entry as it was stored
  - length = 1
  - [0]: same as the whole information of the stored resource slot row

<a id="reading-a-kernel-group-resource-slot-is-batch-loaded-by-id-nothing"></a>

#### [a-kernel-group-resource-slot-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted nothing loads a kernel group resource slot by id, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.batch_load_kernel_group_resource_slots_by_ids: user-2 loads a resource slot of the session session-1's kernel group by id

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### batch_load_kernel_groups_by_ids

<a id="reading-a-kernel-group-is-batch-loaded-by-id-project"></a>

#### [a-kernel-group-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted session read in the project loads a kernel group by id, it comes back exactly as it was stored

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.batch_load_kernel_groups_by_ids: user-2 loads the kernel group of the session session-1 by id

Then

- the kernel group comes back as one entry exactly as it was stored
  - length = 1
  - [0]: same as the whole information of the stored kernel group

<a id="reading-a-kernel-group-is-batch-loaded-by-id-nothing"></a>

#### [a-kernel-group-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted nothing loads a kernel group by id, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.batch_load_kernel_groups_by_ids: user-2 loads the kernel group of the session session-1 by id

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### batch_load_main_kernel_groups

<a id="reading-a-main-kernel-group-is-batch-loaded-by-session-id-project"></a>

#### [a-main-kernel-group-is-batch-loaded-by-session-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted session read in the project loads the main kernel group of a session, it comes back exactly as it was stored

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.batch_load_main_kernel_groups: user-2 loads the main kernel group of the session session-1 by session id

Then

- the main kernel group of the session comes back as one entry as it was stored
  - length = 1
  - [0]: same as the whole information of the stored kernel group

<a id="reading-a-main-kernel-group-is-batch-loaded-by-session-id-nothing"></a>

#### [a-main-kernel-group-is-batch-loaded-by-session-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted nothing loads the main kernel group of a session, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.batch_load_main_kernel_groups: user-2 loads the main kernel group of the session session-1 by session id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search_kernel_group_environs

<a id="searching-the-kernel-group-environs-of-a-session-project"></a>

#### [the-kernel-group-environs-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted session read in the project searches the environment variables of a session's kernel groups, the stored environment variable comes back

Given

- one pending session with a kernel and its kernel group, the same shape laid beside it in the same project and again in another project, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1
  - Session beside-session-1: waiting to be scheduled
  - Session beside-session-1: has one main kernel group
  - Session beside-session-1(has one main kernel group): has one environment variable
  - Session beside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session beside-session-1: has one kernel asking for slot-1 1
  - Project outside-project-1
  - Session outside-session-1: waiting to be scheduled
  - Session outside-session-1: has one main kernel group
  - Session outside-session-1(has one main kernel group): has one environment variable
  - Session outside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session outside-session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.scoped_search_kernel_group_environs: user-2 searches the environment variables of session-1's kernel groups

Then

- the environment variable comes back exactly as it was stored
  - items: same as the whole information of the stored environment variable row
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-kernel-group-environs-of-a-session-nothing"></a>

#### [the-kernel-group-environs-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted nothing searches the environment variables of a session's kernel groups, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.scoped_search_kernel_group_environs: user-2 searches the environment variables of session-1's kernel groups

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search_kernel_group_resource_slots

<a id="searching-the-kernel-group-resource-slots-of-a-session-project"></a>

#### [the-kernel-group-resource-slots-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted session read in the project searches the resource slots of a session's kernel groups, the stored resource slot comes back

Given

- one pending session with a kernel and its kernel group, the same shape laid beside it in the same project and again in another project, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1
  - Session beside-session-1: waiting to be scheduled
  - Session beside-session-1: has one main kernel group
  - Session beside-session-1(has one main kernel group): has one environment variable
  - Session beside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session beside-session-1: has one kernel asking for slot-1 1
  - Project outside-project-1
  - Session outside-session-1: waiting to be scheduled
  - Session outside-session-1: has one main kernel group
  - Session outside-session-1(has one main kernel group): has one environment variable
  - Session outside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session outside-session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.scoped_search_kernel_group_resource_slots: user-2 searches the resource slots of session-1's kernel groups

Then

- the resource slot row comes back exactly as it was stored
  - items: same as the whole information of the stored resource slot row
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-kernel-group-resource-slots-of-a-session-nothing"></a>

#### [the-kernel-group-resource-slots-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted nothing searches the resource slots of a session's kernel groups, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.scoped_search_kernel_group_resource_slots: user-2 searches the resource slots of session-1's kernel groups

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search_kernel_groups

<a id="searching-the-kernel-groups-of-a-session-project"></a>

#### [the-kernel-groups-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted session read in the project searches the kernel groups of a session, the stored kernel group comes back

Given

- one pending session with a kernel and its kernel group, the same shape laid beside it in the same project and again in another project, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1
  - Session beside-session-1: waiting to be scheduled
  - Session beside-session-1: has one main kernel group
  - Session beside-session-1(has one main kernel group): has one environment variable
  - Session beside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session beside-session-1: has one kernel asking for slot-1 1
  - Project outside-project-1
  - Session outside-session-1: waiting to be scheduled
  - Session outside-session-1: has one main kernel group
  - Session outside-session-1(has one main kernel group): has one environment variable
  - Session outside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session outside-session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.scoped_search_kernel_groups: user-2 searches the kernel groups of session-1

Then

- the kernel group comes back exactly as it was stored
  - items: same as the whole information of the stored kernel group
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-kernel-groups-of-a-session-nothing"></a>

#### [the-kernel-groups-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted nothing searches the kernel groups of a session, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.scoped_search_kernel_groups: user-2 searches the kernel groups of session-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### admin_search

<a id="session-a-scenario-that-laid-no-session-finds-none"></a>

#### [a-scenario-that-laid-no-session-finds-none](/tests/scenario/bai_scenario/manager/session/test_session.py): pass

when the superadmin searches with no session seeded, the answer is empty

Given

- one domain and one superadmin in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- SessionAdapter.admin_search: user-1 searches everything without a filter

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching_details-session-scheduling-conditions-are-preserved-when-configured"></a>

#### [session-scheduling-conditions-are-preserved-when-configured](/tests/scenario/bai_scenario/manager/session/test_searching_details.py): pass

when the superadmin reads the set session scheduling conditions, they are kept with the existing session information

Given

- a session with all three values set and the superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session group session-group-1: places the sessions on different agents when possible
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-2: alive, and has not reported any slot yet
  - Session session-1: a pending session with a session group and requested_starts_at set
  - Session session-1: has one designated agent
  - Session session-1: has one designated agent

When

- SessionAdapter.admin_search: user-2 searches everything without a filter

Then

- the whole session information including the scheduling conditions comes back exactly as it was stored
  - items: same as the whole information of the stored session
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_details-session-scheduling-conditions-are-preserved-when-unset"></a>

#### [session-scheduling-conditions-are-preserved-when-unset](/tests/scenario/bai_scenario/manager/session/test_searching_details.py): pass

when the superadmin reads the unset session scheduling conditions, they are kept with the existing session information

Given

- a session with none of the three values set and the superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled

When

- SessionAdapter.admin_search: user-2 searches everything without a filter

Then

- the whole session information including the scheduling conditions comes back exactly as it was stored
  - items: same as the whole information of the stored session
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="session-a-user-granted-nothing-may-not-search-sessions"></a>

#### [a-user-granted-nothing-may-not-search-sessions](/tests/scenario/bai_scenario/manager/session/test_session.py): pass

an unfiltered search is open only to the superadmin role, so a user granted nothing is rejected for lacking the role

Given

- one domain and one user in it
  - Domain host-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SessionAdapter.admin_search: user-1 searches everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_kernels

<a id="searching-superadmin-searches-every-kernel"></a>

#### [superadmin-searches-every-kernel](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a superadmin holding no permission searches every kernel, the stored kernel comes back; a role checks this operation, so the requesting user is a superadmin

Given

- one pending session with a kernel and its kernel group, the same shape laid beside it in the same project and again in another project, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Session beside-session-1: waiting to be scheduled
  - Session beside-session-1: has one main kernel group
  - Session beside-session-1(has one main kernel group): has one environment variable
  - Session beside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session beside-session-1: has one kernel asking for slot-1 1
  - Project outside-project-1
  - Session outside-session-1: waiting to be scheduled
  - Session outside-session-1: has one main kernel group
  - Session outside-session-1(has one main kernel group): has one environment variable
  - Session outside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session outside-session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.admin_search_kernels: user-2 searches every kernel without a filter

Then

- the kernel comes back exactly as it was stored
  - items: same as the whole information of the stored kernel
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-a-superadmin-searches-every-kernel"></a>

#### [a-user-who-is-not-a-superadmin-searches-every-kernel](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user who is not a superadmin searches every kernel, the role rejects it

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.admin_search_kernels: user-2 searches every kernel without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-a-session-is-batch-loaded-by-id-project"></a>

#### [a-session-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted session read in the project loads a session by id, it comes back exactly as it was stored

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.batch_load_by_ids: user-2 loads the session session-1 by id

Then

- the session comes back as one entry exactly as it was stored
  - length = 1
  - [0]: same as the whole information of the stored session

<a id="reading-a-session-is-batch-loaded-by-id-nothing"></a>

#### [a-session-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted nothing loads a session by id, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.batch_load_by_ids: user-2 loads the session session-1 by id

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### batch_load_kernels_by_ids

<a id="reading-a-kernel-is-batch-loaded-by-id-project"></a>

#### [a-kernel-is-batch-loaded-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted session read in the project loads a kernel by id, it comes back exactly as it was stored

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.batch_load_kernels_by_ids: user-2 loads the kernel of the session session-1 by id

Then

- the kernel comes back as one entry exactly as it was stored
  - length = 1
  - [0]: same as the whole information of the stored kernel

<a id="reading-a-kernel-is-batch-loaded-by-id-nothing"></a>

#### [a-kernel-is-batch-loaded-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted nothing loads a kernel by id, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.batch_load_kernels_by_ids: user-2 loads the kernel of the session session-1 by id

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### gql_search_by_project

<a id="searching-gql_search_by_project-project"></a>

#### [gql_search_by_project-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted session read in the project searches sessions in that project's scope, the stored session comes back

Given

- one pending session with a kernel and its kernel group, the same shape laid beside it in the same project and again in another project, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1
  - Session beside-session-1: waiting to be scheduled
  - Session beside-session-1: has one main kernel group
  - Session beside-session-1(has one main kernel group): has one environment variable
  - Session beside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session beside-session-1: has one kernel asking for slot-1 1
  - Project outside-project-1
  - Session outside-session-1: waiting to be scheduled
  - Session outside-session-1: has one main kernel group
  - Session outside-session-1(has one main kernel group): has one environment variable
  - Session outside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session outside-session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.gql_search_by_project: user-2 searches the sessions of team-1

Then

- the session of the project comes back exactly as it was stored
  - items: same as the whole information of the stored session
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-gql_search_by_project-nothing"></a>

#### [gql_search_by_project-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted nothing searches sessions in a project scope, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.gql_search_by_project: user-2 searches the sessions of team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### project_search

<a id="searching-project_search-project"></a>

#### [project_search-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted session read in the project searches sessions in that project's scope, the stored session comes back

Given

- one pending session with a kernel and its kernel group, the same shape laid beside it in the same project and again in another project, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1
  - Session beside-session-1: waiting to be scheduled
  - Session beside-session-1: has one main kernel group
  - Session beside-session-1(has one main kernel group): has one environment variable
  - Session beside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session beside-session-1: has one kernel asking for slot-1 1
  - Project outside-project-1
  - Session outside-session-1: waiting to be scheduled
  - Session outside-session-1: has one main kernel group
  - Session outside-session-1(has one main kernel group): has one environment variable
  - Session outside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session outside-session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.project_search: user-2 searches sessions by the project id of team-1

Then

- the session of the project comes back exactly as it was stored
  - items: same as the whole information of the stored session
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-project_search-nothing"></a>

#### [project_search-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted nothing searches sessions in a project scope, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.project_search: user-2 searches sessions by the project id of team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search

<a id="searching-scoped_search-project"></a>

#### [scoped_search-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted session read in the project searches sessions in that project's scope, the stored session comes back

Given

- one pending session with a kernel and its kernel group, the same shape laid beside it in the same project and again in another project, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1
  - Session beside-session-1: waiting to be scheduled
  - Session beside-session-1: has one main kernel group
  - Session beside-session-1(has one main kernel group): has one environment variable
  - Session beside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session beside-session-1: has one kernel asking for slot-1 1
  - Project outside-project-1
  - Session outside-session-1: waiting to be scheduled
  - Session outside-session-1: has one main kernel group
  - Session outside-session-1(has one main kernel group): has one environment variable
  - Session outside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session outside-session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.scoped_search: user-2 searches sessions in the scope of team-1

Then

- the session of the project comes back exactly as it was stored
  - items: same as the whole information of the stored session
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-scoped_search-nothing"></a>

#### [scoped_search-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted nothing searches sessions in a project scope, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.scoped_search: user-2 searches sessions in the scope of team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_kernels_by_agent

<a id="agent_searching-an-agent-that-runs-no-kernel-superadmin"></a>

#### [an-agent-that-runs-no-kernel-superadmin](/tests/scenario/bai_scenario/manager/session/test_agent_searching.py): pass

when the kernels are searched for an agent that runs none, the answer is empty; a role checks this operation, so the requesting user is a superadmin

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.search_kernels_by_agent: user-2 searches the kernels one agent runs

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="agent_searching-an-agent-that-runs-no-kernel-a-user-who-is-not-a-superadmin"></a>

#### [an-agent-that-runs-no-kernel-a-user-who-is-not-a-superadmin](/tests/scenario/bai_scenario/manager/session/test_agent_searching.py): pass

when a user who is not a superadmin searches the kernels of an agent, the role rejects it

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.search_kernels_by_agent: user-2 searches the kernels one agent runs

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search_kernels_by_session

<a id="searching-the-kernels-of-a-session-project"></a>

#### [the-kernels-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted session read in the project searches the kernels of a session, the stored kernel comes back

Given

- one pending session with a kernel and its kernel group, the same shape laid beside it in the same project and again in another project, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1
  - Session beside-session-1: waiting to be scheduled
  - Session beside-session-1: has one main kernel group
  - Session beside-session-1(has one main kernel group): has one environment variable
  - Session beside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session beside-session-1: has one kernel asking for slot-1 1
  - Project outside-project-1
  - Session outside-session-1: waiting to be scheduled
  - Session outside-session-1: has one main kernel group
  - Session outside-session-1(has one main kernel group): has one environment variable
  - Session outside-session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session outside-session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.search_kernels_by_session: user-2 searches the kernels of session-1

Then

- the kernel comes back exactly as it was stored
  - items: same as the whole information of the stored kernel
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-kernels-of-a-session-nothing"></a>

#### [the-kernels-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_searching.py): pass

when a user granted nothing searches the kernels of a session, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.search_kernels_by_session: user-2 searches the kernels of session-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_sessions_by_agent

<a id="agent_searching-an-agent-that-runs-no-session-superadmin"></a>

#### [an-agent-that-runs-no-session-superadmin](/tests/scenario/bai_scenario/manager/session/test_agent_searching.py): pass

when the sessions are searched for an agent that runs none, the answer is empty; a role checks this operation, so the requesting user is a superadmin

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.search_sessions_by_agent: user-2 searches the sessions one agent runs

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="agent_searching-an-agent-that-runs-no-session-a-user-who-is-not-a-superadmin"></a>

#### [an-agent-that-runs-no-session-a-user-who-is-not-a-superadmin](/tests/scenario/bai_scenario/manager/session/test_agent_searching.py): pass

when a user who is not a superadmin searches the sessions of an agent, the role rejects it

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.search_sessions_by_agent: user-2 searches the sessions one agent runs

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_resource_allocation_by_kernel

<a id="loading_allocations-a-kernel-allocation-is-batch-loaded-project"></a>

#### [a-kernel-allocation-is-batch-loaded-project](/tests/scenario/bai_scenario/manager/session/test_loading_allocations.py): pass

when a user granted session read in the project loads the resource allocation of a kernel, the allocation it asked for comes back

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.batch_resource_allocation_by_kernel: user-2 loads the resource allocation of the kernel of session-1 by id

Then

- the resource allocation of the kernel comes back as one entry holding what it asked for
  - length = 1
  - [0]: same as the stored resource allocation

<a id="loading_allocations-a-kernel-allocation-is-batch-loaded-nothing"></a>

#### [a-kernel-allocation-is-batch-loaded-nothing](/tests/scenario/bai_scenario/manager/session/test_loading_allocations.py): pass

when a user granted nothing loads the resource allocation of a kernel, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.batch_resource_allocation_by_kernel: user-2 loads the resource allocation of the kernel of session-1 by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### batch_resource_allocation_by_session

<a id="loading_allocations-a-session-allocation-is-batch-loaded-project"></a>

#### [a-session-allocation-is-batch-loaded-project](/tests/scenario/bai_scenario/manager/session/test_loading_allocations.py): pass

when a user granted session read in the project loads the resource allocation of a session, the allocation it asked for comes back

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.batch_resource_allocation_by_session: user-2 loads the resource allocation of the session session-1 by id

Then

- the resource allocation of the session comes back as one entry holding what it asked for
  - length = 1
  - [0]: same as the stored resource allocation

<a id="loading_allocations-a-session-allocation-is-batch-loaded-nothing"></a>

#### [a-session-allocation-is-batch-loaded-nothing](/tests/scenario/bai_scenario/manager/session/test_loading_allocations.py): pass

when a user granted nothing loads the resource allocation of a session, the call succeeds but that entry is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.batch_resource_allocation_by_session: user-2 loads the resource allocation of the session session-1 by id

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### compute_schedule

<a id="computing_schedule-computing-whether-a-kernel-fits-granted-with-an-agent"></a>

#### [computing-whether-a-kernel-fits-granted-with-an-agent](/tests/scenario/bai_scenario/manager/session/test_computing_schedule.py): pass

when a user who can read the resource group computes a kernel against a group whose agent holds enough of the slot, the kernel is answered as fitting

Given

- one resource group with an agent reporting capacity and one user who can read the group
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type cpu: a revision may leave it unfilled
  - Resource slot type mem: a revision may leave it unfilled
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: cpu slot capacity 8 reported, 0 in use
  - Agent agent-1: mem slot capacity 34359738368 reported, 0 in use
  - Prepare a user granted the READ role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: READ allowed on every resource_group
    - regular user user-2: holds Role group-role-1

When

- SessionAdapter.compute_schedule: user-2 computes whether a kernel asking for cpu and mem fits the resource group

Then

- the slots and architecture asked for come back, and the one kernel is answered as fitting
  - results count = 1
  - requested_slots: the slots asked for: cpu 1, mem 2147483648
  - requested_architecture = 'x86_64'
  - success = True
  - reason_hint = None

<a id="computing_schedule-computing-whether-a-kernel-fits-granted-nothing-with-an-agent"></a>

#### [computing-whether-a-kernel-fits-granted-nothing-with-an-agent](/tests/scenario/bai_scenario/manager/session/test_computing_schedule.py): pass

when a user who may not read the resource group computes whether a kernel fits, the call is rejected for lack of permission

Given

- one resource group with an agent reporting capacity and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type cpu: a revision may leave it unfilled
  - Resource slot type mem: a revision may leave it unfilled
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: cpu slot capacity 8 reported, 0 in use
  - Agent agent-1: mem slot capacity 34359738368 reported, 0 in use

When

- SessionAdapter.compute_schedule: user-2 computes whether a kernel asking for cpu and mem fits the resource group

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="computing_schedule-computing-whether-a-kernel-fits-granted-without-an-agent"></a>

#### [computing-whether-a-kernel-fits-granted-without-an-agent](/tests/scenario/bai_scenario/manager/session/test_computing_schedule.py): pass

when a user who can read the resource group computes a kernel against a group with no agent, the call is rejected because no agent is there

Given

- one resource group with no agent and one user who can read the group
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type cpu: a revision may leave it unfilled
  - Resource slot type mem: a revision may leave it unfilled
  - Prepare a user granted the READ role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: READ allowed on every resource_group
    - regular user user-2: holds Role group-role-1

When

- SessionAdapter.compute_schedule: user-2 computes whether a kernel asking for cpu and mem fits the resource group

Then

- the call is rejected
  - rejected: NoAgentsInResourceGroupError

### enqueue

<a id="enqueueing-creating-a-session-granted"></a>

#### [creating-a-session-granted](/tests/scenario/bai_scenario/manager/session/test_enqueueing.py): pass

when a user who may create sessions in the project creates one, the whole pending session comes back

Given

- a resource group whose agent holds the slots a session asks for, and one user who may create sessions in that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Project team-1 whose sessions can use Resource group resource-group-1
  - Resource slot type cpu: a revision may leave it unfilled
  - Resource slot type mem: a revision may leave it unfilled
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: cpu slot capacity 8 reported, 0 in use
  - Agent agent-1: mem slot capacity 34359738368 reported, 0 in use
  - Prepare a user who may create and read sessions in the project
    - Role session-owner-1: applies only within the scope it is granted in
    - Role session-owner-1: CREATE allowed on every session
    - Role session-owner-1: READ allowed on every session
    - regular user user-2: holds Role session-owner-1

When

- SessionAdapter.enqueue: user-2 creates the session created-session in that project

Then

- the whole session that was created comes back as it was stored
  - id: skipped: the database generates it
  - entity_id: same as the id
  - image_ids: same as the image of the session
  - domain_name = 'home-1'
  - user_id: same as the caller's id
  - project_id: same as the id of the project
  - metadata.creation_id: a non-empty value this run made
  - metadata.name = 'created-session'
  - metadata.session_type = 'interactive'
  - metadata.access_key: same as the key the session was requested with
  - metadata.cluster_mode = 'SINGLE_NODE'
  - metadata.cluster_size = 1
  - metadata.tier = 10
  - metadata.priority = 10
  - metadata.job_priority = 0
  - metadata.is_preemptible = False
  - metadata.tag = None
  - resource.allocation: the allocation of cpu 1, mem 2147483648
  - resource.resource_group_name = 'resource-group-1'
  - resource.session_group_id = None
  - resource.designated_agent_ids = None
  - lifecycle.status = 'PENDING'
  - lifecycle.result = 'undefined'
  - lifecycle.created_at: the time this run wrote
  - lifecycle.terminated_at = None
  - lifecycle.starts_at = None
  - lifecycle.requested_starts_at = None
  - lifecycle.batch_timeout = None
  - runtime.environ = None
  - runtime.bootstrap_script = None
  - runtime.startup_command = None
  - runtime.callback_url = None
  - network.use_host_network = False
  - network.network_type = 'volatile'
  - network.network_id = None
  - replica_id = None

<a id="enqueueing-creating-a-session-granted-nothing"></a>

#### [creating-a-session-granted-nothing](/tests/scenario/bai_scenario/manager/session/test_enqueueing.py): pass

when a user granted nothing creates a session in a project, the call is rejected for lack of permission

Given

- a resource group whose agent holds the slots a session asks for, and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Project team-1 whose sessions can use Resource group resource-group-1
  - Resource slot type cpu: a revision may leave it unfilled
  - Resource slot type mem: a revision may leave it unfilled
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: cpu slot capacity 8 reported, 0 in use
  - Agent agent-1: mem slot capacity 34359738368 reported, 0 in use

When

- SessionAdapter.enqueue: user-2 creates the session created-session in that project

Then

- the call is rejected
  - rejected: NotEnoughPermission

### exclude_idle_checks

<a id="idle_checking-excluding-a-pair-from-idle-checks-granted-a-checker-that-is-not-there"></a>

#### [excluding-a-pair-from-idle-checks-granted-a-checker-that-is-not-there](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

when a user granted session update in the project excludes a session with a checker the catalog does not hold, that pair comes back in the failed list

Given

- one pending session and one idle checker, and one user granted the session update permission in that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Prepare a user granted a session permission in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-updater-1: applies only within the scope it is granted in
    - Role session-updater-1: UPDATE allowed on every session
    - regular user user-2: holds Role session-updater-1

When

- SessionAdapter.exclude_idle_checks: user-2 excludes the session and one checker the catalog does not hold from idle checks

Then

- no pair is excluded and the one the caller named comes back in the failed list
  - items = []
  - failed count = 1
  - failed[0].session_id: same as the id of the session
  - failed[0].checker_id: same as the id of the checker named
  - failed[0].message: a reason containing 'Idle checker'

<a id="idle_checking-excluding-a-pair-from-idle-checks-granted-the-laid-pair"></a>

#### [excluding-a-pair-from-idle-checks-granted-the-laid-pair](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

when a user granted session update in the project excludes one session and checker pair, that pair comes back excluded

Given

- one pending session and one idle checker, and one user granted the session update permission in that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Prepare a user granted a session permission in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-updater-1: applies only within the scope it is granted in
    - Role session-updater-1: UPDATE allowed on every session
    - regular user user-2: holds Role session-updater-1

When

- SessionAdapter.exclude_idle_checks: user-2 excludes the session and the checker from idle checks

Then

- the one pair comes back excluded and nothing failed
  - items count = 1
  - failed count = 0
  - items[0].checker_id: same as the id of the checker
  - items[0].session_id: same as the id of the session

<a id="idle_checking-excluding-a-pair-from-idle-checks-granted-nothing-the-laid-pair"></a>

#### [excluding-a-pair-from-idle-checks-granted-nothing-the-laid-pair](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

when a user granted nothing excludes a session from idle checks, the call is rejected for lack of permission

Given

- one pending session and one idle checker, and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds

When

- SessionAdapter.exclude_idle_checks: user-2 excludes the session and the checker from idle checks

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get

<a id="reading-a-session-is-read-by-id-project"></a>

#### [a-session-is-read-by-id-project](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted session read in the project reads a session by id, it comes back exactly as it was stored

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.get: user-2 reads the session session-1 by id

Then

- the whole session comes back exactly as it was stored
  - session: same as the whole information of the stored session

<a id="reading-a-session-is-read-by-id-nothing"></a>

#### [a-session-is-read-by-id-nothing](/tests/scenario/bai_scenario/manager/session/test_reading.py): pass

when a user granted nothing reads a session by id, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.get: user-2 reads the session session-1 by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_logs

<a id="logs_and_services-the-container-log-of-a-session-project"></a>

#### [the-container-log-of-a-session-project](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

when a user granted session read in the project reads the container log of a session, the log the agent answered comes back

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.get_logs: user-2 reads the container log of session-1

Then

- the container log the agent answered comes back as it is
  - logs = 'the container log this run hands back'

<a id="logs_and_services-the-container-log-of-a-session-nothing"></a>

#### [the-container-log-of-a-session-nothing](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

when a user granted nothing reads the container log of a session, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.get_logs: user-2 reads the container log of session-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### include_idle_checks

<a id="idle_checking-including-a-pair-in-idle-checks-granted-a-checker-that-is-not-there"></a>

#### [including-a-pair-in-idle-checks-granted-a-checker-that-is-not-there](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

when a user granted session update in the project includes a session with a checker the catalog does not hold, that pair comes back in the failed list

Given

- one pending session and one idle checker, and one user granted the session update permission in that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Prepare a user granted a session permission in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-updater-1: applies only within the scope it is granted in
    - Role session-updater-1: UPDATE allowed on every session
    - regular user user-2: holds Role session-updater-1

When

- SessionAdapter.include_idle_checks: user-2 includes the session and one checker the catalog does not hold in idle checks again

Then

- no pair is included and the one the caller named comes back in the failed list
  - items = []
  - failed count = 1
  - failed[0].session_id: same as the id of the session
  - failed[0].checker_id: same as the id of the checker named
  - failed[0].message: a reason containing 'Idle checker'

<a id="idle_checking-including-a-pair-in-idle-checks-granted-the-laid-pair"></a>

#### [including-a-pair-in-idle-checks-granted-the-laid-pair](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

when a user granted session update in the project includes one session and checker pair again, that pair comes back included

Given

- one pending session and one idle checker, and one user granted the session update permission in that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Prepare a user granted a session permission in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-updater-1: applies only within the scope it is granted in
    - Role session-updater-1: UPDATE allowed on every session
    - regular user user-2: holds Role session-updater-1

When

- SessionAdapter.include_idle_checks: user-2 includes the session and the checker in idle checks again

Then

- the one pair comes back included and nothing failed
  - items count = 1
  - failed count = 0
  - items[0].checker_id: same as the id of the checker
  - items[0].session_id: same as the id of the session

<a id="idle_checking-including-a-pair-in-idle-checks-granted-nothing-the-laid-pair"></a>

#### [including-a-pair-in-idle-checks-granted-nothing-the-laid-pair](/tests/scenario/bai_scenario/manager/session/test_idle_checking.py): pass

when a user granted nothing includes a session in idle checks again, the call is rejected for lack of permission

Given

- one pending session and one idle checker, and one user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds

When

- SessionAdapter.include_idle_checks: user-2 includes the session and the checker in idle checks again

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_terminate

<a id="partial_bulk_terminating-a-user-granted-nothing-terminates-none"></a>

#### [a-user-granted-nothing-terminates-none](/tests/scenario/bai_scenario/manager/session/test_partial_bulk_terminating.py): pass

when a user granted nothing tries to terminate a pending session, none is terminated and it comes back in the failed list for lack of permission

Given

- one pending session and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled

When

- SessionAdapter.partial_bulk_terminate: user-2 terminates a pending session in one call

Then

- no session is terminated and the target comes back in the failed list for lack of permission
  - successes = []
  - failed count = 1
  - failed[0].id: same as the id of the pending session
  - failed[0].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_terminating-a-user-granted-session-soft-delete-in-the-project-terminates-its-session"></a>

#### [a-user-granted-session-soft-delete-in-the-project-terminates-its-session](/tests/scenario/bai_scenario/manager/session/test_partial_bulk_terminating.py): pass

when a user granted session soft delete in the project scope terminates the pending session of that project, it comes back as cancelled in the processed list

Given

- one pending session and one regular user granted the session soft delete permission in the project scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled
  - Prepare a user granted the session soft delete permission in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-terminator-1: applies only within the scope it is granted in
    - Role session-terminator-1: SOFT_DELETE allowed on every session
    - regular user user-2: holds Role session-terminator-1

When

- SessionAdapter.partial_bulk_terminate: user-2 terminates a pending session in one call

Then

- the pending session comes back in the processed list as cancelled and nothing failed
  - successes count = 1
  - failed = []
  - successes[0].id: same as the id of the pending session
  - successes[0].status = <SessionTerminationStatusEnum.CANCELLED: 'cancelled'>

<a id="partial_bulk_terminating-terminating-several-skips-the-missing-one"></a>

#### [terminating-several-skips-the-missing-one](/tests/scenario/bai_scenario/manager/session/test_partial_bulk_terminating.py): pass

when the superadmin terminates a pending session and a missing id in one call, the pending session comes back as cancelled and the missing id as skipped in the processed list

Given

- one pending session and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled

When

- SessionAdapter.partial_bulk_terminate: user-2 terminates a pending session and a missing id in one call

Then

- the pending session comes back as cancelled and the missing id as skipped in the processed list, and nothing failed
  - successes count = 2
  - failed = []
  - successes[0].id: same as the id of the pending session
  - successes[0].status = <SessionTerminationStatusEnum.CANCELLED: 'cancelled'>
  - successes[1].id: same as the missing id given in the request
  - successes[1].status = <SessionTerminationStatusEnum.SKIPPED: 'skipped'>

### shutdown_service

<a id="logs_and_services-shutting-down-a-service-granted"></a>

#### [shutting-down-a-service-granted](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

when a user granted session soft delete in the project shuts a service of a session down, the call answers nothing

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted a session permission in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-updater-1: applies only within the scope it is granted in
    - Role session-updater-1: SOFT_DELETE allowed on every session
    - regular user user-2: holds Role session-updater-1

When

- SessionAdapter.shutdown_service: user-2 shuts a service of session-1 down

Then

- the call answers nothing and raises nothing
  - answered = None

<a id="logs_and_services-shutting-down-a-service-granted-nothing"></a>

#### [shutting-down-a-service-granted-nothing](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

when a user granted nothing shuts a service of a session down, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.shutdown_service: user-2 shuts a service of session-1 down

Then

- the call is rejected
  - rejected: NotEnoughPermission

### start_service

<a id="logs_and_services-starting-a-service-granted"></a>

#### [starting-a-service-granted](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

when a user granted session create in the project starts a service of a session whose resource group has no proxy address, the call is rejected as unavailable

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted a session permission in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-updater-1: applies only within the scope it is granted in
    - Role session-updater-1: CREATE allowed on every session
    - regular user user-2: holds Role session-updater-1

When

- SessionAdapter.start_service: user-2 starts a service of session-1

Then

- the call is rejected
  - rejected: ServiceUnavailable

<a id="logs_and_services-starting-a-service-granted-nothing"></a>

#### [starting-a-service-granted-nothing](/tests/scenario/bai_scenario/manager/session/test_logs_and_services.py): pass

when a user granted nothing starts a service of a session, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.start_service: user-2 starts a service of session-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### terminate

<a id="terminating-a-superadmin-terminates-a-pending-session"></a>

#### [a-superadmin-terminates-a-pending-session](/tests/scenario/bai_scenario/manager/session/test_terminating.py): pass

when the superadmin terminates a pending session, it comes back in the cancelled list

Given

- one pending session and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled

When

- SessionAdapter.terminate: user-2 terminates a pending session

Then

- the pending session comes back in the cancelled list and the other lists are empty
  - cancelled count = 1
  - terminating = []
  - force_terminated = []
  - skipped = []
  - cancelled[0]: same as the id of the pending session

<a id="terminating-a-user-granted-nothing-may-not-terminate"></a>

#### [a-user-granted-nothing-may-not-terminate](/tests/scenario/bai_scenario/manager/session/test_terminating.py): pass

when a user granted nothing tries to terminate a pending session, the whole call is rejected

Given

- one pending session and one regular user holding no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled

When

- SessionAdapter.terminate: user-2 terminates a pending session

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="updating-a-session-update-with-no-field-project"></a>

#### [a-session-update-with-no-field-project](/tests/scenario/bai_scenario/manager/session/test_updating.py): pass

when a user granted session read in the project updates a session with no value to change, the current session comes back

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- SessionAdapter.update: user-2 updates the session with no value to change

Then

- the current session comes back exactly as it was stored
  - session: same as the whole information of the stored session

<a id="updating-a-session-update-with-no-field-nothing"></a>

#### [a-session-update-with-no-field-nothing](/tests/scenario/bai_scenario/manager/session/test_updating.py): pass

when a user granted nothing updates a session with no value to change, the call is rejected for lack of permission

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1

When

- SessionAdapter.update: user-2 updates the session with no value to change

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="updating-renaming-a-session-that-is-not-running-is-refused"></a>

#### [renaming-a-session-that-is-not-running-is-refused](/tests/scenario/bai_scenario/manager/session/test_updating.py): pass

when a user granted session update in the project renames a session that is not running, the call is rejected because of its state

Given

- one pending session with a kernel and its kernel group, and one user who reads it
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1(has one main kernel group): has one environment variable
  - Session session-1(has one main kernel group): asks for 1 in the slot-1 slot
  - Session session-1: has one kernel asking for slot-1 1
  - Prepare a user granted a session permission in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-updater-1: applies only within the scope it is granted in
    - Role session-updater-1: UPDATE allowed on every session
    - regular user user-2: holds Role session-updater-1

When

- SessionAdapter.update: user-2 renames the session session-1

Then

- the call is rejected
  - rejected: InvalidAPIParameters

