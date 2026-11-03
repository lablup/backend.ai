## login_client_type

[background](/src/ai/backend/manager/api/adapters/login_client_type/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/login_client_type/adapter.py)

Scenario: incomplete 4 / 8

- built from ops (8)
  - admin_create: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✗ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_update: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - update: representative success ✓ · representative rejection ✓

**admin_create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a login client type with a name and a description, the node comes back carrying the given values](#creating-a-login-client-type-made-with-a-description-carries-it-back) | answered |
| [when the superadmin creates a login client type with only a name, the node comes back with an empty description](#creating-the-superadmin-makes-a-login-client-type-with-a-name-alone) | answered |
| [when a login client type with the same name already exists, creating another with that name is rejected as a duplicate name](#creating-a-login-client-type-name-already-taken-is-refused) | rejected |
| [when a user who is not the superadmin creates a login client type, it is rejected because the role is insufficient](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type) | rejected |
| [turning permission enforcement off still does not let a user who is not the superadmin create a login client type](#creating-turning-enforcement-off-does-not-let-a-user-create-a-login-client-type) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when a user granted nothing reads a login client type by id, the whole login client type comes back. This read checks authentication alone](#reading-a-user-granted-nothing-reads-a-login-client-type-by-id) | answered |
| [when it is read by an id nothing answers to, it is rejected because the target cannot be found](#reading-reading-a-login-client-type-id-nothing-answers-to-is-refused) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several login client types at once, nothing is purged and every one comes back in the failed list because there is no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-login-client-types) | answered |
| [when the superadmin purges two login client types and an unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging-purging-several-login-client-types-answers-for-the-missing-one) | answered |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to update several login client types at once, nothing is updated and every one comes back in the failed list because there is no permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-login-client-types) | answered |
| [when the superadmin changes the descriptions of several login client types at once, they all come back with the new description and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-login-client-types-at-once) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin deletes a login client type, a response comes back carrying the id of the deleted type](#retiring-the-superadmin-deletes-a-login-client-type) | answered |
| [turning permission enforcement off lets even a user granted nothing delete a login client type](#retiring-turning-enforcement-off-lets-a-user-delete-a-login-client-type) | answered |
| [when a user granted nothing deletes a login client type, it is rejected for a lack of permission](#retiring-a-user-granted-nothing-may-not-delete-a-login-client-type) | rejected |
| [when the superadmin deletes an id nothing answers to, it is rejected because the target cannot be found](#retiring-deleting-a-login-client-type-id-nothing-answers-to-is-not-found) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when two login client types exist and a user granted nothing reads without a filter, both are counted](#searching-a-user-granted-nothing-counts-every-login-client-type-laid) | answered |

**update**

| scenario | verdict |
|---|---|
| [when it is updated without giving any value, the node comes back with nothing changed](#editing-a-login-client-type-edit-giving-no-value-changes-nothing) | answered |
| [when a login client type with a description is updated to clear the description, the description goes away](#editing-clearing-a-login-client-type-description-leaves-it-empty) | answered |
| [when the superadmin changes only the name of a login client type, the name becomes the new value and the description stays as it was](#editing-renaming-a-login-client-type-leaves-its-description-alone) | answered |
| [turning permission enforcement off lets even a user granted nothing update a login client type](#editing-turning-enforcement-off-lets-a-user-edit-a-login-client-type) | answered |
| [when a user granted nothing updates an id nothing answers to, it is rejected for a lack of permission rather than a missing target, because the permission check runs first and no permission is granted on a row that does not exist](#editing-a-user-granted-nothing-editing-an-unknown-login-client-type-id-is-refused-for-permission) | rejected |
| [when a user granted nothing updates a login client type, it is rejected for a lack of permission. The type belongs to no scope, so there is no way to receive that permission](#editing-a-user-granted-nothing-may-not-edit-a-login-client-type) | rejected |
| [when one of two login client types is renamed to the name of the other, it is rejected as a duplicate name. Unlike at creation, the repository constraint violation propagates as it is](#editing-renaming-a-login-client-type-to-a-name-already-taken-is-refused) | rejected |
| [when the superadmin updates an id nothing answers to, it is rejected because the target cannot be found](#editing-the-superadmin-editing-a-login-client-type-id-nothing-answers-to-is-not-found) | rejected |

### admin_create

<a id="creating-a-login-client-type-made-with-a-description-carries-it-back"></a>

#### [a-login-client-type-made-with-a-description-carries-it-back](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

when the superadmin creates a login client type with a name and a description, the node comes back carrying the given values

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- LoginClientTypeAdapter.admin_create: user-1 creates the login client type webui

Then

- the whole login client type just created comes back
  - id: skipped: the database generates it
  - name = 'webui'
  - description = 'the description just set'
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="creating-the-superadmin-makes-a-login-client-type-with-a-name-alone"></a>

#### [the-superadmin-makes-a-login-client-type-with-a-name-alone](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

when the superadmin creates a login client type with only a name, the node comes back with an empty description

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- LoginClientTypeAdapter.admin_create: user-1 creates the login client type webui

Then

- the whole login client type just created comes back
  - id: skipped: the database generates it
  - name = 'webui'
  - description = None
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="creating-a-login-client-type-name-already-taken-is-refused"></a>

#### [a-login-client-type-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

when a login client type with the same name already exists, creating another with that name is rejected as a duplicate name

Given

- one login client type and one superadmin
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.admin_create: user-1 creates the login client type again with the existing name client-1

Then

- the call is rejected
  - rejected: LoginClientTypeConflict

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

when a user who is not the superadmin creates a login client type, it is rejected because the role is insufficient

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- LoginClientTypeAdapter.admin_create: user-1 creates the login client type webui

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-does-not-let-a-user-create-a-login-client-type"></a>

#### [turning-enforcement-off-does-not-let-a-user-create-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_creating.py): pass

turning permission enforcement off still does not let a user who is not the superadmin create a login client type

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- LoginClientTypeAdapter.admin_create: user-1 creates the login client type webui

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-a-user-granted-nothing-reads-a-login-client-type-by-id"></a>

#### [a-user-granted-nothing-reads-a-login-client-type-by-id](/tests/scenario/bai_scenario/manager/login_client_type/test_reading.py): pass

when a user granted nothing reads a login client type by id, the whole login client type comes back. This read checks authentication alone

Given

- one login client type and one regular user
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.get: user-1 reads a login client type by client-1

Then

- the whole login client type created in advance comes back
  - id: skipped: the database generates it
  - name = 'client-1'
  - description = 'a login client type created in advance'
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="reading-reading-a-login-client-type-id-nothing-answers-to-is-refused"></a>

#### [reading-a-login-client-type-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_reading.py): pass

when it is read by an id nothing answers to, it is rejected because the target cannot be found

Given

- one login client type and one regular user
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.get: user-1 reads a login client type by an id nothing answers to

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-login-client-types"></a>

#### [a-user-granted-nothing-purges-none-of-several-login-client-types](/tests/scenario/bai_scenario/manager/login_client_type/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several login client types at once, nothing is purged and every one comes back in the failed list because there is no permission

Given

- 2 login client types and one regular user
  - Login client type wanted-1
  - Login client type other-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.partial_bulk_purge: user-1 purges 2 login client types at once

Then

- no login client type is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target login client type
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target login client type
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-login-client-types-answers-for-the-missing-one"></a>

#### [purging-several-login-client-types-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/login_client_type/test_partial_bulk_purging.py): pass

when the superadmin purges two login client types and an unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it

Given

- 2 login client types and one superadmin
  - Login client type wanted-1
  - Login client type other-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.partial_bulk_purge: user-1 purges 2 login client types and one unknown id at once

Then

- every login client type comes back in the processed list and the unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - id: skipped: the database generates it
  - name = 'wanted-1'
  - description = 'a login client type created in advance'
  - created_at: the time this run wrote
  - modified_at: the time this run wrote
  - id: skipped: the database generates it
  - name = 'other-1'
  - description = 'a login client type created in advance'
  - created_at: the time this run wrote
  - modified_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-login-client-types"></a>

#### [a-user-granted-nothing-edits-none-of-several-login-client-types](/tests/scenario/bai_scenario/manager/login_client_type/test_partial_bulk_editing.py): pass

when a user granted nothing tries to update several login client types at once, nothing is updated and every one comes back in the failed list because there is no permission

Given

- 2 login client types and one regular user
  - Login client type wanted-1
  - Login client type other-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.partial_bulk_update: user-1 updates the description of 2 login client types at once

Then

- no login client type is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target login client type
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target login client type
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-login-client-types-at-once"></a>

#### [the-superadmin-edits-several-login-client-types-at-once](/tests/scenario/bai_scenario/manager/login_client_type/test_partial_bulk_editing.py): pass

when the superadmin changes the descriptions of several login client types at once, they all come back with the new description and nothing failed

Given

- 2 login client types and one superadmin
  - Login client type wanted-1
  - Login client type other-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.partial_bulk_update: user-1 updates the description of 2 login client types at once

Then

- every login client type comes back with the new description and nothing failed
  - successes count = 2
  - failed = []
  - id: skipped: the database generates it
  - name = 'wanted-1'
  - description = 'the description updated at once'
  - created_at: the time this run wrote
  - modified_at: the time this run wrote
  - id: skipped: the database generates it
  - name = 'other-1'
  - description = 'the description updated at once'
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

### purge

<a id="retiring-the-superadmin-deletes-a-login-client-type"></a>

#### [the-superadmin-deletes-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py): pass

when the superadmin deletes a login client type, a response comes back carrying the id of the deleted type

Given

- one login client type and one superadmin
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.purge: user-1 deletes client-1

Then

- the id of the deleted login client type comes back
  - id: same as the login client type created in advance

<a id="retiring-turning-enforcement-off-lets-a-user-delete-a-login-client-type"></a>

#### [turning-enforcement-off-lets-a-user-delete-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py): pass

turning permission enforcement off lets even a user granted nothing delete a login client type

Given

- one login client type and one regular user
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.purge: user-1 deletes client-1

Then

- the id of the deleted login client type comes back
  - id: same as the login client type created in advance

<a id="retiring-a-user-granted-nothing-may-not-delete-a-login-client-type"></a>

#### [a-user-granted-nothing-may-not-delete-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py): pass

when a user granted nothing deletes a login client type, it is rejected for a lack of permission

Given

- one login client type and one regular user
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.purge: user-1 deletes client-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-deleting-a-login-client-type-id-nothing-answers-to-is-not-found"></a>

#### [deleting-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_retiring.py): pass

when the superadmin deletes an id nothing answers to, it is rejected because the target cannot be found

Given

- one login client type and one superadmin
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.purge: user-1 deletes an id nothing answers to

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search

<a id="searching-a-user-granted-nothing-counts-every-login-client-type-laid"></a>

#### [a-user-granted-nothing-counts-every-login-client-type-laid](/tests/scenario/bai_scenario/manager/login_client_type/test_searching.py): pass

when two login client types exist and a user granted nothing reads without a filter, both are counted

Given

- 2 login client types and one regular user
  - Login client type wanted-1
  - Login client type other-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.search: user-1 reads every login client type without a filter

Then

- every login client type created in advance is counted
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

### update

<a id="editing-a-login-client-type-edit-giving-no-value-changes-nothing"></a>

#### [a-login-client-type-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

when it is updated without giving any value, the node comes back with nothing changed

Given

- one login client type and one superadmin
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.update: user-1 updates nothing of client-1

Then

- the whole login client type created in advance comes back
  - id: skipped: the database generates it
  - name = 'client-1'
  - description = 'a login client type created in advance'
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="editing-clearing-a-login-client-type-description-leaves-it-empty"></a>

#### [clearing-a-login-client-type-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

when a login client type with a description is updated to clear the description, the description goes away

Given

- one login client type and one superadmin
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.update: user-1 updates the description of client-1

Then

- the whole login client type created in advance comes back
  - id: skipped: the database generates it
  - name = 'client-1'
  - description = None
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="editing-renaming-a-login-client-type-leaves-its-description-alone"></a>

#### [renaming-a-login-client-type-leaves-its-description-alone](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

when the superadmin changes only the name of a login client type, the name becomes the new value and the description stays as it was

Given

- one login client type and one superadmin
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.update: user-1 updates the name of client-1

Then

- the whole login client type created in advance comes back
  - id: skipped: the database generates it
  - name = 'renamed'
  - description = 'a login client type created in advance'
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="editing-turning-enforcement-off-lets-a-user-edit-a-login-client-type"></a>

#### [turning-enforcement-off-lets-a-user-edit-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

turning permission enforcement off lets even a user granted nothing update a login client type

Given

- one login client type and one regular user
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.update: user-1 updates the name of client-1

Then

- the whole login client type created in advance comes back
  - id: skipped: the database generates it
  - name = 'renamed'
  - description = 'a login client type created in advance'
  - created_at: the time this run wrote
  - modified_at: the time this run wrote

<a id="editing-a-user-granted-nothing-editing-an-unknown-login-client-type-id-is-refused-for-permission"></a>

#### [a-user-granted-nothing-editing-an-unknown-login-client-type-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

when a user granted nothing updates an id nothing answers to, it is rejected for a lack of permission rather than a missing target, because the permission check runs first and no permission is granted on a row that does not exist

Given

- one login client type and one regular user
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.update: user-1 updates the name of an id nothing answers to

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-a-user-granted-nothing-may-not-edit-a-login-client-type"></a>

#### [a-user-granted-nothing-may-not-edit-a-login-client-type](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

when a user granted nothing updates a login client type, it is rejected for a lack of permission. The type belongs to no scope, so there is no way to receive that permission

Given

- one login client type and one regular user
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - regular user user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.update: user-1 updates the name of client-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-renaming-a-login-client-type-to-a-name-already-taken-is-refused"></a>

#### [renaming-a-login-client-type-to-a-name-already-taken-is-refused](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

when one of two login client types is renamed to the name of the other, it is rejected as a duplicate name. Unlike at creation, the repository constraint violation propagates as it is

Given

- 2 login client types and one superadmin
  - Login client type wanted-1
  - Login client type other-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.update: user-1 renames wanted-1 to other-1

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="editing-the-superadmin-editing-a-login-client-type-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-login-client-type-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/login_client_type/test_editing.py): pass

when the superadmin updates an id nothing answers to, it is rejected because the target cannot be found

Given

- one login client type and one superadmin
  - Login client type client-1
  - Domain home-1
  - Prepare a user granted read permission on login_client_type in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every login_client_type
    - superadmin user-1: holds Role public-reader-1

When

- LoginClientTypeAdapter.update: user-1 updates the name of an id nothing answers to

Then

- the call is rejected
  - rejected: EntityNotFoundError

