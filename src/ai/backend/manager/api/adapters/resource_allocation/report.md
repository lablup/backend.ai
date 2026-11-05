## resource_allocation

[adapter](/src/ai/backend/manager/api/adapters/resource_allocation/adapter.py)

Scenario: incomplete 2 / 12

- direct implementation (12)
  - admin_domain_usage: success present 1 · rejection present 1 (single_entity)
  - admin_effective_allocation: success absent · rejection present 1 (scope): SCENARIO-GAP
  - admin_effective_allocation_resolved: success absent · rejection present 1 (scope, single_entity): SCENARIO-GAP
  - check_preset_availability: success present 1 · rejection present 1 (scope)
  - check_preset_availability_for_current_user: success present 1 · rejection present 1 (scope, single_entity)
  - effective_allocation: success present 3 · rejection present 1 (scope)
  - effective_allocation_for_current_user: success present 1 · rejection present 1 (scope, single_entity)
  - my_concurrency: success present 1 · rejection present 1 (single_entity)
  - my_keypair_usage: success present 1 · rejection present 1 (single_entity)
  - my_user_usage: success present 1 · rejection present 1 (single_entity)
  - project_usage: success present 1 · rejection present 1 (single_entity)
  - resource_group_usage: success present 1 · rejection present 1 (global_scope)

**admin_domain_usage**

