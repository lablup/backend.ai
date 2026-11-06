## idle_checker

[background](/src/ai/backend/manager/api/adapters/idle_checker/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/idle_checker/adapter.py)

Scenario: incomplete 2 / 6

- built from ops (4)
  - admin_partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - admin_purge: representative success ✓ · representative rejection ✓
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✗: SCENARIO-GAP
- direct implementation (2)
  - admin_create: success present 1 · rejection present 1 (global_scope)
  - admin_update: success present 1 · rejection present 1 (global_scope)

**admin_partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several idle checkers in one call, none is deleted and all come back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-checkers) | answered |
| [when the superadmin purges two idle checkers and a missing id in one call, the two come back as deleted idle checkers and the missing id comes back in the failed list because no target answers to it](#partial_bulk_purging-the-superadmin-purges-several-and-is-answered-for-the-missing-one) | answered |

**admin_purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges one idle checker, the purge is answered with the id of the checker put in the request](#retiring-the-superadmin-purges-an-idle-checker) | answered |
| [when a user granted nothing tries to purge one idle checker, it is rejected for lack of permission](#retiring-a-user-granted-nothing-may-not-purge-an-idle-checker) | rejected |

**admin_search**

| scenario | verdict |
|---|---|
| [when the call reads with a checker type none of the checkers uses as a filter, no checker comes back](#searching-a-checker-type-no-checker-uses-leaves-nothing) | answered |
| [when the call reads with a time after the checkers were written as a filter, no checker comes back](#searching-a-created-at-filter-after-the-written-time-leaves-nothing) | answered |
| [when the call reads with the name of one of several checkers as a filter, only the one checker of that name comes back](#searching-a-name-filter-narrows-the-answer-to-that-checker) | answered |
| [when the call reads with the id of one checker as a filter, only that one checker comes back](#searching-an-entity-id-filter-narrows-the-answer-to-that-checker) | answered |
| [when the call reads ordered by name in the reverse direction, the checkers come back in the reverse order of their names](#searching-an-order-by-name-brings-the-checkers-back-in-name-order) | answered |
| [when the call reads with a time after the checkers were updated as a filter, no checker comes back](#searching-an-updated-at-filter-after-the-written-time-leaves-nothing) | answered |
| [the operation is gated by the global role, so when the superadmin searches without a filter, every checker seeded in advance is counted once and comes back](#searching-the-superadmin-searches-idle-checkers-without-a-filter) | answered |
| [the operation is gated by the global role, so when a user who is not the superadmin searches, it is rejected for lack of role](#searching-a-user-who-is-not-the-superadmin-may-not-search-idle-checkers) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when the superadmin batch-loads two checkers created in advance and one unknown id, they come back in the order asked and the item for the unknown id is empty](#reading-the-superadmin-batch-load-leaves-a-missing-id-empty) | answered |

**admin_create**

| scenario | verdict |
|---|---|
| [the operation is gated by the global role, so when the superadmin creates a session lifetime checker, it comes back with the values the request named](#creating-the-superadmin-makes-an-idle-checker) | answered |
| [the operation is gated by the global role, so when a user who is not the superadmin creates a checker, it is rejected for lack of role](#creating-a-user-who-is-not-the-superadmin-may-not-make-an-idle-checker) | rejected |

**admin_update**

| scenario | verdict |
|---|---|
| [the operation is gated by the global role, so when the superadmin changes a checker, it comes back with the changed spec](#editing-the-superadmin-edits-an-idle-checker) | answered |
| [the operation is gated by the global role, so when a user who is not the superadmin edits a checker, it is rejected for lack of role](#editing-a-user-who-is-not-the-superadmin-may-not-edit-an-idle-checker) | rejected |

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

### admin_purge

<a id="retiring-the-superadmin-purges-an-idle-checker"></a>

#### [the-superadmin-purges-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_retiring.py): pass

when the superadmin purges one idle checker, the purge is answered with the id of the checker put in the request

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

- IdleCheckerAdapter.admin_purge: user-1 purges the checker idle-checker-1

Then

- the purge is answered with the id of the checker put in the request
  - id: same as the checker put in the request
  - entity_id: same as the checker put in the request

<a id="retiring-a-user-granted-nothing-may-not-purge-an-idle-checker"></a>

#### [a-user-granted-nothing-may-not-purge-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_retiring.py): pass

when a user granted nothing tries to purge one idle checker, it is rejected for lack of permission

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

- IdleCheckerAdapter.admin_purge: user-1 purges the checker idle-checker-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### admin_search

<a id="searching-a-checker-type-no-checker-uses-leaves-nothing"></a>

#### [a-checker-type-no-checker-uses-leaves-nothing](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

when the call reads with a checker type none of the checkers uses as a filter, no checker comes back

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

- IdleCheckerAdapter.admin_search: user-1 reads with a checker type none of the checkers seeded in advance uses

Then

- no checker is counted
  - total_count = 0
  - items count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-created-at-filter-after-the-written-time-leaves-nothing"></a>

#### [a-created-at-filter-after-the-written-time-leaves-nothing](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

when the call reads with a time after the checkers were written as a filter, no checker comes back

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

- IdleCheckerAdapter.admin_search: user-1 reads with a time a second after the checkers were written

Then

- no checker is counted
  - total_count = 0
  - items count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-name-filter-narrows-the-answer-to-that-checker"></a>

#### [a-name-filter-narrows-the-answer-to-that-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

when the call reads with the name of one of several checkers as a filter, only the one checker of that name comes back

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

- IdleCheckerAdapter.admin_search: user-1 reads with the name idle-checker-1 as the filter

Then

- only the one checker seeded in advance is counted once and comes back whole
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0]: same as the whole checker seeded in advance

<a id="searching-an-entity-id-filter-narrows-the-answer-to-that-checker"></a>

#### [an-entity-id-filter-narrows-the-answer-to-that-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

when the call reads with the id of one checker as a filter, only that one checker comes back

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

- IdleCheckerAdapter.admin_search: user-1 reads with the id of one checker seeded in advance as the filter

Then

- only the one checker seeded in advance is counted once and comes back whole
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0]: same as the whole checker seeded in advance

<a id="searching-an-order-by-name-brings-the-checkers-back-in-name-order"></a>

#### [an-order-by-name-brings-the-checkers-back-in-name-order](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

when the call reads ordered by name in the reverse direction, the checkers come back in the reverse order of their names

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

- IdleCheckerAdapter.admin_search: user-1 reads ordered by name, the reverse direction

Then

- every checker seeded in advance is counted once, in the reverse order of their names
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0]: same as the whole checker seeded in advance with the number 1 name in the reverse order
  - items[1]: same as the whole checker seeded in advance with the number 2 name in the reverse order

<a id="searching-an-updated-at-filter-after-the-written-time-leaves-nothing"></a>

#### [an-updated-at-filter-after-the-written-time-leaves-nothing](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

when the call reads with a time after the checkers were updated as a filter, no checker comes back

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

- IdleCheckerAdapter.admin_search: user-1 reads with a time a second after the checkers were updated

Then

- no checker is counted
  - total_count = 0
  - items count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-superadmin-searches-idle-checkers-without-a-filter"></a>

#### [the-superadmin-searches-idle-checkers-without-a-filter](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

the operation is gated by the global role, so when the superadmin searches without a filter, every checker seeded in advance is counted once and comes back

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

- IdleCheckerAdapter.admin_search: user-1 reads everything without a filter

Then

- every checker seeded in advance is counted once, and each whole checker comes back
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0]: same as the whole checker seeded in advance number 1
  - items[1]: same as the whole checker seeded in advance number 2

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-idle-checkers"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-idle-checkers](/tests/scenario/bai_scenario/manager/idle_checker/test_searching.py): pass

the operation is gated by the global role, so when a user who is not the superadmin searches, it is rejected for lack of role

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

- IdleCheckerAdapter.admin_search: user-1 reads everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/idle_checker/test_reading.py): pass

when the superadmin batch-loads two checkers created in advance and one unknown id, they come back in the order asked and the item for the unknown id is empty

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

- IdleCheckerAdapter.batch_load_by_ids: user-1 batch-loads the 2 checkers created in advance and one unknown id

Then

- they come back in the order asked and the item for an unknown id is empty
  - len(items) = 3
  - items[0]: same as the whole checker seeded in advance number 1
  - items[1]: same as the whole checker seeded in advance number 2
  - items[2] = None

### admin_create

<a id="creating-the-superadmin-makes-an-idle-checker"></a>

#### [the-superadmin-makes-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_creating.py): pass

the operation is gated by the global role, so when the superadmin creates a session lifetime checker, it comes back with the values the request named

Given

- no idle checker and one caller
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- IdleCheckerAdapter.admin_create: user-1 creates a checker ending sessions after 7200 seconds

Then

- the whole checker just created comes back
  - id: skipped: the database generates it
  - entity_id: skipped: the database generates it
  - name = 'created-checker'
  - description = None
  - checker_type = 'session_lifetime'
  - target_session_types = [<SessionTypes.INTERACTIVE: 'interactive'>]
  - initial_grace_period_seconds = 0
  - spec.type = 'session_lifetime'
  - spec.session_lifetime.max_lifetime_seconds = 7200
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-user-who-is-not-the-superadmin-may-not-make-an-idle-checker"></a>

#### [a-user-who-is-not-the-superadmin-may-not-make-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_creating.py): pass

the operation is gated by the global role, so when a user who is not the superadmin creates a checker, it is rejected for lack of role

Given

- no idle checker and one caller
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- IdleCheckerAdapter.admin_create: user-1 creates a checker ending sessions after 7200 seconds

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_update

<a id="editing-the-superadmin-edits-an-idle-checker"></a>

#### [the-superadmin-edits-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_editing.py): pass

the operation is gated by the global role, so when the superadmin changes a checker, it comes back with the changed spec

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

- IdleCheckerAdapter.admin_update: user-1 changes the checker idle-checker-1 to the network timeout checker of 5400 seconds

Then

- the whole checker edited comes back
  - id: same as the checker laid
  - entity_id: same as the checker laid
  - name = 'idle-checker-1'
  - description = None
  - checker_type = 'network_timeout'
  - target_session_types = [<SessionTypes.INTERACTIVE: 'interactive'>]
  - initial_grace_period_seconds = 0
  - spec.type = 'network_timeout'
  - spec.network.max_network_inactivity_seconds = 5400
  - created_at: skipped: the time written before the edit
  - updated_at: the time this run wrote

<a id="editing-a-user-who-is-not-the-superadmin-may-not-edit-an-idle-checker"></a>

#### [a-user-who-is-not-the-superadmin-may-not-edit-an-idle-checker](/tests/scenario/bai_scenario/manager/idle_checker/test_editing.py): pass

the operation is gated by the global role, so when a user who is not the superadmin edits a checker, it is rejected for lack of role

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

- IdleCheckerAdapter.admin_update: user-1 changes the checker idle-checker-1 to the network timeout checker of 5400 seconds

Then

- the call is rejected
  - rejected: InsufficientPrivilege

