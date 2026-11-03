## idle_checker_assignment

[background](/src/ai/backend/manager/api/adapters/idle_checker_assignment/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/idle_checker_assignment/adapter.py)

Scenario: incomplete 7 / 7

- direct implementation (7)
  - admin_create: success absent · rejection absent (relation): SCENARIO-GAP
  - admin_search: success absent · rejection absent (global_scope): SCENARIO-GAP
  - partial_bulk_purge: success present 2 · rejection absent (relation): SCENARIO-GAP
  - partial_bulk_update: success present 2 · rejection absent (relation): SCENARIO-GAP
  - purge: success absent · rejection absent (relation): SCENARIO-GAP
  - scoped_search: success absent · rejection absent (scope): SCENARIO-GAP
  - update: success absent · rejection absent (relation): SCENARIO-GAP

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several assignments in one call, none is deleted and all come back in the failed list because they cannot be found](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-assignments) | answered |
| [when the superadmin purges two assignments and a missing id in one call, the two come back as they were before the purge and the missing id comes back in the failed list because no target answers to it](#partial_bulk_purging-the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to disable several assignments in one call, none is disabled and all come back in the failed list because they cannot be found](#partial_bulk_editing-a-user-granted-nothing-disables-none-of-several-assignments) | answered |
| [when the superadmin disables several assignments in one call, all come back as disabled assignments and nothing failed](#partial_bulk_editing-the-superadmin-disables-several-assignments-at-once) | answered |

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-assignments"></a>

#### [a-user-granted-nothing-purges-none-of-several-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several assignments in one call, none is deleted and all come back in the failed list because they cannot be found

Given

- one idle checker enabled on 2 domains and one regular user
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Domain scope-1
  - Domain scope-2
  - Domain scope-1 has enabled Idle checker idle-checker-1
  - Domain scope-2 has enabled Idle checker idle-checker-1
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

When

- IdleCheckerAssignmentAdapter.partial_bulk_purge: user-2 purges 2 assignments in one call

Then

- no assignment is processed and every requested assignment comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id put in the request number 1
  - failed[0].message: a reason containing 'Cannot resolve the given idle_checker key'
  - failed[1].id: same as the id put in the request number 2
  - failed[1].message: a reason containing 'Cannot resolve the given idle_checker key'

<a id="partial_bulk_purging-the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one"></a>

#### [the-superadmin-purges-several-assignments-and-is-answered-for-the-missing-one](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_purging.py): pass

when the superadmin purges two assignments and a missing id in one call, the two come back as they were before the purge and the missing id comes back in the failed list because no target answers to it

Given

- one idle checker enabled on 2 domains and one superadmin
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Domain scope-1
  - Domain scope-2
  - Domain scope-1 has enabled Idle checker idle-checker-1
  - Domain scope-2 has enabled Idle checker idle-checker-1
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- IdleCheckerAssignmentAdapter.partial_bulk_purge: user-1 purges 2 assignments and a missing id in one call

Then

- every requested assignment comes back enabled and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: same as the id put in the request number 1
  - successes[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[0].scope_id: same as the domain seeded in advance number 1
  - successes[0].idle_checker_id: same as the checker seeded in advance
  - successes[0].enabled = True
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the id put in the request number 2
  - successes[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[1].scope_id: same as the domain seeded in advance number 2
  - successes[1].idle_checker_id: same as the checker seeded in advance
  - successes[1].enabled = True
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'No such idle checker assignment'

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-disables-none-of-several-assignments"></a>

#### [a-user-granted-nothing-disables-none-of-several-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_editing.py): pass

when a user granted nothing tries to disable several assignments in one call, none is disabled and all come back in the failed list because they cannot be found

Given

- one idle checker enabled on 2 domains and one regular user
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Domain scope-1
  - Domain scope-2
  - Domain scope-1 has enabled Idle checker idle-checker-1
  - Domain scope-2 has enabled Idle checker idle-checker-1
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

When

- IdleCheckerAssignmentAdapter.partial_bulk_update: user-2 disables 2 assignments in one call

Then

- no assignment is processed and every requested assignment comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id put in the request number 1
  - failed[0].message: a reason containing 'Cannot resolve the given idle_checker key'
  - failed[1].id: same as the id put in the request number 2
  - failed[1].message: a reason containing 'Cannot resolve the given idle_checker key'

<a id="partial_bulk_editing-the-superadmin-disables-several-assignments-at-once"></a>

#### [the-superadmin-disables-several-assignments-at-once](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_partial_bulk_editing.py): pass

when the superadmin disables several assignments in one call, all come back as disabled assignments and nothing failed

Given

- one idle checker enabled on 2 domains and one superadmin
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Domain scope-1
  - Domain scope-2
  - Domain scope-1 has enabled Idle checker idle-checker-1
  - Domain scope-2 has enabled Idle checker idle-checker-1
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- IdleCheckerAssignmentAdapter.partial_bulk_update: user-1 disables 2 assignments in one call

Then

- every requested assignment comes back disabled and nothing failed
  - successes count = 2
  - successes[0].id: same as the id put in the request number 1
  - successes[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[0].scope_id: same as the domain seeded in advance number 1
  - successes[0].idle_checker_id: same as the checker seeded in advance
  - successes[0].enabled = False
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the id put in the request number 2
  - successes[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - successes[1].scope_id: same as the domain seeded in advance number 2
  - successes[1].idle_checker_id: same as the checker seeded in advance
  - successes[1].enabled = False
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

