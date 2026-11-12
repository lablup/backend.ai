## fair_share

[background](/src/ai/backend/manager/api/adapters/fair_share/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/fair_share/adapter.py)

Scenario: complete

- direct implementation (15)
  - atomic_bulk_upsert_domain: success present 1 · rejection present 2 (scope)
  - atomic_bulk_upsert_project: success present 1 · rejection present 2 (scope)
  - atomic_bulk_upsert_user: success present 1 · rejection present 2 (scope)
  - get_domain: success present 1 · rejection present 2 (scope)
  - get_project: success present 1 · rejection present 2 (scope)
  - get_user: success present 1 · rejection present 2 (scope)
  - search_domain: success present 1 · rejection present 1 (global_scope)
  - search_project: success present 1 · rejection present 1 (global_scope)
  - search_rg_domain: success present 1 · rejection present 2 (scope)
  - search_rg_project: success present 1 · rejection present 2 (scope)
  - search_rg_user: success present 1 · rejection present 2 (scope)
  - search_user: success present 1 · rejection present 1 (global_scope)
  - upsert_domain: success present 1 · rejection present 2 (scope)
  - upsert_project: success present 1 · rejection present 2 (scope)
  - upsert_user: success present 1 · rejection present 2 (scope)

**atomic_bulk_upsert_domain**