| scenario | verdict |
|---|---|
| [when the superadmin reads a domain's usage, the registered slot type's limit comes back unlimited and the usage is zero](#usage-the-superadmin-reads-a-domains-usage) | answered |
| [when the superadmin reads the usage of a domain name nothing answers to, the call is rejected as no such target](#usage-reading-the-usage-of-a-domain-nothing-answers-to-is-not-found) | rejected |

**admin_effective_allocation**

| scenario | verdict |
|---|---|
| [reading the effective allocation by the admin path with a given key is rejected as no such domain, because the call reads with an empty domain name](#effective_allocation-the-admin-path-with-a-given-key-finds-no-domain) | rejected |

**admin_effective_allocation_resolved**

| scenario | verdict |
|---|---|
| [reading a user's effective allocation by the admin path is rejected as no such domain, because the call reads with an empty domain name](#effective_allocation-the-admin-path-reading-a-users-effective-allocation-finds-no-domain) | rejected |

**check_preset_availability**

| scenario | verdict |
|---|---|
| [when the superadmin checks preset availability with a given key and policy, every preset seeded in advance comes back marked as available](#checking_presets-the-superadmin-checks-available-presets-with-a-given-key) | answered |
| [a user granted nothing checking preset availability with a given key is rejected for not enough permission](#checking_presets-a-user-granted-nothing-may-not-check-preset-availability-with-a-given-key) | rejected |

**check_preset_availability_for_current_user**

| scenario | verdict |
|---|---|
| [when the superadmin checks preset availability with their own keypair, every preset seeded in advance comes back marked as available](#checking_presets-the-superadmin-checks-available-presets-for-themselves) | answered |
| [a user granted nothing checking preset availability is rejected for not enough permission](#checking_presets-a-user-granted-nothing-may-not-check-preset-availability) | rejected |

**effective_allocation**

| scenario | verdict |
|---|---|
| [a user who can read sessions in the project scope reading the effective allocation gets the resource group scope but not the project scope under the default settings](#effective_allocation-a-user-reading-sessions-reads-the-effective-allocation) | answered |
| [hiding agents drops the resource group scope from the effective allocation of a user who can read sessions in the project scope](#effective_allocation-hiding-agents-drops-the-resource-group-scope) | answered |
| [turning group resource visibility on puts the project scope into the effective allocation of a user who can read sessions in the project scope](#effective_allocation-turning-group-resource-visibility-on-shows-the-project-scope) | answered |
| [a user granted nothing reading a project's effective allocation is rejected for not enough permission](#effective_allocation-a-user-granted-nothing-may-not-read-the-effective-allocation) | rejected |

**effective_allocation_for_current_user**

| scenario | verdict |
|---|---|
| [when the superadmin reads their own effective allocation, both the project and the resource group scopes are included](#effective_allocation-the-superadmin-reads-their-own-effective-allocation) | answered |
| [a user granted nothing reading their own effective allocation is rejected for not enough permission](#effective_allocation-a-user-granted-nothing-may-not-read-their-own-effective-allocation) | rejected |

**my_concurrency**

| scenario | verdict |
|---|---|
| [when the superadmin reads their own concurrent session counts, all zero comes back because no session exists](#usage-the-superadmin-reads-their-own-concurrency) | answered |
| [a user granted nothing reading their own concurrent session counts is rejected for not enough permission](#usage-a-user-granted-nothing-may-not-read-their-own-concurrency) | rejected |

**my_keypair_usage**

| scenario | verdict |
|---|---|
| [when the superadmin reads their default keypair's usage, the registered slot type's limit comes back unlimited and the usage is zero](#usage-the-superadmin-reads-their-own-keypair-usage) | answered |
| [a user granted nothing reading their own keypair usage is rejected for not enough permission](#usage-a-user-granted-nothing-may-not-read-their-own-keypair-usage) | rejected |

**my_user_usage**

| scenario | verdict |
|---|---|
| [when the superadmin reads their own usage, the registered slot type's limit comes back unlimited and the usage is zero](#usage-the-superadmin-reads-their-own-user-usage) | answered |
| [a user granted nothing reading their own usage is rejected for not enough permission](#usage-a-user-granted-nothing-may-not-read-their-own-user-usage) | rejected |

**project_usage**

| scenario | verdict |
|---|---|
| [when the superadmin reads a project's usage, the registered slot type's limit comes back unlimited and the usage is zero](#usage-the-superadmin-reads-a-projects-usage) | answered |
| [a user granted nothing reading a project's usage is rejected for not enough permission](#usage-a-user-granted-nothing-may-not-read-a-projects-usage) | rejected |

**resource_group_usage**

| scenario | verdict |
|---|---|
| [when the superadmin reads a resource group's usage, capacity, usage and free are all empty because no agent exists](#usage-the-superadmin-reads-a-resource-groups-usage) | answered |
| [a user who is not the superadmin reading a resource group's usage is rejected for lacking the role](#usage-a-user-may-not-read-a-resource-groups-usage) | rejected |

### admin_domain_usage

<a id="usage-the-superadmin-reads-a-domains-usage"></a>

#### [the-superadmin-reads-a-domains-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

when the superadmin reads a domain's usage, the registered slot type's limit comes back unlimited and the usage is zero

Given

- one place and one superadmin. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.admin_domain_usage: user-1 reads the usage of the domain home-1

Then

- the domain scope's limit is unlimited and the usage is zero
  - domain.limits = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]
  - domain.used = [ResourceSlotEntryInfo(resource_type='slot-1', quantity=Decimal('0'))]
  - domain.assignable = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]

<a id="usage-reading-the-usage-of-a-domain-nothing-answers-to-is-not-found"></a>

#### [reading-the-usage-of-a-domain-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

when the superadmin reads the usage of a domain name nothing answers to, the call is rejected as no such target

Given

- one place and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.admin_domain_usage: user-1 reads the usage of the domain a name that does not exist

Then

- the call is rejected
  - rejected: EntityNotFoundError

### admin_effective_allocation

<a id="effective_allocation-the-admin-path-with-a-given-key-finds-no-domain"></a>

#### [the-admin-path-with-a-given-key-finds-no-domain](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

reading the effective allocation by the admin path with a given key is rejected as no such domain, because the call reads with an empty domain name

Given

- one place and one superadmin. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.admin_effective_allocation: user-1 reads the effective allocation by the admin path

Then

- the call is rejected
  - rejected: DomainNotFound

### admin_effective_allocation_resolved

<a id="effective_allocation-the-admin-path-reading-a-users-effective-allocation-finds-no-domain"></a>

#### [the-admin-path-reading-a-users-effective-allocation-finds-no-domain](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

reading a user's effective allocation by the admin path is rejected as no such domain, because the call reads with an empty domain name

Given

- one place and one superadmin. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.admin_effective_allocation_resolved: user-1 reads the effective allocation of user-1 by the admin path

Then

- the call is rejected
  - rejected: DomainNotFound

### check_preset_availability

<a id="checking_presets-the-superadmin-checks-available-presets-with-a-given-key"></a>

#### [the-superadmin-checks-available-presets-with-a-given-key](/tests/scenario/bai_scenario/manager/resource_allocation/test_checking_presets.py): pass

when the superadmin checks preset availability with a given key and policy, every preset seeded in advance comes back marked as available

Given

- one place and one superadmin. one resource slot type is registered. 2 presets exist
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group

When

- ResourceAllocationAdapter.check_preset_availability: user-1 checks which presets can be used in the project team-1

Then

- every preset seeded in advance comes back marked as available
  - len(presets) = 2
  - presets[0].id: same as the id of the preset seeded in advance
  - presets[0].name = 'preset-1'
  - presets[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - presets[0].shared_memory = None
  - presets[0].resource_group_name = None
  - presets[0].available = True
  - presets[1].id: same as the id of the preset seeded in advance
  - presets[1].name = 'preset-2'
  - presets[1].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - presets[1].shared_memory = None
  - presets[1].resource_group_name = None
  - presets[1].available = True

<a id="checking_presets-a-user-granted-nothing-may-not-check-preset-availability-with-a-given-key"></a>

#### [a-user-granted-nothing-may-not-check-preset-availability-with-a-given-key](/tests/scenario/bai_scenario/manager/resource_allocation/test_checking_presets.py): pass

a user granted nothing checking preset availability with a given key is rejected for not enough permission

Given

- one place and one regular user. one resource slot type is registered. one preset exists
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Resource preset preset-1: belongs to public because it is bound to no resource group

When

- ResourceAllocationAdapter.check_preset_availability: user-1 checks which presets can be used in the project team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### check_preset_availability_for_current_user

<a id="checking_presets-the-superadmin-checks-available-presets-for-themselves"></a>

#### [the-superadmin-checks-available-presets-for-themselves](/tests/scenario/bai_scenario/manager/resource_allocation/test_checking_presets.py): pass

when the superadmin checks preset availability with their own keypair, every preset seeded in advance comes back marked as available

Given

- one place and one superadmin. one resource slot type is registered. 2 presets exist
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one
  - Resource preset preset-1: belongs to public because it is bound to no resource group
  - Resource preset preset-2: belongs to public because it is bound to no resource group

When

- ResourceAllocationAdapter.check_preset_availability_for_current_user: user-1 checks which presets can be used in the project team-1

Then

- every preset seeded in advance comes back marked as available
  - len(presets) = 2
  - presets[0].id: same as the id of the preset seeded in advance
  - presets[0].name = 'preset-1'
  - presets[0].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - presets[0].shared_memory = None
  - presets[0].resource_group_name = None
  - presets[0].available = True
  - presets[1].id: same as the id of the preset seeded in advance
  - presets[1].name = 'preset-2'
  - presets[1].resource_slots = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('1')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('1073741824'))]
  - presets[1].shared_memory = None
  - presets[1].resource_group_name = None
  - presets[1].available = True

<a id="checking_presets-a-user-granted-nothing-may-not-check-preset-availability"></a>

#### [a-user-granted-nothing-may-not-check-preset-availability](/tests/scenario/bai_scenario/manager/resource_allocation/test_checking_presets.py): pass

a user granted nothing checking preset availability is rejected for not enough permission

Given

- one place and one regular user. one resource slot type is registered. one preset exists
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - Resource preset preset-1: belongs to public because it is bound to no resource group

When

- ResourceAllocationAdapter.check_preset_availability_for_current_user: user-1 checks which presets can be used in the project team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### effective_allocation

<a id="effective_allocation-a-user-reading-sessions-reads-the-effective-allocation"></a>

#### [a-user-reading-sessions-reads-the-effective-allocation](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

a user who can read sessions in the project scope reading the effective allocation gets the resource group scope but not the project scope under the default settings

Given

- one place and one regular user. that user can read sessions in the project scope. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - a user granted permission to read sessions in the project scope
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-1: holds Role session-reader-1

When

- ResourceAllocationAdapter.effective_allocation: user-1 reads the effective allocation of the project team-1

Then

- the whole effective allocation comes back. the project scope is absent. the resource group scope is included
  - assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.keypair.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.domain.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project = None
  - breakdown.resource_group.capacity = []
  - breakdown.resource_group.used = []
  - breakdown.resource_group.free = []
  - breakdown.resource_group.max_per_node = []

<a id="effective_allocation-hiding-agents-drops-the-resource-group-scope"></a>

#### [hiding-agents-drops-the-resource-group-scope](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

hiding agents drops the resource group scope from the effective allocation of a user who can read sessions in the project scope

Given

- one place and one regular user. that user can read sessions in the project scope. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - a user granted permission to read sessions in the project scope
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-1: holds Role session-reader-1

When

- ResourceAllocationAdapter.effective_allocation: user-1 reads the effective allocation of the project team-1

Then

- the whole effective allocation comes back. the project scope is absent. the resource group scope is absent
  - assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.keypair.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.domain.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project = None
  - breakdown.resource_group = None

<a id="effective_allocation-turning-group-resource-visibility-on-shows-the-project-scope"></a>

#### [turning-group-resource-visibility-on-shows-the-project-scope](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

turning group resource visibility on puts the project scope into the effective allocation of a user who can read sessions in the project scope

Given

- one place and one regular user. that user can read sessions in the project scope. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one
  - a user granted permission to read sessions in the project scope
    - Role session-reader-1: applies only within the scope it is granted in
    - Role session-reader-1: READ allowed on every session
    - regular user user-1: holds Role session-reader-1

When

- ResourceAllocationAdapter.effective_allocation: user-1 reads the effective allocation of the project team-1

Then

- the whole effective allocation comes back. the project scope is included. the resource group scope is included
  - assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.keypair.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.domain.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.project.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.resource_group.capacity = []
  - breakdown.resource_group.used = []
  - breakdown.resource_group.free = []
  - breakdown.resource_group.max_per_node = []

<a id="effective_allocation-a-user-granted-nothing-may-not-read-the-effective-allocation"></a>

#### [a-user-granted-nothing-may-not-read-the-effective-allocation](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

a user granted nothing reading a project's effective allocation is rejected for not enough permission

Given

- one place and one regular user. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.effective_allocation: user-1 reads the effective allocation of the project team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### effective_allocation_for_current_user

<a id="effective_allocation-the-superadmin-reads-their-own-effective-allocation"></a>

#### [the-superadmin-reads-their-own-effective-allocation](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

when the superadmin reads their own effective allocation, both the project and the resource group scopes are included

Given

- one place and one superadmin. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.effective_allocation_for_current_user: user-1 reads their own effective allocation

Then

- the whole effective allocation comes back. the project scope is included. the resource group scope is included
  - assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.keypair.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.keypair.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.domain.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.domain.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project.limits = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.project.used = [ResourceSlotEntryInfo(resource_type='cpu', quantity=Decimal('0')), ResourceSlotEntryInfo(resource_type='mem', quantity=Decimal('0'))]
  - breakdown.project.assignable = [ResourceLimitEntryInfo(resource_type='cpu', quantity=None, unlimited=True), ResourceLimitEntryInfo(resource_type='mem', quantity=None, unlimited=True)]
  - breakdown.resource_group.capacity = []
  - breakdown.resource_group.used = []
  - breakdown.resource_group.free = []
  - breakdown.resource_group.max_per_node = []

<a id="effective_allocation-a-user-granted-nothing-may-not-read-their-own-effective-allocation"></a>

#### [a-user-granted-nothing-may-not-read-their-own-effective-allocation](/tests/scenario/bai_scenario/manager/resource_allocation/test_effective_allocation.py): pass

a user granted nothing reading their own effective allocation is rejected for not enough permission

Given

- one place and one regular user. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.effective_allocation_for_current_user: user-1 reads their own effective allocation

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_concurrency

<a id="usage-the-superadmin-reads-their-own-concurrency"></a>

#### [the-superadmin-reads-their-own-concurrency](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

when the superadmin reads their own concurrent session counts, all zero comes back because no session exists

Given

- one place and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.my_concurrency: user-1 reads their own concurrent session counts

Then

- that user's session counts come back, all zero because no session exists
  - user_id: same as the id of the calling user
  - session_count = 0
  - private_session_count = 0

<a id="usage-a-user-granted-nothing-may-not-read-their-own-concurrency"></a>

#### [a-user-granted-nothing-may-not-read-their-own-concurrency](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

a user granted nothing reading their own concurrent session counts is rejected for not enough permission

Given

- one place and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.my_concurrency: user-1 reads their own concurrent session counts

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_keypair_usage

<a id="usage-the-superadmin-reads-their-own-keypair-usage"></a>

#### [the-superadmin-reads-their-own-keypair-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

when the superadmin reads their default keypair's usage, the registered slot type's limit comes back unlimited and the usage is zero

Given

- one place and one superadmin. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.my_keypair_usage: user-1 reads the usage of their default keypair

Then

- the keypair scope's limit is unlimited and the usage is zero
  - keypair.limits = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]
  - keypair.used = [ResourceSlotEntryInfo(resource_type='slot-1', quantity=Decimal('0'))]
  - keypair.assignable = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]

<a id="usage-a-user-granted-nothing-may-not-read-their-own-keypair-usage"></a>

#### [a-user-granted-nothing-may-not-read-their-own-keypair-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

a user granted nothing reading their own keypair usage is rejected for not enough permission

Given

- one place and one regular user. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.my_keypair_usage: user-1 reads the usage of their default keypair

Then

- the call is rejected
  - rejected: NotEnoughPermission

### my_user_usage

<a id="usage-the-superadmin-reads-their-own-user-usage"></a>

#### [the-superadmin-reads-their-own-user-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

when the superadmin reads their own usage, the registered slot type's limit comes back unlimited and the usage is zero

Given

- one place and one superadmin. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.my_user_usage: user-1 reads their own resource usage

Then

- the user scope's limit is unlimited and the usage is zero
  - user.limits = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]
  - user.used = [ResourceSlotEntryInfo(resource_type='slot-1', quantity=Decimal('0'))]
  - user.assignable = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]

<a id="usage-a-user-granted-nothing-may-not-read-their-own-user-usage"></a>

#### [a-user-granted-nothing-may-not-read-their-own-user-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

a user granted nothing reading their own usage is rejected for not enough permission

Given

- one place and one regular user. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.my_user_usage: user-1 reads their own resource usage

Then

- the call is rejected
  - rejected: NotEnoughPermission

### project_usage

<a id="usage-the-superadmin-reads-a-projects-usage"></a>

#### [the-superadmin-reads-a-projects-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

when the superadmin reads a project's usage, the registered slot type's limit comes back unlimited and the usage is zero

Given

- one place and one superadmin. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.project_usage: user-1 reads the usage of the project team-1

Then

- the project scope's limit is unlimited and the usage is zero
  - project.limits = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]
  - project.used = [ResourceSlotEntryInfo(resource_type='slot-1', quantity=Decimal('0'))]
  - project.assignable = [ResourceLimitEntryInfo(resource_type='slot-1', quantity=None, unlimited=True)]

<a id="usage-a-user-granted-nothing-may-not-read-a-projects-usage"></a>

#### [a-user-granted-nothing-may-not-read-a-projects-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

a user granted nothing reading a project's usage is rejected for not enough permission

Given

- one place and one regular user. one resource slot type is registered
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Resource slot type slot-1: count type
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.project_usage: user-1 reads the usage of the project team-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### resource_group_usage

<a id="usage-the-superadmin-reads-a-resource-groups-usage"></a>

#### [the-superadmin-reads-a-resource-groups-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

when the superadmin reads a resource group's usage, capacity, usage and free are all empty because no agent exists

Given

- one place and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - superadmin user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.resource_group_usage: user-1 reads the usage of the resource group group-1

Then

- the resource group's capacity, usage and free amount are all empty
  - resource_group.capacity = []
  - resource_group.used = []
  - resource_group.free = []
  - resource_group.max_per_node = []

<a id="usage-a-user-may-not-read-a-resource-groups-usage"></a>

#### [a-user-may-not-read-a-resource-groups-usage](/tests/scenario/bai_scenario/manager/resource_allocation/test_usage.py): pass

a user who is not the superadmin reading a resource group's usage is rejected for lacking the role

Given

- one place and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Keypair policy keypair-policy-2: up to 5 concurrent sessions
  - regular user user-1: has one more active keypair besides the default one

When

- ResourceAllocationAdapter.resource_group_usage: user-1 reads the usage of the resource group group-1

Then

- the call is rejected
  - rejected: InsufficientPrivilege

