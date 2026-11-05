## agent

[adapter](/src/ai/backend/manager/api/adapters/agent/adapter.py)

Scenario: complete

- ops + direct implementation (4)
  - admin_search: success present 4 · rejection present 1 (atomic_bulk_scoped_search_ops, global_searcher_ops, partial_bulk)
  - batch_load_by_ids: success present 2 · rejection present 1 (atomic_bulk_scoped_search_ops, partial_bulk, partial_bulk_get_ops)
  - batch_load_by_uuids: success present 1 · rejection present 2 (atomic_bulk_scoped_search_ops, partial_bulk, partial_bulk_get_ops)
  - batch_load_container_counts: success present 2 · rejection present 1 (partial_bulk, partial_bulk_get_ops)
- direct implementation (3)
  - get_total_resources: success present 1 · rejection present 1 (global_scope)
  - update_resource_group: success present 2 · rejection present 3 (global_scope)
  - update_resource_group_from_body: success present 1 · rejection present 1 (global_scope)

**admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches ordered by id ascending, every agent registered in advance comes back whole](#searching-the-superadmin-orders-the-agents-by-name) | answered |
| [when the superadmin searches every agent, every agent registered in advance comes back whole](#searching-the-superadmin-pages-through-every-agent) | answered |
| [when the superadmin searches by an agent name, only that agent comes back](#searching-the-superadmin-picks-an-agent-by-its-name) | answered |
| [when the superadmin searches by a resource group name, only the agents of that group come back](#searching-the-superadmin-picks-the-agents-of-a-resource-group) | answered |
| [the search is open to the superadmin alone, so a regular user holding no permission is rejected for lack of privilege](#searching-a-user-granted-nothing-may-not-search-the-agents) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user who can read the agents of the resource group loads one by name, the whole agent comes back](#batch_loading-a-user-reading-the-group-loads-an-agent-by-name) | answered |
| [a name nothing answers to comes back as an empty value](#batch_loading-an-unknown-agent-name-answers-an-empty-value) | answered |
| [when a user who can read one group loads an agent of another group beside it, that entry is rejected for lack of permission](#batch_loading-a-user-reading-one-group-gets-a-denial-for-the-agent-of-another) | rejected |

**batch_load_by_uuids**

| scenario | verdict |
|---|---|
| [when a user who can read the agents of the resource group loads one by its entity id, the whole agent comes back](#batch_loading-a-user-reading-the-group-loads-an-agent-by-entity-id) | answered |
| [when a user granted nothing loads an agent by its entity id, that entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-gets-a-denial-for-the-agent-entity-id) | rejected |
| [a read by entity id is checked per id, so an id nothing answers to comes back as a denial rather than an empty value](#batch_loading-an-unknown-agent-entity-id-answers-a-denial) | rejected |

**batch_load_container_counts**

| scenario | verdict |
|---|---|
| [when a user who can read the agents of the resource group counts containers, zero comes back because nothing runs on the agent](#batch_loading-a-user-reading-the-group-counts-no-container-on-the-agent) | answered |
| [the container count of a name nothing answers to comes back as zero](#batch_loading-an-unknown-agent-name-counts-no-container) | answered |
| [when a user granted nothing counts containers, the entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-gets-a-denial-for-the-container-count) | rejected |

**get_total_resources**

| scenario | verdict |
|---|---|
| [when the superadmin reads the total, the sum of the capacity and usage the live agents report comes back](#total_resources-the-superadmin-reads-the-total-of-the-slots-the-agents-report) | answered |
| [the read is open to the superadmin alone, so a regular user holding no permission is rejected for lack of privilege](#total_resources-a-user-granted-nothing-may-not-read-the-total) | rejected |

**update_resource_group**

| scenario | verdict |
|---|---|
| [when an agent designated by a session of another group is moved with force, the designation is dropped and the answer carrying the new group comes back](#changing_resource_group-force-moves-an-agent-designated-by-another-groups-session) | answered |
| [when the superadmin moves an agent to another resource group, the answer carrying the new group comes back](#changing_resource_group-the-superadmin-moves-an-agent-to-another-resource-group) | answered |
| [the move is open to the superadmin alone, so a regular user holding no permission is rejected for lack of privilege](#changing_resource_group-a-user-granted-nothing-may-not-move-an-agent) | rejected |
| [when an agent designated by a session of another group is moved without force, the call is rejected as conflicting](#changing_resource_group-an-agent-designated-by-another-groups-session-needs-force) | rejected |
| [when the superadmin moves an agent under the reschedule policy, the call is rejected as not supported yet](#changing_resource_group-asking-to-reschedule-the-conflicting-sessions-is-not-supported) | rejected |

**update_resource_group_from_body**

| scenario | verdict |
|---|---|
| [when the superadmin moves an agent through the REST body, the answer carrying the new group comes back](#changing_resource_group-the-superadmin-moves-an-agent-through-the-rest-body) | answered |
| [the move is open to the superadmin alone, so a regular user holding no permission is rejected for lack of privilege even through the REST body](#changing_resource_group-a-user-granted-nothing-may-not-move-an-agent-through-the-rest-body) | rejected |

### admin_search

<a id="searching-the-superadmin-orders-the-agents-by-name"></a>

#### [the-superadmin-orders-the-agents-by-name](/tests/scenario/bai_scenario/manager/agent/test_searching.py): pass

when the superadmin searches ordered by id ascending, every agent registered in advance comes back whole

Given

- 2 agents and one superadmin
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-2: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AgentAdapter.admin_search: user-1 searches the agents ordered by id ascending

Then

- the 2 agents registered in advance come back whole
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].present = True
  - items[0].id = 'agent-1'
  - items[0].entity_id: same as the id of the agent laid in advance
  - items[0].uuid: same as the id of the agent laid in advance
  - items[0].capacity = {}
  - items[0].used = {}
  - items[0].free = {}
  - items[0].status = 'ALIVE'
  - items[0].status_changed = None
  - items[0].first_contact: the time this run wrote
  - items[0].lost_at = None
  - items[0].schedulable = True
  - items[0].architecture = 'x86_64'
  - items[0].version = '0.0.0'
  - items[0].auto_terminate_abusing_kernel = False
  - items[0].compute_plugins = None
  - items[0].region = 'local'
  - items[0].addr = 'tcp://agent-1:6001'
  - items[0].scaling_group = 'mine-1'
  - items[0].permissions = ['read_attribute', 'update_attribute', 'create_compute_session', 'create_service']
  - items[1].present = True
  - items[1].id = 'agent-2'
  - items[1].entity_id: same as the id of the agent laid in advance
  - items[1].uuid: same as the id of the agent laid in advance
  - items[1].capacity = {}
  - items[1].used = {}
  - items[1].free = {}
  - items[1].status = 'ALIVE'
  - items[1].status_changed = None
  - items[1].first_contact: the time this run wrote
  - items[1].lost_at = None
  - items[1].schedulable = True
  - items[1].architecture = 'x86_64'
  - items[1].version = '0.0.0'
  - items[1].auto_terminate_abusing_kernel = False
  - items[1].compute_plugins = None
  - items[1].region = 'local'
  - items[1].addr = 'tcp://agent-2:6001'
  - items[1].scaling_group = 'mine-1'
  - items[1].permissions = ['read_attribute', 'update_attribute', 'create_compute_session', 'create_service']

<a id="searching-the-superadmin-pages-through-every-agent"></a>

#### [the-superadmin-pages-through-every-agent](/tests/scenario/bai_scenario/manager/agent/test_searching.py): pass

when the superadmin searches every agent, every agent registered in advance comes back whole

Given

- 2 agents and one superadmin
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-2: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AgentAdapter.admin_search: user-1 searches every agent

Then

- the 2 agents registered in advance come back whole
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].present = True
  - items[0].id = 'agent-1'
  - items[0].entity_id: same as the id of the agent laid in advance
  - items[0].uuid: same as the id of the agent laid in advance
  - items[0].capacity = {}
  - items[0].used = {}
  - items[0].free = {}
  - items[0].status = 'ALIVE'
  - items[0].status_changed = None
  - items[0].first_contact: the time this run wrote
  - items[0].lost_at = None
  - items[0].schedulable = True
  - items[0].architecture = 'x86_64'
  - items[0].version = '0.0.0'
  - items[0].auto_terminate_abusing_kernel = False
  - items[0].compute_plugins = None
  - items[0].region = 'local'
  - items[0].addr = 'tcp://agent-1:6001'
  - items[0].scaling_group = 'mine-1'
  - items[0].permissions = ['read_attribute', 'update_attribute', 'create_compute_session', 'create_service']
  - items[1].present = True
  - items[1].id = 'agent-2'
  - items[1].entity_id: same as the id of the agent laid in advance
  - items[1].uuid: same as the id of the agent laid in advance
  - items[1].capacity = {}
  - items[1].used = {}
  - items[1].free = {}
  - items[1].status = 'ALIVE'
  - items[1].status_changed = None
  - items[1].first_contact: the time this run wrote
  - items[1].lost_at = None
  - items[1].schedulable = True
  - items[1].architecture = 'x86_64'
  - items[1].version = '0.0.0'
  - items[1].auto_terminate_abusing_kernel = False
  - items[1].compute_plugins = None
  - items[1].region = 'local'
  - items[1].addr = 'tcp://agent-2:6001'
  - items[1].scaling_group = 'mine-1'
  - items[1].permissions = ['read_attribute', 'update_attribute', 'create_compute_session', 'create_service']

<a id="searching-the-superadmin-picks-an-agent-by-its-name"></a>

#### [the-superadmin-picks-an-agent-by-its-name](/tests/scenario/bai_scenario/manager/agent/test_searching.py): pass

when the superadmin searches by an agent name, only that agent comes back

Given

- 2 agents and one superadmin
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-2: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AgentAdapter.admin_search: user-1 searches the agents naming agent-2

Then

- the 1 agents registered in advance come back whole
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].present = True
  - items[0].id = 'agent-2'
  - items[0].entity_id: same as the id of the agent laid in advance
  - items[0].uuid: same as the id of the agent laid in advance
  - items[0].capacity = {}
  - items[0].used = {}
  - items[0].free = {}
  - items[0].status = 'ALIVE'
  - items[0].status_changed = None
  - items[0].first_contact: the time this run wrote
  - items[0].lost_at = None
  - items[0].schedulable = True
  - items[0].architecture = 'x86_64'
  - items[0].version = '0.0.0'
  - items[0].auto_terminate_abusing_kernel = False
  - items[0].compute_plugins = None
  - items[0].region = 'local'
  - items[0].addr = 'tcp://agent-2:6001'
  - items[0].scaling_group = 'mine-1'
  - items[0].permissions = ['read_attribute', 'update_attribute', 'create_compute_session', 'create_service']

<a id="searching-the-superadmin-picks-the-agents-of-a-resource-group"></a>

#### [the-superadmin-picks-the-agents-of-a-resource-group](/tests/scenario/bai_scenario/manager/agent/test_searching.py): pass

when the superadmin searches by a resource group name, only the agents of that group come back

Given

- 2 agents and one superadmin
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-2: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AgentAdapter.admin_search: user-1 searches the agents in resource group mine-1

Then

- the 2 agents registered in advance come back whole
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].present = True
  - items[0].id = 'agent-1'
  - items[0].entity_id: same as the id of the agent laid in advance
  - items[0].uuid: same as the id of the agent laid in advance
  - items[0].capacity = {}
  - items[0].used = {}
  - items[0].free = {}
  - items[0].status = 'ALIVE'
  - items[0].status_changed = None
  - items[0].first_contact: the time this run wrote
  - items[0].lost_at = None
  - items[0].schedulable = True
  - items[0].architecture = 'x86_64'
  - items[0].version = '0.0.0'
  - items[0].auto_terminate_abusing_kernel = False
  - items[0].compute_plugins = None
  - items[0].region = 'local'
  - items[0].addr = 'tcp://agent-1:6001'
  - items[0].scaling_group = 'mine-1'
  - items[0].permissions = ['read_attribute', 'update_attribute', 'create_compute_session', 'create_service']
  - items[1].present = True
  - items[1].id = 'agent-2'
  - items[1].entity_id: same as the id of the agent laid in advance
  - items[1].uuid: same as the id of the agent laid in advance
  - items[1].capacity = {}
  - items[1].used = {}
  - items[1].free = {}
  - items[1].status = 'ALIVE'
  - items[1].status_changed = None
  - items[1].first_contact: the time this run wrote
  - items[1].lost_at = None
  - items[1].schedulable = True
  - items[1].architecture = 'x86_64'
  - items[1].version = '0.0.0'
  - items[1].auto_terminate_abusing_kernel = False
  - items[1].compute_plugins = None
  - items[1].region = 'local'
  - items[1].addr = 'tcp://agent-2:6001'
  - items[1].scaling_group = 'mine-1'
  - items[1].permissions = ['read_attribute', 'update_attribute', 'create_compute_session', 'create_service']

<a id="searching-a-user-granted-nothing-may-not-search-the-agents"></a>

#### [a-user-granted-nothing-may-not-search-the-agents](/tests/scenario/bai_scenario/manager/agent/test_searching.py): pass

the search is open to the superadmin alone, so a regular user holding no permission is rejected for lack of privilege

Given

- 1 agents and one regular user
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AgentAdapter.admin_search: user-1 searches every agent

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-a-user-reading-the-group-loads-an-agent-by-name"></a>

#### [a-user-reading-the-group-loads-an-agent-by-name](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

when a user who can read the agents of the resource group loads one by name, the whole agent comes back

Given

- 1 agents and one the regular user granted permission to read the agents of the group
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare a user granted permission to read agents in the resource group
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role agent-reader-1: applies only within the scope it is granted in
    - Role agent-reader-1: READ allowed on every agent
    - regular user user-1: holds Role agent-reader-1

When

- AgentAdapter.batch_load_by_ids: user-1 loads the names of 1 agents at once

Then

- the agents registered in advance come back as nodes in input order
  - length = 1
  - [0].id = 'agent-1'
  - [0].entity_id: same as the id of the agent laid in advance
  - [0].uuid: same as the id of the agent laid in advance
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: the time this run wrote
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']

<a id="batch_loading-an-unknown-agent-name-answers-an-empty-value"></a>

#### [an-unknown-agent-name-answers-an-empty-value](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

a name nothing answers to comes back as an empty value

Given

- 1 agents and one the regular user granted permission to read the agents of the group
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare a user granted permission to read agents in the resource group
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role agent-reader-1: applies only within the scope it is granted in
    - Role agent-reader-1: READ allowed on every agent
    - regular user user-1: holds Role agent-reader-1

When

- AgentAdapter.batch_load_by_ids: user-1 loads the names of 1 agents and one unknown name at once

Then

- the agents registered in advance come back as nodes in input order and the unknown name entry as an empty value
  - length = 2
  - [0].id = 'agent-1'
  - [0].entity_id: same as the id of the agent laid in advance
  - [0].uuid: same as the id of the agent laid in advance
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: the time this run wrote
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']
  - [1] = None

<a id="batch_loading-a-user-reading-one-group-gets-a-denial-for-the-agent-of-another"></a>

#### [a-user-reading-one-group-gets-a-denial-for-the-agent-of-another](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

when a user who can read one group loads an agent of another group beside it, that entry is rejected for lack of permission

Given

- 1 agents, 1 agents in another group and one the regular user granted permission to read the agents of the group
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Resource group elsewhere-1: uses the fifo scheduler
  - Agent agent-2: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare a user granted permission to read agents in the resource group
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role agent-reader-1: applies only within the scope it is granted in
    - Role agent-reader-1: READ allowed on every agent
    - regular user user-1: holds Role agent-reader-1

When

- AgentAdapter.batch_load_by_ids: user-1 loads the names of 2 agents at once

Then

- the agents the caller may read come back as nodes and the rest of the entries are rejected for lack of permission
  - length = 2
  - [0].id = 'agent-1'
  - [0].entity_id: same as the id of the agent laid in advance
  - [0].uuid: same as the id of the agent laid in advance
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: the time this run wrote
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']
  - rejected: NotEnoughPermission

### batch_load_by_uuids

<a id="batch_loading-a-user-reading-the-group-loads-an-agent-by-entity-id"></a>

#### [a-user-reading-the-group-loads-an-agent-by-entity-id](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

when a user who can read the agents of the resource group loads one by its entity id, the whole agent comes back

Given

- 1 agents and one the regular user granted permission to read the agents of the group
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare a user granted permission to read agents in the resource group
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role agent-reader-1: applies only within the scope it is granted in
    - Role agent-reader-1: READ allowed on every agent
    - regular user user-1: holds Role agent-reader-1

When

- AgentAdapter.batch_load_by_uuids: user-1 loads the ids of 1 agents at once

Then

- the agents registered in advance come back as nodes in input order
  - length = 1
  - [0].id = 'agent-1'
  - [0].entity_id: same as the id of the agent laid in advance
  - [0].uuid: same as the id of the agent laid in advance
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: the time this run wrote
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']

<a id="batch_loading-a-user-granted-nothing-gets-a-denial-for-the-agent-entity-id"></a>

#### [a-user-granted-nothing-gets-a-denial-for-the-agent-entity-id](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

when a user granted nothing loads an agent by its entity id, that entry is rejected for lack of permission

Given

- 1 agents and one regular user
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AgentAdapter.batch_load_by_uuids: user-1 loads the ids of 1 agents at once

Then

- the agents the caller may read come back as nodes and the rest of the entries are rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

<a id="batch_loading-an-unknown-agent-entity-id-answers-a-denial"></a>

#### [an-unknown-agent-entity-id-answers-a-denial](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

a read by entity id is checked per id, so an id nothing answers to comes back as a denial rather than an empty value

Given

- 1 agents and one the regular user granted permission to read the agents of the group
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare a user granted permission to read agents in the resource group
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role agent-reader-1: applies only within the scope it is granted in
    - Role agent-reader-1: READ allowed on every agent
    - regular user user-1: holds Role agent-reader-1

When

- AgentAdapter.batch_load_by_uuids: user-1 loads the ids of 1 agents and one unknown id at once

Then

- the agents registered in advance come back as nodes in input order and the unknown id entry is rejected for lack of permission
  - length = 2
  - [0].id = 'agent-1'
  - [0].entity_id: same as the id of the agent laid in advance
  - [0].uuid: same as the id of the agent laid in advance
  - [0].capacity = {}
  - [0].used = {}
  - [0].free = {}
  - [0].status = 'ALIVE'
  - [0].status_changed = None
  - [0].first_contact: the time this run wrote
  - [0].lost_at = None
  - [0].schedulable = True
  - [0].architecture = 'x86_64'
  - [0].version = '0.0.0'
  - [0].auto_terminate_abusing_kernel = False
  - [0].compute_plugins = None
  - [0].region = 'local'
  - [0].addr = 'tcp://agent-1:6001'
  - [0].scaling_group = 'mine-1'
  - [0].permissions = ['read_attribute']
  - rejected: NotEnoughPermission

### batch_load_container_counts

<a id="batch_loading-a-user-reading-the-group-counts-no-container-on-the-agent"></a>

#### [a-user-reading-the-group-counts-no-container-on-the-agent](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

when a user who can read the agents of the resource group counts containers, zero comes back because nothing runs on the agent

Given

- 1 agents and one the regular user granted permission to read the agents of the group
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare a user granted permission to read agents in the resource group
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role agent-reader-1: applies only within the scope it is granted in
    - Role agent-reader-1: READ allowed on every agent
    - regular user user-1: holds Role agent-reader-1

When

- AgentAdapter.batch_load_container_counts: user-1 counts the containers of 1 agents at once

Then

- the container count of each agent comes back in input order
  - length = 1
  - [0] = 0

<a id="batch_loading-an-unknown-agent-name-counts-no-container"></a>

#### [an-unknown-agent-name-counts-no-container](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

the container count of a name nothing answers to comes back as zero

Given

- 1 agents and one the regular user granted permission to read the agents of the group
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare a user granted permission to read agents in the resource group
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role agent-reader-1: applies only within the scope it is granted in
    - Role agent-reader-1: READ allowed on every agent
    - regular user user-1: holds Role agent-reader-1

When

- AgentAdapter.batch_load_container_counts: user-1 counts the containers of 1 agents and one unknown name at once

Then

- the count comes back as zero for the agents the caller may read and for the unknown name entry
  - length = 2
  - [0] = 0
  - [1] = 0

<a id="batch_loading-a-user-granted-nothing-gets-a-denial-for-the-container-count"></a>

#### [a-user-granted-nothing-gets-a-denial-for-the-container-count](/tests/scenario/bai_scenario/manager/agent/test_batch_loading.py): pass

when a user granted nothing counts containers, the entry is rejected for lack of permission

Given

- 1 agents and one regular user
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AgentAdapter.batch_load_container_counts: user-1 counts the containers of 1 agents at once

Then

- the entry of an agent the caller may not read is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### get_total_resources

<a id="total_resources-the-superadmin-reads-the-total-of-the-slots-the-agents-report"></a>

#### [the-superadmin-reads-the-total-of-the-slots-the-agents-report](/tests/scenario/bai_scenario/manager/agent/test_total_resources.py): pass

when the superadmin reads the total, the sum of the capacity and usage the live agents report comes back

Given

- 2 agents, each reporting 1 slots and one superadmin
  - Resource group mine-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: slot-1 slot capacity 10 reported, 1 in use
  - Agent agent-2: alive, and has not reported any slot yet
  - Agent agent-2: slot-1 slot capacity 10 reported, 1 in use
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AgentAdapter.get_total_resources: user-1 reads the cluster-wide total resources

Then

- the sum of the slots the agents report comes back
  - total_capacity_slots = {'slot-1': '20'}
  - total_used_slots = {'slot-1': '2'}
  - total_free_slots = {'slot-1': '18'}

<a id="total_resources-a-user-granted-nothing-may-not-read-the-total"></a>

#### [a-user-granted-nothing-may-not-read-the-total](/tests/scenario/bai_scenario/manager/agent/test_total_resources.py): pass

the read is open to the superadmin alone, so a regular user holding no permission is rejected for lack of privilege

Given

- 1 agents and one regular user
  - Resource group mine-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AgentAdapter.get_total_resources: user-1 reads the cluster-wide total resources

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### update_resource_group

<a id="changing_resource_group-force-moves-an-agent-designated-by-another-groups-session"></a>

#### [force-moves-an-agent-designated-by-another-groups-session](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

when an agent designated by a session of another group is moved with force, the designation is dropped and the answer carrying the new group comes back

Given

- one agent designated by a session of another group, a group to move it to, and one superadmin
  - Resource group before-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Resource group after-1: uses the fifo scheduler
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Domain home-2
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled
  - Session session-1: has one designated agent

When

- AgentAdapter.update_resource_group: user-1 with force moves agent agent-1 to group after-1

Then

- the answer carrying the new resource group comes back
  - agent_id = 'agent-1'
  - resource_group_id: same as the id of the group laid in advance to move to
  - policy = 'terminate'
  - conflicting_session_ids = []
  - terminating_session_ids = []

<a id="changing_resource_group-the-superadmin-moves-an-agent-to-another-resource-group"></a>

#### [the-superadmin-moves-an-agent-to-another-resource-group](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

when the superadmin moves an agent to another resource group, the answer carrying the new group comes back

Given

- one agent, a group to move it to, and one superadmin
  - Resource group before-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Resource group after-1: uses the fifo scheduler
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AgentAdapter.update_resource_group: user-1 moves agent agent-1 to group after-1

Then

- the answer carrying the new resource group comes back
  - agent_id = 'agent-1'
  - resource_group_id: same as the id of the group laid in advance to move to
  - policy = 'terminate'
  - conflicting_session_ids = []
  - terminating_session_ids = []

<a id="changing_resource_group-a-user-granted-nothing-may-not-move-an-agent"></a>

#### [a-user-granted-nothing-may-not-move-an-agent](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

the move is open to the superadmin alone, so a regular user holding no permission is rejected for lack of privilege

Given

- one agent, a group to move it to, and one regular user
  - Resource group before-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Resource group after-1: uses the fifo scheduler
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AgentAdapter.update_resource_group: user-1 moves agent agent-1 to group after-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="changing_resource_group-an-agent-designated-by-another-groups-session-needs-force"></a>

#### [an-agent-designated-by-another-groups-session-needs-force](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

when an agent designated by a session of another group is moved without force, the call is rejected as conflicting

Given

- one agent designated by a session of another group, a group to move it to, and one superadmin
  - Resource group before-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Resource group after-1: uses the fifo scheduler
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Domain home-2
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Keypair policy keypair-policy-3: up to 5 concurrent sessions
  - regular user user-2: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Session session-1: waiting to be scheduled
  - Session session-1: has one designated agent

When

- AgentAdapter.update_resource_group: user-1 moves agent agent-1 to group after-1

Then

- the call is rejected
  - rejected: AgentHasConflictingSessions

<a id="changing_resource_group-asking-to-reschedule-the-conflicting-sessions-is-not-supported"></a>

#### [asking-to-reschedule-the-conflicting-sessions-is-not-supported](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

when the superadmin moves an agent under the reschedule policy, the call is rejected as not supported yet

Given

- one agent, a group to move it to, and one superadmin
  - Resource group before-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Resource group after-1: uses the fifo scheduler
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AgentAdapter.update_resource_group: user-1 under the reschedule policy moves agent agent-1 to group after-1

Then

- the call is rejected
  - rejected: ConflictingSessionRescheduleNotSupported

### update_resource_group_from_body

<a id="changing_resource_group-the-superadmin-moves-an-agent-through-the-rest-body"></a>

#### [the-superadmin-moves-an-agent-through-the-rest-body](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

when the superadmin moves an agent through the REST body, the answer carrying the new group comes back

Given

- one agent, a group to move it to, and one superadmin
  - Resource group before-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Resource group after-1: uses the fifo scheduler
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AgentAdapter.update_resource_group_from_body: user-1 through the REST body moves agent agent-1 to group after-1

Then

- the answer carrying the new resource group comes back
  - agent_id = 'agent-1'
  - resource_group_id: same as the id of the group laid in advance to move to
  - policy = 'terminate'
  - conflicting_session_ids = []
  - terminating_session_ids = []

<a id="changing_resource_group-a-user-granted-nothing-may-not-move-an-agent-through-the-rest-body"></a>

#### [a-user-granted-nothing-may-not-move-an-agent-through-the-rest-body](/tests/scenario/bai_scenario/manager/agent/test_changing_resource_group.py): pass

the move is open to the superadmin alone, so a regular user holding no permission is rejected for lack of privilege even through the REST body

Given

- one agent, a group to move it to, and one regular user
  - Resource group before-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Resource group after-1: uses the fifo scheduler
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AgentAdapter.update_resource_group_from_body: user-1 through the REST body moves agent agent-1 to group after-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

