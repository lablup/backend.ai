## system_session_environ

[background](/src/ai/backend/manager/api/adapters/system_session_environ/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/system_session_environ/adapter.py)

Scenario: complete

- built from ops (7)
  - bulk_get_ids: representative success ✓ · representative rejection ✓
  - delete: representative success ✓ · representative rejection ✓
  - global_search: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - restore: representative success ✓ · representative rejection ✓
  - scoped_search: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - create: success present 1 · rejection present 3 (scope)
  - public_list_value_sources: success present 1 · rejection present 1 (public)

**bulk_get_ids**

| scenario | verdict |
|---|---|
| [when a user granted read permission in public loads two rows seeded in advance at once, the two come back in the requested order](#reading-a-user-granted-read-reads-several-environs-in-the-requested-order) | answered |
| [when a user granted nothing loads several ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission](#reading-a-user-granted-nothing-reading-many-environ-ids-is-refused-on-every-id) | rejected |

**delete**

| scenario | verdict |
|---|---|
| [when a user granted delete permission in public deletes a system session environ, the whole row comes back with the deletion time](#deleting-a-user-granted-delete-deletes-an-environ) | answered |
| [when a user granted nothing tries to delete a system session environ, it is rejected for lack of permission](#deleting-a-user-granted-nothing-may-not-delete-an-environ) | rejected |

**global_search**

| scenario | verdict |
|---|---|
| [when the superadmin filters by key, orders by key ascending and asks for one page across every scope, only the row with that key comes back. This call is gated by the global role](#searching-the-superadmin-searching-every-scope-finds-the-filtered-row) | answered |
| [when a user who is not the superadmin searches across every scope, it is rejected for lack of permission. This call is gated by the global role](#searching-a-user-who-is-not-the-superadmin-may-not-search-every-scope) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted purge permission in public purges a system session environ, the id of the purged row comes back](#purging-a-user-granted-purge-purges-an-environ) | answered |
| [when a user granted nothing tries to purge a system session environ, it is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-purge-an-environ) | rejected |

**restore**

| scenario | verdict |
|---|---|
| [when a user granted delete permission in public restores a deleted system session environ, the whole row comes back with no deletion time](#deleting-a-user-granted-delete-restores-a-deleted-environ) | answered |
| [when a user granted nothing tries to restore a system session environ, it is rejected for lack of permission](#deleting-a-user-granted-nothing-may-not-restore-an-environ) | rejected |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a user granted read permission in public filters by key, orders by key ascending and asks for one page in the public scope, only the public row with that key comes back, and neither the row under the same key in another scope nor the row the filter excludes comes back](#searching-a-user-granted-read-searching-public-counts-the-matching-public-row) | answered |
| [when a user granted nothing searches the public scope, it is rejected for lack of permission](#searching-a-user-granted-nothing-may-not-search-the-public-scope) | rejected |

**update**

| scenario | verdict |
|---|---|
| [when a user granted update permission in public changes a system session environ key, the whole row comes back with the new key and a last change time this run wrote](#editing-a-user-granted-update-changes-the-key-of-an-environ) | answered |
| [when a user granted nothing tries to change the key, it is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-edit-an-environ) | rejected |
| [when the key of a soft-deleted row is changed, it is rejected with a demand to restore it first](#editing-editing-a-deleted-environ-is-refused) | rejected |
| [when a row is changed to a key another row already holds at the same scope, it is rejected](#editing-editing-an-environ-to-a-key-another-row-holds-is-refused) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when a user granted create permission in public registers a system session environ, the whole registered row comes back](#creating-a-user-granted-create-registers-an-environ-in-public) | answered |
| [when a user granted nothing tries to register a system session environ, it is rejected for lack of permission](#creating-a-user-granted-nothing-may-not-create-an-environ) | rejected |
| [when a registration names a key another row already holds at the same scope, it is rejected](#creating-registering-an-environ-under-a-key-already-held-is-refused) | rejected |
| [when a registration names a value source the manager does not know, it is rejected](#creating-registering-an-environ-with-an-unknown-value-source-is-refused) | rejected |

**public_list_value_sources**

| scenario | verdict |
|---|---|
| [any authenticated user can read the list of value sources the manager provides](#reading-any-authenticated-user-reads-the-value-sources) | answered |
| [when the value source list is read with no caller, it is rejected. This call checks authentication alone](#reading-a-call-with-no-caller-is-refused-the-value-sources) | rejected |

### bulk_get_ids

<a id="reading-a-user-granted-read-reads-several-environs-in-the-requested-order"></a>

#### [a-user-granted-read-reads-several-environs-in-the-requested-order](/tests/scenario/bai_scenario/manager/system_session_environ/test_reading.py): pass

when a user granted read permission in public loads two rows seeded in advance at once, the two come back in the requested order

Given

- two system session environs registered at the public scope and one user granted READ on system session environs in the public scope
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - system session environ SCENARIO_OTHER_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare a user granted READ on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: READ allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.bulk_get_ids: user-1 loads two rows seeded in advance at once

Then

- the rows seeded in advance come back in the requested order
  - length = 2
  - [0].entity_id: same as the row seeded in advance
  - [0].key = 'SCENARIO_SEEDED_KEY'
  - [0].value_source = 'session_id'
  - [0].scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - [0].scope.scope_id: same as the id of the scope it is bound to
  - [0].created_at: same as the row's creation time
  - [0].updated_at: same as the row's last change time
  - [0].deleted_at = None
  - [1].entity_id: same as the row seeded in advance
  - [1].key = 'SCENARIO_OTHER_KEY'
  - [1].value_source = 'session_id'
  - [1].scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - [1].scope.scope_id: same as the id of the scope it is bound to
  - [1].created_at: same as the row's creation time
  - [1].updated_at: same as the row's last change time
  - [1].deleted_at = None

<a id="reading-a-user-granted-nothing-reading-many-environ-ids-is-refused-on-every-id"></a>

#### [a-user-granted-nothing-reading-many-environ-ids-is-refused-on-every-id](/tests/scenario/bai_scenario/manager/system_session_environ/test_reading.py): pass

when a user granted nothing loads several ids at once, instead of rejecting the whole request, every entry comes back holding a rejection for lack of permission

Given

- two system session environs registered at the public scope and one regular user
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - system session environ SCENARIO_OTHER_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.bulk_get_ids: user-1 loads two rows seeded in advance at once

Then

- every entry comes back holding a rejection for lack of permission
  - length = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### delete

<a id="deleting-a-user-granted-delete-deletes-an-environ"></a>

#### [a-user-granted-delete-deletes-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

when a user granted delete permission in public deletes a system session environ, the whole row comes back with the deletion time

Given

- one system session environ registered at the public scope and one user granted SOFT_DELETE on system session environs in the public scope
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare a user granted SOFT_DELETE on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: SOFT_DELETE allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.delete: user-1 deletes SCENARIO_SEEDED_KEY

Then

- the whole row seeded in advance comes back, with the deletion time and the last change time written by this run
  - entity_id: same as the row seeded in advance
  - key = 'SCENARIO_SEEDED_KEY'
  - value_source = 'session_id'
  - scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - scope.scope_id: same as the id of the scope it is bound to
  - created_at: same as the row's creation time
  - updated_at: the time this run wrote
  - deleted_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-delete-an-environ"></a>

#### [a-user-granted-nothing-may-not-delete-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

when a user granted nothing tries to delete a system session environ, it is rejected for lack of permission

Given

- one system session environ registered at the public scope and one regular user
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.delete: user-1 deletes SCENARIO_SEEDED_KEY

Then

- the call is rejected
  - rejected: NotEnoughPermission

### global_search

<a id="searching-the-superadmin-searching-every-scope-finds-the-filtered-row"></a>

#### [the-superadmin-searching-every-scope-finds-the-filtered-row](/tests/scenario/bai_scenario/manager/system_session_environ/test_searching.py): pass

when the superadmin filters by key, orders by key ascending and asks for one page across every scope, only the row with that key comes back. This call is gated by the global role

Given

- two system session environs at the public scope, one at a domain scope and one superadmin
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - system session environ SCENARIO_OTHER_KEY: injects the session_id value at the public scope
  - Domain elsewhere-1
  - domain-scoped system session environ SCENARIO_OTHER_KEY: injects the session_id value at the domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.global_search: user-1 filters by key, orders by key ascending and asks for one page while searching system session environs across every scope

Then

- only the filtered row comes back, and the row the filter excludes does not come back
  - length = 1
  - [0].entity_id: same as the row seeded in advance
  - [0].key = 'SCENARIO_SEEDED_KEY'
  - [0].value_source = 'session_id'
  - [0].scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - [0].scope.scope_id: same as the id of the scope it is bound to
  - [0].created_at: same as the row's creation time
  - [0].updated_at: same as the row's last change time
  - [0].deleted_at = None
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-every-scope"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-scope](/tests/scenario/bai_scenario/manager/system_session_environ/test_searching.py): pass

when a user who is not the superadmin searches across every scope, it is rejected for lack of permission. This call is gated by the global role

Given

- two system session environs registered at the public scope and one regular user
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - system session environ SCENARIO_OTHER_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.global_search: user-1 filters by key, orders by key ascending and asks for one page while searching system session environs across every scope

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### purge

<a id="purging-a-user-granted-purge-purges-an-environ"></a>

#### [a-user-granted-purge-purges-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_purging.py): pass

when a user granted purge permission in public purges a system session environ, the id of the purged row comes back

Given

- one system session environ registered at the public scope and one user granted HARD_DELETE on system session environs in the public scope
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare a user granted HARD_DELETE on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: HARD_DELETE allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.purge: user-1 purges SCENARIO_SEEDED_KEY

Then

- the id of the purged row comes back
  - entity_id: same as the row seeded in advance

<a id="purging-a-user-granted-nothing-may-not-purge-an-environ"></a>

#### [a-user-granted-nothing-may-not-purge-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_purging.py): pass

when a user granted nothing tries to purge a system session environ, it is rejected for lack of permission

Given

- one system session environ registered at the public scope and one regular user
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.purge: user-1 purges SCENARIO_SEEDED_KEY

Then

- the call is rejected
  - rejected: NotEnoughPermission

### restore

<a id="deleting-a-user-granted-delete-restores-a-deleted-environ"></a>

#### [a-user-granted-delete-restores-a-deleted-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

when a user granted delete permission in public restores a deleted system session environ, the whole row comes back with no deletion time

Given

- one system session environ deleted at the public scope and one user granted SOFT_DELETE on system session environs in the public scope
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - deleted system session environ deleted-environ-1: its deletion time is recorded
  - Domain home-1
  - Prepare a user granted SOFT_DELETE on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: SOFT_DELETE allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.restore: user-1 restores SCENARIO_SEEDED_KEY

Then

- the whole row seeded in advance comes back with no deletion time and the last change time written by this run
  - entity_id: same as the row seeded in advance
  - key = 'SCENARIO_SEEDED_KEY'
  - value_source = 'session_id'
  - scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - scope.scope_id: same as the id of the scope it is bound to
  - created_at: same as the row's creation time
  - updated_at: the time this run wrote
  - deleted_at = None

<a id="deleting-a-user-granted-nothing-may-not-restore-an-environ"></a>

#### [a-user-granted-nothing-may-not-restore-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_deleting.py): pass

when a user granted nothing tries to restore a system session environ, it is rejected for lack of permission

Given

- one system session environ deleted at the public scope and one regular user
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - deleted system session environ deleted-environ-1: its deletion time is recorded
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.restore: user-1 restores SCENARIO_SEEDED_KEY

Then

- the call is rejected
  - rejected: NotEnoughPermission

### scoped_search

<a id="searching-a-user-granted-read-searching-public-counts-the-matching-public-row"></a>

#### [a-user-granted-read-searching-public-counts-the-matching-public-row](/tests/scenario/bai_scenario/manager/system_session_environ/test_searching.py): pass

when a user granted read permission in public filters by key, orders by key ascending and asks for one page in the public scope, only the public row with that key comes back, and neither the row under the same key in another scope nor the row the filter excludes comes back

Given

- two system session environs at the public scope, one at a domain scope under the same key, and one user granted read permission in the public scope
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - system session environ SCENARIO_OTHER_KEY: injects the session_id value at the public scope
  - Domain elsewhere-1
  - domain-scoped system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the domain scope
  - Domain home-1
  - Prepare a user granted READ on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: READ allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.scoped_search: user-1 filters by key, orders by key ascending and asks for one page while searching system session environs in the public scope

Then

- only the filtered row comes back, and neither the row outside the scope nor the row the filter excludes comes back
  - length = 1
  - [0].entity_id: same as the row seeded in advance
  - [0].key = 'SCENARIO_SEEDED_KEY'
  - [0].value_source = 'session_id'
  - [0].scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - [0].scope.scope_id: same as the id of the scope it is bound to
  - [0].created_at: same as the row's creation time
  - [0].updated_at: same as the row's last change time
  - [0].deleted_at = None
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-granted-nothing-may-not-search-the-public-scope"></a>

#### [a-user-granted-nothing-may-not-search-the-public-scope](/tests/scenario/bai_scenario/manager/system_session_environ/test_searching.py): pass

when a user granted nothing searches the public scope, it is rejected for lack of permission

Given

- two system session environs registered at the public scope and one regular user
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - system session environ SCENARIO_OTHER_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.scoped_search: user-1 filters by key, orders by key ascending and asks for one page while searching system session environs in the public scope

Then

- the call is rejected
  - rejected: NotEnoughPermission

### update

<a id="editing-a-user-granted-update-changes-the-key-of-an-environ"></a>

#### [a-user-granted-update-changes-the-key-of-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_editing.py): pass

when a user granted update permission in public changes a system session environ key, the whole row comes back with the new key and a last change time this run wrote

Given

- one system session environ registered at the public scope and one user granted UPDATE on system session environs in the public scope
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare a user granted UPDATE on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: UPDATE allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.update: user-1 changes the key of SCENARIO_SEEDED_KEY to SCENARIO_EDITED_KEY

Then

- the whole row seeded in advance comes back
  - entity_id: same as the row seeded in advance
  - key = 'SCENARIO_EDITED_KEY'
  - value_source = 'session_id'
  - scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - scope.scope_id: same as the id of the scope it is bound to
  - created_at: same as the row's creation time
  - updated_at: the time this run wrote
  - deleted_at = None

<a id="editing-a-user-granted-nothing-may-not-edit-an-environ"></a>

#### [a-user-granted-nothing-may-not-edit-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_editing.py): pass

when a user granted nothing tries to change the key, it is rejected for lack of permission

Given

- one system session environ registered at the public scope and one regular user
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.update: user-1 changes the key of SCENARIO_SEEDED_KEY to SCENARIO_EDITED_KEY

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-editing-a-deleted-environ-is-refused"></a>

#### [editing-a-deleted-environ-is-refused](/tests/scenario/bai_scenario/manager/system_session_environ/test_editing.py): pass

when the key of a soft-deleted row is changed, it is rejected with a demand to restore it first

Given

- one system session environ deleted at the public scope and one user granted UPDATE on system session environs in the public scope
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - deleted system session environ deleted-environ-1: its deletion time is recorded
  - Domain home-1
  - Prepare a user granted UPDATE on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: UPDATE allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.update: user-1 changes the key of SCENARIO_SEEDED_KEY to SCENARIO_EDITED_KEY

Then

- the call is rejected
  - rejected: SystemSessionEnvironDeleted

<a id="editing-editing-an-environ-to-a-key-another-row-holds-is-refused"></a>

#### [editing-an-environ-to-a-key-another-row-holds-is-refused](/tests/scenario/bai_scenario/manager/system_session_environ/test_editing.py): pass

when a row is changed to a key another row already holds at the same scope, it is rejected

Given

- two system session environs registered at the public scope and one user granted UPDATE on system session environs in the public scope
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - system session environ SCENARIO_OTHER_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare a user granted UPDATE on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: UPDATE allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.update: user-1 changes the key of SCENARIO_SEEDED_KEY to SCENARIO_OTHER_KEY

Then

- the call is rejected
  - rejected: SystemSessionEnvironKeyConflict

### create

<a id="creating-a-user-granted-create-registers-an-environ-in-public"></a>

#### [a-user-granted-create-registers-an-environ-in-public](/tests/scenario/bai_scenario/manager/system_session_environ/test_creating.py): pass

when a user granted create permission in public registers a system session environ, the whole registered row comes back

Given

- one user granted CREATE on system session environs in the public scope
  - Domain home-1
  - Prepare a user granted CREATE on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: CREATE allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.create: user-1 registers a system session environ

Then

- the whole registered row comes back
  - entity_id: skipped: the database generates it
  - key = 'SCENARIO_CREATED_KEY'
  - value_source = 'user_email'
  - scope.scope_type = <SystemSessionEnvironScopeType.PUBLIC: 'public'>
  - scope.scope_id: same as the id of the public scope
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - deleted_at = None

<a id="creating-a-user-granted-nothing-may-not-create-an-environ"></a>

#### [a-user-granted-nothing-may-not-create-an-environ](/tests/scenario/bai_scenario/manager/system_session_environ/test_creating.py): pass

when a user granted nothing tries to register a system session environ, it is rejected for lack of permission

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.create: user-1 registers a system session environ

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="creating-registering-an-environ-under-a-key-already-held-is-refused"></a>

#### [registering-an-environ-under-a-key-already-held-is-refused](/tests/scenario/bai_scenario/manager/system_session_environ/test_creating.py): pass

when a registration names a key another row already holds at the same scope, it is rejected

Given

- one row already registered and one user granted create permission in public
  - system session environ SCENARIO_SEEDED_KEY: injects the session_id value at the public scope
  - Domain home-1
  - Prepare a user granted CREATE on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: CREATE allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.create: user-1 registers a system session environ

Then

- the call is rejected
  - rejected: SystemSessionEnvironKeyConflict

<a id="creating-registering-an-environ-with-an-unknown-value-source-is-refused"></a>

#### [registering-an-environ-with-an-unknown-value-source-is-refused](/tests/scenario/bai_scenario/manager/system_session_environ/test_creating.py): pass

when a registration names a value source the manager does not know, it is rejected

Given

- one user granted CREATE on system session environs in the public scope
  - Domain home-1
  - Prepare a user granted CREATE on system session environs in the public scope
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role environ-writer-1: applies only within the scope it is granted in
    - Role environ-writer-1: CREATE allowed on every system_session_environ
    - regular user user-1: holds Role environ-writer-1

When

- SystemSessionEnvironAdapter.create: user-1 registers a system session environ

Then

- the call is rejected
  - rejected: UnknownSystemSessionEnvironValueSource

### public_list_value_sources

<a id="reading-any-authenticated-user-reads-the-value-sources"></a>

#### [any-authenticated-user-reads-the-value-sources](/tests/scenario/bai_scenario/manager/system_session_environ/test_reading.py): pass

any authenticated user can read the list of value sources the manager provides

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.public_list_value_sources: user-1 reads the value sources the manager provides

Then

- every value source the manager provides comes back
  - items = ['session_id', 'session_name', 'cluster_size', 'cluster_replicas', 'cluster_hosts', 'preopen_ports', 'user_uuid', 'user_email', 'user_name', 'access_key']

<a id="reading-a-call-with-no-caller-is-refused-the-value-sources"></a>

#### [a-call-with-no-caller-is-refused-the-value-sources](/tests/scenario/bai_scenario/manager/system_session_environ/test_reading.py): pass

when the value source list is read with no caller, it is rejected. This call checks authentication alone

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- SystemSessionEnvironAdapter.public_list_value_sources: user-1 reads the value sources the manager provides

Then

- the call is rejected
  - rejected: UserNotFound

