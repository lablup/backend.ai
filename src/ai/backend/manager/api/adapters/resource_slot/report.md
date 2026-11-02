## resource_slot

[background](/src/ai/backend/manager/api/adapters/resource_slot/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/resource_slot/adapter.py)

Scenario: incomplete 2 / 14

- built from ops (10)
  - admin_create_slot_type: representative success ✓ · representative rejection ✓
  - admin_update_slot_type: representative success ✓ · representative rejection ✓
  - get_slot_type: representative success ✓ · representative rejection ✓
  - lookup_slot_type: representative success ✓ · representative rejection ✓
  - partial_bulk_purge_slot_types: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge_slot_type: representative success ✓ · representative rejection ✓
  - scoped_search_agent_resources: representative success ✓ · representative rejection ✓
  - search_agent_resources: representative success ✓ · representative rejection ✓
  - search_allocations: representative success ✓ · representative rejection ✓
  - search_slot_types: representative success ✓ · representative rejection ✗: SCENARIO-GAP
- direct implementation (4)
  - get_agent_resource: success present 2 · rejection present 6 (single_entity)
  - get_domain_resource_overview: success present 3 · rejection present 3 (scope)
  - get_kernel_allocation: success present 3 · rejection present 4 (single_entity)
  - get_project_resource_overview: success present 5 · rejection present 1 (scope)

**admin_create_slot_type**

