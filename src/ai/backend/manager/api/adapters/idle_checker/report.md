## idle_checker

[background](/src/ai/backend/manager/api/adapters/idle_checker/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/idle_checker/adapter.py)

Scenario: incomplete 6 / 6

- built from ops (4)
  - admin_partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - admin_purge: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - admin_search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- direct implementation (2)
  - admin_create: success absent · rejection absent (global_scope): SCENARIO-GAP
  - admin_update: success absent · rejection absent (global_scope): SCENARIO-GAP

**admin_partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several idle checkers in one call, none is deleted and all come back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-checkers) | answered |
| [when the superadmin purges two idle checkers and a missing id in one call, the two come back as deleted idle checkers and the missing id comes back in the failed list because no target answers to it](#partial_bulk_purging-the-superadmin-purges-several-and-is-answered-for-the-missing-one) | answered |

### admin_partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-checkers"></a>

#### [a-user-granted-nothing-purges-none-of-several-checkers](/tests/scenario/bai_scenario/manager/idle_checker/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several idle checkers in one call, none is deleted and all come back in the failed list for lack of permission

Given

- 2 idle checkers and one regular user
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Idle checker idle-checker-2: ends interactive sessions after 3600 seconds
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- IdleCheckerAdapter.admin_partial_bulk_purge: user-1 purges 2 idle checkers in one call

Then

- no checker is deleted and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the checker seeded in advance number 1
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the checker seeded in advance number 2
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-the-superadmin-purges-several-and-is-answered-for-the-missing-one"></a>

#### [the-superadmin-purges-several-and-is-answered-for-the-missing-one](/tests/scenario/bai_scenario/manager/idle_checker/test_partial_bulk_purging.py): pass

when the superadmin purges two idle checkers and a missing id in one call, the two come back as deleted idle checkers and the missing id comes back in the failed list because no target answers to it

Given

- 2 idle checkers and one superadmin
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Idle checker idle-checker-2: ends interactive sessions after 3600 seconds
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- IdleCheckerAdapter.admin_partial_bulk_purge: user-1 purges 2 idle checkers and a missing id in one call

Then

- every checker seeded in advance comes back deleted and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - failed count = 1
  - successes[0]: same as the whole checker seeded in advance number 1
  - successes[1]: same as the whole checker seeded in advance number 2
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

