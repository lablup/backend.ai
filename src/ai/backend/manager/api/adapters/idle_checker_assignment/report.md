## idle_checker_assignment

[background](/src/ai/backend/manager/api/adapters/idle_checker_assignment/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/idle_checker_assignment/adapter.py)

Scenario: incomplete 2 / 7

- direct implementation (7)
  - admin_create: success present 1 · rejection present 1 (relation)
  - admin_search: success present 1 · rejection present 1 (global_scope)
  - partial_bulk_purge: success present 2 · rejection absent (relation): SCENARIO-GAP
  - partial_bulk_update: success present 2 · rejection absent (relation): SCENARIO-GAP
  - purge: success present 1 · rejection present 1 (relation)
  - scoped_search: success present 1 · rejection present 1 (scope)
  - update: success present 1 · rejection present 1 (relation)

**admin_create**

| scenario | verdict |
|---|---|
| [when the superadmin enables a checker on a domain, the assignment between the checker and the domain the request named comes back enabled](#creating-the-superadmin-enables-an-idle-checker-on-a-domain) | answered |
| [when a checker and a domain exist and a user granted nothing enables the checker on the domain, it is rejected for lack of permission](#creating-an-assignment-created-by-a-user-granted-nothing-is-refused) | rejected |

**admin_search**

| scenario | verdict |
|---|---|
| [the operation is gated by the global role, so when the superadmin searches with the checker as the filter, the time order and a page size in one request, the assignments of that checker are all counted once and come back whole](#searching-the-superadmin-searches-idle-checker-assignments) | answered |
| [when two assignments exist and a user granted nothing searches, it is rejected for lack of role](#searching-an-assignment-search-by-a-user-granted-nothing-is-refused) | rejected |

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

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges one assignment, the purge is answered with the id of the assignment put in the request](#retiring-the-superadmin-purges-an-idle-checker-assignment) | answered |
| [when two assignments exist and a user granted nothing tries to purge one, it is rejected because the target cannot be resolved](#retiring-an-assignment-purge-by-a-user-granted-nothing-is-refused) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when the superadmin searches scoped to two domains, with the checker as the filter, the time order and a page size in one request, only the assignments of those domains are counted once and come back whole](#scoped_searching-the-superadmin-scoped-searches-idle-checker-assignments) | answered |
| [when two assignments exist and a user granted nothing searches with a scope, it is rejected for lack of permission](#scoped_searching-a-scoped-assignment-search-by-a-user-granted-nothing-is-refused) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin disables an assignment, it comes back disabled](#updating-the-superadmin-disables-an-idle-checker-assignment) | answered |
| [when two assignments exist and a user granted nothing tries to disable one, it is rejected because the target cannot be resolved](#updating-an-assignment-update-by-a-user-granted-nothing-is-refused) | rejected |

### admin_create

<a id="creating-the-superadmin-enables-an-idle-checker-on-a-domain"></a>

#### [the-superadmin-enables-an-idle-checker-on-a-domain](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_creating.py): pass

when the superadmin enables a checker on a domain, the assignment between the checker and the domain the request named comes back enabled

Given

- one idle checker, one domain and one superadmin
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Domain scope-1
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- IdleCheckerAssignmentAdapter.admin_create: user-1 enables the checker on the domain scope-1

Then

- the assignment between the checker and the domain the request named comes back enabled
  - id: skipped: the database generates it
  - scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - scope_id: same as the domain seeded in advance
  - idle_checker_id: same as the checker seeded in advance
  - enabled = True
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-an-assignment-created-by-a-user-granted-nothing-is-refused"></a>

#### [an-assignment-created-by-a-user-granted-nothing-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_creating.py): pass

when a checker and a domain exist and a user granted nothing enables the checker on the domain, it is rejected for lack of permission

Given

- one idle checker, one domain and one regular user
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Domain scope-1
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- IdleCheckerAssignmentAdapter.admin_create: user-1 enables the checker on the domain scope-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### admin_search

<a id="searching-the-superadmin-searches-idle-checker-assignments"></a>

#### [the-superadmin-searches-idle-checker-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_searching.py): pass

the operation is gated by the global role, so when the superadmin searches with the checker as the filter, the time order and a page size in one request, the assignments of that checker are all counted once and come back whole

Given

- one idle checker enabled on 2 domains and one superadmin, and another checker is enabled on the first domain
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Domain scope-1
  - Domain scope-2
  - Domain scope-1 has enabled Idle checker idle-checker-1
  - Domain scope-2 has enabled Idle checker idle-checker-1
  - Idle checker idle-checker-2: ends interactive sessions after 3600 seconds
  - Domain scope-1 has enabled Idle checker idle-checker-2
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- IdleCheckerAssignmentAdapter.admin_search: user-1 reads with the checker as the filter, the time order and a page size in one request

Then

- the filter excludes the other checker's assignment, so every assignment seeded in advance is counted once and each comes back whole
  - total_count = 2
  - items count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].id: same as the seeded assignment in the order read by id
  - items[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - items[0].scope_id: same as the domain seeded in advance
  - items[0].idle_checker_id: same as the checker seeded in advance
  - items[0].enabled = True
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: same as the seeded assignment in the order read by id
  - items[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - items[1].scope_id: same as the domain seeded in advance
  - items[1].idle_checker_id: same as the checker seeded in advance
  - items[1].enabled = True
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote

<a id="searching-an-assignment-search-by-a-user-granted-nothing-is-refused"></a>

#### [an-assignment-search-by-a-user-granted-nothing-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_searching.py): pass

when two assignments exist and a user granted nothing searches, it is rejected for lack of role

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

- IdleCheckerAssignmentAdapter.admin_search: user-2 reads with the checker as the filter, the time order and a page size in one request

Then

- the call is rejected
  - rejected: InsufficientPrivilege

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

### purge

<a id="retiring-the-superadmin-purges-an-idle-checker-assignment"></a>

#### [the-superadmin-purges-an-idle-checker-assignment](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_retiring.py): pass

when the superadmin purges one assignment, the purge is answered with the id of the assignment put in the request

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

- IdleCheckerAssignmentAdapter.purge: user-1 purges the assignment of the domain scope-1

Then

- the purge is answered with the id of the assignment put in the request
  - id: same as the assignment put in the request

<a id="retiring-an-assignment-purge-by-a-user-granted-nothing-is-refused"></a>

#### [an-assignment-purge-by-a-user-granted-nothing-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_retiring.py): pass

when two assignments exist and a user granted nothing tries to purge one, it is rejected because the target cannot be resolved

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

- IdleCheckerAssignmentAdapter.purge: user-2 purges the assignment of the domain scope-1

Then

- the call is rejected
  - rejected: GenericBadRequest

### scoped_search

<a id="scoped_searching-the-superadmin-scoped-searches-idle-checker-assignments"></a>

#### [the-superadmin-scoped-searches-idle-checker-assignments](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_scoped_searching.py): pass

when the superadmin searches scoped to two domains, with the checker as the filter, the time order and a page size in one request, only the assignments of those domains are counted once and come back whole

Given

- one idle checker enabled on 3 domains and one superadmin, and another checker is enabled on the first domain
  - Idle checker idle-checker-1: ends interactive sessions after 3600 seconds
  - Domain scope-1
  - Domain scope-2
  - Domain scope-3
  - Domain scope-1 has enabled Idle checker idle-checker-1
  - Domain scope-2 has enabled Idle checker idle-checker-1
  - Domain scope-3 has enabled Idle checker idle-checker-1
  - Idle checker idle-checker-2: ends interactive sessions after 3600 seconds
  - Domain scope-1 has enabled Idle checker idle-checker-2
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- IdleCheckerAssignmentAdapter.scoped_search: user-1 reads scoped to the domains scope-1 and scope-2, with the checker as the filter

Then

- only the assignments of the domains named in the scope are counted once and each comes back whole, and the assignment of the domain outside the scope does not come back
  - total_count = 2
  - items count = 2
  - has_next_page = False
  - has_previous_page = False
  - items in the domain outside the scope = []
  - items[0].id: same as the seeded assignment in the order read by id
  - items[0].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - items[0].scope_id: same as the domain seeded in advance
  - items[0].idle_checker_id: same as the checker seeded in advance
  - items[0].enabled = True
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: same as the seeded assignment in the order read by id
  - items[1].scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - items[1].scope_id: same as the domain seeded in advance
  - items[1].idle_checker_id: same as the checker seeded in advance
  - items[1].enabled = True
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote

<a id="scoped_searching-a-scoped-assignment-search-by-a-user-granted-nothing-is-refused"></a>

#### [a-scoped-assignment-search-by-a-user-granted-nothing-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_scoped_searching.py): pass

when two assignments exist and a user granted nothing searches with a scope, it is rejected for lack of permission

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

- IdleCheckerAssignmentAdapter.scoped_search: user-2 reads scoped to the domains scope-1 and scope-2, with the checker as the filter

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="updating-the-superadmin-disables-an-idle-checker-assignment"></a>

#### [the-superadmin-disables-an-idle-checker-assignment](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_updating.py): pass

when the superadmin disables an assignment, it comes back disabled

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

- IdleCheckerAssignmentAdapter.update: user-1 disables the assignment of the domain scope-1

Then

- the whole assignment updated comes back disabled
  - scope_type = <IdleCheckerScopeTypeDTO.DOMAIN: 'domain'>
  - scope_id: same as the domain seeded in advance
  - idle_checker_id: same as the checker seeded in advance
  - enabled = False
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="updating-an-assignment-update-by-a-user-granted-nothing-is-refused"></a>

#### [an-assignment-update-by-a-user-granted-nothing-is-refused](/tests/scenario/bai_scenario/manager/idle_checker_assignment/test_updating.py): pass

when two assignments exist and a user granted nothing tries to disable one, it is rejected because the target cannot be resolved

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

- IdleCheckerAssignmentAdapter.update: user-2 disables the assignment of the domain scope-1

Then

- the call is rejected
  - rejected: GenericBadRequest