| scenario | verdict |
|---|---|
| [when the superadmin creates a slot type with the display name, description, unit, icon, number format and rank given, the node comes back with those values as given](#creating-a-slot-type-made-with-every-display-value-carries-them-back) | answered |
| [when the superadmin creates a slot type of the bytes kind, the node comes back with that kind](#creating-a-slot-type-of-the-bytes-kind-is-made) | answered |
| [when the superadmin creates a slot type of the count kind, the node comes back with that kind](#creating-a-slot-type-of-the-count-kind-is-made) | answered |
| [when the superadmin creates a slot type of the unified kind, the node comes back with that kind](#creating-a-slot-type-of-the-unified-kind-is-made) | answered |
| [when the superadmin creates a slot type of the unique kind, the node comes back with that kind](#creating-a-slot-type-of-the-unique-kind-is-made) | answered |
| [when the superadmin creates a slot type with only a name and a kind, the node comes back with every display string empty, required false, enabled true, rank 0, and a decimal number format without rounding](#creating-the-superadmin-makes-a-slot-type-with-a-name-and-a-kind-alone) | answered |
| [when a slot type of the same name exists, creating it again with that name is rejected as a duplicate. This scenario is not overwritten because the agent resource, kernel allocation, model card resource request, deployment preset resource slot and deployment revision resource slot tables refer to it](#creating-a-slot-name-already-taken-is-refused) | rejected |
| [a user who is not the superadmin creating a slot type is rejected for lack of role](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-slot-type) | rejected |
| [turning permission checks off still does not let a user who is not the superadmin create a slot type](#creating-turning-enforcement-off-does-not-let-a-user-create-a-slot-type) | rejected |

**admin_update_slot_type**

| scenario | verdict |
|---|---|
| [editing a slot type with only its name and every other value omitted brings back a node that changed nothing](#editing-a-slot-type-edit-giving-no-value-changes-nothing) | answered |
| [turning off the enabled flag of a slot type that is in use brings back a node that is not enabled](#editing-disabling-a-slot-type-answers-it-disabled) | answered |
| [when the superadmin edits only the display name of a slot type named by its name, the display name becomes the new value and the rest stays](#editing-editing-a-slot-type-display-name-leaves-the-rest-alone) | answered |
| [a user who is not the superadmin editing a slot type is rejected for lack of role](#editing-a-user-who-is-not-the-superadmin-may-not-edit-a-slot-type) | rejected |
| [when the superadmin edits a name nothing answers to, the call is rejected as not found](#editing-the-superadmin-editing-a-slot-name-nothing-answers-to-is-not-found) | rejected |
| [turning permission checks off still does not let a user who is not the superadmin edit a slot type](#editing-turning-enforcement-off-does-not-let-a-user-edit-a-slot-type) | rejected |

**get_slot_type**

| scenario | verdict |
|---|---|
| [when a user granted nothing reads by name, the whole slot type comes back. Neither the name resolution step nor the read after it checks anything but authentication](#reading-a-user-granted-nothing-reads-a-slot-type-by-name) | answered |
| [reading under a name nothing answers to is rejected. The permission check follows on the resolved target, so a name that does not exist and a name the caller cannot reach are rejected for the same reason](#reading-reading-a-slot-name-nothing-answers-to-is-refused) | rejected |

**lookup_slot_type**

| scenario | verdict |
|---|---|
| [when a user granted nothing looks up an id by name, the id of that slot type comes back](#looking_up-a-user-granted-nothing-looks-up-a-slot-type-by-name) | answered |
| [looking up an id under a name nothing answers to is rejected as a bad request](#looking_up-looking-up-a-slot-name-nothing-answers-to-is-refused) | rejected |

**partial_bulk_purge_slot_types**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several slot types at once, none is deleted and every one comes back in the failed list because the user has no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-slot-types) | answered |
| [when the superadmin purges two slot types nothing refers to and one missing id at once, the two come back in the form before deletion and the missing id comes back in the failed list because nothing answers to it](#partial_bulk_purging-purging-several-slot-types-answers-for-the-missing-one) | answered |

**purge_slot_type**

| scenario | verdict |
|---|---|
| [when the superadmin purges a slot type nothing refers to by its id, the answer carries the name that was deleted](#retiring-the-superadmin-purges-a-slot-type-nothing-refers-to) | answered |
| [turning permission checks off lets a user granted nothing purge a slot type](#retiring-turning-enforcement-off-lets-a-user-purge-a-slot-type) | answered |
| [when the superadmin purges a slot type a deployment revision still uses, the call is rejected because the slot type is still in use](#retiring-a-slot-type-a-deployment-revision-still-uses-may-not-be-purged) | rejected |
| [when the superadmin purges a slot type a kernel still holds an allocation for, the call is rejected because the slot type is still in use](#retiring-a-slot-type-a-kernel-still-asks-for-may-not-be-purged) | rejected |
| [when a user granted nothing purges a slot type, the call is rejected for lack of permission. This is a different check from the one that rejects an edit for lack of role](#retiring-a-user-granted-nothing-may-not-purge-a-slot-type) | rejected |
| [when a user granted nothing purges an id nothing answers to, the call is rejected for lack of permission, not as not found, because whether the caller can use it is checked before the target is found](#retiring-a-user-granted-nothing-purging-an-unknown-slot-type-id-is-refused-by-permission) | rejected |
| [when the superadmin purges an id nothing answers to, the call is rejected as not found](#retiring-purging-a-slot-type-id-nothing-answers-to-is-not-found) | rejected |

**scoped_search_agent_resources**

| scenario | verdict |
|---|---|
| [when a user who can read the agents of the resource group reads an agent that reports two slots by naming it, every slot the agent reports comes back](#scoped_searching_agent_resources-a-user-reading-agents-in-the-group-finds-every-slot-the-agent-reports) | answered |
| [when a user who can read the agents of the resource group reads that agent by naming it before it reports any slot, the answer is empty](#scoped_searching_agent_resources-a-user-reading-agents-in-the-group-searches-the-agent-and-finds-no-slot) | answered |
| [when the superadmin reads an agent that does not report any slot yet by naming it, the answer is empty](#scoped_searching_agent_resources-the-superadmin-searches-the-agent-and-finds-no-slot) | answered |
| [turning permission checks off lets a user granted nothing read an agent by naming it](#scoped_searching_agent_resources-turning-enforcement-off-lets-a-user-search-an-agent-s-resources) | answered |
| [when a user granted nothing reads an agent by naming it, the call is rejected for lack of permission](#scoped_searching_agent_resources-a-user-granted-nothing-may-not-search-an-agent-s-resources) | rejected |
| [when a user who can read only one of two agents names both, the whole call is rejected for lack of permission. It does not answer with only the readable one](#scoped_searching_agent_resources-one-agent-the-caller-may-not-read-refuses-the-whole-search) | rejected |

**search_agent_resources**

| scenario | verdict |
|---|---|
| [when a monitor reads without a filter, the answer comes back. A read that checks whether the caller is the superadmin also passes for a monitor](#searching_agent_resources-a-monitor-may-search-agent-resources) | answered |
| [when one agent reports two slots and the call reads with the name of one slot as a filter, only the row of that slot stays in the answer](#searching_agent_resources-a-slot-name-filter-narrows-the-answer-to-that-slot) | answered |
| [when two agents report slots and the call reads with one agent as a filter, only the rows of that agent stay in the answer](#searching_agent_resources-an-agent-filter-narrows-the-answer-to-that-agent-s-slots) | answered |
| [when only an agent that does not report any slot exists and the superadmin reads without a filter, the answer is empty](#searching_agent_resources-an-agent-reporting-no-slot-means-none-is-found) | answered |
| [when two slots are reported and the call asks for only the first one, the first one in slot name order comes back and the answer says a next page exists](#searching_agent_resources-asking-for-the-first-slot-answers-one-and-a-next-page) | answered |
| [when 11 slots are reported and the call reads without a size, the first 10 in slot name order come back and the answer says a next page exists](#searching_agent_resources-omitting-the-page-size-answers-ten-slots-and-a-next-page) | answered |
| [when two agents report slots and the superadmin reads without a filter, every reported slot comes back](#searching_agent_resources-the-superadmin-finds-every-slot-the-agents-report) | answered |
| [when a user granted nothing reads, the call is rejected for lack of role](#searching_agent_resources-a-user-granted-nothing-may-not-search-agent-resources) | rejected |
| [turning permission checks off still does not let a user who is neither the superadmin nor a monitor read. The superadmin check does not read that setting](#searching_agent_resources-turning-enforcement-off-still-refuses-a-user-searching-agent-resources) | rejected |

**search_allocations**

| scenario | verdict |
|---|---|
| [when two kernels ask for one slot each and the call reads with the id of one kernel as a filter, only the allocations of that kernel stay in the answer](#searching_allocations-a-kernel-id-filter-narrows-the-answer-to-that-kernel-s-allocations) | answered |
| [when a monitor reads without a filter, every allocation is counted. A read that checks whether the caller is the superadmin also passes for a monitor](#searching_allocations-a-monitor-counts-every-allocation-laid) | answered |
| [when one kernel asks for two slots and the call reads with the name of one slot as a filter, only the allocation of that slot stays in the answer](#searching_allocations-a-slot-name-filter-narrows-the-answer-to-that-slot-s-allocation) | answered |
| [when 11 allocations exist and the call reads without a size, 10 come back and the answer says a next page exists](#searching_allocations-omitting-the-page-size-answers-ten-allocations-and-a-next-page) | answered |
| [when one kernel asks for two slots and the superadmin reads without a filter, both allocations are counted](#searching_allocations-the-superadmin-counts-every-allocation-laid) | answered |
| [when a user granted nothing reads, the call is rejected for lack of role](#searching_allocations-a-user-granted-nothing-may-not-search-allocations) | rejected |
| [turning permission checks off still does not let a user who is neither the superadmin nor a monitor read. The superadmin check does not read that setting](#searching_allocations-turning-enforcement-off-still-refuses-a-user-searching-allocations) | rejected |

**search_slot_types**

| scenario | verdict |
|---|---|
| [when the call reads with the name of one of several slot types as a filter, only the slot type of that name stays in the answer](#searching-a-name-filter-narrows-the-answer-to-the-slot-type-it-names) | answered |
| [when two slot types exist and a user granted nothing reads without a filter, both are counted](#searching-a-user-granted-nothing-counts-every-slot-type-laid) | answered |
| [when 11 slot types exist and the call reads without a size, 10 come back and the answer says a next page exists](#searching-omitting-the-page-size-answers-ten-slot-types-and-a-next-page) | answered |

**get_agent_resource**

| scenario | verdict |
|---|---|
| [when a user who can read the agents of the resource group reads a slot the agent reports, the capacity and usage reported for that slot come back](#reading_agent_resources-a-user-reading-agents-in-the-group-reads-a-slot-the-agent-reports) | answered |
| [when the superadmin reads a slot the agent reports, the capacity and usage reported for that slot come back](#reading_agent_resources-the-superadmin-reads-a-slot-the-agent-reports) | answered |
| [when a user granted nothing reads, the call is rejected for lack of permission. The permission on the agent is checked before the slot is found](#reading_agent_resources-a-user-granted-nothing-may-not-read-an-agent-slot) | rejected |
| [when a user granted nothing reads under an agent name nothing answers to, the call is rejected as not found. The name resolution step checks authentication only, and the permission is checked on the resolved agent](#reading_agent_resources-a-user-granted-nothing-reading-an-unknown-agent-name-is-not-found) | rejected |
| [when a user who can read the agents of the resource group reads a slot the agent does not report, the call passes the permission check and is then rejected as not found](#reading_agent_resources-a-user-reading-agents-in-the-group-reaches-the-slot-the-agent-does-not-report) | rejected |
| [when the superadmin reads a slot the agent does not report, the call is rejected as not found](#reading_agent_resources-reading-a-slot-the-agent-does-not-report-is-not-found) | rejected |
| [when the superadmin reads under an agent name nothing answers to, the call is rejected as not found](#reading_agent_resources-reading-an-agent-name-nothing-answers-to-is-not-found) | rejected |
| [turning permission checks off lets a user granted nothing pass the permission check, and the call is rejected as not found because the agent does not report the slot](#reading_agent_resources-turning-enforcement-off-lets-a-user-pass-the-gate-to-the-slot-the-agent-does-not-report) | rejected |

**get_domain_resource_overview**

| scenario | verdict |
|---|---|
| [when a user who can read sessions in the domain scope reads the overview of that domain, the overview comes back](#reading_domain_overview-a-user-reading-sessions-in-the-domain-reads-its-overview) | answered |
| [when the superadmin reads the overview of a domain that holds only pending kernels, no slot is occupied and the session count is 0. The overview counts only kernels that occupied or were allocated a resource, not kernels that only asked](#reading_domain_overview-the-superadmin-reads-a-domain-overview-that-counts-no-pending-kernel) | answered |
| [turning permission checks off lets a user granted nothing read the domain overview](#reading_domain_overview-turning-enforcement-off-lets-a-user-read-a-domain-overview) | answered |
| [when a user granted nothing reads, the call is rejected for lack of permission](#reading_domain_overview-a-user-granted-nothing-may-not-read-a-domain-overview) | rejected |
| [when a user who can read sessions only in the project scope reads the overview of the domain the project belongs to, the call is rejected for lack of permission. The domain overview checks the permission in the domain scope](#reading_domain_overview-a-user-reading-sessions-in-the-project-may-not-read-the-domain-overview) | rejected |
| [reading with a domain name nothing answers to is rejected as not found](#reading_domain_overview-reading-the-overview-of-a-domain-name-nothing-answers-to-is-not-found) | rejected |

**get_kernel_allocation**

| scenario | verdict |
|---|---|
| [when a user who can read sessions in the project scope reads, the whole allocation comes back. The allocation belongs to the session the kernel belongs to, so the permission on the session lets the user read the allocation](#reading_allocations-a-user-reading-sessions-in-the-project-reads-a-kernel-slot-allocation) | answered |
| [when the superadmin reads by kernel id and slot name, the whole allocation comes back. The kernel is not scheduled yet, so it holds only the requested amount and no actual usage](#reading_allocations-the-superadmin-reads-a-kernel-slot-allocation) | answered |
| [turning permission checks off lets a user granted nothing read the allocation](#reading_allocations-turning-enforcement-off-lets-a-user-read-a-kernel-slot-allocation) | answered |
| [when a user granted nothing reads, the call is rejected because the kernel id cannot be resolved. The step that resolves the kernel id to a session checks the permission on that session, and answers the same way when there is no permission and when there is no kernel](#reading_allocations-a-user-granted-nothing-may-not-read-a-kernel-slot-allocation) | rejected |
| [when a user granted nothing reads with a kernel id nothing answers to, the call is rejected for the same reason that the kernel id cannot be resolved. The answer does not tell whether that kernel exists](#reading_allocations-a-user-granted-nothing-reading-an-unknown-kernel-id-is-refused-the-same-way) | rejected |
| [when the superadmin reads with a kernel id nothing answers to, the call is rejected as not found. The superadmin, who passes every check, is answered with the fact that it is missing](#reading_allocations-reading-a-kernel-id-nothing-answers-to-is-not-found) | rejected |
| [when the superadmin reads with a slot name the kernel did not ask for, the call is rejected as not found](#reading_allocations-reading-a-slot-the-kernel-did-not-ask-for-is-not-found) | rejected |

**get_project_resource_overview**

| scenario | verdict |
|---|---|
| [when a user who can read sessions in the domain scope reads the overview of a project in that domain, the overview comes back. The permission in the domain scope also applies to the projects in it](#reading_project_overview-a-user-reading-sessions-in-the-domain-reads-a-project-overview-in-it) | answered |
| [when a user who can read sessions in the project scope reads the overview of that project, the overview comes back](#reading_project_overview-a-user-reading-sessions-in-the-project-reads-its-overview) | answered |
| [when the superadmin reads with a project id nothing answers to, an overview with no occupied slot and a session count of 0 comes back. Unlike the domain overview, a project is named by its id, so there is no resolution step and the call does not check whether the project exists](#reading_project_overview-reading-the-overview-of-a-project-id-nothing-answers-to-answers-an-empty-overview) | answered |
| [when the superadmin reads the overview of a project that holds only pending kernels, no slot is occupied and the session count is 0. The overview counts only kernels that occupied or were allocated a resource, not kernels that only asked](#reading_project_overview-the-superadmin-reads-a-project-overview-that-counts-no-pending-kernel) | answered |
| [turning permission checks off lets a user granted nothing read the project overview](#reading_project_overview-turning-enforcement-off-lets-a-user-read-a-project-overview) | answered |
| [when a user granted nothing reads, the call is rejected for lack of permission](#reading_project_overview-a-user-granted-nothing-may-not-read-a-project-overview) | rejected |

### admin_create_slot_type

<a id="creating-a-slot-type-made-with-every-display-value-carries-them-back"></a>

#### [a-slot-type-made-with-every-display-value-carries-them-back](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py): pass

when the superadmin creates a slot type with the display name, description, unit, icon, number format and rank given, the node comes back with those values as given

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.admin_create_slot_type: user-1 creates the count slot cuda.shares giving every display value

Then

- the whole slot type just created comes back
  - id = 'cuda.shares'
  - uuid: skipped: the database generates it
  - slot_name = 'cuda.shares'
  - slot_type = 'count'
  - required = True
  - enabled = False
  - display_name = 'GPU shares'
  - description = 'fractional GPU'
  - display_unit = 'share'
  - display_icon = 'gpu'
  - number_format = NumberFormatInfo(binary=True, round_length=2)
  - rank = 3

<a id="creating-a-slot-type-of-the-bytes-kind-is-made"></a>

#### [a-slot-type-of-the-bytes-kind-is-made](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py): pass

when the superadmin creates a slot type of the bytes kind, the node comes back with that kind

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.admin_create_slot_type: user-1 creates the bytes slot cuda.shares giving only a name and a kind

Then

- the whole slot type just created comes back
  - id = 'cuda.shares'
  - uuid: skipped: the database generates it
  - slot_name = 'cuda.shares'
  - slot_type = 'bytes'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

<a id="creating-a-slot-type-of-the-count-kind-is-made"></a>

#### [a-slot-type-of-the-count-kind-is-made](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py): pass

when the superadmin creates a slot type of the count kind, the node comes back with that kind

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.admin_create_slot_type: user-1 creates the count slot cuda.shares giving only a name and a kind

Then

- the whole slot type just created comes back
  - id = 'cuda.shares'
  - uuid: skipped: the database generates it
  - slot_name = 'cuda.shares'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

<a id="creating-a-slot-type-of-the-unified-kind-is-made"></a>

#### [a-slot-type-of-the-unified-kind-is-made](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py): pass

when the superadmin creates a slot type of the unified kind, the node comes back with that kind

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.admin_create_slot_type: user-1 creates the unified slot cuda.shares giving only a name and a kind

Then

- the whole slot type just created comes back
  - id = 'cuda.shares'
  - uuid: skipped: the database generates it
  - slot_name = 'cuda.shares'
  - slot_type = 'unified'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

<a id="creating-a-slot-type-of-the-unique-kind-is-made"></a>

#### [a-slot-type-of-the-unique-kind-is-made](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py): pass

when the superadmin creates a slot type of the unique kind, the node comes back with that kind

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.admin_create_slot_type: user-1 creates the unique slot cuda.shares giving only a name and a kind

Then

- the whole slot type just created comes back
  - id = 'cuda.shares'
  - uuid: skipped: the database generates it
  - slot_name = 'cuda.shares'
  - slot_type = 'unique'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

<a id="creating-the-superadmin-makes-a-slot-type-with-a-name-and-a-kind-alone"></a>

#### [the-superadmin-makes-a-slot-type-with-a-name-and-a-kind-alone](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py): pass

when the superadmin creates a slot type with only a name and a kind, the node comes back with every display string empty, required false, enabled true, rank 0, and a decimal number format without rounding

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.admin_create_slot_type: user-1 creates the count slot cuda.shares giving only a name and a kind

Then

- the whole slot type just created comes back
  - id = 'cuda.shares'
  - uuid: skipped: the database generates it
  - slot_name = 'cuda.shares'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = ''
  - description = ''
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

<a id="creating-a-slot-name-already-taken-is-refused"></a>

#### [a-slot-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py): pass

when a slot type of the same name exists, creating it again with that name is rejected as a duplicate. This scenario is not overwritten because the agent resource, kernel allocation, model card resource request, deployment preset resource slot and deployment revision resource slot tables refer to it

Given

- one resource slot type and one superadmin
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - superadmin user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.admin_create_slot_type: user-1 creates it again with the name slot-1 that already exists

Then

- the call is rejected
  - rejected: ResourceSlotTypeAlreadyExists

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-slot-type"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py): pass

a user who is not the superadmin creating a slot type is rejected for lack of role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.admin_create_slot_type: user-1 creates the count slot cuda.shares giving only a name and a kind

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-does-not-let-a-user-create-a-slot-type"></a>

#### [turning-enforcement-off-does-not-let-a-user-create-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_creating.py): pass

turning permission checks off still does not let a user who is not the superadmin create a slot type

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.admin_create_slot_type: user-1 creates the count slot cuda.shares giving only a name and a kind

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_update_slot_type

<a id="editing-a-slot-type-edit-giving-no-value-changes-nothing"></a>

#### [a-slot-type-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py): pass

editing a slot type with only its name and every other value omitted brings back a node that changed nothing

Given

- one resource slot type and one superadmin
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - superadmin user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.admin_update_slot_type: user-1 edits slot-1 without giving a value

Then

- the whole slot type seeded in advance comes back
  - id = 'slot-1'
  - uuid: skipped: the database generates it
  - slot_name = 'slot-1'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = 'a slot prepared in advance'
  - description = 'a slot type prepared in advance'
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

<a id="editing-disabling-a-slot-type-answers-it-disabled"></a>

#### [disabling-a-slot-type-answers-it-disabled](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py): pass

turning off the enabled flag of a slot type that is in use brings back a node that is not enabled

Given

- one resource slot type and one superadmin
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - superadmin user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.admin_update_slot_type: user-1 edits the enabled flag of slot-1

Then

- the whole slot type seeded in advance comes back
  - id = 'slot-1'
  - uuid: skipped: the database generates it
  - slot_name = 'slot-1'
  - slot_type = 'count'
  - required = False
  - enabled = False
  - display_name = 'a slot prepared in advance'
  - description = 'a slot type prepared in advance'
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

<a id="editing-editing-a-slot-type-display-name-leaves-the-rest-alone"></a>

#### [editing-a-slot-type-display-name-leaves-the-rest-alone](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py): pass

when the superadmin edits only the display name of a slot type named by its name, the display name becomes the new value and the rest stays

Given

- one resource slot type and one superadmin
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - superadmin user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.admin_update_slot_type: user-1 edits the display name of slot-1

Then

- the whole slot type seeded in advance comes back
  - id = 'slot-1'
  - uuid: skipped: the database generates it
  - slot_name = 'slot-1'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = 'GPU shares'
  - description = 'a slot type prepared in advance'
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

<a id="editing-a-user-who-is-not-the-superadmin-may-not-edit-a-slot-type"></a>

#### [a-user-who-is-not-the-superadmin-may-not-edit-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py): pass

a user who is not the superadmin editing a slot type is rejected for lack of role

Given

- one resource slot type and one regular user
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.admin_update_slot_type: user-1 edits the display name of slot-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="editing-the-superadmin-editing-a-slot-name-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-slot-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py): pass

when the superadmin edits a name nothing answers to, the call is rejected as not found

Given

- one resource slot type and one superadmin
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - superadmin user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.admin_update_slot_type: user-1 edits the display name of no-such-slot

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="editing-turning-enforcement-off-does-not-let-a-user-edit-a-slot-type"></a>

#### [turning-enforcement-off-does-not-let-a-user-edit-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_editing.py): pass

turning permission checks off still does not let a user who is not the superadmin edit a slot type

Given

- one resource slot type and one regular user
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.admin_update_slot_type: user-1 edits the display name of slot-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get_slot_type

<a id="reading-a-user-granted-nothing-reads-a-slot-type-by-name"></a>

#### [a-user-granted-nothing-reads-a-slot-type-by-name](/tests/scenario/bai_scenario/manager/resource_slot/test_reading.py): pass

when a user granted nothing reads by name, the whole slot type comes back. Neither the name resolution step nor the read after it checks anything but authentication

Given

- one resource slot type and one regular user
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.get_slot_type: user-1 reads under the name slot-1

Then

- the whole slot type seeded in advance comes back
  - id = 'slot-1'
  - uuid: skipped: the database generates it
  - slot_name = 'slot-1'
  - slot_type = 'count'
  - required = False
  - enabled = True
  - display_name = 'a slot prepared in advance'
  - description = 'a slot type prepared in advance'
  - display_unit = ''
  - display_icon = ''
  - number_format = NumberFormatInfo(binary=False, round_length=0)
  - rank = 0

<a id="reading-reading-a-slot-name-nothing-answers-to-is-refused"></a>

#### [reading-a-slot-name-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/resource_slot/test_reading.py): pass

reading under a name nothing answers to is rejected. The permission check follows on the resolved target, so a name that does not exist and a name the caller cannot reach are rejected for the same reason

Given

- one resource slot type and one regular user
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.get_slot_type: user-1 reads under the name no-such-slot

Then

- the call is rejected
  - rejected: GenericBadRequest

### lookup_slot_type

<a id="looking_up-a-user-granted-nothing-looks-up-a-slot-type-by-name"></a>

#### [a-user-granted-nothing-looks-up-a-slot-type-by-name](/tests/scenario/bai_scenario/manager/resource_slot/test_looking_up.py): pass

when a user granted nothing looks up an id by name, the id of that slot type comes back

Given

- one resource slot type and one regular user
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.lookup_slot_type: user-1 looks up the id under the name slot-1

Then

- the id of the slot type stored in advance comes back
  - id: same as the id of the slot type stored in advance

<a id="looking_up-looking-up-a-slot-name-nothing-answers-to-is-refused"></a>

#### [looking-up-a-slot-name-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/resource_slot/test_looking_up.py): pass

looking up an id under a name nothing answers to is rejected as a bad request

Given

- one resource slot type and one regular user
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.lookup_slot_type: user-1 looks up the id under the name no-such-slot

Then

- the call is rejected
  - rejected: GenericBadRequest

### partial_bulk_purge_slot_types

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-slot-types"></a>

#### [a-user-granted-nothing-purges-none-of-several-slot-types](/tests/scenario/bai_scenario/manager/resource_slot/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several slot types at once, none is deleted and every one comes back in the failed list because the user has no permission

Given

- 2 resource slot types and one regular user
  - Resource slot type wanted-1: count type
  - Resource slot type other-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.partial_bulk_purge_slot_types: user-1 purges 2 slot types at once

Then

- no slot type is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the slot type stored in advance
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the slot type stored in advance
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-slot-types-answers-for-the-missing-one"></a>

#### [purging-several-slot-types-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/resource_slot/test_partial_bulk_purging.py): pass

when the superadmin purges two slot types nothing refers to and one missing id at once, the two come back in the form before deletion and the missing id comes back in the failed list because nothing answers to it

Given

- 2 resource slot types and one superadmin
  - Resource slot type wanted-1: count type
  - Resource slot type other-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - superadmin user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.partial_bulk_purge_slot_types: user-1 purges 2 slot types and one missing id at once

Then

- every slot type stored in advance comes back in the form before deletion, and the missing id comes back in the failed list because nothing answers to it
  - successes count = 2
  - successes[0].id = 'wanted-1'
  - successes[0].uuid: skipped: the database generates it
  - successes[0].slot_name = 'wanted-1'
  - successes[0].slot_type = 'count'
  - successes[0].required = False
  - successes[0].enabled = True
  - successes[0].display_name = 'a slot type seeded in advance'
  - successes[0].description = 'a slot type prepared in advance'
  - successes[0].display_unit = ''
  - successes[0].display_icon = ''
  - successes[0].number_format = NumberFormatInfo(binary=False, round_length=0)
  - successes[0].rank = 0
  - successes[1].id = 'other-1'
  - successes[1].uuid: skipped: the database generates it
  - successes[1].slot_name = 'other-1'
  - successes[1].slot_type = 'count'
  - successes[1].required = False
  - successes[1].enabled = True
  - successes[1].display_name = 'a slot prepared in advance'
  - successes[1].description = 'a slot type prepared in advance'
  - successes[1].display_unit = ''
  - successes[1].display_icon = ''
  - successes[1].number_format = NumberFormatInfo(binary=False, round_length=0)
  - successes[1].rank = 0
  - failed count = 1
  - failed[0].id: same as the missing id put in the request
  - failed[0].message: a reason containing 'not found'

### purge_slot_type

<a id="retiring-the-superadmin-purges-a-slot-type-nothing-refers-to"></a>

#### [the-superadmin-purges-a-slot-type-nothing-refers-to](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py): pass

when the superadmin purges a slot type nothing refers to by its id, the answer carries the name that was deleted

Given

- one resource slot type and one superadmin
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - superadmin user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.purge_slot_type: user-1 purges slot-1

Then

- the name of the deleted slot type comes back
  - slot_name = 'slot-1'

<a id="retiring-turning-enforcement-off-lets-a-user-purge-a-slot-type"></a>

#### [turning-enforcement-off-lets-a-user-purge-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py): pass

turning permission checks off lets a user granted nothing purge a slot type

Given

- one resource slot type and one regular user
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.purge_slot_type: user-1 purges slot-1

Then

- the name of the deleted slot type comes back
  - slot_name = 'slot-1'

<a id="retiring-a-slot-type-a-deployment-revision-still-uses-may-not-be-purged"></a>

#### [a-slot-type-a-deployment-revision-still-uses-may-not-be-purged](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py): pass

when the superadmin purges a slot type a deployment revision still uses, the call is rejected because the slot type is still in use

Given

- one resource slot type that one deployment revision uses and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user with no deployment permission
    - Prepare one user in the domain
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
  - Deployment deployment-1: replica count 1, has no revision yet
  - Prepare the image, model vfolder, runtime variant and resource slot types a revision stands on
    - Container registry registry-1: image source
    - Image image-1: x86_64 image
    - Personal vfolder folder-1: is placed in that person's personal project and is ready to use
    - Grant permission to read vfolders
      - Role folder-reader-1: applies only within the scope it is granted in
      - Role folder-reader-1: READ allowed on every vfolder
      - superadmin user-1: holds Role folder-reader-1
    - Runtime variant runtime-1: the baseline model definition is empty, and it reads no config file from the model vfolder
    - Resource slot type cpu: a revision may leave it unfilled
    - Resource slot type mem: a revision may leave it unfilled
  - Deployment deployment-1: has one revision

When

- ResourceSlotAdapter.purge_slot_type: user-1 purges cpu

Then

- the call is rejected
  - rejected: ResourceSlotTypeInUse

<a id="retiring-a-slot-type-a-kernel-still-asks-for-may-not-be-purged"></a>

#### [a-slot-type-a-kernel-still-asks-for-may-not-be-purged](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py): pass

when the superadmin purges a slot type a kernel still holds an allocation for, the call is rejected because the slot type is still in use

Given

- one resource slot type that one waiting kernel asks for and one superadmin
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
  - Session session-1: has one kernel asking for slot-1 1

When

- ResourceSlotAdapter.purge_slot_type: user-2 purges slot-1

Then

- the call is rejected
  - rejected: ResourceSlotTypeInUse

<a id="retiring-a-user-granted-nothing-may-not-purge-a-slot-type"></a>

#### [a-user-granted-nothing-may-not-purge-a-slot-type](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py): pass

when a user granted nothing purges a slot type, the call is rejected for lack of permission. This is a different check from the one that rejects an edit for lack of role

Given

- one resource slot type and one regular user
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.purge_slot_type: user-1 purges slot-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-a-user-granted-nothing-purging-an-unknown-slot-type-id-is-refused-by-permission"></a>

#### [a-user-granted-nothing-purging-an-unknown-slot-type-id-is-refused-by-permission](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py): pass

when a user granted nothing purges an id nothing answers to, the call is rejected for lack of permission, not as not found, because whether the caller can use it is checked before the target is found

Given

- one resource slot type and one regular user
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.purge_slot_type: user-1 purges an id nothing answers to

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-purging-a-slot-type-id-nothing-answers-to-is-not-found"></a>

#### [purging-a-slot-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_retiring.py): pass

when the superadmin purges an id nothing answers to, the call is rejected as not found

Given

- one resource slot type and one superadmin
  - Resource slot type slot-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - superadmin user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.purge_slot_type: user-1 purges an id nothing answers to

Then

- the call is rejected
  - rejected: EntityNotFoundError

### scoped_search_agent_resources

<a id="scoped_searching_agent_resources-a-user-reading-agents-in-the-group-finds-every-slot-the-agent-reports"></a>

#### [a-user-reading-agents-in-the-group-finds-every-slot-the-agent-reports](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py): pass

when a user who can read the agents of the resource group reads an agent that reports two slots by naming it, every slot the agent reports comes back

Given

- one agent reporting 2 slots and one regular user who can read agents
  - Resource slot type slot-1: count type
  - Resource slot type slot-2: count type
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: slot-1 slot capacity 10 reported, 1 in use
  - Agent agent-1: slot-2 slot capacity 20 reported, 1 in use
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

- ResourceSlotAdapter.scoped_search_agent_resources: user-1 reads the agent agent-1 by naming it

Then

- the whole reported slot rows come back
  - len(items) = 2
  - items[0].id = 'agent-1:slot-1'
  - items[0].field_id: skipped: the database generates it
  - items[0].agent_id = 'agent-1'
  - items[0].slot_name = 'slot-1'
  - items[0].capacity: seen as a number, 10
  - items[0].used: seen as a number, 1
  - items[1].id = 'agent-1:slot-2'
  - items[1].field_id: skipped: the database generates it
  - items[1].agent_id = 'agent-1'
  - items[1].slot_name = 'slot-2'
  - items[1].capacity: seen as a number, 20
  - items[1].used: seen as a number, 1
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching_agent_resources-a-user-reading-agents-in-the-group-searches-the-agent-and-finds-no-slot"></a>

#### [a-user-reading-agents-in-the-group-searches-the-agent-and-finds-no-slot](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py): pass

when a user who can read the agents of the resource group reads that agent by naming it before it reports any slot, the answer is empty

Given

- one agent and one regular user who can read it
  - Resource group resource-group-1: uses the fifo scheduler
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

- ResourceSlotAdapter.scoped_search_agent_resources: user-1 reads the agent agent-1 by naming it

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching_agent_resources-the-superadmin-searches-the-agent-and-finds-no-slot"></a>

#### [the-superadmin-searches-the-agent-and-finds-no-slot](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py): pass

when the superadmin reads an agent that does not report any slot yet by naming it, the answer is empty

Given

- one agent and one superadmin
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.scoped_search_agent_resources: user-1 reads the agent agent-1 by naming it

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching_agent_resources-turning-enforcement-off-lets-a-user-search-an-agent-s-resources"></a>

#### [turning-enforcement-off-lets-a-user-search-an-agent-s-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py): pass

turning permission checks off lets a user granted nothing read an agent by naming it

Given

- one agent and one regular user
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.scoped_search_agent_resources: user-1 reads the agent agent-1 by naming it

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching_agent_resources-a-user-granted-nothing-may-not-search-an-agent-s-resources"></a>

#### [a-user-granted-nothing-may-not-search-an-agent-s-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py): pass

when a user granted nothing reads an agent by naming it, the call is rejected for lack of permission

Given

- one agent and one regular user
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.scoped_search_agent_resources: user-1 reads the agent agent-1 by naming it

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching_agent_resources-one-agent-the-caller-may-not-read-refuses-the-whole-search"></a>

#### [one-agent-the-caller-may-not-read-refuses-the-whole-search](/tests/scenario/bai_scenario/manager/resource_slot/test_scoped_searching_agent_resources.py): pass

when a user who can read only one of two agents names both, the whole call is rejected for lack of permission. It does not answer with only the readable one

Given

- two agents in different resource groups and one Regular user who can read the agents of one group only
  - Resource group mine-1: uses the fifo scheduler
  - Agent readable-1: alive, and has not reported any slot yet
  - Resource group elsewhere-1: uses the fifo scheduler
  - Agent other-1: alive, and has not reported any slot yet
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

- ResourceSlotAdapter.scoped_search_agent_resources: user-1 reads the agents readable-1 and other-1 by naming both

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_agent_resources

<a id="searching_agent_resources-a-monitor-may-search-agent-resources"></a>

#### [a-monitor-may-search-agent-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py): pass

when a monitor reads without a filter, the answer comes back. A read that checks whether the caller is the superadmin also passes for a monitor

Given

- one agent and one monitor
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.search_agent_resources: user-1 reads everything without a filter

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching_agent_resources-a-slot-name-filter-narrows-the-answer-to-that-slot"></a>

#### [a-slot-name-filter-narrows-the-answer-to-that-slot](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py): pass

when one agent reports two slots and the call reads with the name of one slot as a filter, only the row of that slot stays in the answer

Given

- one agent reporting 2 slots and one superadmin
  - Resource slot type slot-1: count type
  - Resource slot type slot-2: count type
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: slot-1 slot capacity 10 reported, 1 in use
  - Agent agent-1: slot-2 slot capacity 20 reported, 1 in use
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.search_agent_resources: user-1 reads with the slot name filter slot-2

Then

- the whole reported slot rows come back in this order
  - len(items) = 1
  - items[0].id = 'agent-1:slot-2'
  - items[0].field_id: skipped: the database generates it
  - items[0].agent_id = 'agent-1'
  - items[0].slot_name = 'slot-2'
  - items[0].capacity: seen as a number, 20
  - items[0].used: seen as a number, 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_agent_resources-an-agent-filter-narrows-the-answer-to-that-agent-s-slots"></a>

#### [an-agent-filter-narrows-the-answer-to-that-agent-s-slots](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py): pass

when two agents report slots and the call reads with one agent as a filter, only the rows of that agent stay in the answer

Given

- 2 agents each reporting 1 slots and one superadmin
  - Resource slot type slot-1: count type
  - Resource group resource-group-1: uses the fifo scheduler
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

- ResourceSlotAdapter.search_agent_resources: user-1 reads with the agent filter agent-2

Then

- the whole reported slot rows come back in this order
  - len(items) = 1
  - items[0].id = 'agent-2:slot-1'
  - items[0].field_id: skipped: the database generates it
  - items[0].agent_id = 'agent-2'
  - items[0].slot_name = 'slot-1'
  - items[0].capacity: seen as a number, 10
  - items[0].used: seen as a number, 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_agent_resources-an-agent-reporting-no-slot-means-none-is-found"></a>

#### [an-agent-reporting-no-slot-means-none-is-found](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py): pass

when only an agent that does not report any slot exists and the superadmin reads without a filter, the answer is empty

Given

- one agent and one superadmin
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.search_agent_resources: user-1 reads everything without a filter

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching_agent_resources-asking-for-the-first-slot-answers-one-and-a-next-page"></a>

#### [asking-for-the-first-slot-answers-one-and-a-next-page](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py): pass

when two slots are reported and the call asks for only the first one, the first one in slot name order comes back and the answer says a next page exists

Given

- one agent reporting 2 slots and one superadmin
  - Resource slot type slot-1: count type
  - Resource slot type slot-2: count type
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: slot-1 slot capacity 10 reported, 1 in use
  - Agent agent-1: slot-2 slot capacity 20 reported, 1 in use
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.search_agent_resources: user-1 reads asking for only the first 1

Then

- the rows first in slot name order come back and the answer says another page follows
  - len(items) = 1
  - items[0].id = 'agent-1:slot-1'
  - items[0].field_id: skipped: the database generates it
  - items[0].agent_id = 'agent-1'
  - items[0].slot_name = 'slot-1'
  - items[0].capacity: seen as a number, 10
  - items[0].used: seen as a number, 1
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="searching_agent_resources-omitting-the-page-size-answers-ten-slots-and-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-slots-and-a-next-page](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py): pass

when 11 slots are reported and the call reads without a size, the first 10 in slot name order come back and the answer says a next page exists

Given

- one agent reporting 11 slots and one superadmin
  - Resource slot type slot-1: count type
  - Resource slot type slot-2: count type
  - Resource slot type slot-3: count type
  - Resource slot type slot-4: count type
  - Resource slot type slot-5: count type
  - Resource slot type slot-6: count type
  - Resource slot type slot-7: count type
  - Resource slot type slot-8: count type
  - Resource slot type slot-9: count type
  - Resource slot type slot-10: count type
  - Resource slot type slot-11: count type
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: slot-1 slot capacity 10 reported, 1 in use
  - Agent agent-1: slot-2 slot capacity 20 reported, 1 in use
  - Agent agent-1: slot-3 slot capacity 30 reported, 1 in use
  - Agent agent-1: slot-4 slot capacity 40 reported, 1 in use
  - Agent agent-1: slot-5 slot capacity 50 reported, 1 in use
  - Agent agent-1: slot-6 slot capacity 60 reported, 1 in use
  - Agent agent-1: slot-7 slot capacity 70 reported, 1 in use
  - Agent agent-1: slot-8 slot capacity 80 reported, 1 in use
  - Agent agent-1: slot-9 slot capacity 90 reported, 1 in use
  - Agent agent-1: slot-10 slot capacity 100 reported, 1 in use
  - Agent agent-1: slot-11 slot capacity 110 reported, 1 in use
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.search_agent_resources: user-1 reads everything without a filter

Then

- the rows first in slot name order come back and the answer says another page follows
  - len(items) = 10
  - items[0].id = 'agent-1:slot-1'
  - items[0].field_id: skipped: the database generates it
  - items[0].agent_id = 'agent-1'
  - items[0].slot_name = 'slot-1'
  - items[0].capacity: seen as a number, 10
  - items[0].used: seen as a number, 1
  - items[1].id = 'agent-1:slot-10'
  - items[1].field_id: skipped: the database generates it
  - items[1].agent_id = 'agent-1'
  - items[1].slot_name = 'slot-10'
  - items[1].capacity: seen as a number, 100
  - items[1].used: seen as a number, 1
  - items[2].id = 'agent-1:slot-11'
  - items[2].field_id: skipped: the database generates it
  - items[2].agent_id = 'agent-1'
  - items[2].slot_name = 'slot-11'
  - items[2].capacity: seen as a number, 110
  - items[2].used: seen as a number, 1
  - items[3].id = 'agent-1:slot-2'
  - items[3].field_id: skipped: the database generates it
  - items[3].agent_id = 'agent-1'
  - items[3].slot_name = 'slot-2'
  - items[3].capacity: seen as a number, 20
  - items[3].used: seen as a number, 1
  - items[4].id = 'agent-1:slot-3'
  - items[4].field_id: skipped: the database generates it
  - items[4].agent_id = 'agent-1'
  - items[4].slot_name = 'slot-3'
  - items[4].capacity: seen as a number, 30
  - items[4].used: seen as a number, 1
  - items[5].id = 'agent-1:slot-4'
  - items[5].field_id: skipped: the database generates it
  - items[5].agent_id = 'agent-1'
  - items[5].slot_name = 'slot-4'
  - items[5].capacity: seen as a number, 40
  - items[5].used: seen as a number, 1
  - items[6].id = 'agent-1:slot-5'
  - items[6].field_id: skipped: the database generates it
  - items[6].agent_id = 'agent-1'
  - items[6].slot_name = 'slot-5'
  - items[6].capacity: seen as a number, 50
  - items[6].used: seen as a number, 1
  - items[7].id = 'agent-1:slot-6'
  - items[7].field_id: skipped: the database generates it
  - items[7].agent_id = 'agent-1'
  - items[7].slot_name = 'slot-6'
  - items[7].capacity: seen as a number, 60
  - items[7].used: seen as a number, 1
  - items[8].id = 'agent-1:slot-7'
  - items[8].field_id: skipped: the database generates it
  - items[8].agent_id = 'agent-1'
  - items[8].slot_name = 'slot-7'
  - items[8].capacity: seen as a number, 70
  - items[8].used: seen as a number, 1
  - items[9].id = 'agent-1:slot-8'
  - items[9].field_id: skipped: the database generates it
  - items[9].agent_id = 'agent-1'
  - items[9].slot_name = 'slot-8'
  - items[9].capacity: seen as a number, 80
  - items[9].used: seen as a number, 1
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching_agent_resources-the-superadmin-finds-every-slot-the-agents-report"></a>

#### [the-superadmin-finds-every-slot-the-agents-report](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py): pass

when two agents report slots and the superadmin reads without a filter, every reported slot comes back

Given

- 2 agents each reporting 1 slots and one superadmin
  - Resource slot type slot-1: count type
  - Resource group resource-group-1: uses the fifo scheduler
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

- ResourceSlotAdapter.search_agent_resources: user-1 reads everything without a filter

Then

- the whole reported slot rows come back
  - len(items) = 2
  - items[0].id = 'agent-1:slot-1'
  - items[0].field_id: skipped: the database generates it
  - items[0].agent_id = 'agent-1'
  - items[0].slot_name = 'slot-1'
  - items[0].capacity: seen as a number, 10
  - items[0].used: seen as a number, 1
  - items[1].id = 'agent-2:slot-1'
  - items[1].field_id: skipped: the database generates it
  - items[1].agent_id = 'agent-2'
  - items[1].slot_name = 'slot-1'
  - items[1].capacity: seen as a number, 10
  - items[1].used: seen as a number, 1
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_agent_resources-a-user-granted-nothing-may-not-search-agent-resources"></a>

#### [a-user-granted-nothing-may-not-search-agent-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py): pass

when a user granted nothing reads, the call is rejected for lack of role

Given

- one agent and one regular user
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.search_agent_resources: user-1 reads everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="searching_agent_resources-turning-enforcement-off-still-refuses-a-user-searching-agent-resources"></a>

#### [turning-enforcement-off-still-refuses-a-user-searching-agent-resources](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_agent_resources.py): pass

turning permission checks off still does not let a user who is neither the superadmin nor a monitor read. The superadmin check does not read that setting

Given

- one agent and one regular user
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.search_agent_resources: user-1 reads everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search_allocations

<a id="searching_allocations-a-kernel-id-filter-narrows-the-answer-to-that-kernel-s-allocations"></a>

#### [a-kernel-id-filter-narrows-the-answer-to-that-kernel-s-allocations](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py): pass

when two kernels ask for one slot each and the call reads with the id of one kernel as a filter, only the allocations of that kernel stay in the answer

Given

- 2 kernels each asking for 1 slots and one superadmin
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
  - Session session-1: has one kernel asking for slot-1 1
  - Session session-2: waiting to be scheduled
  - Session session-2: has one main kernel group
  - Session session-2: has one kernel asking for slot-1 1

When

- ResourceSlotAdapter.search_allocations: user-2 reads with the id of one kernel stored in advance as a filter

Then

- only the allocations of the kernel the filter names come back
  - items: same as the id of the kernel the filter picks and its slot names
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_allocations-a-monitor-counts-every-allocation-laid"></a>

#### [a-monitor-counts-every-allocation-laid](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py): pass

when a monitor reads without a filter, every allocation is counted. A read that checks whether the caller is the superadmin also passes for a monitor

Given

- 1 kernels each asking for 2 slots and one monitor
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
    - monitor user-2: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Container registry registry-1: image source
  - Image image-1: x86_64 image
  - Resource slot type slot-1: count type
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.search_allocations: user-2 reads everything without a filter

Then

- every allocation seeded in advance is counted
  - items: same as the ids and slot names of the kernels seeded in advance
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_allocations-a-slot-name-filter-narrows-the-answer-to-that-slot-s-allocation"></a>

#### [a-slot-name-filter-narrows-the-answer-to-that-slot-s-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py): pass

when one kernel asks for two slots and the call reads with the name of one slot as a filter, only the allocation of that slot stays in the answer

Given

- 1 kernels each asking for 2 slots and one superadmin
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.search_allocations: user-2 reads with the slot name filter slot-1

Then

- only the one allocation of the slot the filter names comes back
  - items = ['slot-1']
  - items[0].kernel_id: same as the id of the kernel the filter picks
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching_allocations-omitting-the-page-size-answers-ten-allocations-and-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-allocations-and-a-next-page](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py): pass

when 11 allocations exist and the call reads without a size, 10 come back and the answer says a next page exists

Given

- 1 kernels each asking for 11 slots and one superadmin
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
  - Resource slot type slot-2: count type
  - Resource slot type slot-3: count type
  - Resource slot type slot-4: count type
  - Resource slot type slot-5: count type
  - Resource slot type slot-6: count type
  - Resource slot type slot-7: count type
  - Resource slot type slot-8: count type
  - Resource slot type slot-9: count type
  - Resource slot type slot-10: count type
  - Resource slot type slot-11: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2, slot-3 3, slot-4 4, slot-5 5, slot-6 6, slot-7 7, slot-8 8, slot-9 9, slot-10 10, slot-11 11

When

- ResourceSlotAdapter.search_allocations: user-2 reads everything without a filter

Then

- the first page of the default size comes back
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching_allocations-the-superadmin-counts-every-allocation-laid"></a>

#### [the-superadmin-counts-every-allocation-laid](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py): pass

when one kernel asks for two slots and the superadmin reads without a filter, both allocations are counted

Given

- 1 kernels each asking for 2 slots and one superadmin
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.search_allocations: user-2 reads everything without a filter

Then

- every allocation seeded in advance is counted
  - items: same as the ids and slot names of the kernels seeded in advance
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching_allocations-a-user-granted-nothing-may-not-search-allocations"></a>

#### [a-user-granted-nothing-may-not-search-allocations](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py): pass

when a user granted nothing reads, the call is rejected for lack of role

Given

- 1 kernels each asking for 2 slots and one regular user
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.search_allocations: user-2 reads everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="searching_allocations-turning-enforcement-off-still-refuses-a-user-searching-allocations"></a>

#### [turning-enforcement-off-still-refuses-a-user-searching-allocations](/tests/scenario/bai_scenario/manager/resource_slot/test_searching_allocations.py): pass

turning permission checks off still does not let a user who is neither the superadmin nor a monitor read. The superadmin check does not read that setting

Given

- 1 kernels each asking for 2 slots and one regular user
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.search_allocations: user-2 reads everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search_slot_types

<a id="searching-a-name-filter-narrows-the-answer-to-the-slot-type-it-names"></a>

#### [a-name-filter-narrows-the-answer-to-the-slot-type-it-names](/tests/scenario/bai_scenario/manager/resource_slot/test_searching.py): pass

when the call reads with the name of one of several slot types as a filter, only the slot type of that name stays in the answer

Given

- 3 resource slot types and one regular user
  - Resource slot type wanted-1: count type
  - Resource slot type other-1: count type
  - Resource slot type other-2: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.search_slot_types: user-1 reads with the name filter wanted-1

Then

- only the one slot type the filter names comes back
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-counts-every-slot-type-laid"></a>

#### [a-user-granted-nothing-counts-every-slot-type-laid](/tests/scenario/bai_scenario/manager/resource_slot/test_searching.py): pass

when two slot types exist and a user granted nothing reads without a filter, both are counted

Given

- 2 resource slot types and one regular user
  - Resource slot type wanted-1: count type
  - Resource slot type other-1: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.search_slot_types: user-1 reads everything without a filter

Then

- every slot type seeded in advance is counted
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-omitting-the-page-size-answers-ten-slot-types-and-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-slot-types-and-a-next-page](/tests/scenario/bai_scenario/manager/resource_slot/test_searching.py): pass

when 11 slot types exist and the call reads without a size, 10 come back and the answer says a next page exists

Given

- 11 resource slot types and one regular user
  - Resource slot type wanted-1: count type
  - Resource slot type other-1: count type
  - Resource slot type other-2: count type
  - Resource slot type other-3: count type
  - Resource slot type other-4: count type
  - Resource slot type other-5: count type
  - Resource slot type other-6: count type
  - Resource slot type other-7: count type
  - Resource slot type other-8: count type
  - Resource slot type other-9: count type
  - Resource slot type other-10: count type
  - Domain home-1
  - Prepare a user granted read permission on resource_slot_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every resource_slot_type
    - regular user user-1: holds Role public-reader-1

When

- ResourceSlotAdapter.search_slot_types: user-1 reads everything without a filter

Then

- the first page of the default size comes back
  - len(items) = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

### get_agent_resource

<a id="reading_agent_resources-a-user-reading-agents-in-the-group-reads-a-slot-the-agent-reports"></a>

#### [a-user-reading-agents-in-the-group-reads-a-slot-the-agent-reports](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py): pass

when a user who can read the agents of the resource group reads a slot the agent reports, the capacity and usage reported for that slot come back

Given

- one agent reporting 1 slots and one regular user who can read agents
  - Resource slot type slot-1: count type
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: slot-1 slot capacity 10 reported, 1 in use
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

- ResourceSlotAdapter.get_agent_resource: user-1 reads the slot-1 slot of agent agent-1

Then

- the whole reported slot row comes back
  - id = 'agent-1:slot-1'
  - field_id: skipped: the database generates it
  - agent_id = 'agent-1'
  - slot_name = 'slot-1'
  - capacity: seen as a number, 10
  - used: seen as a number, 1

<a id="reading_agent_resources-the-superadmin-reads-a-slot-the-agent-reports"></a>

#### [the-superadmin-reads-a-slot-the-agent-reports](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py): pass

when the superadmin reads a slot the agent reports, the capacity and usage reported for that slot come back

Given

- one agent reporting 1 slots and one superadmin
  - Resource slot type slot-1: count type
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Agent agent-1: slot-1 slot capacity 10 reported, 1 in use
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.get_agent_resource: user-1 reads the slot-1 slot of agent agent-1

Then

- the whole reported slot row comes back
  - id = 'agent-1:slot-1'
  - field_id: skipped: the database generates it
  - agent_id = 'agent-1'
  - slot_name = 'slot-1'
  - capacity: seen as a number, 10
  - used: seen as a number, 1

<a id="reading_agent_resources-a-user-granted-nothing-may-not-read-an-agent-slot"></a>

#### [a-user-granted-nothing-may-not-read-an-agent-slot](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py): pass

when a user granted nothing reads, the call is rejected for lack of permission. The permission on the agent is checked before the slot is found

Given

- one agent and one regular user
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.get_agent_resource: user-1 reads the cpu slot of agent agent-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading_agent_resources-a-user-granted-nothing-reading-an-unknown-agent-name-is-not-found"></a>

#### [a-user-granted-nothing-reading-an-unknown-agent-name-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py): pass

when a user granted nothing reads under an agent name nothing answers to, the call is rejected as not found. The name resolution step checks authentication only, and the permission is checked on the resolved agent

Given

- one agent and one regular user
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.get_agent_resource: user-1 reads the cpu slot of agent no-such-agent

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="reading_agent_resources-a-user-reading-agents-in-the-group-reaches-the-slot-the-agent-does-not-report"></a>

#### [a-user-reading-agents-in-the-group-reaches-the-slot-the-agent-does-not-report](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py): pass

when a user who can read the agents of the resource group reads a slot the agent does not report, the call passes the permission check and is then rejected as not found

Given

- one agent and one regular user who can read it
  - Resource group resource-group-1: uses the fifo scheduler
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

- ResourceSlotAdapter.get_agent_resource: user-1 reads the cpu slot of agent agent-1

Then

- the call is rejected
  - rejected: AgentResourceNotFound

<a id="reading_agent_resources-reading-a-slot-the-agent-does-not-report-is-not-found"></a>

#### [reading-a-slot-the-agent-does-not-report-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py): pass

when the superadmin reads a slot the agent does not report, the call is rejected as not found

Given

- one agent and one superadmin
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.get_agent_resource: user-1 reads the cpu slot of agent agent-1

Then

- the call is rejected
  - rejected: AgentResourceNotFound

<a id="reading_agent_resources-reading-an-agent-name-nothing-answers-to-is-not-found"></a>

#### [reading-an-agent-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py): pass

when the superadmin reads under an agent name nothing answers to, the call is rejected as not found

Given

- one agent and one superadmin
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.get_agent_resource: user-1 reads the cpu slot of agent no-such-agent

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="reading_agent_resources-turning-enforcement-off-lets-a-user-pass-the-gate-to-the-slot-the-agent-does-not-report"></a>

#### [turning-enforcement-off-lets-a-user-pass-the-gate-to-the-slot-the-agent-does-not-report](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_agent_resources.py): pass

turning permission checks off lets a user granted nothing pass the permission check, and the call is rejected as not found because the agent does not report the slot

Given

- one agent and one regular user
  - Resource group resource-group-1: uses the fifo scheduler
  - Agent agent-1: alive, and has not reported any slot yet
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ResourceSlotAdapter.get_agent_resource: user-1 reads the cpu slot of agent agent-1

Then

- the call is rejected
  - rejected: AgentResourceNotFound

### get_domain_resource_overview

<a id="reading_domain_overview-a-user-reading-sessions-in-the-domain-reads-its-overview"></a>

#### [a-user-reading-sessions-in-the-domain-reads-its-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py): pass

when a user who can read sessions in the domain scope reads the overview of that domain, the overview comes back

Given

- one kernel waiting and asking for two slots, and one regular user who can read sessions in the domain scope
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2
  - Prepare a user granted permission to read sessions in the domain scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- ResourceSlotAdapter.get_domain_resource_overview: user-2 reads the overview of the domain home-1

Then

- an overview with no occupied slot and a session count of zero comes back
  - slots.entries = []
  - session_count = 0

<a id="reading_domain_overview-the-superadmin-reads-a-domain-overview-that-counts-no-pending-kernel"></a>

#### [the-superadmin-reads-a-domain-overview-that-counts-no-pending-kernel](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py): pass

when the superadmin reads the overview of a domain that holds only pending kernels, no slot is occupied and the session count is 0. The overview counts only kernels that occupied or were allocated a resource, not kernels that only asked

Given

- one kernel waiting and asking for two slots, and one superadmin
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_domain_resource_overview: user-2 reads the overview of the domain home-1

Then

- an overview with no occupied slot and a session count of zero comes back
  - slots.entries = []
  - session_count = 0

<a id="reading_domain_overview-turning-enforcement-off-lets-a-user-read-a-domain-overview"></a>

#### [turning-enforcement-off-lets-a-user-read-a-domain-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py): pass

turning permission checks off lets a user granted nothing read the domain overview

Given

- one kernel waiting and asking for two slots, and one regular user
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_domain_resource_overview: user-2 reads the overview of the domain home-1

Then

- an overview with no occupied slot and a session count of zero comes back
  - slots.entries = []
  - session_count = 0

<a id="reading_domain_overview-a-user-granted-nothing-may-not-read-a-domain-overview"></a>

#### [a-user-granted-nothing-may-not-read-a-domain-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py): pass

when a user granted nothing reads, the call is rejected for lack of permission

Given

- one kernel waiting and asking for two slots, and one regular user
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_domain_resource_overview: user-2 reads the overview of the domain home-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading_domain_overview-a-user-reading-sessions-in-the-project-may-not-read-the-domain-overview"></a>

#### [a-user-reading-sessions-in-the-project-may-not-read-the-domain-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py): pass

when a user who can read sessions only in the project scope reads the overview of the domain the project belongs to, the call is rejected for lack of permission. The domain overview checks the permission in the domain scope

Given

- one kernel waiting and asking for two slots, and one regular user who can read sessions in the project scope
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- ResourceSlotAdapter.get_domain_resource_overview: user-2 reads the overview of the domain home-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading_domain_overview-reading-the-overview-of-a-domain-name-nothing-answers-to-is-not-found"></a>

#### [reading-the-overview-of-a-domain-name-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_domain_overview.py): pass

reading with a domain name nothing answers to is rejected as not found

Given

- one kernel waiting and asking for two slots, and one superadmin
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_domain_resource_overview: user-2 reads the overview of the domain no-such-domain

Then

- the call is rejected
  - rejected: EntityNotFoundError

### get_kernel_allocation

<a id="reading_allocations-a-user-reading-sessions-in-the-project-reads-a-kernel-slot-allocation"></a>

#### [a-user-reading-sessions-in-the-project-reads-a-kernel-slot-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py): pass

when a user who can read sessions in the project scope reads, the whole allocation comes back. The allocation belongs to the session the kernel belongs to, so the permission on the session lets the user read the allocation

Given

- one kernel waiting and asking for two slots, and one regular user who can read sessions in the project scope
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- ResourceSlotAdapter.get_kernel_allocation: user-2 reads with the id of the kernel stored in advance and the slot name slot-1

Then

- the whole allocation of that kernel comes back
  - id: same as the id and slot name of the kernel seeded in advance
  - kernel_id: same as the id of the kernel seeded in advance
  - slot_name = 'slot-1'
  - requested: seen as a number, 1
  - used = None

<a id="reading_allocations-the-superadmin-reads-a-kernel-slot-allocation"></a>

#### [the-superadmin-reads-a-kernel-slot-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py): pass

when the superadmin reads by kernel id and slot name, the whole allocation comes back. The kernel is not scheduled yet, so it holds only the requested amount and no actual usage

Given

- one kernel waiting and asking for two slots, and one superadmin
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_kernel_allocation: user-2 reads with the id of the kernel stored in advance and the slot name slot-1

Then

- the whole allocation of that kernel comes back
  - id: same as the id and slot name of the kernel seeded in advance
  - kernel_id: same as the id of the kernel seeded in advance
  - slot_name = 'slot-1'
  - requested: seen as a number, 1
  - used = None

<a id="reading_allocations-turning-enforcement-off-lets-a-user-read-a-kernel-slot-allocation"></a>

#### [turning-enforcement-off-lets-a-user-read-a-kernel-slot-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py): pass

turning permission checks off lets a user granted nothing read the allocation

Given

- one kernel waiting and asking for two slots, and one regular user
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_kernel_allocation: user-2 reads with the id of the kernel stored in advance and the slot name slot-1

Then

- the whole allocation of that kernel comes back
  - id: same as the id and slot name of the kernel seeded in advance
  - kernel_id: same as the id of the kernel seeded in advance
  - slot_name = 'slot-1'
  - requested: seen as a number, 1
  - used = None

<a id="reading_allocations-a-user-granted-nothing-may-not-read-a-kernel-slot-allocation"></a>

#### [a-user-granted-nothing-may-not-read-a-kernel-slot-allocation](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py): pass

when a user granted nothing reads, the call is rejected because the kernel id cannot be resolved. The step that resolves the kernel id to a session checks the permission on that session, and answers the same way when there is no permission and when there is no kernel

Given

- one kernel waiting and asking for two slots, and one regular user
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_kernel_allocation: user-2 reads with the id of the kernel stored in advance and the slot name slot-1

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="reading_allocations-a-user-granted-nothing-reading-an-unknown-kernel-id-is-refused-the-same-way"></a>

#### [a-user-granted-nothing-reading-an-unknown-kernel-id-is-refused-the-same-way](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py): pass

when a user granted nothing reads with a kernel id nothing answers to, the call is rejected for the same reason that the kernel id cannot be resolved. The answer does not tell whether that kernel exists

Given

- one kernel waiting and asking for two slots, and one regular user
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_kernel_allocation: user-2 reads with a kernel id nothing answers to and the slot name slot-1

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="reading_allocations-reading-a-kernel-id-nothing-answers-to-is-not-found"></a>

#### [reading-a-kernel-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py): pass

when the superadmin reads with a kernel id nothing answers to, the call is rejected as not found. The superadmin, who passes every check, is answered with the fact that it is missing

Given

- one kernel waiting and asking for two slots, and one superadmin
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_kernel_allocation: user-2 reads with a kernel id nothing answers to and the slot name slot-1

Then

- the call is rejected
  - rejected: FieldNotFoundError

<a id="reading_allocations-reading-a-slot-the-kernel-did-not-ask-for-is-not-found"></a>

#### [reading-a-slot-the-kernel-did-not-ask-for-is-not-found](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_allocations.py): pass

when the superadmin reads with a slot name the kernel did not ask for, the call is rejected as not found

Given

- one kernel waiting and asking for two slots, and one superadmin
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_kernel_allocation: user-2 reads with the id of the kernel stored in advance and the slot name no-such-slot

Then

- the call is rejected
  - rejected: ResourceAllocationNotFound

### get_project_resource_overview

<a id="reading_project_overview-a-user-reading-sessions-in-the-domain-reads-a-project-overview-in-it"></a>

#### [a-user-reading-sessions-in-the-domain-reads-a-project-overview-in-it](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py): pass

when a user who can read sessions in the domain scope reads the overview of a project in that domain, the overview comes back. The permission in the domain scope also applies to the projects in it

Given

- one kernel waiting and asking for two slots, and one regular user who can read sessions in the domain scope
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2
  - Prepare a user granted permission to read sessions in the domain scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- ResourceSlotAdapter.get_project_resource_overview: user-2 reads the overview with the id of the project team-1

Then

- an overview with no occupied slot and a session count of zero comes back
  - slots.entries = []
  - session_count = 0

<a id="reading_project_overview-a-user-reading-sessions-in-the-project-reads-its-overview"></a>

#### [a-user-reading-sessions-in-the-project-reads-its-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py): pass

when a user who can read sessions in the project scope reads the overview of that project, the overview comes back

Given

- one kernel waiting and asking for two slots, and one regular user who can read sessions in the project scope
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2
  - Prepare a user granted permission to read sessions in the project scope
    - Prepare one user in the domain
      - User resource policy user-policy-2: up to 10 folders per user
      - Keypair policy keypair-policy-3: up to 5 concurrent sessions
      - regular user user-2: has their own keypair and personal project
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-2: holds Role session-reader-1

When

- ResourceSlotAdapter.get_project_resource_overview: user-2 reads the overview with the id of the project team-1

Then

- an overview with no occupied slot and a session count of zero comes back
  - slots.entries = []
  - session_count = 0

<a id="reading_project_overview-reading-the-overview-of-a-project-id-nothing-answers-to-answers-an-empty-overview"></a>

#### [reading-the-overview-of-a-project-id-nothing-answers-to-answers-an-empty-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py): pass

when the superadmin reads with a project id nothing answers to, an overview with no occupied slot and a session count of 0 comes back. Unlike the domain overview, a project is named by its id, so there is no resolution step and the call does not check whether the project exists

Given

- one kernel waiting and asking for two slots, and one superadmin
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_project_resource_overview: user-2 reads the overview with a project id nothing answers to

Then

- an overview with no occupied slot and a session count of zero comes back
  - slots.entries = []
  - session_count = 0

<a id="reading_project_overview-the-superadmin-reads-a-project-overview-that-counts-no-pending-kernel"></a>

#### [the-superadmin-reads-a-project-overview-that-counts-no-pending-kernel](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py): pass

when the superadmin reads the overview of a project that holds only pending kernels, no slot is occupied and the session count is 0. The overview counts only kernels that occupied or were allocated a resource, not kernels that only asked

Given

- one kernel waiting and asking for two slots, and one superadmin
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_project_resource_overview: user-2 reads the overview with the id of the project team-1

Then

- an overview with no occupied slot and a session count of zero comes back
  - slots.entries = []
  - session_count = 0

<a id="reading_project_overview-turning-enforcement-off-lets-a-user-read-a-project-overview"></a>

#### [turning-enforcement-off-lets-a-user-read-a-project-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py): pass

turning permission checks off lets a user granted nothing read the project overview

Given

- one kernel waiting and asking for two slots, and one regular user
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_project_resource_overview: user-2 reads the overview with the id of the project team-1

Then

- an overview with no occupied slot and a session count of zero comes back
  - slots.entries = []
  - session_count = 0

<a id="reading_project_overview-a-user-granted-nothing-may-not-read-a-project-overview"></a>

#### [a-user-granted-nothing-may-not-read-a-project-overview](/tests/scenario/bai_scenario/manager/resource_slot/test_reading_project_overview.py): pass

when a user granted nothing reads, the call is rejected for lack of permission

Given

- one kernel waiting and asking for two slots, and one regular user
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
  - Resource slot type slot-2: count type
  - Session session-1: waiting to be scheduled
  - Session session-1: has one main kernel group
  - Session session-1: has one kernel asking for slot-1 1, slot-2 2

When

- ResourceSlotAdapter.get_project_resource_overview: user-2 reads the overview with the id of the project team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

