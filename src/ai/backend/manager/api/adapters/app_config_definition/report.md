## app_config_definition

[background](/src/ai/backend/manager/api/adapters/app_config_definition/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/app_config_definition/adapter.py)

Scenario: incomplete 1 / 6

- built from ops (4)
  - admin_create: representative success ✓ · representative rejection ✓
  - admin_get: representative success ✓ · representative rejection ✓
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
- direct implementation (2)
  - partial_bulk_purge: success present 2 · rejection absent (partial_bulk): SCENARIO-GAP
  - purge: success present 2 · rejection present 2 (single_entity)

**admin_create**

| scenario | verdict |
|---|---|
| [when the superadmin registers a config definition with only a name, the node comes back with the name as given and the id and times filled by the server](#registering-the-superadmin-registers-a-name) | answered |
| [when the superadmin registers again with a name already registered, it is rejected, but the answer does not say the name is taken and the database constraint violation propagates as it is](#registering-a-name-already-registered-is-refused-as-a-constraint-violation) | rejected |
| [when a regular user tries to register a config definition, it is rejected because the user has no superadmin privilege](#registering-a-user-who-is-not-the-superadmin-may-not-register-a-name) | rejected |
| [turning RBAC enforcement off still rejects registering a config definition by a regular user](#registering-turning-enforcement-off-still-does-not-let-a-user-register-a-name) | rejected |

**admin_get**

| scenario | verdict |
|---|---|
| [when one config definition exists and the superadmin reads it by id, every field of the definition comes back](#reading-the-superadmin-reads-a-definition-by-id) | answered |
| [turning RBAC enforcement off lets a regular user with no permission read a config definition](#reading-turning-enforcement-off-lets-a-plain-user-read) | answered |
| [when a regular user with no permission reads the same config definition, it is rejected because the user has no entity read permission](#reading-a-user-who-is-not-the-superadmin-may-not-read-a-definition) | rejected |
| [when the superadmin reads by a missing id, it is rejected because no such target exists. Only a user who passes the permission check sees this answer](#reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

**admin_search**

| scenario | verdict |
|---|---|
| [when three config definitions exist and the superadmin searches everything without a filter, all three are counted](#searching-the-superadmin-counts-every-definition) | answered |
| [when a regular user searches everything, it is rejected because the user has no superadmin privilege](#searching-a-user-who-is-not-the-superadmin-may-not-search-definitions) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [an empty id list answers empty](#reading_many-an-empty-id-list-answers-empty) | answered |
| [when the superadmin reads the same config definition id twice, the same node comes back twice, keeping the input order](#reading_many-duplicate-ids-keep-their-input-positions) | answered |
| [when the superadmin reads two config definitions and one missing id at once, the two come back as nodes and the item for the missing id is empty. Only a user who passes the permission check sees an empty item](#reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty) | answered |
| [when a user who is not the superadmin reads two config definitions and one missing id at once, the whole request is not blocked; all three items are rejected for that item alone for lack of permission](#reading_many-a-user-who-is-not-the-superadmin-is-refused-per-id) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a regular user with no permission tries to purge two config definitions at once, nothing is purged and both come back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-definitions) | answered |
| [when the superadmin purges two config definitions and a missing id at once, both come back in the succeeded list and the missing id comes back in the failed list because no such target exists](#partial_bulk_purging-purging-several-answers-for-the-missing-one) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges a config definition holding an allow-list entry and a config fragment, the dependent rows do not block the purge and the id of the definition comes back](#purging-a-definition-holding-an-entry-and-a-fragment-is-still-purged) | answered |
| [when the superadmin purges a config definition with no dependent rows, the purged id comes back](#purging-the-superadmin-purges-a-definition) | answered |
| [when a regular user with no permission purges the same config definition, it is rejected because the user has no entity purge permission](#purging-a-user-who-is-not-the-superadmin-may-not-purge-a-definition) | rejected |
| [when the superadmin purges a missing id, it is rejected because no such target exists](#purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

### admin_create

<a id="registering-the-superadmin-registers-a-name"></a>

#### [the-superadmin-registers-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py): pass

when the superadmin registers a config definition with only a name, the node comes back with the name as given and the id and times filled by the server

Given

- one config definition, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_create: user-1 registers the config name fresh-config

Then

- every field of the registered config definition comes back
  - ID: skipped: the database generates it
  - config_name = 'fresh-config'
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="registering-a-name-already-registered-is-refused-as-a-constraint-violation"></a>

#### [a-name-already-registered-is-refused-as-a-constraint-violation](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py): pass

when the superadmin registers again with a name already registered, it is rejected, but the answer does not say the name is taken and the database constraint violation propagates as it is

Given

- one config definition, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_create: user-1 registers the config name config-1

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="registering-a-user-who-is-not-the-superadmin-may-not-register-a-name"></a>

#### [a-user-who-is-not-the-superadmin-may-not-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py): pass

when a regular user tries to register a config definition, it is rejected because the user has no superadmin privilege

Given

- one config definition, and one Regular user with no permission
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_create: user-1 registers the config name fresh-config

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="registering-turning-enforcement-off-still-does-not-let-a-user-register-a-name"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-register-a-name](/tests/scenario/bai_scenario/manager/app_config_definition/test_registering.py): pass

turning RBAC enforcement off still rejects registering a config definition by a regular user

Given

- one config definition, and one Regular user with no permission
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_create: user-1 registers the config name fresh-config

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### admin_get

<a id="reading-the-superadmin-reads-a-definition-by-id"></a>

#### [the-superadmin-reads-a-definition-by-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py): pass

when one config definition exists and the superadmin reads it by id, every field of the definition comes back

Given

- one config definition, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_get: user-1 reads config-1 by id

Then

- every field of the config definition made in advance comes back
  - ID: same as the config definition made in advance
  - config_name = 'config-1'
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-turning-enforcement-off-lets-a-plain-user-read"></a>

#### [turning-enforcement-off-lets-a-plain-user-read](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py): pass

turning RBAC enforcement off lets a regular user with no permission read a config definition

Given

- one config definition, and one Regular user with no permission
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_get: user-1 reads config-1 by id

Then

- every field of the config definition made in advance comes back
  - ID: same as the config definition made in advance
  - config_name = 'config-1'
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-a-user-who-is-not-the-superadmin-may-not-read-a-definition"></a>

#### [a-user-who-is-not-the-superadmin-may-not-read-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py): pass

when a regular user with no permission reads the same config definition, it is rejected because the user has no entity read permission

Given

- one config definition, and one Regular user with no permission
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_get: user-1 reads config-1 by id

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading.py): pass

when the superadmin reads by a missing id, it is rejected because no such target exists. Only a user who passes the permission check sees this answer

Given

- one config definition, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_get: user-1 reads by a missing id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### admin_search

<a id="searching-the-superadmin-counts-every-definition"></a>

#### [the-superadmin-counts-every-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py): pass

when three config definitions exist and the superadmin searches everything without a filter, all three are counted

Given

- 3 config definitions, and one superadmin
  - Domain home-1
  - Config definition definition-1: the config of this name is registered
  - Config definition definition-2: the config of this name is registered
  - Config definition definition-3: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_search: user-1 reads everything without a filter

Then

- every config definition made in advance is counted, and only those
  - items = ['definition-1', 'definition-2', 'definition-3']
  - total_count = 3
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-definitions"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-definitions](/tests/scenario/bai_scenario/manager/app_config_definition/test_searching.py): pass

when a regular user searches everything, it is rejected because the user has no superadmin privilege

Given

- 3 config definitions, and one Regular user with no permission
  - Domain home-1
  - Config definition definition-1: the config of this name is registered
  - Config definition definition-2: the config of this name is registered
  - Config definition definition-3: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.admin_search: user-1 reads everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="reading_many-an-empty-id-list-answers-empty"></a>

#### [an-empty-id-list-answers-empty](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py): pass

an empty id list answers empty

Given

- two config definitions, and one Regular user with no permission
  - Domain home-1
  - Config definition first-1: the config of this name is registered
  - Config definition second-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.batch_load_by_ids: user-1 reads with an empty id list

Then

- an empty answer comes back
  - items = []

<a id="reading_many-duplicate-ids-keep-their-input-positions"></a>

#### [duplicate-ids-keep-their-input-positions](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py): pass

when the superadmin reads the same config definition id twice, the same node comes back twice, keeping the input order

Given

- two config definitions, and one superadmin
  - Domain home-1
  - Config definition first-1: the config of this name is registered
  - Config definition second-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.batch_load_by_ids: user-1 reads the id of the first config definition twice

Then

- the same config definition comes back for both items of the duplicate id
  - items = 2
  - items[0].ID: same as the first config definition made in advance
  - items[1].ID: same as the first config definition made in advance

<a id="reading_many-the-superadmin-reads-both-and-a-missing-id-comes-back-empty"></a>

#### [the-superadmin-reads-both-and-a-missing-id-comes-back-empty](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py): pass

when the superadmin reads two config definitions and one missing id at once, the two come back as nodes and the item for the missing id is empty. Only a user who passes the permission check sees an empty item

Given

- two config definitions, and one superadmin
  - Domain home-1
  - Config definition first-1: the config of this name is registered
  - Config definition second-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.batch_load_by_ids: user-1 reads first-1, second-1 and a missing id at once

Then

- the two existing items come back as nodes and the item for the missing id is empty
  - items = 3
  - items[0].ID: same as the first config definition made in advance
  - items[1].ID: same as the second config definition made in advance
  - items[2] = None

<a id="reading_many-a-user-who-is-not-the-superadmin-is-refused-per-id"></a>

#### [a-user-who-is-not-the-superadmin-is-refused-per-id](/tests/scenario/bai_scenario/manager/app_config_definition/test_reading_many.py): pass

when a user who is not the superadmin reads two config definitions and one missing id at once, the whole request is not blocked; all three items are rejected for that item alone for lack of permission

Given

- two config definitions, and one Regular user with no permission
  - Domain home-1
  - Config definition first-1: the config of this name is registered
  - Config definition second-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.batch_load_by_ids: user-1 reads first-1, second-1 and a missing id at once

Then

- both existing items and the missing id are rejected for that item alone
  - items = 3
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-definitions"></a>

#### [a-user-granted-nothing-purges-none-of-several-definitions](/tests/scenario/bai_scenario/manager/app_config_definition/test_partial_bulk_purging.py): pass

when a regular user with no permission tries to purge two config definitions at once, nothing is purged and both come back in the failed list for lack of permission

Given

- two config definitions, and one Regular user with no permission
  - Domain home-1
  - Config definition first-1: the config of this name is registered
  - Config definition second-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.partial_bulk_purge: user-1 purges two config definitions at once

Then

- no config definition is processed and both come back in the failed list for lack of permission
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id prepared
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id prepared
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-answers-for-the-missing-one"></a>

#### [purging-several-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/app_config_definition/test_partial_bulk_purging.py): pass

when the superadmin purges two config definitions and a missing id at once, both come back in the succeeded list and the missing id comes back in the failed list because no such target exists

Given

- two config definitions, and one superadmin
  - Domain home-1
  - Config definition first-1: the config of this name is registered
  - Config definition second-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.partial_bulk_purge: user-1 purges two config definitions and a missing id at once

Then

- both config definitions come back in the succeeded list, and the missing id comes back in the failed list because no such target exists
  - successes: same as the two ids prepared
  - failed count = 1
  - failed[0].id: same as the missing id put in the request
  - failed[0].message: a reason containing 'not found'

### purge

<a id="purging-a-definition-holding-an-entry-and-a-fragment-is-still-purged"></a>

#### [a-definition-holding-an-entry-and-a-fragment-is-still-purged](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py): pass

when the superadmin purges a config definition holding an allow-list entry and a config fragment, the dependent rows do not block the purge and the id of the definition comes back

Given

- one config definition holding an allow-list entry and a config fragment, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Allow-list entry entry-1: the config of this name can be set in the public scope, rank is the default of the scope kind
  - public app config fragment public-fragment-1: value {'theme': 'light'}
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.purge: user-1 purges config-1

Then

- it answers with the id of the purged config definition
  - ID: same as the config definition made in advance

<a id="purging-the-superadmin-purges-a-definition"></a>

#### [the-superadmin-purges-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py): pass

when the superadmin purges a config definition with no dependent rows, the purged id comes back

Given

- one config definition, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.purge: user-1 purges config-1

Then

- it answers with the id of the purged config definition
  - ID: same as the config definition made in advance

<a id="purging-a-user-who-is-not-the-superadmin-may-not-purge-a-definition"></a>

#### [a-user-who-is-not-the-superadmin-may-not-purge-a-definition](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py): pass

when a regular user with no permission purges the same config definition, it is rejected because the user has no entity purge permission

Given

- one config definition, and one Regular user with no permission
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.purge: user-1 purges config-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/app_config_definition/test_purging.py): pass

when the superadmin purges a missing id, it is rejected because no such target exists

Given

- one config definition, and one superadmin
  - Domain home-1
  - Config definition config-1: the config of this name is registered
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AppConfigDefinitionAdapter.purge: user-1 purges a missing id

Then

- the call is rejected
  - rejected: EntityNotFoundError

