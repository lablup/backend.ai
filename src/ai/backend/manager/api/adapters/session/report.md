## session

[background](/src/ai/backend/manager/api/adapters/session/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/session/adapter.py)

Scenario: incomplete 28 / 30

- built from ops (7)
  - batch_load_kernel_group_environs_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_kernel_group_resource_slots_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_kernel_groups_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_main_kernel_groups: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - scoped_search_kernel_group_environs: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - scoped_search_kernel_group_resource_slots: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - scoped_search_kernel_groups: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- ops + direct implementation (10)
  - admin_search: success present 3 · rejection present 1 (global_searcher_ops, partial_bulk)
  - admin_search_kernels: success absent · rejection absent (atomic_bulk_field, global_searcher_ops): SCENARIO-GAP
  - batch_load_by_ids: success absent · rejection absent (partial_bulk, partial_bulk_get_ops): SCENARIO-GAP
  - batch_load_kernels_by_ids: success absent · rejection absent (atomic_bulk_field, partial_bulk_get_ops): SCENARIO-GAP
  - gql_search_by_project: success absent · rejection absent (partial_bulk, scoped_search_ops): SCENARIO-GAP
  - project_search: success absent · rejection absent (partial_bulk, scoped_search_ops): SCENARIO-GAP
  - scoped_search: success absent · rejection absent (partial_bulk, scoped_search_ops): SCENARIO-GAP
  - search_kernels_by_agent: success absent · rejection absent (atomic_bulk_field, global_searcher_ops): SCENARIO-GAP
  - search_kernels_by_session: success absent · rejection absent (atomic_bulk_field, atomic_bulk_scoped_search_ops): SCENARIO-GAP
  - search_sessions_by_agent: success absent · rejection absent (global_searcher_ops, partial_bulk): SCENARIO-GAP
- direct implementation (13)
  - batch_resource_allocation_by_kernel: success absent · rejection absent (atomic_bulk_field): SCENARIO-GAP
  - batch_resource_allocation_by_session: success absent · rejection absent (partial_bulk): SCENARIO-GAP
  - compute_schedule: success absent · rejection absent (single_entity): SCENARIO-GAP
  - enqueue: success absent · rejection absent (partial_bulk, scope): SCENARIO-GAP
  - exclude_idle_checks: success absent · rejection absent (legacy_partial_bulk): SCENARIO-GAP
  - get: success absent · rejection absent (partial_bulk, single_entity): SCENARIO-GAP
  - get_logs: success absent · rejection absent (single_entity): SCENARIO-GAP
  - include_idle_checks: success absent · rejection absent (legacy_partial_bulk): SCENARIO-GAP
  - partial_bulk_terminate: success present 3 · rejection absent (partial_bulk): SCENARIO-GAP
  - shutdown_service: success absent · rejection absent (single_entity): SCENARIO-GAP
  - start_service: success absent · rejection absent (single_entity): SCENARIO-GAP
  - terminate: success present 1 · rejection present 1 (partial_bulk)
  - update: success absent · rejection absent (partial_bulk, single_entity): SCENARIO-GAP

**admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches with no session seeded, the answer is empty](#session-a-scenario-that-laid-no-session-finds-none) | answered |
| [when the superadmin reads the set session scheduling conditions, they are kept with the existing session information](#searching_details-session-scheduling-conditions-are-preserved-when-configured) | answered |
| [when the superadmin reads the unset session scheduling conditions, they are kept with the existing session information](#searching_details-session-scheduling-conditions-are-preserved-when-unset) | answered |
| [an unfiltered search is open only to the superadmin role, so a user granted nothing is rejected for lacking the role](#session-a-user-granted-nothing-may-not-search-sessions) | rejected |

**partial_bulk_terminate**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to terminate a pending session, none is terminated and it comes back in the failed list for lack of permission](#partial_bulk_terminating-a-user-granted-nothing-terminates-none) | answered |
| [when a user granted session soft delete in the project scope terminates the pending session of that project, it comes back as cancelled in the processed list](#partial_bulk_terminating-a-user-granted-session-soft-delete-in-the-project-terminates-its-session) | answered |
| [when the superadmin terminates a pending session and a missing id in one call, the pending session comes back as cancelled and the missing id as skipped in the processed list](#partial_bulk_terminating-terminating-several-skips-the-missing-one) | answered |

**terminate**

| scenario | verdict |
|---|---|
| [when the superadmin terminates a pending session, it comes back in the cancelled list](#terminating-a-superadmin-terminates-a-pending-session) | answered |
| [when a user granted nothing tries to terminate a pending session, the whole call is rejected](#terminating-a-user-granted-nothing-may-not-terminate) | rejected |

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

