## role_preset

[background](/src/ai/backend/manager/api/adapters/role_preset/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/role_preset/adapter.py)

Scenario: incomplete 16 / 21

- built from ops (14)
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - batch_load_permissions_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - bulk_delete: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - bulk_purge: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - bulk_restore: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - delete: representative success ✓ · representative rejection ✓
  - get: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_delete: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_restore: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - restore: representative success ✓ · representative rejection ✓
  - search: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - search_permission_presets: representative success ✗ · representative rejection ✗: SCENARIO-GAP
- direct implementation (7)
  - atomic_bulk_add_permissions: success present 1 · rejection present 1 (single_entity)
  - bulk_add_permissions: success absent · rejection absent (single_entity): SCENARIO-GAP
  - bulk_remove_permissions: success absent · rejection absent (partial_bulk_field): SCENARIO-GAP
  - create: success absent · rejection absent (scope): SCENARIO-GAP
  - partial_bulk_remove_permissions: success present 2 · rejection absent (partial_bulk_field): SCENARIO-GAP
  - partial_bulk_update: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - update: success present 1 · rejection present 1 (single_entity)

**delete**

| scenario | verdict |
|---|---|
| [when the superadmin soft deletes a preset, the whole preset marked deleted comes back](#deleting-the-superadmin-soft-deletes-a-preset) | answered |
| [when a user granted nothing tries to soft delete a preset, it is rejected for lack of permission](#deleting-a-user-granted-nothing-may-not-soft-delete-a-preset) | rejected |

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

**atomic_bulk_add_permissions**

| scenario | verdict |
|---|---|
| [when the superadmin adds two permission entries to a preset that has none, the two entries added come back under the preset](#permission_editing-the-superadmin-adds-entries-to-a-preset) | answered |
| [when a user granted nothing tries to add permission entries to a preset, it is rejected for lack of permission](#permission_editing-a-user-granted-nothing-may-not-add-entries) | rejected |

**partial_bulk_remove_permissions**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to remove several permission entries at once, none is removed and every one comes back in the failed list for lack of permission](#permission_editing-a-user-granted-nothing-removes-none-of-the-entries) | answered |
| [when the superadmin removes two permission entries and one missing id at once, the two come back in the processed list and the missing id comes back in the failed list](#permission_editing-removing-entries-answers-for-the-missing-one) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to edit several presets at once, none is edited and every one comes back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets) | answered |
| [when the superadmin turns auto assign on for several presets at once, all of them come back with the new value and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-presets-at-once) | answered |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin renames a preset, the whole preset carrying the new name comes back](#editing-the-superadmin-renames-a-preset) | answered |
| [when a user granted nothing tries to rename a preset, it is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-rename-a-preset) | rejected |

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