| scenario | verdict |
|---|---|
| [when the superadmin sets the weights of two domains at once, a count comes back saying that two were set](#atomic_bulk_upserting-the-superadmin-sets-several-domain-weights-at-once) | answered |
| [when a user granted nothing tries to set the weights of two domains at once, it is rejected for a lack of permission](#atomic_bulk_upserting-a-user-granted-nothing-may-not-set-several-domain-weights) | rejected |
| [when a user granted the update permission through a role assigned on the group tries to set the weights of two domains at once, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group](#atomic_bulk_upserting-a-user-granted-update-on-the-group-may-not-set-several-domain-weights) | rejected |

**atomic_bulk_upsert_project**

| scenario | verdict |
|---|---|
| [when the superadmin sets the weights of two projects at once, a count comes back saying that two were set](#atomic_bulk_upserting_project-the-superadmin-sets-several-project-weights-at-once) | answered |
| [when a user granted nothing tries to set the weights of two projects at once, it is rejected for a lack of permission](#atomic_bulk_upserting_project-a-user-granted-nothing-may-not-set-several-project-weights) | rejected |
| [when a user granted the update permission through a role assigned on the group tries to set the weights of two projects at once, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group](#atomic_bulk_upserting_project-a-user-granted-update-on-the-group-may-not-set-several-project-weights) | rejected |

**atomic_bulk_upsert_user**

| scenario | verdict |
|---|---|
| [when the superadmin sets the weights of two users at once, a count comes back saying that two were set](#atomic_bulk_upserting_user-the-superadmin-sets-several-user-weights-at-once) | answered |
| [when a user granted nothing tries to set the weights of two users at once, it is rejected for a lack of permission](#atomic_bulk_upserting_user-a-user-granted-nothing-may-not-set-several-user-weights) | rejected |
| [when a user granted the update permission through a role assigned on the group tries to set the weights of two users at once, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group](#atomic_bulk_upserting_user-a-user-granted-update-on-the-group-may-not-set-several-user-weights) | rejected |

**get_domain**

| scenario | verdict |
|---|---|
| [when a user granted the fair share read role in the resource group scope reads the fair share of a domain, the values recorded in that group come back](#getting-a-user-granted-fair-share-read-on-the-group-reads-a-domain-fair-share) | answered |
| [when a user granted only the fair share update role in the resource group scope reads the fair share of a domain, it is rejected for a lack of permission](#getting-a-user-granted-only-fair-share-update-may-not-read-a-domain-fair-share) | rejected |
| [when a user granted the fair share read role reads the fair share of a domain under a resource group name nobody created, it fails because the resource group is not found](#getting-reading-a-domain-fair-share-in-an-unknown-resource-group-fails) | rejected |

**get_project**

| scenario | verdict |
|---|---|
| [when a user granted the fair share read role in the resource group scope reads the fair share of a project, the values recorded in that group come back](#getting-a-user-granted-fair-share-read-on-the-group-reads-a-project-fair-share) | answered |
| [when a user granted only the fair share update role in the resource group scope reads the fair share of a project, it is rejected for a lack of permission](#getting-a-user-granted-only-fair-share-update-may-not-read-a-project-fair-share) | rejected |
| [when a user granted the fair share read role reads the fair share of a project under a resource group name nobody created, it fails because the resource group is not found](#getting-reading-a-project-fair-share-in-an-unknown-resource-group-fails) | rejected |

**get_user**

| scenario | verdict |
|---|---|
| [when a user granted the fair share read role in the resource group scope reads the fair share of a user, the values recorded in that group come back](#getting-a-user-granted-fair-share-read-on-the-group-reads-a-user-fair-share) | answered |
| [when a user granted only the fair share update role in the resource group scope reads the fair share of a user, it is rejected for a lack of permission](#getting-a-user-granted-only-fair-share-update-may-not-read-a-user-fair-share) | rejected |
| [when a user granted the fair share read role reads the fair share of a user under a resource group name nobody created, it fails because the resource group is not found](#getting-reading-a-user-fair-share-in-an-unknown-resource-group-fails) | rejected |

**search_domain**

| scenario | verdict |
|---|---|
| [this search is gated by the global role. When the superadmin searches the domain fair shares with one resource group filter, by name, for one item, the two records of that group are counted, the record first by name comes back, and the record in the other group does not](#searching-the-superadmin-searches-the-domain-fair-shares-of-one-group) | answered |
| [when a regular user searches the domain fair shares across resource groups, it is rejected for lacking the role](#searching-a-regular-user-may-not-search-domain-fair-shares-across-groups) | rejected |

**search_project**

| scenario | verdict |
|---|---|
| [this search is gated by the global role. When the superadmin searches the project fair shares with one resource group filter, by name, for one item, the two records of that group are counted, the record first by name comes back, and the record in the other group does not](#searching-the-superadmin-searches-the-project-fair-shares-of-one-group) | answered |
| [when a regular user searches the project fair shares across resource groups, it is rejected for lacking the role](#searching-a-regular-user-may-not-search-project-fair-shares-across-groups) | rejected |

**search_rg_domain**

| scenario | verdict |
|---|---|
| [when a user granted the fair share read role in the resource group scope searches the domain fair shares of that group with the active filter, by name, for the second item, the two active ones are counted and the second comes back; a domain recorded only in the other resource group comes back with this group's defaults and the inactive domain does not come back](#scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-domain-fair-shares) | answered |
| [when a user granted only the fair share update role in the resource group scope searches the domain fair shares of that group, it is rejected for a lack of permission](#scoped_searching-a-user-granted-only-fair-share-update-may-not-search-domain-fair-shares) | rejected |
| [when a user granted the fair share read role searches the domain fair shares under a resource group name nobody created, it fails because the resource group is not found](#scoped_searching-searching-domain-fair-shares-in-an-unknown-resource-group-fails) | rejected |

**search_rg_project**

| scenario | verdict |
|---|---|
| [when a user granted the fair share read role in the resource group scope searches the project fair shares of that group with the active filter, by name, for the second item, the two active ones are counted and the second comes back; the project of another domain and the inactive project do not come back](#scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-project-fair-shares) | answered |
| [when a user granted only the fair share update role in the resource group scope searches the project fair shares of that group, it is rejected for a lack of permission](#scoped_searching-a-user-granted-only-fair-share-update-may-not-search-project-fair-shares) | rejected |
| [when a user granted the fair share read role searches the project fair shares under a resource group name nobody created, it fails because the resource group is not found](#scoped_searching-searching-project-fair-shares-in-an-unknown-resource-group-fails) | rejected |

**search_rg_user**

| scenario | verdict |
|---|---|
| [when a user granted the fair share read role in the resource group scope searches the user fair shares of that group with the active filter, by name, for the second item, the two active ones are counted and the second comes back; the member of another project and the inactive member do not come back](#scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-user-fair-shares) | answered |
| [when a user granted only the fair share update role in the resource group scope searches the user fair shares of that group, it is rejected for a lack of permission](#scoped_searching-a-user-granted-only-fair-share-update-may-not-search-user-fair-shares) | rejected |
| [when a user granted the fair share read role searches the user fair shares under a resource group name nobody created, it fails because the resource group is not found](#scoped_searching-searching-user-fair-shares-in-an-unknown-resource-group-fails) | rejected |

**search_user**

| scenario | verdict |
|---|---|
| [this search is gated by the global role. When the superadmin searches the user fair shares with one resource group filter, by name, for one item, the two records of that group are counted, the record first by name comes back, and the record in the other group does not](#searching-the-superadmin-searches-the-user-fair-shares-of-one-group) | answered |
| [when a regular user searches the user fair shares across resource groups, it is rejected for lacking the role](#searching-a-regular-user-may-not-search-user-fair-shares-across-groups) | rejected |

**upsert_domain**

| scenario | verdict |
|---|---|
| [when the superadmin sets the weight of a domain in the group, the record comes back carrying that weight and the rest of the settings are the group defaults](#upserting-the-superadmin-sets-a-domain-weight) | answered |
| [when a user granted nothing tries to set the weight of a domain, it is rejected for a lack of permission](#upserting-a-user-granted-nothing-may-not-set-a-domain-weight) | rejected |
| [when a user granted the update permission through a role assigned on the group tries to set the weight of a domain, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group](#upserting-a-user-granted-update-on-the-group-may-not-set-a-domain-weight) | rejected |

**upsert_project**

| scenario | verdict |
|---|---|
| [when the superadmin sets the weight of a project in the group, the record comes back carrying that weight and the rest of the settings are the group defaults](#upserting_project-the-superadmin-sets-a-project-weight) | answered |
| [when a user granted nothing tries to set the weight of a project, it is rejected for a lack of permission](#upserting_project-a-user-granted-nothing-may-not-set-a-project-weight) | rejected |
| [when a user granted the update permission through a role assigned on the group tries to set the weight of a project, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group](#upserting_project-a-user-granted-update-on-the-group-may-not-set-a-project-weight) | rejected |

**upsert_user**

| scenario | verdict |
|---|---|
| [when the superadmin sets the weight of a user in the group, the record comes back carrying that weight and the rest of the settings are the group defaults](#upserting_user-the-superadmin-sets-a-user-weight) | answered |
| [when a user granted nothing tries to set the weight of a user, it is rejected for a lack of permission](#upserting_user-a-user-granted-nothing-may-not-set-a-user-weight) | rejected |
| [when a user granted the update permission through a role assigned on the group tries to set the weight of a user, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group](#upserting_user-a-user-granted-update-on-the-group-may-not-set-a-user-weight) | rejected |

### atomic_bulk_upsert_domain

<a id="atomic_bulk_upserting-the-superadmin-sets-several-domain-weights-at-once"></a>

#### [the-superadmin-sets-several-domain-weights-at-once](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting.py): pass

when the superadmin sets the weights of two domains at once, a count comes back saying that two were set

Given

- one resource group and 2 domains, and one superadmin
  - Domain home-1
  - Domain other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- FairShareAdapter.atomic_bulk_upsert_domain: user-1 sets the weights of 2 domains in resource-group-1 at once

Then

- a count comes back saying how many domains were set
  - upserted_count = 2

<a id="atomic_bulk_upserting-a-user-granted-nothing-may-not-set-several-domain-weights"></a>

#### [a-user-granted-nothing-may-not-set-several-domain-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting.py): pass

when a user granted nothing tries to set the weights of two domains at once, it is rejected for a lack of permission

Given

- one resource group and 2 domains, and one regular user
  - Domain home-1
  - Domain other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- FairShareAdapter.atomic_bulk_upsert_domain: user-1 sets the weights of 2 domains in resource-group-1 at once

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="atomic_bulk_upserting-a-user-granted-update-on-the-group-may-not-set-several-domain-weights"></a>

#### [a-user-granted-update-on-the-group-may-not-set-several-domain-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting.py): pass

when a user granted the update permission through a role assigned on the group tries to set the weights of two domains at once, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group

Given

- one resource group and 2 domains, and the regular user granted the UPDATE role in the resource group scope
  - Domain home-1
  - Domain other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- FairShareAdapter.atomic_bulk_upsert_domain: user-1 sets the weights of 2 domains in resource-group-1 at once

Then

- the call is rejected
  - rejected: NotEnoughPermission

### atomic_bulk_upsert_project

<a id="atomic_bulk_upserting_project-the-superadmin-sets-several-project-weights-at-once"></a>

#### [the-superadmin-sets-several-project-weights-at-once](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_project.py): pass

when the superadmin sets the weights of two projects at once, a count comes back saying that two were set

Given

- one resource group and 2 projects, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-2
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- FairShareAdapter.atomic_bulk_upsert_project: user-1 sets the weights of 2 projects in resource-group-1 at once

Then

- a count comes back saying how many projects were set
  - upserted_count = 2

<a id="atomic_bulk_upserting_project-a-user-granted-nothing-may-not-set-several-project-weights"></a>

#### [a-user-granted-nothing-may-not-set-several-project-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_project.py): pass

when a user granted nothing tries to set the weights of two projects at once, it is rejected for a lack of permission

Given

- one resource group and 2 projects, and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-2
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- FairShareAdapter.atomic_bulk_upsert_project: user-1 sets the weights of 2 projects in resource-group-1 at once

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="atomic_bulk_upserting_project-a-user-granted-update-on-the-group-may-not-set-several-project-weights"></a>

#### [a-user-granted-update-on-the-group-may-not-set-several-project-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_project.py): pass

when a user granted the update permission through a role assigned on the group tries to set the weights of two projects at once, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group

Given

- one resource group and 2 projects, and the regular user granted the UPDATE role in the resource group scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-2
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- FairShareAdapter.atomic_bulk_upsert_project: user-1 sets the weights of 2 projects in resource-group-1 at once

Then

- the call is rejected
  - rejected: NotEnoughPermission

### atomic_bulk_upsert_user

<a id="atomic_bulk_upserting_user-the-superadmin-sets-several-user-weights-at-once"></a>

#### [the-superadmin-sets-several-user-weights-at-once](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_user.py): pass

when the superadmin sets the weights of two users at once, a count comes back saying that two were set

Given

- one resource group, one project and 2 users, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Resource group resource-group-1: uses the fifo scheduler

When

- FairShareAdapter.atomic_bulk_upsert_user: user-3 sets the weights of 2 users in resource-group-1 at once

Then

- a count comes back saying how many users were set
  - upserted_count = 2

<a id="atomic_bulk_upserting_user-a-user-granted-nothing-may-not-set-several-user-weights"></a>

#### [a-user-granted-nothing-may-not-set-several-user-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_user.py): pass

when a user granted nothing tries to set the weights of two users at once, it is rejected for a lack of permission

Given

- one resource group, one project and 2 users, and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Resource group resource-group-1: uses the fifo scheduler

When

- FairShareAdapter.atomic_bulk_upsert_user: user-3 sets the weights of 2 users in resource-group-1 at once

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="atomic_bulk_upserting_user-a-user-granted-update-on-the-group-may-not-set-several-user-weights"></a>

#### [a-user-granted-update-on-the-group-may-not-set-several-user-weights](/tests/scenario/bai_scenario/manager/fair_share/test_atomic_bulk_upserting_user.py): pass

when a user granted the update permission through a role assigned on the group tries to set the weights of two users at once, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group

Given

- one resource group, one project and 2 users, and the regular user granted the UPDATE role in the resource group scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-3: holds Role group-role-1

When

- FairShareAdapter.atomic_bulk_upsert_user: user-3 sets the weights of 2 users in resource-group-1 at once

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get_domain

<a id="getting-a-user-granted-fair-share-read-on-the-group-reads-a-domain-fair-share"></a>

#### [a-user-granted-fair-share-read-on-the-group-reads-a-domain-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

when a user granted the fair share read role in the resource group scope reads the fair share of a domain, the values recorded in that group come back

Given

- one resource group and one domain whose fair share is recorded in it, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of domain home-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.get_domain: user-1 reads the fair share of domain home-1 in resource-group-1

Then

- the fair share record of that domain comes back with the seeded values
  - id = 'resource-group-1:home-1'
  - resource_group_name = 'resource-group-1'
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 14
  - spec.lookback_days = 56
  - spec.decay_unit_days = 2
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('0.5')
  - calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - calculation_snapshot.normalized_usage = Decimal('0.25')
  - calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - calculation_snapshot.last_calculated_at: the time this run wrote
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="getting-a-user-granted-only-fair-share-update-may-not-read-a-domain-fair-share"></a>

#### [a-user-granted-only-fair-share-update-may-not-read-a-domain-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

when a user granted only the fair share update role in the resource group scope reads the fair share of a domain, it is rejected for a lack of permission

Given

- one resource group and one domain whose fair share is recorded in it, and one regular user granted the fair share UPDATE role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share UPDATE role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: UPDATE allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of domain home-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.get_domain: user-1 reads the fair share of domain home-1 in resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="getting-reading-a-domain-fair-share-in-an-unknown-resource-group-fails"></a>

#### [reading-a-domain-fair-share-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

when a user granted the fair share read role reads the fair share of a domain under a resource group name nobody created, it fails because the resource group is not found

Given

- one resource group and one domain whose fair share is recorded in it, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of domain home-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.get_domain: user-1 reads the fair share of domain home-1 under a resource group name nobody created

Then

- the call is rejected
  - rejected: EntityNotFoundError

### get_project

<a id="getting-a-user-granted-fair-share-read-on-the-group-reads-a-project-fair-share"></a>

#### [a-user-granted-fair-share-read-on-the-group-reads-a-project-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

when a user granted the fair share read role in the resource group scope reads the fair share of a project, the values recorded in that group come back

Given

- one resource group and one project whose fair share is recorded in it, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.get_project: user-1 reads the fair share of project team-1 in resource-group-1

Then

- the fair share record of that project comes back with the seeded values
  - id: same as the resource group name and the ids of what the record is about, joined by colons
  - resource_group_name = 'resource-group-1'
  - project_id: same as the id of the seeded project
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 14
  - spec.lookback_days = 56
  - spec.decay_unit_days = 2
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('0.5')
  - calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - calculation_snapshot.normalized_usage = Decimal('0.25')
  - calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - calculation_snapshot.last_calculated_at: the time this run wrote
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="getting-a-user-granted-only-fair-share-update-may-not-read-a-project-fair-share"></a>

#### [a-user-granted-only-fair-share-update-may-not-read-a-project-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

when a user granted only the fair share update role in the resource group scope reads the fair share of a project, it is rejected for a lack of permission

Given

- one resource group and one project whose fair share is recorded in it, and one regular user granted the fair share UPDATE role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share UPDATE role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: UPDATE allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.get_project: user-1 reads the fair share of project team-1 in resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="getting-reading-a-project-fair-share-in-an-unknown-resource-group-fails"></a>

#### [reading-a-project-fair-share-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

when a user granted the fair share read role reads the fair share of a project under a resource group name nobody created, it fails because the resource group is not found

Given

- one resource group and one project whose fair share is recorded in it, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.get_project: user-1 reads the fair share of project team-1 under a resource group name nobody created

Then

- the call is rejected
  - rejected: EntityNotFoundError

### get_user

<a id="getting-a-user-granted-fair-share-read-on-the-group-reads-a-user-fair-share"></a>

#### [a-user-granted-fair-share-read-on-the-group-reads-a-user-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

when a user granted the fair share read role in the resource group scope reads the fair share of a user, the values recorded in that group come back

Given

- one resource group, one project and one project member whose fair share is recorded in the group, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user on the project member list
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user member-1: has their own keypair and personal project
    - regular user member-1: added to the member list of Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of user member-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.get_user: user-1 reads the fair share of user member-1 in resource-group-1

Then

- the fair share record of that member comes back with the seeded values
  - id: same as the resource group name and the ids of what the record is about, joined by colons
  - resource_group_name = 'resource-group-1'
  - user_uuid: same as the id of the seeded user
  - project_id: same as the id of the seeded project
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 14
  - spec.lookback_days = 56
  - spec.decay_unit_days = 2
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('0.5')
  - calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - calculation_snapshot.normalized_usage = Decimal('0.25')
  - calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - calculation_snapshot.last_calculated_at: the time this run wrote
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="getting-a-user-granted-only-fair-share-update-may-not-read-a-user-fair-share"></a>

#### [a-user-granted-only-fair-share-update-may-not-read-a-user-fair-share](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

when a user granted only the fair share update role in the resource group scope reads the fair share of a user, it is rejected for a lack of permission

Given

- one resource group, one project and one project member whose fair share is recorded in the group, and one regular user granted the fair share UPDATE role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user on the project member list
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user member-1: has their own keypair and personal project
    - regular user member-1: added to the member list of Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share UPDATE role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: UPDATE allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of user member-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.get_user: user-1 reads the fair share of user member-1 in resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="getting-reading-a-user-fair-share-in-an-unknown-resource-group-fails"></a>

#### [reading-a-user-fair-share-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_getting.py): pass

when a user granted the fair share read role reads the fair share of a user under a resource group name nobody created, it fails because the resource group is not found

Given

- one resource group, one project and one project member whose fair share is recorded in the group, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user on the project member list
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user member-1: has their own keypair and personal project
    - regular user member-1: added to the member list of Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of user member-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.get_user: user-1 reads the fair share of user member-1 under a resource group name nobody created

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search_domain

<a id="searching-the-superadmin-searches-the-domain-fair-shares-of-one-group"></a>

#### [the-superadmin-searches-the-domain-fair-shares-of-one-group](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

this search is gated by the global role. When the superadmin searches the domain fair shares with one resource group filter, by name, for one item, the two records of that group are counted, the record first by name comes back, and the record in the other group does not

Given

- the fair shares of two domains are recorded in one resource group and that of one of them in another resource group, and one superadmin
  - Domain home-1
  - Domain other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource group elsewhere-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Resource group resource-group-1: fair share of domain home-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group resource-group-1: fair share of domain other-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group elsewhere-1: fair share of domain home-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_domain: user-1 asks for one item from the front with the resource group resource-group-1 filter, in ascending domain name order

Then

- the two records of that group are counted and only the record of the domain first by name comes back
  - total_count = 2
  - items.count = 1
  - items[0].id = 'resource-group-1:home-1'
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: the time this run wrote
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="searching-a-regular-user-may-not-search-domain-fair-shares-across-groups"></a>

#### [a-regular-user-may-not-search-domain-fair-shares-across-groups](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

when a regular user searches the domain fair shares across resource groups, it is rejected for lacking the role

Given

- the fair shares of two domains are recorded in one resource group and that of one of them in another resource group, and one regular user
  - Domain home-1
  - Domain other-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource group elsewhere-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Resource group resource-group-1: fair share of domain home-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group resource-group-1: fair share of domain other-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group elsewhere-1: fair share of domain home-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_domain: user-1 asks for one item from the front with the resource group resource-group-1 filter, in ascending domain name order

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search_project

<a id="searching-the-superadmin-searches-the-project-fair-shares-of-one-group"></a>

#### [the-superadmin-searches-the-project-fair-shares-of-one-group](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

this search is gated by the global role. When the superadmin searches the project fair shares with one resource group filter, by name, for one item, the two records of that group are counted, the record first by name comes back, and the record in the other group does not

Given

- the fair shares of two projects are recorded in one resource group and that of one of them in another resource group, and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource group elsewhere-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project alpha-1
  - Project beta-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Resource group resource-group-1: fair share of project alpha-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group resource-group-1: fair share of project beta-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group elsewhere-1: fair share of project alpha-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_project: user-1 asks for one item from the front with the resource group resource-group-1 filter, in ascending project name order

Then

- the two records of that group are counted and only the record of the project first by name comes back
  - total_count = 2
  - items.count = 1
  - items[0].id: same as the resource group name and the ids of what the record is about, joined by colons
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].project_id: same as the id of the seeded project
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: the time this run wrote
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="searching-a-regular-user-may-not-search-project-fair-shares-across-groups"></a>

#### [a-regular-user-may-not-search-project-fair-shares-across-groups](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

when a regular user searches the project fair shares across resource groups, it is rejected for lacking the role

Given

- the fair shares of two projects are recorded in one resource group and that of one of them in another resource group, and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource group elsewhere-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project alpha-1
  - Project beta-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Resource group resource-group-1: fair share of project alpha-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group resource-group-1: fair share of project beta-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group elsewhere-1: fair share of project alpha-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_project: user-1 asks for one item from the front with the resource group resource-group-1 filter, in ascending project name order

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search_rg_domain

<a id="scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-domain-fair-shares"></a>

#### [a-user-granted-fair-share-read-on-the-group-searches-its-domain-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

when a user granted the fair share read role in the resource group scope searches the domain fair shares of that group with the active filter, by name, for the second item, the two active ones are counted and the second comes back; a domain recorded only in the other resource group comes back with this group's defaults and the inactive domain does not come back

Given

- two resource groups, two active domains and one inactive domain, the fair share of one active domain recorded only in the other resource group, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Domain other-1
  - Domain dormant-1: inactive
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource group elsewhere-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group elsewhere-1: fair share of domain other-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_rg_domain: user-1 searches in resource-group-1 the domains with the active filter, in ascending domain name order, skipping one item and asking for one

Then

- the two active domains are counted, and the second domain comes back with this group's defaults rather than the record in the other resource group
  - total_count = 2
  - items.count = 1
  - items[0].id = 'resource-group-1:other-1'
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].domain_name = 'other-1'
  - items[0].spec.weight = Decimal('1.0')
  - items[0].spec.uses_default = True
  - items[0].spec.half_life_days = 7
  - items[0].spec.lookback_days = 28
  - items[0].spec.decay_unit_days = 1
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('1')
  - items[0].calculation_snapshot.total_decayed_usage = []
  - items[0].calculation_snapshot.normalized_usage = Decimal('0')
  - items[0].calculation_snapshot.lookback_start: skipped: it depends on the date of the request
  - items[0].calculation_snapshot.lookback_end: skipped: it depends on the date of the request
  - items[0].calculation_snapshot.last_calculated_at: the time this run wrote
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="scoped_searching-a-user-granted-only-fair-share-update-may-not-search-domain-fair-shares"></a>

#### [a-user-granted-only-fair-share-update-may-not-search-domain-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

when a user granted only the fair share update role in the resource group scope searches the domain fair shares of that group, it is rejected for a lack of permission

Given

- two resource groups, two active domains and one inactive domain, the fair share of one active domain recorded only in the other resource group, and one regular user granted the fair share UPDATE role in the resource group scope
  - Domain home-1
  - Domain other-1
  - Domain dormant-1: inactive
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource group elsewhere-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share UPDATE role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: UPDATE allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group elsewhere-1: fair share of domain other-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_rg_domain: user-1 searches in resource-group-1 the domains with the active filter, in ascending domain name order, skipping one item and asking for one

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-searching-domain-fair-shares-in-an-unknown-resource-group-fails"></a>

#### [searching-domain-fair-shares-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

when a user granted the fair share read role searches the domain fair shares under a resource group name nobody created, it fails because the resource group is not found

Given

- two resource groups, two active domains and one inactive domain, the fair share of one active domain recorded only in the other resource group, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Domain other-1
  - Domain dormant-1: inactive
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource group elsewhere-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group elsewhere-1: fair share of domain other-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_rg_domain: user-1 searches under a resource group name nobody created the domains with the active filter, in ascending domain name order, skipping one item and asking for one

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search_rg_project

<a id="scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-project-fair-shares"></a>

#### [a-user-granted-fair-share-read-on-the-group-searches-its-project-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

when a user granted the fair share read role in the resource group scope searches the project fair shares of that group with the active filter, by name, for the second item, the two active ones are counted and the second comes back; the project of another domain and the inactive project do not come back

Given

- one resource group, two active projects and one inactive project in the domain, one project in another domain, the fair share of one active project recorded in the group, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Domain far-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project alpha-1
  - Project beta-1
  - Project dormant-1: inactive
  - Project aside-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of project beta-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_rg_project: user-1 searches in resource-group-1 the projects of domain home-1 with the active filter, in ascending project name order, skipping one item and asking for one

Then

- the two active projects of that domain are counted, and the second one comes back with its recorded fair share
  - total_count = 2
  - items.count = 1
  - items[0].id: same as the resource group name and the ids of what the record is about, joined by colons
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].project_id: same as the id of the seeded project
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: the time this run wrote
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="scoped_searching-a-user-granted-only-fair-share-update-may-not-search-project-fair-shares"></a>

#### [a-user-granted-only-fair-share-update-may-not-search-project-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

when a user granted only the fair share update role in the resource group scope searches the project fair shares of that group, it is rejected for a lack of permission

Given

- one resource group, two active projects and one inactive project in the domain, one project in another domain, the fair share of one active project recorded in the group, and one regular user granted the fair share UPDATE role in the resource group scope
  - Domain home-1
  - Domain far-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project alpha-1
  - Project beta-1
  - Project dormant-1: inactive
  - Project aside-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share UPDATE role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: UPDATE allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of project beta-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_rg_project: user-1 searches in resource-group-1 the projects of domain home-1 with the active filter, in ascending project name order, skipping one item and asking for one

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-searching-project-fair-shares-in-an-unknown-resource-group-fails"></a>

#### [searching-project-fair-shares-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

when a user granted the fair share read role searches the project fair shares under a resource group name nobody created, it fails because the resource group is not found

Given

- one resource group, two active projects and one inactive project in the domain, one project in another domain, the fair share of one active project recorded in the group, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Domain far-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project alpha-1
  - Project beta-1
  - Project dormant-1: inactive
  - Project aside-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of project beta-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_rg_project: user-1 searches under a resource group name nobody created the projects of domain home-1 with the active filter, in ascending project name order, skipping one item and asking for one

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search_rg_user

<a id="scoped_searching-a-user-granted-fair-share-read-on-the-group-searches-its-user-fair-shares"></a>

#### [a-user-granted-fair-share-read-on-the-group-searches-its-user-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

when a user granted the fair share read role in the resource group scope searches the user fair shares of that group with the active filter, by name, for the second item, the two active ones are counted and the second comes back; the member of another project and the inactive member do not come back

Given

- one resource group, two active members and one inactive member of the project, one member of another project, the fair share of one active member recorded in the group, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project aside-1
  - Prepare one user on the project member list
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user alpha-1: has their own keypair and personal project
    - regular user alpha-1: added to the member list of Project team-1
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user beta-1: has their own keypair and personal project
    - regular user beta-1: added to the member list of Project team-1
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user dormant-1: status inactive, has their own keypair and personal project
    - regular user dormant-1: added to the member list of Project team-1
    - User resource policy user-policy-4: up to 10 folders per user
    - Keypair policy keypair-policy-4: up to 5 concurrent sessions
    - regular user outsider-1: has their own keypair and personal project
    - regular user outsider-1: added to the member list of Project aside-1
  - Prepare one user in the domain
    - User resource policy user-policy-5: up to 10 folders per user
    - Keypair policy keypair-policy-5: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of user beta-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_rg_user: user-1 searches in resource-group-1 the members of project team-1 with the active filter, in ascending username order, skipping one item and asking for one

Then

- the two active members of that project are counted, and the second one comes back with their recorded fair share
  - total_count = 2
  - items.count = 1
  - items[0].id: same as the resource group name and the ids of what the record is about, joined by colons
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].user_uuid: same as the id of the seeded user
  - items[0].project_id: same as the id of the seeded project
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: the time this run wrote
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="scoped_searching-a-user-granted-only-fair-share-update-may-not-search-user-fair-shares"></a>

#### [a-user-granted-only-fair-share-update-may-not-search-user-fair-shares](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

when a user granted only the fair share update role in the resource group scope searches the user fair shares of that group, it is rejected for a lack of permission

Given

- one resource group, two active members and one inactive member of the project, one member of another project, the fair share of one active member recorded in the group, and one regular user granted the fair share UPDATE role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project aside-1
  - Prepare one user on the project member list
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user alpha-1: has their own keypair and personal project
    - regular user alpha-1: added to the member list of Project team-1
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user beta-1: has their own keypair and personal project
    - regular user beta-1: added to the member list of Project team-1
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user dormant-1: status inactive, has their own keypair and personal project
    - regular user dormant-1: added to the member list of Project team-1
    - User resource policy user-policy-4: up to 10 folders per user
    - Keypair policy keypair-policy-4: up to 5 concurrent sessions
    - regular user outsider-1: has their own keypair and personal project
    - regular user outsider-1: added to the member list of Project aside-1
  - Prepare one user in the domain
    - User resource policy user-policy-5: up to 10 folders per user
    - Keypair policy keypair-policy-5: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share UPDATE role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: UPDATE allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of user beta-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_rg_user: user-1 searches in resource-group-1 the members of project team-1 with the active filter, in ascending username order, skipping one item and asking for one

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-searching-user-fair-shares-in-an-unknown-resource-group-fails"></a>

#### [searching-user-fair-shares-in-an-unknown-resource-group-fails](/tests/scenario/bai_scenario/manager/fair_share/test_scoped_searching.py): pass

when a user granted the fair share read role searches the user fair shares under a resource group name nobody created, it fails because the resource group is not found

Given

- one resource group, two active members and one inactive member of the project, one member of another project, the fair share of one active member recorded in the group, and one regular user granted the fair share READ role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project aside-1
  - Prepare one user on the project member list
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user alpha-1: has their own keypair and personal project
    - regular user alpha-1: added to the member list of Project team-1
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user beta-1: has their own keypair and personal project
    - regular user beta-1: added to the member list of Project team-1
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user dormant-1: status inactive, has their own keypair and personal project
    - regular user dormant-1: added to the member list of Project team-1
    - User resource policy user-policy-4: up to 10 folders per user
    - Keypair policy keypair-policy-4: up to 5 concurrent sessions
    - regular user outsider-1: has their own keypair and personal project
    - regular user outsider-1: added to the member list of Project aside-1
  - Prepare one user in the domain
    - User resource policy user-policy-5: up to 10 folders per user
    - Keypair policy keypair-policy-5: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the fair share READ role in the resource group scope
    - Role fair-share-role-1: applies only within the scope it is granted in
    - Role fair-share-role-1: READ allowed on every global
    - regular user user-1: holds Role fair-share-role-1
  - Resource group resource-group-1: fair share of user beta-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_rg_user: user-1 searches under a resource group name nobody created the members of project team-1 with the active filter, in ascending username order, skipping one item and asking for one

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search_user

<a id="searching-the-superadmin-searches-the-user-fair-shares-of-one-group"></a>

#### [the-superadmin-searches-the-user-fair-shares-of-one-group](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

this search is gated by the global role. When the superadmin searches the user fair shares with one resource group filter, by name, for one item, the two records of that group are counted, the record first by name comes back, and the record in the other group does not

Given

- the fair shares of two project members are recorded in one resource group and that of one of them in another resource group, and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource group elsewhere-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user on the project member list
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user alpha-1: has their own keypair and personal project
    - regular user alpha-1: added to the member list of Project team-1
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user beta-1: has their own keypair and personal project
    - regular user beta-1: added to the member list of Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - Resource group resource-group-1: fair share of user alpha-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group resource-group-1: fair share of user beta-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group elsewhere-1: fair share of user alpha-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_user: user-1 asks for one item from the front with the resource group resource-group-1 filter, in ascending username order

Then

- the two records of that group are counted and only the record of the member first by username comes back
  - total_count = 2
  - items.count = 1
  - items[0].id: same as the resource group name and the ids of what the record is about, joined by colons
  - items[0].resource_group_name = 'resource-group-1'
  - items[0].user_uuid: same as the id of the seeded user
  - items[0].project_id: same as the id of the seeded project
  - items[0].domain_name = 'home-1'
  - items[0].spec.weight = Decimal('2.5')
  - items[0].spec.uses_default = False
  - items[0].spec.half_life_days = 14
  - items[0].spec.lookback_days = 56
  - items[0].spec.decay_unit_days = 2
  - items[0].spec.resource_weights = []
  - items[0].calculation_snapshot.fair_share_factor = Decimal('0.5')
  - items[0].calculation_snapshot.total_decayed_usage = [('cpu', Decimal('4'))]
  - items[0].calculation_snapshot.normalized_usage = Decimal('0.25')
  - items[0].calculation_snapshot.lookback_start = datetime.date(2026, 1, 1)
  - items[0].calculation_snapshot.lookback_end = datetime.date(2026, 2, 26)
  - items[0].calculation_snapshot.last_calculated_at: the time this run wrote
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote

<a id="searching-a-regular-user-may-not-search-user-fair-shares-across-groups"></a>

#### [a-regular-user-may-not-search-user-fair-shares-across-groups](/tests/scenario/bai_scenario/manager/fair_share/test_searching.py): pass

when a regular user searches the user fair shares across resource groups, it is rejected for lacking the role

Given

- the fair shares of two project members are recorded in one resource group and that of one of them in another resource group, and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Resource group elsewhere-1: uses the fifo scheduler
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user on the project member list
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user alpha-1: has their own keypair and personal project
    - regular user alpha-1: added to the member list of Project team-1
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user beta-1: has their own keypair and personal project
    - regular user beta-1: added to the member list of Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Resource group resource-group-1: fair share of user alpha-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group resource-group-1: fair share of user beta-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5
  - Resource group elsewhere-1: fair share of user alpha-1 in project team-1: weight 2.5, half life 14 days, lookback 56 days, decay unit 2 days, calculated factor 0.5

When

- FairShareAdapter.search_user: user-1 asks for one item from the front with the resource group resource-group-1 filter, in ascending username order

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### upsert_domain

<a id="upserting-the-superadmin-sets-a-domain-weight"></a>

#### [the-superadmin-sets-a-domain-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting.py): pass

when the superadmin sets the weight of a domain in the group, the record comes back carrying that weight and the rest of the settings are the group defaults

Given

- one resource group and 1 domains, and one superadmin
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- FairShareAdapter.upsert_domain: user-1 sets the weight of home-1 in resource-group-1

Then

- the record comes back carrying the weight just set and the rest of the settings are the group defaults
  - id: skipped: the database generates it
  - resource_group_name = 'resource-group-1'
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 7
  - spec.lookback_days = 28
  - spec.decay_unit_days = 1
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('1')
  - calculation_snapshot.total_decayed_usage = []
  - calculation_snapshot.normalized_usage = Decimal('0')
  - calculation_snapshot.lookback_start: skipped: it depends on the date written
  - calculation_snapshot.lookback_end: skipped: it depends on the date written
  - calculation_snapshot.last_calculated_at: the time this run wrote
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="upserting-a-user-granted-nothing-may-not-set-a-domain-weight"></a>

#### [a-user-granted-nothing-may-not-set-a-domain-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting.py): pass

when a user granted nothing tries to set the weight of a domain, it is rejected for a lack of permission

Given

- one resource group and 1 domains, and one regular user
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- FairShareAdapter.upsert_domain: user-1 sets the weight of home-1 in resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="upserting-a-user-granted-update-on-the-group-may-not-set-a-domain-weight"></a>

#### [a-user-granted-update-on-the-group-may-not-set-a-domain-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting.py): pass

when a user granted the update permission through a role assigned on the group tries to set the weight of a domain, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group

Given

- one resource group and 1 domains, and the regular user granted the UPDATE role in the resource group scope
  - Domain home-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- FairShareAdapter.upsert_domain: user-1 sets the weight of home-1 in resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### upsert_project

<a id="upserting_project-the-superadmin-sets-a-project-weight"></a>

#### [the-superadmin-sets-a-project-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_project.py): pass

when the superadmin sets the weight of a project in the group, the record comes back carrying that weight and the rest of the settings are the group defaults

Given

- one resource group and 1 projects, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- FairShareAdapter.upsert_project: user-1 sets the weight of the first project in resource-group-1

Then

- the record comes back carrying the weight just set and the rest of the settings are the group defaults
  - id: same as the group name joined with the id of the project seeded in advance
  - resource_group_name = 'resource-group-1'
  - project_id: same as the id of the project seeded in advance
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 7
  - spec.lookback_days = 28
  - spec.decay_unit_days = 1
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('1')
  - calculation_snapshot.total_decayed_usage = []
  - calculation_snapshot.normalized_usage = Decimal('0')
  - calculation_snapshot.lookback_start: skipped: it depends on the date written
  - calculation_snapshot.lookback_end: skipped: it depends on the date written
  - calculation_snapshot.last_calculated_at: the time this run wrote
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="upserting_project-a-user-granted-nothing-may-not-set-a-project-weight"></a>

#### [a-user-granted-nothing-may-not-set-a-project-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_project.py): pass

when a user granted nothing tries to set the weight of a project, it is rejected for a lack of permission

Given

- one resource group and 1 projects, and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- FairShareAdapter.upsert_project: user-1 sets the weight of the first project in resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="upserting_project-a-user-granted-update-on-the-group-may-not-set-a-project-weight"></a>

#### [a-user-granted-update-on-the-group-may-not-set-a-project-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_project.py): pass

when a user granted the update permission through a role assigned on the group tries to set the weight of a project, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group

Given

- one resource group and 1 projects, and the regular user granted the UPDATE role in the resource group scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-1: holds Role group-role-1

When

- FairShareAdapter.upsert_project: user-1 sets the weight of the first project in resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### upsert_user

<a id="upserting_user-the-superadmin-sets-a-user-weight"></a>

#### [the-superadmin-sets-a-user-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_user.py): pass

when the superadmin sets the weight of a user in the group, the record comes back carrying that weight and the rest of the settings are the group defaults

Given

- one resource group, one project and 1 users, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - superadmin user-2: has their own keypair and personal project
  - Resource group resource-group-1: uses the fifo scheduler

When

- FairShareAdapter.upsert_user: user-2 sets the weight of the first user in resource-group-1

Then

- the record comes back carrying the weight just set and the rest of the settings are the group defaults
  - id: same as the group name joined with the ids of the user and the project seeded in advance
  - resource_group_name = 'resource-group-1'
  - user_uuid: same as the id of the user seeded in advance
  - project_id: same as the id of the project seeded in advance
  - domain_name = 'home-1'
  - spec.weight = Decimal('2.5')
  - spec.uses_default = False
  - spec.half_life_days = 7
  - spec.lookback_days = 28
  - spec.decay_unit_days = 1
  - spec.resource_weights = []
  - calculation_snapshot.fair_share_factor = Decimal('1')
  - calculation_snapshot.total_decayed_usage = []
  - calculation_snapshot.normalized_usage = Decimal('0')
  - calculation_snapshot.lookback_start: skipped: it depends on the date written
  - calculation_snapshot.lookback_end: skipped: it depends on the date written
  - calculation_snapshot.last_calculated_at: the time this run wrote
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="upserting_user-a-user-granted-nothing-may-not-set-a-user-weight"></a>

#### [a-user-granted-nothing-may-not-set-a-user-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_user.py): pass

when a user granted nothing tries to set the weight of a user, it is rejected for a lack of permission

Given

- one resource group, one project and 1 users, and one regular user
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Resource group resource-group-1: uses the fifo scheduler

When

- FairShareAdapter.upsert_user: user-2 sets the weight of the first user in resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="upserting_user-a-user-granted-update-on-the-group-may-not-set-a-user-weight"></a>

#### [a-user-granted-update-on-the-group-may-not-set-a-user-weight](/tests/scenario/bai_scenario/manager/fair_share/test_upserting_user.py): pass

when a user granted the update permission through a role assigned on the group tries to set the weight of a user, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group

Given

- one resource group, one project and 1 users, and the regular user granted the UPDATE role in the resource group scope
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Resource group resource-group-1: uses the fifo scheduler
  - Prepare a user granted the UPDATE role in the resource group scope
    - Role group-role-1: applies only within the scope it is granted in
    - Role group-role-1: UPDATE allowed on every resource_group
    - regular user user-2: holds Role group-role-1

When

- FairShareAdapter.upsert_user: user-2 sets the weight of the first user in resource-group-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

