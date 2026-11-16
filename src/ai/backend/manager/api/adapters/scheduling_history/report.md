## scheduling_history

[adapter](/src/ai/backend/manager/api/adapters/scheduling_history/adapter.py)

Scenario: complete

- built from ops (10)
  - admin_search_deployment_history: representative success ✓ · representative rejection ✓
  - admin_search_kernel_history: representative success ✓ · representative rejection ✓
  - admin_search_replica_group_history: representative success ✓ · representative rejection ✓
  - admin_search_route_history: representative success ✓ · representative rejection ✓
  - admin_search_session_history: representative success ✓ · representative rejection ✓
  - batch_load_deployment_histories_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_kernel_histories_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_replica_group_histories_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_route_histories_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_session_histories_by_ids: representative success ✓ · representative rejection ✓
- direct implementation (5)
  - deployment_scoped_search: success present 1 · rejection present 1 (scope)
  - route_scoped_search: success present 1 · rejection present 1 (scope)
  - scoped_search_kernel_history: success present 1 · rejection present 2 (scope)
  - scoped_search_replica_group_history: success present 1 · rejection present 2 (scope)
  - session_scoped_search: success present 1 · rejection present 1 (scope)

**admin_search_deployment_history**

| scenario | verdict |
|---|---|
| [when the superadmin pages through deployment histories with a condition that keeps one history laid in advance, only that history comes back as one page](#searching-the-superadmin-pages-through-deployment-histories) | answered |
| [when a user other than the superadmin pages through deployment histories, the call is rejected for lack of privilege](#searching-a-user-granted-nothing-may-not-page-through-deployment-histories) | rejected |

**admin_search_kernel_history**

| scenario | verdict |
|---|---|
| [when the superadmin pages through kernel histories with a condition that keeps one history laid in advance, only that history comes back as one page](#searching-the-superadmin-pages-through-kernel-histories) | answered |
| [when a user other than the superadmin pages through kernel histories, the call is rejected for lack of privilege](#searching-a-user-granted-nothing-may-not-page-through-kernel-histories) | rejected |

**admin_search_replica_group_history**

| scenario | verdict |
|---|---|
| [when the superadmin pages through replica group histories with a condition that keeps one history laid in advance, only that history comes back as one page](#searching-the-superadmin-pages-through-replica-group-histories) | answered |
| [when a user other than the superadmin pages through replica group histories, the call is rejected for lack of privilege](#searching-a-user-granted-nothing-may-not-page-through-replica-group-histories) | rejected |

**admin_search_route_history**

| scenario | verdict |
|---|---|
| [when the superadmin pages through route histories with a condition that keeps one history laid in advance, only that history comes back as one page](#searching-the-superadmin-pages-through-route-histories) | answered |
| [when a user other than the superadmin pages through route histories, the call is rejected for lack of privilege](#searching-a-user-granted-nothing-may-not-page-through-route-histories) | rejected |

**admin_search_session_history**

| scenario | verdict |
|---|---|
| [when the superadmin pages through session histories with a condition that keeps one history laid in advance, only that history comes back as one page](#searching-the-superadmin-pages-through-session-histories) | answered |
| [when a user other than the superadmin pages through session histories, the call is rejected for lack of privilege](#searching-a-user-granted-nothing-may-not-page-through-session-histories) | rejected |

**batch_load_deployment_histories_by_ids**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments reads a deployment history by its id, the history comes back whole as a node](#batch_loading-a-reader-loads-the-deployment-history) | answered |
| [when a regular user granted permission to read sessions and deployments reads deployment histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value](#batch_loading-a-reader-loads-the-deployment-history-with-an-unknown-id) | answered |
| [when a user granted nothing reads another's deployment history by id, that entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-may-not-load-the-deployment-history) | rejected |

**batch_load_kernel_histories_by_ids**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments reads a kernel history by its id, the history comes back whole as a node](#batch_loading-a-reader-loads-the-kernel-history) | answered |
| [when a regular user granted permission to read sessions and deployments reads kernel histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value](#batch_loading-a-reader-loads-the-kernel-history-with-an-unknown-id) | answered |
| [when a user granted nothing reads another's kernel history by id, that entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-may-not-load-the-kernel-history) | rejected |

**batch_load_replica_group_histories_by_ids**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments reads a replica group history by its id, the history comes back whole as a node](#batch_loading-a-reader-loads-the-replica-group-history) | answered |
| [when a regular user granted permission to read sessions and deployments reads replica group histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value](#batch_loading-a-reader-loads-the-replica-group-history-with-an-unknown-id) | answered |
| [when a user granted nothing reads another's replica group history by id, that entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-may-not-load-the-replica-group-history) | rejected |

**batch_load_route_histories_by_ids**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments reads a route history by its id, the history comes back whole as a node](#batch_loading-a-reader-loads-the-route-history) | answered |
| [when a regular user granted permission to read sessions and deployments reads route histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value](#batch_loading-a-reader-loads-the-route-history-with-an-unknown-id) | answered |
| [when a user granted nothing reads another's route history by id, that entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-may-not-load-the-route-history) | rejected |

**batch_load_session_histories_by_ids**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments reads a session history by its id, the history comes back whole as a node](#batch_loading-a-reader-loads-the-session-history) | answered |
| [when a regular user granted permission to read sessions and deployments reads session histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value](#batch_loading-a-reader-loads-the-session-history-with-an-unknown-id) | answered |
| [when a user granted nothing reads another's session history by id, that entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-may-not-load-the-session-history) | rejected |

**deployment_scoped_search**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments pages through deployment histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page](#scoped_searching-a-reader-pages-through-the-scoped-deployment-histories) | answered |
| [when a user granted nothing pages through deployment histories of a scope, the call is rejected for lack of permission](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-deployment-histories) | rejected |

**route_scoped_search**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments pages through route histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page](#scoped_searching-a-reader-pages-through-the-scoped-route-histories) | answered |
| [when a user granted nothing pages through the route histories of a scope, the request is rejected](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-route-histories) | rejected |

**scoped_search_kernel_history**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments pages through kernel histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page](#scoped_searching-a-reader-pages-through-the-scoped-kernel-histories) | answered |
| [when a user granted nothing pages through kernel histories of a scope, the call is rejected for lack of permission](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-kernel-histories) | rejected |
| [when the superadmin pages through kernel histories naming two scope items, the request is rejected](#scoped_searching-kernel-history-scope-naming-two-items-is-refused) | rejected |

**scoped_search_replica_group_history**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments pages through replica group histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page](#scoped_searching-a-reader-pages-through-the-scoped-replica-group-histories) | answered |
| [when a user granted nothing pages through replica group histories of a scope, the call is rejected for lack of permission](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-replica-group-histories) | rejected |
| [when the superadmin pages through replica group histories naming two scope items, the request is rejected](#scoped_searching-replica-group-history-scope-naming-two-items-is-refused) | rejected |

**session_scoped_search**

| scenario | verdict |
|---|---|
| [when a regular user granted permission to read sessions and deployments pages through session histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page](#scoped_searching-a-reader-pages-through-the-scoped-session-histories) | answered |
| [when a user granted nothing pages through session histories of a scope, the call is rejected for lack of permission](#scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-session-histories) | rejected |

### admin_search_deployment_history

<a id="searching-the-superadmin-pages-through-deployment-histories"></a>

#### [the-superadmin-pages-through-deployment-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when the superadmin pages through deployment histories with a condition that keeps one history laid in advance, only that history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying a scheduling history row, one more set of each outside the scope, and one superadmin
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded

When

- SchedulingHistoryAdapter.admin_search_deployment_history: user-2 pages through deployment histories with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].deployment_id: same as the id of the deployment laid in advance
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = None
  - items[0].to_status = None
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="searching-a-user-granted-nothing-may-not-page-through-deployment-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-deployment-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when a user other than the superadmin pages through deployment histories, the call is rejected for lack of privilege

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.admin_search_deployment_history: user-2 pages through every deployment history without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_kernel_history

<a id="searching-the-superadmin-pages-through-kernel-histories"></a>

#### [the-superadmin-pages-through-kernel-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when the superadmin pages through kernel histories with a condition that keeps one history laid in advance, only that history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying a scheduling history row, one more set of each outside the scope, and one superadmin
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded

When

- SchedulingHistoryAdapter.admin_search_kernel_history: user-2 pages through kernel histories with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].kernel_id: same as the id of the kernel laid in advance
  - items[0].session_id: same as the id of the session laid in advance
  - items[0].phase = 'scheduling'
  - items[0].from_status = 'PREPARING'
  - items[0].to_status = 'PULLING'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="searching-a-user-granted-nothing-may-not-page-through-kernel-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-kernel-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when a user other than the superadmin pages through kernel histories, the call is rejected for lack of privilege

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.admin_search_kernel_history: user-2 pages through every kernel history without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_replica_group_history

<a id="searching-the-superadmin-pages-through-replica-group-histories"></a>

#### [the-superadmin-pages-through-replica-group-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when the superadmin pages through replica group histories with a condition that keeps one history laid in advance, only that history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying a scheduling history row, one more set of each outside the scope, and one superadmin
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded

When

- SchedulingHistoryAdapter.admin_search_replica_group_history: user-2 pages through replica group histories with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].deployment_id: same as the id of the deployment laid in advance
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = None
  - items[0].to_status = None
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="searching-a-user-granted-nothing-may-not-page-through-replica-group-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-replica-group-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when a user other than the superadmin pages through replica group histories, the call is rejected for lack of privilege

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.admin_search_replica_group_history: user-2 pages through every replica group history without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_route_history

<a id="searching-the-superadmin-pages-through-route-histories"></a>

#### [the-superadmin-pages-through-route-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when the superadmin pages through route histories with a condition that keeps one history laid in advance, only that history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying a scheduling history row, one more set of each outside the scope, and one superadmin
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded

When

- SchedulingHistoryAdapter.admin_search_route_history: user-2 pages through route histories with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].route_id: same as the id of the replica laid in advance
  - items[0].deployment_id: same as the id of the deployment laid in advance
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = 'provisioning'
  - items[0].to_status = 'running'
  - items[0].from_sub_status = 'pending'
  - items[0].to_sub_status = 'warming_up'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="searching-a-user-granted-nothing-may-not-page-through-route-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-route-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when a user other than the superadmin pages through route histories, the call is rejected for lack of privilege

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.admin_search_route_history: user-2 pages through every route history without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_search_session_history

<a id="searching-the-superadmin-pages-through-session-histories"></a>

#### [the-superadmin-pages-through-session-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when the superadmin pages through session histories with a condition that keeps one history laid in advance, only that history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying a scheduling history row, one more set of each outside the scope, and one superadmin
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded

When

- SchedulingHistoryAdapter.admin_search_session_history: user-2 pages through session histories with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].session_id: same as the id of the session laid in advance
  - items[0].phase = 'scheduling'
  - items[0].from_status = 'PENDING'
  - items[0].to_status = 'SCHEDULED'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="searching-a-user-granted-nothing-may-not-page-through-session-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-session-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_searching.py): pass

when a user other than the superadmin pages through session histories, the call is rejected for lack of privilege

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.admin_search_session_history: user-2 pages through every session history without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_deployment_histories_by_ids

<a id="batch_loading-a-reader-loads-the-deployment-history"></a>

#### [a-reader-loads-the-deployment-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads a deployment history by its id, the history comes back whole as a node

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_deployment_histories_by_ids: user-2 reads the deployment histories by the id laid in advance

Then

- the history laid in advance comes back as a node
  - length = 1
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].deployment_id: same as the id of the deployment laid in advance
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = None
  - [0].to_status = None
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote

<a id="batch_loading-a-reader-loads-the-deployment-history-with-an-unknown-id"></a>

#### [a-reader-loads-the-deployment-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads deployment histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_deployment_histories_by_ids: user-2 reads the deployment histories by the id laid in advance and an unknown id

Then

- the history laid in advance comes back as a node and the unknown id entry as an empty value
  - length = 2
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].deployment_id: same as the id of the deployment laid in advance
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = None
  - [0].to_status = None
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-deployment-history"></a>

#### [a-user-granted-nothing-may-not-load-the-deployment-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a user granted nothing reads another's deployment history by id, that entry is rejected for lack of permission

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.batch_load_deployment_histories_by_ids: user-2 reads the deployment histories by the id laid in advance

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### batch_load_kernel_histories_by_ids

<a id="batch_loading-a-reader-loads-the-kernel-history"></a>

#### [a-reader-loads-the-kernel-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads a kernel history by its id, the history comes back whole as a node

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_kernel_histories_by_ids: user-2 reads the kernel histories by the id laid in advance

Then

- the history laid in advance comes back as a node
  - length = 1
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].kernel_id: same as the id of the kernel laid in advance
  - [0].session_id: same as the id of the session laid in advance
  - [0].phase = 'scheduling'
  - [0].from_status = 'PREPARING'
  - [0].to_status = 'PULLING'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote

<a id="batch_loading-a-reader-loads-the-kernel-history-with-an-unknown-id"></a>

#### [a-reader-loads-the-kernel-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads kernel histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_kernel_histories_by_ids: user-2 reads the kernel histories by the id laid in advance and an unknown id

Then

- the history laid in advance comes back as a node and the unknown id entry as an empty value
  - length = 2
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].kernel_id: same as the id of the kernel laid in advance
  - [0].session_id: same as the id of the session laid in advance
  - [0].phase = 'scheduling'
  - [0].from_status = 'PREPARING'
  - [0].to_status = 'PULLING'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-kernel-history"></a>

#### [a-user-granted-nothing-may-not-load-the-kernel-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a user granted nothing reads another's kernel history by id, that entry is rejected for lack of permission

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.batch_load_kernel_histories_by_ids: user-2 reads the kernel histories by the id laid in advance

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### batch_load_replica_group_histories_by_ids

<a id="batch_loading-a-reader-loads-the-replica-group-history"></a>

#### [a-reader-loads-the-replica-group-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads a replica group history by its id, the history comes back whole as a node

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_replica_group_histories_by_ids: user-2 reads the replica group histories by the id laid in advance

Then

- the history laid in advance comes back as a node
  - length = 1
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].deployment_id: same as the id of the deployment laid in advance
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = None
  - [0].to_status = None
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote

<a id="batch_loading-a-reader-loads-the-replica-group-history-with-an-unknown-id"></a>

#### [a-reader-loads-the-replica-group-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads replica group histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_replica_group_histories_by_ids: user-2 reads the replica group histories by the id laid in advance and an unknown id

Then

- the history laid in advance comes back as a node and the unknown id entry as an empty value
  - length = 2
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].deployment_id: same as the id of the deployment laid in advance
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = None
  - [0].to_status = None
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-replica-group-history"></a>

#### [a-user-granted-nothing-may-not-load-the-replica-group-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a user granted nothing reads another's replica group history by id, that entry is rejected for lack of permission

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.batch_load_replica_group_histories_by_ids: user-2 reads the replica group histories by the id laid in advance

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### batch_load_route_histories_by_ids

<a id="batch_loading-a-reader-loads-the-route-history"></a>

#### [a-reader-loads-the-route-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads a route history by its id, the history comes back whole as a node

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_route_histories_by_ids: user-2 reads the route histories by the id laid in advance

Then

- the history laid in advance comes back as a node
  - length = 1
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].route_id: same as the id of the replica laid in advance
  - [0].deployment_id: same as the id of the deployment laid in advance
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = 'provisioning'
  - [0].to_status = 'running'
  - [0].from_sub_status = 'pending'
  - [0].to_sub_status = 'warming_up'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote

<a id="batch_loading-a-reader-loads-the-route-history-with-an-unknown-id"></a>

#### [a-reader-loads-the-route-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads route histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_route_histories_by_ids: user-2 reads the route histories by the id laid in advance and an unknown id

Then

- the history laid in advance comes back as a node and the unknown id entry as an empty value
  - length = 2
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].route_id: same as the id of the replica laid in advance
  - [0].deployment_id: same as the id of the deployment laid in advance
  - [0].category = 'lifecycle'
  - [0].phase = 'lifecycle'
  - [0].from_status = 'provisioning'
  - [0].to_status = 'running'
  - [0].from_sub_status = 'pending'
  - [0].to_sub_status = 'warming_up'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-route-history"></a>

#### [a-user-granted-nothing-may-not-load-the-route-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a user granted nothing reads another's route history by id, that entry is rejected for lack of permission

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.batch_load_route_histories_by_ids: user-2 reads the route histories by the id laid in advance

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### batch_load_session_histories_by_ids

<a id="batch_loading-a-reader-loads-the-session-history"></a>

#### [a-reader-loads-the-session-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads a session history by its id, the history comes back whole as a node

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_session_histories_by_ids: user-2 reads the session histories by the id laid in advance

Then

- the history laid in advance comes back as a node
  - length = 1
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].session_id: same as the id of the session laid in advance
  - [0].phase = 'scheduling'
  - [0].from_status = 'PENDING'
  - [0].to_status = 'SCHEDULED'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote

<a id="batch_loading-a-reader-loads-the-session-history-with-an-unknown-id"></a>

#### [a-reader-loads-the-session-history-with-an-unknown-id](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a regular user granted permission to read sessions and deployments reads session histories by a known and an unknown id, the known one comes back as a node and the unknown entry as an empty value

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.batch_load_session_histories_by_ids: user-2 reads the session histories by the id laid in advance and an unknown id

Then

- the history laid in advance comes back as a node and the unknown id entry as an empty value
  - length = 2
  - [0].id: same as the id of the history laid in advance
  - [0].field_id: same as the id of the history laid in advance
  - [0].session_id: same as the id of the session laid in advance
  - [0].phase = 'scheduling'
  - [0].from_status = 'PENDING'
  - [0].to_status = 'SCHEDULED'
  - [0].result = 'SUCCESS'
  - [0].error_code = None
  - [0].message = 'the transition finished'
  - [0].sub_steps = []
  - [0].attempts = 1
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [1] = None

<a id="batch_loading-a-user-granted-nothing-may-not-load-the-session-history"></a>

#### [a-user-granted-nothing-may-not-load-the-session-history](/tests/scenario/bai_scenario/manager/scheduling_history/test_batch_loading.py): pass

when a user granted nothing reads another's session history by id, that entry is rejected for lack of permission

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.batch_load_session_histories_by_ids: user-2 reads the session histories by the id laid in advance

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### deployment_scoped_search

<a id="scoped_searching-a-reader-pages-through-the-scoped-deployment-histories"></a>

#### [a-reader-pages-through-the-scoped-deployment-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a regular user granted permission to read sessions and deployments pages through deployment histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying two scheduling history rows each, one more set of each outside the scope carrying a history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.deployment_scoped_search: user-2 pages through deployment histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].deployment_id: same as the id of the deployment laid in advance
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = None
  - items[0].to_status = None
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-deployment-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-deployment-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a user granted nothing pages through deployment histories of a scope, the call is rejected for lack of permission

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.deployment_scoped_search: user-2 pages through deployment histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the call is rejected
  - rejected: NotEnoughPermission

### route_scoped_search

<a id="scoped_searching-a-reader-pages-through-the-scoped-route-histories"></a>

#### [a-reader-pages-through-the-scoped-route-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a regular user granted permission to read sessions and deployments pages through route histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying two scheduling history rows each, one more set of each outside the scope carrying a history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.route_scoped_search: user-2 pages through route histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].route_id: same as the id of the replica laid in advance
  - items[0].deployment_id: same as the id of the deployment laid in advance
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = 'provisioning'
  - items[0].to_status = 'running'
  - items[0].from_sub_status = 'pending'
  - items[0].to_sub_status = 'warming_up'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-route-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-route-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a user granted nothing pages through the route histories of a scope, the request is rejected

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.route_scoped_search: user-2 pages through route histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the call is rejected
  - rejected: GenericBadRequest

### scoped_search_kernel_history

<a id="scoped_searching-a-reader-pages-through-the-scoped-kernel-histories"></a>

#### [a-reader-pages-through-the-scoped-kernel-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a regular user granted permission to read sessions and deployments pages through kernel histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying two scheduling history rows each, one more set of each outside the scope carrying a history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.scoped_search_kernel_history: user-2 pages through kernel histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].kernel_id: same as the id of the kernel laid in advance
  - items[0].session_id: same as the id of the session laid in advance
  - items[0].phase = 'scheduling'
  - items[0].from_status = 'PREPARING'
  - items[0].to_status = 'PULLING'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-kernel-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-kernel-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a user granted nothing pages through kernel histories of a scope, the call is rejected for lack of permission

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.scoped_search_kernel_history: user-2 pages through kernel histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-kernel-history-scope-naming-two-items-is-refused"></a>

#### [kernel-history-scope-naming-two-items-is-refused](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when the superadmin pages through kernel histories naming two scope items, the request is rejected

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one superadmin
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.scoped_search_kernel_history: user-2 pages through kernel histories naming two scope items

Then

- the call is rejected
  - rejected: InvalidAPIParameters

### scoped_search_replica_group_history

<a id="scoped_searching-a-reader-pages-through-the-scoped-replica-group-histories"></a>

#### [a-reader-pages-through-the-scoped-replica-group-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a regular user granted permission to read sessions and deployments pages through replica group histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying two scheduling history rows each, one more set of each outside the scope carrying a history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.scoped_search_replica_group_history: user-2 pages through replica group histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].deployment_id: same as the id of the deployment laid in advance
  - items[0].category = 'lifecycle'
  - items[0].phase = 'lifecycle'
  - items[0].from_status = None
  - items[0].to_status = None
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-replica-group-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-replica-group-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a user granted nothing pages through replica group histories of a scope, the call is rejected for lack of permission

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.scoped_search_replica_group_history: user-2 pages through replica group histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-replica-group-history-scope-naming-two-items-is-refused"></a>

#### [replica-group-history-scope-naming-two-items-is-refused](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when the superadmin pages through replica group histories naming two scope items, the request is rejected

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one superadmin
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.scoped_search_replica_group_history: user-2 pages through replica group histories naming two scope items

Then

- the call is rejected
  - rejected: InvalidAPIParameters

### session_scoped_search

<a id="scoped_searching-a-reader-pages-through-the-scoped-session-histories"></a>

#### [a-reader-pages-through-the-scoped-session-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a regular user granted permission to read sessions and deployments pages through session histories of the target laid in advance with a condition, the history outside the scope and the one the condition drops are left out and only that one history comes back as one page

Given

- one set of a session, kernel, deployment, route and replica group carrying two scheduling history rows each, one more set of each outside the scope carrying a history row, and one regular user granted permission to read sessions and deployments
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded
  - Session other-session-1: waiting to be scheduled
  - Session other-session-1: has one main kernel group
  - Session other-session-1: has one kernel asking for 
  - Session other-session-1: has one scheduling attempt recorded
  - Session other-session-1: has one scheduling attempt of a kernel recorded
  - Deployment other-deployment-1: replica count 1, has no revision yet
  - Deployment other-deployment-1: has one scheduling attempt of the deployment recorded
  - Session group of a deployment deployment-session-group-2: the session group a deployment creates with its replica group
  - Deployment other-deployment-1: has one replica group holding the session group
  - Deployment other-deployment-1: has one scheduling attempt of the replica group recorded
  - Deployment other-deployment-1: has one replica
  - Deployment other-deployment-1: has one scheduling attempt of a route recorded
  - Prepare a user granted permission to read sessions and deployments
    - Role history-reader-1: applies only within the scope it is granted in
    - Role history-reader-1: READ allowed on every session
    - Role history-reader-1: READ allowed on every deployment
    - regular user user-2: holds Role history-reader-1

When

- SchedulingHistoryAdapter.session_scoped_search: user-2 pages through session histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the one history laid in advance comes back as one page
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the id of the history laid in advance
  - items[0].field_id: same as the id of the history laid in advance
  - items[0].session_id: same as the id of the session laid in advance
  - items[0].phase = 'scheduling'
  - items[0].from_status = 'PENDING'
  - items[0].to_status = 'SCHEDULED'
  - items[0].result = 'SUCCESS'
  - items[0].error_code = None
  - items[0].message = 'the transition finished'
  - items[0].sub_steps = []
  - items[0].attempts = 1
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="scoped_searching-a-user-granted-nothing-may-not-page-through-the-scoped-session-histories"></a>

#### [a-user-granted-nothing-may-not-page-through-the-scoped-session-histories](/tests/scenario/bai_scenario/manager/scheduling_history/test_scoped_searching.py): pass

when a user granted nothing pages through session histories of a scope, the call is rejected for lack of permission

Given

- one session, kernel, deployment, route and replica group each carrying one scheduling history row, and one regular user holding no permission
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
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for 
  - Deployment deployment-1: replica count 1, has no revision yet
  - Session group of a deployment deployment-session-group-1: the session group a deployment creates with its replica group
  - Deployment deployment-1: has one replica group holding the session group
  - Deployment deployment-1: has one replica
  - Session session-1: has one scheduling attempt recorded
  - Session session-1: has one scheduling attempt of a kernel recorded
  - Deployment deployment-1: has one scheduling attempt of the deployment recorded
  - Deployment deployment-1: has one scheduling attempt of a route recorded
  - Deployment deployment-1: has one scheduling attempt of the replica group recorded

When

- SchedulingHistoryAdapter.session_scoped_search: user-2 pages through session histories naming the target laid in advance as the scope, with a condition that keeps one history laid in advance and an order over one item per page

Then

- the call is rejected
  - rejected: NotEnoughPermission

