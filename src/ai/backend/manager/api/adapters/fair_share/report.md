## fair_share

[background](/src/ai/backend/manager/api/adapters/fair_share/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/fair_share/adapter.py)

Scenario: incomplete 13 / 15

- direct implementation (15)
  - atomic_bulk_upsert_domain: success present 1 · rejection present 2 (scope)
  - atomic_bulk_upsert_project: success absent · rejection absent (scope): SCENARIO-GAP
  - atomic_bulk_upsert_user: success absent · rejection absent (scope): SCENARIO-GAP
  - get_domain: success absent · rejection absent (scope): SCENARIO-GAP
  - get_project: success absent · rejection absent (scope): SCENARIO-GAP
  - get_user: success absent · rejection absent (scope): SCENARIO-GAP
  - search_domain: success absent · rejection absent (global_scope): SCENARIO-GAP
  - search_project: success absent · rejection absent (global_scope): SCENARIO-GAP
  - search_rg_domain: success absent · rejection absent (scope): SCENARIO-GAP
  - search_rg_project: success absent · rejection absent (scope): SCENARIO-GAP
  - search_rg_user: success absent · rejection absent (scope): SCENARIO-GAP
  - search_user: success absent · rejection absent (global_scope): SCENARIO-GAP
  - upsert_domain: success present 1 · rejection present 2 (scope)
  - upsert_project: success absent · rejection absent (scope): SCENARIO-GAP
  - upsert_user: success absent · rejection absent (scope): SCENARIO-GAP

**atomic_bulk_upsert_domain**

| scenario | verdict |
|---|---|
| [when the superadmin sets the weights of two domains at once, a count comes back saying that two were set](#atomic_bulk_upserting-the-superadmin-sets-several-domain-weights-at-once) | answered |
| [when a user granted nothing tries to set the weights of two domains at once, it is rejected for a lack of permission](#atomic_bulk_upserting-a-user-granted-nothing-may-not-set-several-domain-weights) | rejected |
| [when a user granted the update permission through a role assigned on the group tries to set the weights of two domains at once, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group](#atomic_bulk_upserting-a-user-granted-update-on-the-group-may-not-set-several-domain-weights) | rejected |

**upsert_domain**

| scenario | verdict |
|---|---|
| [when the superadmin sets the weight of a domain in the group, the record comes back carrying that weight and the rest of the settings are the group defaults](#upserting-the-superadmin-sets-a-domain-weight) | answered |
| [when a user granted nothing tries to set the weight of a domain, it is rejected for a lack of permission](#upserting-a-user-granted-nothing-may-not-set-a-domain-weight) | rejected |
| [when a user granted the update permission through a role assigned on the group tries to set the weight of a domain, it is rejected for a lack of permission. A weight write checks permission against the global target, not the group](#upserting-a-user-granted-update-on-the-group-may-not-set-a-domain-weight) | rejected |

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

