## role_preset

[background](/src/ai/backend/manager/api/adapters/role_preset/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/role_preset/adapter.py)

Scenario: incomplete 11 / 21

- built from ops (14)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_permissions_by_ids: representative success ✓ · representative rejection ✓
  - bulk_delete: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - bulk_purge: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - bulk_restore: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - delete: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - restore: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
  - search_permission_presets: representative success ✓ · representative rejection ✓
- direct implementation (7)
  - atomic_bulk_add_permissions: success present 1 · rejection present 1 (single_entity)
  - bulk_add_permissions: success absent · rejection absent (single_entity): SCENARIO-GAP
  - bulk_remove_permissions: success absent · rejection absent (partial_bulk_field): SCENARIO-GAP
  - create: success present 1 · rejection absent (scope): SCENARIO-GAP
  - partial_bulk_remove_permissions: success present 2 · rejection absent (partial_bulk_field): SCENARIO-GAP
  - partial_bulk_update: success present 3 · rejection absent (partial_bulk): SCENARIO-GAP
  - update: success present 2 · rejection present 2 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted read in global loads the ids of two presets at once, both come back whole in the requested order](#reading-a-user-granted-read-loads-many-presets-in-order) | answered |
| [when a user granted nothing loads the ids of two presets at once, instead of the whole request being rejected, every entry comes back holding a rejection for lack of permission](#reading-a-user-granted-nothing-loading-many-presets-is-denied-on-every-id) | rejected |

**batch_load_permissions_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted read in global loads the ids of two permission entries of a preset at once, both come back whole in the requested order](#permission_reading-a-user-granted-read-loads-permission-entries-in-order) | answered |
| [when a user granted nothing loads the ids of two permission entries at once, instead of the whole request being rejected, every entry comes back holding a rejection for lack of permission](#permission_reading-a-user-granted-nothing-loading-entries-is-denied-on-every-id) | rejected |

**delete**

| scenario | verdict |
|---|---|
| [when the superadmin soft deletes a preset, the whole preset marked deleted comes back](#deleting-the-superadmin-soft-deletes-a-preset) | answered |
| [when a user granted nothing tries to soft delete a preset, it is rejected for lack of permission](#deleting-a-user-granted-nothing-may-not-soft-delete-a-preset) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted read in global reads by id, the whole preset seeded in advance comes back](#reading-a-user-granted-read-reads-a-preset-by-id) | answered |
| [when a user granted nothing tries to read by id, it is rejected for lack of permission](#reading-a-user-granted-nothing-may-not-read-a-preset) | rejected |

**partial_bulk_delete**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to soft delete several presets at once, none is soft-deleted and every one comes back in the failed list for lack of permission](#partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-presets) | answered |
| [when two presets and one missing id are soft-deleted at once, the two come back marked deleted and the missing id comes back in the failed list because there is no such target](#partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one) | answered |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several presets at once, none is purged and every one comes back in the failed list for lack of permission](#partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-presets) | answered |
| [when two presets and one missing id are purged at once, the two come back as they were before the purge and the missing id comes back in the failed list because there is no such target](#partial_bulk_deleting-purging-several-answers-for-the-missing-one) | answered |

**partial_bulk_restore**

| scenario | verdict |
|---|---|
| [when several soft-deleted presets are restored at once, all of them come back not marked deleted](#partial_bulk_deleting-restoring-several-brings-them-back) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges a preset, the whole preset as it was before the purge comes back](#deleting-the-superadmin-purges-a-preset) | answered |
| [when a user granted nothing tries to purge a preset, it is rejected for lack of permission](#deleting-a-user-granted-nothing-may-not-purge-a-preset) | rejected |

**restore**

| scenario | verdict |
|---|---|
| [when a soft-deleted preset is restored, the whole preset not marked deleted comes back](#deleting-restoring-a-soft-deleted-preset-brings-it-back) | answered |
| [when a user granted nothing tries to restore a preset, it is rejected for lack of permission](#deleting-a-user-granted-nothing-may-not-restore-a-preset) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when the superadmin searches with the project-scope filter, name order and a page size of one, only the first matching preset in the order comes back and the rest do not. The global role gates this call](#searching-the-superadmin-finds-one-page-of-matching-presets) | answered |
| [when a user without the global role tries to search presets, it is rejected for lack of permission](#searching-a-user-who-is-not-the-superadmin-may-not-search-presets) | rejected |

**search_permission_presets**

| scenario | verdict |
|---|---|
| [when a user granted read in global searches permission entries with the read-bit filter, entity-type order and a page size of one, only the first matching entry in the order comes back and neither the other matching entry, the entry the filter excludes nor the entry of the other preset comes back](#permission_reading-a-user-granted-read-finds-one-page-of-matching-entries) | answered |
| [when a user granted nothing tries to search the permission entries of a preset, the whole request is rejected for lack of permission](#permission_reading-a-user-granted-nothing-may-not-search-permission-entries) | rejected |

**atomic_bulk_add_permissions**

| scenario | verdict |
|---|---|
| [when the superadmin adds two permission entries to a preset that has none, the two entries added come back under the preset](#permission_editing-the-superadmin-adds-entries-to-a-preset) | answered |
| [when a user granted nothing tries to add permission entries to a preset, it is rejected for lack of permission](#permission_editing-a-user-granted-nothing-may-not-add-entries) | rejected |

**create**

| scenario | verdict |
|---|---|
| [creating a project-scope preset with owner assignment on brings it back turned on](#creating-a-project-preset-is-made-with-owner-assign) | answered |

**partial_bulk_remove_permissions**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to remove several permission entries at once, none is removed and every one comes back in the failed list for lack of permission](#permission_editing-a-user-granted-nothing-removes-none-of-the-entries) | answered |
| [when the superadmin removes two permission entries and one missing id at once, the two come back in the processed list and the missing id comes back in the failed list](#permission_editing-removing-entries-answers-for-the-missing-one) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to edit several presets at once, none is edited and every one comes back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets) | answered |
| [turning on owner assignment of project-scope and domain-scope presets at once edits only the project-scope preset, and the domain-scope preset comes back in the failed list](#partial_bulk_editing-only-the-project-preset-takes-owner-assign) | answered |
| [when the superadmin turns auto assign on for several presets at once, all of them come back with the new value and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-presets-at-once) | answered |

**update**

| scenario | verdict |
|---|---|
| [turning on owner assignment of a project-scope preset brings the whole preset back turned on](#editing-a-project-preset-takes-owner-assign) | answered |
| [when the superadmin renames a preset, the whole preset carrying the new name comes back](#editing-the-superadmin-renames-a-preset) | answered |
| [turning on owner assignment of a preset in a scope other than a project is rejected because there is no owner](#editing-a-domain-preset-refuses-owner-assign) | rejected |
| [when a user granted nothing tries to rename a preset, it is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-rename-a-preset) | rejected |

### batch_load_by_ids

<a id="reading-a-user-granted-read-loads-many-presets-in-order"></a>

#### [a-user-granted-read-loads-many-presets-in-order](/tests/scenario/bai_scenario/manager/role_preset/test_reading.py): pass

when a user granted read in global loads the ids of two presets at once, both come back whole in the requested order

Given

- 2 presets and one user granted READ in global
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare a user granted the READ permission on role presets in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role preset-reader-1: applies only within the scope it is granted in
    - Role preset-reader-1: READ allowed on every role_preset
    - regular user user-1: holds Role preset-reader-1

When

- RolePresetAdapter.batch_load_by_ids: user-1 reads the ids of 2 presets seeded in advance at once

Then

- the presets seeded in advance come back in the requested order
  - length = 2
  - [0].id: same as the id of the preset seeded in advance
  - [0].entity_id: same as the id of the preset seeded in advance
  - [0].name = 'preset-1'
  - [0].scope_type = 'project'
  - [0].role_name_template = None
  - [0].auto_assign = False
  - [0].auto_assign_to_owner = False
  - [0].deleted = False
  - [0].deleted_at = None
  - [0].created_at: same as the time the preset was seeded
  - [0].updated_at: same as the time the preset was seeded
  - [1].id: same as the id of the preset seeded in advance
  - [1].entity_id: same as the id of the preset seeded in advance
  - [1].name = 'preset-2'
  - [1].scope_type = 'project'
  - [1].role_name_template = None
  - [1].auto_assign = False
  - [1].auto_assign_to_owner = False
  - [1].deleted = False
  - [1].deleted_at = None
  - [1].created_at: same as the time the preset was seeded
  - [1].updated_at: same as the time the preset was seeded

<a id="reading-a-user-granted-nothing-loading-many-presets-is-denied-on-every-id"></a>

#### [a-user-granted-nothing-loading-many-presets-is-denied-on-every-id](/tests/scenario/bai_scenario/manager/role_preset/test_reading.py): pass

when a user granted nothing loads the ids of two presets at once, instead of the whole request being rejected, every entry comes back holding a rejection for lack of permission

Given

- 2 presets and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.batch_load_by_ids: user-1 reads the ids of 2 presets seeded in advance at once

Then

- every entry comes back holding a rejection for lack of permission
  - length = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### batch_load_permissions_by_ids

<a id="permission_reading-a-user-granted-read-loads-permission-entries-in-order"></a>

#### [a-user-granted-read-loads-permission-entries-in-order](/tests/scenario/bai_scenario/manager/role_preset/test_permission_reading.py): pass

when a user granted read in global loads the ids of two permission entries of a preset at once, both come back whole in the requested order

Given

- one preset with two permission entries and one user granted READ in global
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-1: READ allowed on every domain
  - Role preset preset-1: UPDATE allowed on every project
  - Domain home-1
  - Prepare a user granted the READ permission on role presets in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role preset-reader-1: applies only within the scope it is granted in
    - Role preset-reader-1: READ allowed on every role_preset
    - regular user user-1: holds Role preset-reader-1

When

- RolePresetAdapter.batch_load_permissions_by_ids: user-1 reads the ids of 2 permission entries of preset-1 at once

Then

- the entries seeded in advance come back in the requested order
  - length = 2
  - [0].id: same as the id of the entry seeded in advance
  - [0].field_id: same as the id of the entry seeded in advance
  - [0].role_preset_id: same as the id of the preset seeded in advance
  - [0].entity_type = 'domain'
  - [0].permission = <PermissionBitDTO.READ: 'read'>
  - [0].created_at: same as the time the entry was seeded
  - [1].id: same as the id of the entry seeded in advance
  - [1].field_id: same as the id of the entry seeded in advance
  - [1].role_preset_id: same as the id of the preset seeded in advance
  - [1].entity_type = 'project'
  - [1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - [1].created_at: same as the time the entry was seeded

<a id="permission_reading-a-user-granted-nothing-loading-entries-is-denied-on-every-id"></a>

#### [a-user-granted-nothing-loading-entries-is-denied-on-every-id](/tests/scenario/bai_scenario/manager/role_preset/test_permission_reading.py): pass

when a user granted nothing loads the ids of two permission entries at once, instead of the whole request being rejected, every entry comes back holding a rejection for lack of permission

Given

- one preset with two permission entries and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-1: READ allowed on every domain
  - Role preset preset-1: UPDATE allowed on every project
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.batch_load_permissions_by_ids: user-1 reads the ids of 2 permission entries of preset-1 at once

Then

- every entry comes back holding a rejection for lack of permission
  - length = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### delete

<a id="deleting-the-superadmin-soft-deletes-a-preset"></a>

#### [the-superadmin-soft-deletes-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

when the superadmin soft deletes a preset, the whole preset marked deleted comes back

Given

- one preset that already exists and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.delete: user-1 soft deletes preset-1

Then

- the whole preset marked deleted comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = True
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-soft-delete-a-preset"></a>

#### [a-user-granted-nothing-may-not-soft-delete-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

when a user granted nothing tries to soft delete a preset, it is rejected for lack of permission

Given

- one preset that already exists and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.delete: user-1 soft deletes preset-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### get

<a id="reading-a-user-granted-read-reads-a-preset-by-id"></a>

#### [a-user-granted-read-reads-a-preset-by-id](/tests/scenario/bai_scenario/manager/role_preset/test_reading.py): pass

when a user granted read in global reads by id, the whole preset seeded in advance comes back

Given

- one preset that already exists and one user granted READ in global
  - Role preset preset-1: for the project scope, with automatic grant enabled, with owner assignment enabled, carrying a role name template
  - Domain home-1
  - Prepare a user granted the READ permission on role presets in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role preset-reader-1: applies only within the scope it is granted in
    - Role preset-reader-1: READ allowed on every role_preset
    - regular user user-1: holds Role preset-reader-1

When

- RolePresetAdapter.get: user-1 reads preset-1 by id

Then

- the whole preset seeded in advance comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - name = 'preset-1'
  - scope_type = 'project'
  - role_name_template = 'team-member'
  - auto_assign = True
  - auto_assign_to_owner = True
  - deleted = False
  - deleted_at = None
  - created_at: same as the time the preset was seeded
  - updated_at: same as the time the preset was seeded

<a id="reading-a-user-granted-nothing-may-not-read-a-preset"></a>

#### [a-user-granted-nothing-may-not-read-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_reading.py): pass

when a user granted nothing tries to read by id, it is rejected for lack of permission

Given

- one preset that already exists and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.get: user-1 reads preset-1 by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_delete

<a id="partial_bulk_deleting-a-user-granted-nothing-soft-deletes-none-of-several-presets"></a>

#### [a-user-granted-nothing-soft-deletes-none-of-several-presets](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

when a user granted nothing tries to soft delete several presets at once, none is soft-deleted and every one comes back in the failed list for lack of permission

Given

- 2 presets and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_delete: user-1 soft deletes 2 presets at once

Then

- nothing is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_deleting-soft-deleting-several-answers-for-the-missing-one"></a>

#### [soft-deleting-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

when two presets and one missing id are soft-deleted at once, the two come back marked deleted and the missing id comes back in the failed list because there is no such target

Given

- 2 presets and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_delete: user-1 soft deletes 2 presets and one missing id at once

Then

- every target preset comes back marked deleted, and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: same as the id of the preset seeded in advance
  - successes[0].entity_id: same as the id of the preset seeded in advance
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = True
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the id of the preset seeded in advance
  - successes[1].entity_id: same as the id of the preset seeded in advance
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = False
  - successes[1].deleted = True
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_purge

<a id="partial_bulk_deleting-a-user-granted-nothing-purges-none-of-several-presets"></a>

#### [a-user-granted-nothing-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

when a user granted nothing tries to purge several presets at once, none is purged and every one comes back in the failed list for lack of permission

Given

- 2 presets and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_purge: user-1 purges 2 presets at once

Then

- nothing is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_deleting-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

when two presets and one missing id are purged at once, the two come back as they were before the purge and the missing id comes back in the failed list because there is no such target

Given

- 2 presets and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_purge: user-1 purges 2 presets and one missing id at once

Then

- every target preset comes back not marked deleted, and an unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - successes[0].id: same as the id of the preset seeded in advance
  - successes[0].entity_id: same as the id of the preset seeded in advance
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = False
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the id of the preset seeded in advance
  - successes[1].entity_id: same as the id of the preset seeded in advance
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = False
  - successes[1].deleted = False
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_restore

<a id="partial_bulk_deleting-restoring-several-brings-them-back"></a>

#### [restoring-several-brings-them-back](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_deleting.py): pass

when several soft-deleted presets are restored at once, all of them come back not marked deleted

Given

- 2 presets and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_restore: user-1 soft deletes 2 presets at once and then restores them at once

Then

- every target preset comes back not marked deleted, and nothing failed
  - successes count = 2
  - successes[0].id: same as the id of the preset seeded in advance
  - successes[0].entity_id: same as the id of the preset seeded in advance
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = False
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the id of the preset seeded in advance
  - successes[1].entity_id: same as the id of the preset seeded in advance
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = False
  - successes[1].deleted = False
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

### purge

<a id="deleting-the-superadmin-purges-a-preset"></a>

#### [the-superadmin-purges-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

when the superadmin purges a preset, the whole preset as it was before the purge comes back

Given

- one preset that already exists and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.purge: user-1 purges preset-1

Then

- the whole preset not marked deleted comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-purge-a-preset"></a>

#### [a-user-granted-nothing-may-not-purge-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

when a user granted nothing tries to purge a preset, it is rejected for lack of permission

Given

- one preset that already exists and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.purge: user-1 purges preset-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### restore

<a id="deleting-restoring-a-soft-deleted-preset-brings-it-back"></a>

#### [restoring-a-soft-deleted-preset-brings-it-back](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

when a soft-deleted preset is restored, the whole preset not marked deleted comes back

Given

- one preset that already exists and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.restore: user-1 soft deletes preset-1 and then restores it

Then

- the whole preset not marked deleted comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="deleting-a-user-granted-nothing-may-not-restore-a-preset"></a>

#### [a-user-granted-nothing-may-not-restore-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_deleting.py): pass

when a user granted nothing tries to restore a preset, it is rejected for lack of permission

Given

- one preset that already exists and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.restore: user-1 restores preset-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search

<a id="searching-the-superadmin-finds-one-page-of-matching-presets"></a>

#### [the-superadmin-finds-one-page-of-matching-presets](/tests/scenario/bai_scenario/manager/role_preset/test_searching.py): pass

when the superadmin searches with the project-scope filter, name order and a page size of one, only the first matching preset in the order comes back and the rest do not. The global role gates this call

Given

- two project-scope presets, one domain-scope preset, and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Role preset preset-3: for the domain scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.search: user-1 searches with the project-scope filter, name order and a page size of one

Then

- of the presets matching the filter, only the first in the order comes back as one page, and neither the other matching preset nor the preset the filter excludes comes back
  - items count = 1
  - items[0].id: same as the id of the preset seeded in advance
  - items[0].entity_id: same as the id of the preset seeded in advance
  - items[0].name = 'preset-1'
  - items[0].scope_type = 'project'
  - items[0].role_name_template = None
  - items[0].auto_assign = False
  - items[0].auto_assign_to_owner = False
  - items[0].deleted = False
  - items[0].deleted_at = None
  - items[0].created_at: same as the time the preset was seeded
  - items[0].updated_at: same as the time the preset was seeded
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-presets"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-presets](/tests/scenario/bai_scenario/manager/role_preset/test_searching.py): pass

when a user without the global role tries to search presets, it is rejected for lack of permission

Given

- two project-scope presets, one domain-scope preset, and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Role preset preset-3: for the domain scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.search: user-1 searches with the project-scope filter, name order and a page size of one

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### search_permission_presets

<a id="permission_reading-a-user-granted-read-finds-one-page-of-matching-entries"></a>

#### [a-user-granted-read-finds-one-page-of-matching-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_reading.py): pass

when a user granted read in global searches permission entries with the read-bit filter, entity-type order and a page size of one, only the first matching entry in the order comes back and neither the other matching entry, the entry the filter excludes nor the entry of the other preset comes back

Given

- one preset with several permission entries, another preset, and one user granted READ in global
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-1: READ allowed on every domain
  - Role preset preset-1: READ allowed on every project
  - Role preset preset-1: UPDATE allowed on every project
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Role preset preset-2: READ allowed on every project
  - Domain home-1
  - Prepare a user granted the READ permission on role presets in global
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role preset-reader-1: applies only within the scope it is granted in
    - Role preset-reader-1: READ allowed on every role_preset
    - regular user user-1: holds Role preset-reader-1

When

- RolePresetAdapter.search_permission_presets: user-1 searches the permission entries of preset-1 with the read-bit filter, entity-type order and a page size of one

Then

- of the entries matching the filter, only the first in the order comes back as one page, and neither the other matching entry, the entry the filter excludes, nor the entry of the other preset comes back
  - items count = 1
  - items[0].id: same as the id of the entry seeded in advance
  - items[0].field_id: same as the id of the entry seeded in advance
  - items[0].role_preset_id: same as the id of the preset seeded in advance
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: same as the time the entry was seeded
  - total_count = 2
  - has_next_page = True
  - has_previous_page = False

<a id="permission_reading-a-user-granted-nothing-may-not-search-permission-entries"></a>

#### [a-user-granted-nothing-may-not-search-permission-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_reading.py): pass

when a user granted nothing tries to search the permission entries of a preset, the whole request is rejected for lack of permission

Given

- one preset with several permission entries, another preset, and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-1: READ allowed on every domain
  - Role preset preset-1: READ allowed on every project
  - Role preset preset-1: UPDATE allowed on every project
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Role preset preset-2: READ allowed on every project
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.search_permission_presets: user-1 searches the permission entries of preset-1 with the read-bit filter, entity-type order and a page size of one

Then

- the call is rejected
  - rejected: NotEnoughPermission

### atomic_bulk_add_permissions

<a id="permission_editing-the-superadmin-adds-entries-to-a-preset"></a>

#### [the-superadmin-adds-entries-to-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py): pass

when the superadmin adds two permission entries to a preset that has none, the two entries added come back under the preset

Given

- one preset that already exists and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.atomic_bulk_add_permissions: user-1 adds 2 permission entries to preset-1

Then

- the two entries added come back under the preset
  - items count = 2
  - items[0].id: skipped: the database generates it
  - items[0].field_id: skipped: the database generates it
  - items[0].role_preset_id: same as the id of the preset seeded in advance
  - items[0].entity_type = 'domain'
  - items[0].permission = <PermissionBitDTO.READ: 'read'>
  - items[0].created_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].field_id: skipped: the database generates it
  - items[1].role_preset_id: same as the id of the preset seeded in advance
  - items[1].entity_type = 'project'
  - items[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - items[1].created_at: the time this run wrote

<a id="permission_editing-a-user-granted-nothing-may-not-add-entries"></a>

#### [a-user-granted-nothing-may-not-add-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py): pass

when a user granted nothing tries to add permission entries to a preset, it is rejected for lack of permission

Given

- one preset that already exists and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.atomic_bulk_add_permissions: user-1 adds 2 permission entries to preset-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### create

<a id="creating-a-project-preset-is-made-with-owner-assign"></a>

#### [a-project-preset-is-made-with-owner-assign](/tests/scenario/bai_scenario/manager/role_preset/test_creating.py): pass

creating a project-scope preset with owner assignment on brings it back turned on

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.create: user-1 creates a project-scope preset with owner assignment on

Then

- the preset with owner assignment turned on comes back
  - name = 'made-preset'
  - auto_assign_to_owner = True

### partial_bulk_remove_permissions

<a id="permission_editing-a-user-granted-nothing-removes-none-of-the-entries"></a>

#### [a-user-granted-nothing-removes-none-of-the-entries](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py): pass

when a user granted nothing tries to remove several permission entries at once, none is removed and every one comes back in the failed list for lack of permission

Given

- one preset with two permission entries and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-1: READ allowed on every domain
  - Role preset preset-1: UPDATE allowed on every project
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_remove_permissions: user-1 removes 2 permission entries from preset-1 at once

Then

- nothing is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="permission_editing-removing-entries-answers-for-the-missing-one"></a>

#### [removing-entries-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/role_preset/test_permission_editing.py): pass

when the superadmin removes two permission entries and one missing id at once, the two come back in the processed list and the missing id comes back in the failed list

Given

- one preset with two permission entries and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-1: READ allowed on every domain
  - Role preset preset-1: UPDATE allowed on every project
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_remove_permissions: user-1 removes 2 permission entries and one missing id from preset-1 at once

Then

- the two entries removed come back in the processed list, and the unknown id comes back in the failed list
  - successes count = 2
  - successes[0].id: same as the id of the entry seeded in advance
  - successes[0].field_id: same as the id of the entry seeded in advance
  - successes[0].role_preset_id: same as the id of the preset seeded in advance
  - successes[0].entity_type = 'domain'
  - successes[0].permission = <PermissionBitDTO.READ: 'read'>
  - successes[0].created_at: same as the time of the entry seeded in advance
  - successes[1].id: same as the id of the entry seeded in advance
  - successes[1].field_id: same as the id of the entry seeded in advance
  - successes[1].role_preset_id: same as the id of the preset seeded in advance
  - successes[1].entity_type = 'project'
  - successes[1].permission = <PermissionBitDTO.UPDATE: 'update'>
  - successes[1].created_at: same as the time of the entry seeded in advance
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets"></a>

#### [a-user-granted-nothing-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_editing.py): pass

when a user granted nothing tries to edit several presets at once, none is edited and every one comes back in the failed list for lack of permission

Given

- 2 presets and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_update: user-1 turns auto assign on for 2 presets at once

Then

- nothing is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-only-the-project-preset-takes-owner-assign"></a>

#### [only-the-project-preset-takes-owner-assign](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_editing.py): pass

turning on owner assignment of project-scope and domain-scope presets at once edits only the project-scope preset, and the domain-scope preset comes back in the failed list

Given

- one project-scope preset, one domain-scope preset, and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the domain scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_update: user-1 turns on owner assignment of 2 presets at once

Then

- only the project-scope preset comes back edited, and the domain-scope preset comes back in the failed list
  - successes count = 1
  - failed count = 1
  - successes[0].auto_assign_to_owner = True
  - successes[0].id: same as the id of the preset seeded in advance
  - successes[0].entity_id: same as the id of the preset seeded in advance
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = False
  - successes[0].deleted = False
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - failed[0].id: same as the id of the second preset

<a id="partial_bulk_editing-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/role_preset/test_partial_bulk_editing.py): pass

when the superadmin turns auto assign on for several presets at once, all of them come back with the new value and nothing failed

Given

- 2 presets and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Role preset preset-2: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.partial_bulk_update: user-1 turns auto assign on for 2 presets at once

Then

- every target preset comes back with the new value, and nothing failed
  - successes count = 2
  - successes[0].id: same as the id of the preset seeded in advance
  - successes[0].entity_id: same as the id of the preset seeded in advance
  - successes[0].name = 'preset-1'
  - successes[0].scope_type = 'project'
  - successes[0].auto_assign = True
  - successes[0].deleted = False
  - successes[0].created_at: the time this run wrote
  - successes[0].updated_at: the time this run wrote
  - successes[1].id: same as the id of the preset seeded in advance
  - successes[1].entity_id: same as the id of the preset seeded in advance
  - successes[1].name = 'preset-2'
  - successes[1].scope_type = 'project'
  - successes[1].auto_assign = True
  - successes[1].deleted = False
  - successes[1].created_at: the time this run wrote
  - successes[1].updated_at: the time this run wrote
  - failed = []

### update

<a id="editing-a-project-preset-takes-owner-assign"></a>

#### [a-project-preset-takes-owner-assign](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py): pass

turning on owner assignment of a project-scope preset brings the whole preset back turned on

Given

- one preset that already exists and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.update: user-1 turns on owner assignment of preset-1

Then

- the whole preset with owner assignment turned on comes back
  - auto_assign_to_owner = True
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - name = 'preset-1'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-the-superadmin-renames-a-preset"></a>

#### [the-superadmin-renames-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py): pass

when the superadmin renames a preset, the whole preset carrying the new name comes back

Given

- one preset that already exists and one superadmin
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.update: user-1 renames preset-1 to renamed-preset

Then

- the whole preset carrying the new name comes back
  - id: same as the id of the preset seeded in advance
  - entity_id: same as the id of the preset seeded in advance
  - name = 'renamed-preset'
  - scope_type = 'project'
  - auto_assign = False
  - deleted = False
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-a-domain-preset-refuses-owner-assign"></a>

#### [a-domain-preset-refuses-owner-assign](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py): pass

turning on owner assignment of a preset in a scope other than a project is rejected because there is no owner

Given

- one preset that already exists in the domain scope and one superadmin
  - Role preset preset-1: for the domain scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RolePresetAdapter.update: user-1 turns on owner assignment of preset-1

Then

- the call is rejected
  - rejected: RolePresetOwnerAssignNotAllowed

<a id="editing-a-user-granted-nothing-may-not-rename-a-preset"></a>

#### [a-user-granted-nothing-may-not-rename-a-preset](/tests/scenario/bai_scenario/manager/role_preset/test_editing.py): pass

when a user granted nothing tries to rename a preset, it is rejected for lack of permission

Given

- one preset that already exists and one user
  - Role preset preset-1: for the project scope, with automatic grant disabled
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RolePresetAdapter.update: user-1 renames preset-1 to renamed-preset

Then

- the call is rejected
  - rejected: NotEnoughPermission

