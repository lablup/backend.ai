## entity_label

[background](/src/ai/backend/manager/api/adapters/entity_label/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/entity_label/adapter.py)

Scenario: incomplete 1 / 7

- built from ops (7)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - partial_bulk_upsert: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
  - search_on: representative success ✓ · representative rejection ✓
  - upsert: representative success ✓ · representative rejection ✓

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when an empty id list is given, an empty list comes back without a check](#batch_loading-a-batch-load-of-no-ids-answers-an-empty-list) | answered |
| [when a user who can read the domains loads two labels and one unknown id at once, the two labels and an empty value come back in input order](#batch_loading-a-reader-loads-two-labels-and-an-unknown-id-in-order) | answered |
| [when a user with no permission loads a label by id, the call succeeds but that entry is rejected for lack of permission](#batch_loading-a-user-granted-nothing-gets-a-rejection-for-the-label) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [purging an existing id followed by an unknown id purges the one that exists and puts the unknown id in the failed list](#partial_bulk_purging-a-missing-id-beside-a-label-is-one-failed-item) | answered |
| [when a user with no permission purges two labels, nothing is purged and both come back in the failed list](#partial_bulk_purging-a-user-granted-nothing-purges-nothing) | answered |
| [purging one label on each of two entities purges both](#partial_bulk_purging-a-writer-purges-labels-of-two-entities) | answered |
| [when a user granted update permission purges two labels of one entity, both are purged and nothing failed](#partial_bulk_purging-a-writer-purges-two-labels-of-one-entity) | answered |
| [purging only two unknown ids purges nothing and puts both in the failed list](#partial_bulk_purging-every-id-missing-is-answered-per-id) | answered |
| [with update permission on one entity only, only that entity's label is purged and the other comes back in the failed list](#partial_bulk_purging-only-the-label-of-the-writable-entity-is-purged) | answered |
| [turning RBAC enforcement off lets a user with no permission purge two labels](#partial_bulk_purging-turning-enforcement-off-lets-anyone-purge) | answered |

**partial_bulk_upsert**

| scenario | verdict |
|---|---|
| [adding a key that is already attached changes only the value of the same label](#partial_bulk_upserting-a-key-already-on-the-entity-takes-the-new-value) | answered |
| [when a user with no permission adds labels, none is added and both entities come back in the failed list](#partial_bulk_upserting-a-user-granted-nothing-labels-nothing) | answered |
| [when a user granted update permission adds two keys to two entities, four labels come back and nothing failed](#partial_bulk_upserting-a-writer-labels-two-entities-with-two-keys) | answered |
| [when the same entity appears in several items, its label comes back for each key and nothing failed](#partial_bulk_upserting-one-entity-in-several-items-gets-every-key) | answered |
| [with update permission on one entity only, its two labels come back and the other entity comes back in the failed list once per key](#partial_bulk_upserting-only-the-writable-entity-is-labeled) | answered |
| [turning RBAC enforcement off lets a user with no permission add labels to two entities with nothing failed](#partial_bulk_upserting-turning-enforcement-off-lets-anyone-label) | answered |
| [when even one type that has no connection and call path is mixed in, the whole request is rejected as invalid and nothing is written](#partial_bulk_upserting-an-unwired-type-refuses-the-whole-call) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when a user granted update permission purges one label, the whole label comes back](#purging-a-writer-purges-one-label) | answered |
| [when a user with no permission purges a label, the request is rejected](#purging-a-user-granted-nothing-cannot-purge-the-label) | rejected |
| [when a user granted update permission purges an unknown label id, the request is rejected](#purging-an-unknown-label-id-is-refused) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when a user who can read two domains pages through both at once, both labels come back whole](#searching-a-reader-pages-through-the-labels-of-two-entities) | answered |
| [when a user with no permission pages through a domain's labels, the call is rejected for lack of permission](#searching-a-user-granted-nothing-cannot-page-through-the-named-scopes) | rejected |

**search_on**

| scenario | verdict |
|---|---|
| [when a user who can read one domain pages through it narrowed to one key, only that key's label comes back](#searching-a-reader-pages-through-one-entities-labels-under-a-key) | answered |
| [when a user with no permission pages through a held domain's labels, the call is rejected for lack of permission](#searching-a-user-granted-nothing-cannot-page-through-a-held-scope) | rejected |

**upsert**

| scenario | verdict |
|---|---|
| [when a user granted update permission puts a new key on a domain, the whole label comes back](#upserting-a-writer-puts-a-new-key-on-an-entity) | answered |
| [when a user granted update permission writes a key that is already attached, the same label comes back with only its value replaced](#upserting-a-writer-replaces-the-value-of-an-existing-key) | answered |
| [when a user with no permission puts a label on a domain, the call is rejected for lack of permission](#upserting-a-user-granted-nothing-cannot-put-a-label-on-the-domain) | rejected |

### batch_load_by_ids

<a id="batch_loading-a-batch-load-of-no-ids-answers-an-empty-list"></a>

#### [a-batch-load-of-no-ids-answers-an-empty-list](/tests/scenario/bai_scenario/manager/entity_label/test_batch_loading.py): pass

when an empty id list is given, an empty list comes back without a check

Given

- 1 domains and one user
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.batch_load_by_ids: user-1 loads with an empty id list

Then

- an empty list comes back
  - loaded = []

<a id="batch_loading-a-reader-loads-two-labels-and-an-unknown-id-in-order"></a>

#### [a-reader-loads-two-labels-and-an-unknown-id-in-order](/tests/scenario/bai_scenario/manager/entity_label/test_batch_loading.py): pass

when a user who can read the domains loads two labels and one unknown id at once, the two labels and an empty value come back in input order

Given

- 1 domains with 2 labels each and one user who can read 1 of them
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Domain target-1: label tier=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to read the domain
    - Role domain-reader-1: applies only within the scope it is granted in
    - Role domain-reader-1: READ allowed on every domain
    - regular user user-1: holds Role domain-reader-1

When

- EntityLabelAdapter.batch_load_by_ids: user-1 loads 2 labels and one unknown id at once

Then

- the labels attached in advance come back as nodes and the unknown id entry as an empty value
  - length = 3
  - [0].entity_type = 'domain'
  - [0].entity_id: same as the id of the target domain
  - [0].key = 'team'
  - [0].value = 'before'
  - [0].created_at: the time this run wrote
  - [0].updated_at: the time this run wrote
  - [0].id: same as the id of the label attached in advance
  - [0].field_id: same as the id of the label attached in advance
  - [1].entity_type = 'domain'
  - [1].entity_id: same as the id of the target domain
  - [1].key = 'tier'
  - [1].value = 'before'
  - [1].created_at: the time this run wrote
  - [1].updated_at: the time this run wrote
  - [1].id: same as the id of the label attached in advance
  - [1].field_id: same as the id of the label attached in advance
  - [2] = None

<a id="batch_loading-a-user-granted-nothing-gets-a-rejection-for-the-label"></a>

#### [a-user-granted-nothing-gets-a-rejection-for-the-label](/tests/scenario/bai_scenario/manager/entity_label/test_batch_loading.py): pass

when a user with no permission loads a label by id, the call succeeds but that entry is rejected for lack of permission

Given

- 1 domains with 1 labels each and one user
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.batch_load_by_ids: user-1 loads 1 labels at once

Then

- that entry is rejected for lack of permission
  - length = 1
  - rejected: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-missing-id-beside-a-label-is-one-failed-item"></a>

#### [a-missing-id-beside-a-label-is-one-failed-item](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

purging an existing id followed by an unknown id purges the one that exists and puts the unknown id in the failed list

Given

- 1 domains with 1 labels each and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.partial_bulk_purge: user-1 purges 1 labels and 1 unknown ids at once

Then

- 1 labels come back purged, and the unknown id come back in the failed list as not found
  - successes count = 1
  - successes[0]: same as the id of the label attached in advance
  - failed count = 1
  - failed[0].id: same as the id put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-a-user-granted-nothing-purges-nothing"></a>

#### [a-user-granted-nothing-purges-nothing](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

when a user with no permission purges two labels, nothing is purged and both come back in the failed list

Given

- 1 domains with 2 labels each and one user
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Domain target-1: label tier=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.partial_bulk_purge: user-1 purges 2 labels at once

Then

- 0 labels come back purged and the rest come back in the failed list
  - successes count = 0
  - failed count = 2
  - failed[0].id: same as the id put in the request
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id put in the request
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-a-writer-purges-labels-of-two-entities"></a>

#### [a-writer-purges-labels-of-two-entities](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

purging one label on each of two entities purges both

Given

- 2 domains with 1 labels each and one user granted permission to update 2 of them
  - Domain home-1
  - Domain target-1
  - Domain target-2
  - Domain target-1: label team=before
  - Domain target-2: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1
    - Role domain-writer-2: applies only within the scope it is granted in
    - Role domain-writer-2: READ allowed on every domain
    - Role domain-writer-2: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-2

When

- EntityLabelAdapter.partial_bulk_purge: user-1 purges 2 labels at once

Then

- 2 labels come back purged and the rest come back in the failed list
  - successes count = 2
  - successes[0]: same as the id of the label attached in advance
  - successes[1]: same as the id of the label attached in advance
  - failed count = 0

<a id="partial_bulk_purging-a-writer-purges-two-labels-of-one-entity"></a>

#### [a-writer-purges-two-labels-of-one-entity](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

when a user granted update permission purges two labels of one entity, both are purged and nothing failed

Given

- 1 domains with 2 labels each and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Domain target-1: label tier=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.partial_bulk_purge: user-1 purges 2 labels at once

Then

- 2 labels come back purged and the rest come back in the failed list
  - successes count = 2
  - successes[0]: same as the id of the label attached in advance
  - successes[1]: same as the id of the label attached in advance
  - failed count = 0

<a id="partial_bulk_purging-every-id-missing-is-answered-per-id"></a>

#### [every-id-missing-is-answered-per-id](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

purging only two unknown ids purges nothing and puts both in the failed list

Given

- 1 domains and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.partial_bulk_purge: user-1 purges 0 labels and 2 unknown ids at once

Then

- 0 labels come back purged, and the unknown ids come back in the failed list as not found
  - successes count = 0
  - failed count = 2
  - failed[0].id: same as the id put in the request
  - failed[0].message: a reason containing 'not found'
  - failed[1].id: same as the id put in the request
  - failed[1].message: a reason containing 'not found'

<a id="partial_bulk_purging-only-the-label-of-the-writable-entity-is-purged"></a>

#### [only-the-label-of-the-writable-entity-is-purged](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

with update permission on one entity only, only that entity's label is purged and the other comes back in the failed list

Given

- 2 domains with 1 labels each and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Domain target-2
  - Domain target-1: label team=before
  - Domain target-2: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.partial_bulk_purge: user-1 purges 2 labels at once

Then

- 1 labels come back purged and the rest come back in the failed list
  - successes count = 1
  - successes[0]: same as the id of the label attached in advance
  - failed count = 1
  - failed[0].id: same as the id put in the request
  - failed[0].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-turning-enforcement-off-lets-anyone-purge"></a>

#### [turning-enforcement-off-lets-anyone-purge](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_purging.py): pass

turning RBAC enforcement off lets a user with no permission purge two labels

Given

- 1 domains with 2 labels each and one user
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Domain target-1: label tier=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.partial_bulk_purge: user-1 purges 2 labels at once

Then

- 2 labels come back purged and the rest come back in the failed list
  - successes count = 2
  - successes[0]: same as the id of the label attached in advance
  - successes[1]: same as the id of the label attached in advance
  - failed count = 0

### partial_bulk_upsert

<a id="partial_bulk_upserting-a-key-already-on-the-entity-takes-the-new-value"></a>

#### [a-key-already-on-the-entity-takes-the-new-value](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

adding a key that is already attached changes only the value of the same label

Given

- 1 domains with 1 labels each and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.partial_bulk_upsert: user-1 adds 1 keys each to 1 domains at once

Then

- labels with 1 keys each come back for 1 domains, and the rest come back in the failed list per key for lack of permission
  - items count = 1
  - items[0].entity_type = 'domain'
  - items[0].entity_id: same as the id of the target domain
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].id: same as the id of the label attached in advance
  - items[0].field_id: same as the id of the label attached in advance
  - failed count = 0

<a id="partial_bulk_upserting-a-user-granted-nothing-labels-nothing"></a>

#### [a-user-granted-nothing-labels-nothing](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

when a user with no permission adds labels, none is added and both entities come back in the failed list

Given

- 2 domains and one user
  - Domain home-1
  - Domain target-1
  - Domain target-2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.partial_bulk_upsert: user-1 adds 1 keys each to 2 domains at once

Then

- labels with 1 keys each come back for 0 domains, and the rest come back in the failed list per key for lack of permission
  - items count = 0
  - failed count = 2
  - failed[0].entity_type = 'domain'
  - failed[0].entity_id: same as the id of the target domain
  - failed[0].key = 'team'
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].entity_type = 'domain'
  - failed[1].entity_id: same as the id of the target domain
  - failed[1].key = 'team'
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_upserting-a-writer-labels-two-entities-with-two-keys"></a>

#### [a-writer-labels-two-entities-with-two-keys](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

when a user granted update permission adds two keys to two entities, four labels come back and nothing failed

Given

- 2 domains and one user granted permission to update 2 of them
  - Domain home-1
  - Domain target-1
  - Domain target-2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1
    - Role domain-writer-2: applies only within the scope it is granted in
    - Role domain-writer-2: READ allowed on every domain
    - Role domain-writer-2: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-2

When

- EntityLabelAdapter.partial_bulk_upsert: user-1 adds 2 keys each to 2 domains at once

Then

- labels with 2 keys each come back for 2 domains, and the rest come back in the failed list per key for lack of permission
  - items count = 4
  - items[0].entity_type = 'domain'
  - items[0].entity_id: same as the id of the target domain
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].id: skipped: the database generates it
  - items[0].field_id: same as the label id
  - items[1].entity_type = 'domain'
  - items[1].entity_id: same as the id of the target domain
  - items[1].key = 'tier'
  - items[1].value = 'after'
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].field_id: same as the label id
  - items[2].entity_type = 'domain'
  - items[2].entity_id: same as the id of the target domain
  - items[2].key = 'team'
  - items[2].value = 'after'
  - items[2].created_at: the time this run wrote
  - items[2].updated_at: the time this run wrote
  - items[2].id: skipped: the database generates it
  - items[2].field_id: same as the label id
  - items[3].entity_type = 'domain'
  - items[3].entity_id: same as the id of the target domain
  - items[3].key = 'tier'
  - items[3].value = 'after'
  - items[3].created_at: the time this run wrote
  - items[3].updated_at: the time this run wrote
  - items[3].id: skipped: the database generates it
  - items[3].field_id: same as the label id
  - failed count = 0

<a id="partial_bulk_upserting-one-entity-in-several-items-gets-every-key"></a>

#### [one-entity-in-several-items-gets-every-key](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

when the same entity appears in several items, its label comes back for each key and nothing failed

Given

- 1 domains and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.partial_bulk_upsert: user-1 adds 2 keys each to 1 domains at once

Then

- labels with 2 keys each come back for 1 domains, and the rest come back in the failed list per key for lack of permission
  - items count = 2
  - items[0].entity_type = 'domain'
  - items[0].entity_id: same as the id of the target domain
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].id: skipped: the database generates it
  - items[0].field_id: same as the label id
  - items[1].entity_type = 'domain'
  - items[1].entity_id: same as the id of the target domain
  - items[1].key = 'tier'
  - items[1].value = 'after'
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].field_id: same as the label id
  - failed count = 0

<a id="partial_bulk_upserting-only-the-writable-entity-is-labeled"></a>

#### [only-the-writable-entity-is-labeled](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

with update permission on one entity only, its two labels come back and the other entity comes back in the failed list once per key

Given

- 2 domains and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Domain target-2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.partial_bulk_upsert: user-1 adds 2 keys each to 2 domains at once

Then

- labels with 2 keys each come back for 1 domains, and the rest come back in the failed list per key for lack of permission
  - items count = 2
  - items[0].entity_type = 'domain'
  - items[0].entity_id: same as the id of the target domain
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].id: skipped: the database generates it
  - items[0].field_id: same as the label id
  - items[1].entity_type = 'domain'
  - items[1].entity_id: same as the id of the target domain
  - items[1].key = 'tier'
  - items[1].value = 'after'
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].field_id: same as the label id
  - failed count = 2
  - failed[0].entity_type = 'domain'
  - failed[0].entity_id: same as the id of the target domain
  - failed[0].key = 'team'
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].entity_type = 'domain'
  - failed[1].entity_id: same as the id of the target domain
  - failed[1].key = 'tier'
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_upserting-turning-enforcement-off-lets-anyone-label"></a>

#### [turning-enforcement-off-lets-anyone-label](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

turning RBAC enforcement off lets a user with no permission add labels to two entities with nothing failed

Given

- 2 domains and one user
  - Domain home-1
  - Domain target-1
  - Domain target-2
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.partial_bulk_upsert: user-1 adds 1 keys each to 2 domains at once

Then

- labels with 1 keys each come back for 2 domains, and the rest come back in the failed list per key for lack of permission
  - items count = 2
  - items[0].entity_type = 'domain'
  - items[0].entity_id: same as the id of the target domain
  - items[0].key = 'team'
  - items[0].value = 'after'
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].id: skipped: the database generates it
  - items[0].field_id: same as the label id
  - items[1].entity_type = 'domain'
  - items[1].entity_id: same as the id of the target domain
  - items[1].key = 'team'
  - items[1].value = 'after'
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[1].id: skipped: the database generates it
  - items[1].field_id: same as the label id
  - failed count = 0

<a id="partial_bulk_upserting-an-unwired-type-refuses-the-whole-call"></a>

#### [an-unwired-type-refuses-the-whole-call](/tests/scenario/bai_scenario/manager/entity_label/test_partial_bulk_upserting.py): pass

when even one type that has no connection and call path is mixed in, the whole request is rejected as invalid and nothing is written

Given

- 1 domains and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.partial_bulk_upsert: user-1 adds 1 keys each to 1 domains and one unknown type at once

Then

- the call is rejected
  - rejected: InvalidAPIParameters

### purge

<a id="purging-a-writer-purges-one-label"></a>

#### [a-writer-purges-one-label](/tests/scenario/bai_scenario/manager/entity_label/test_purging.py): pass

when a user granted update permission purges one label, the whole label comes back

Given

- 1 domains with 1 labels each and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.purge: user-1 purges the label under key team

Then

- the label that was purged comes back whole
  - label.entity_type = 'domain'
  - label.entity_id: same as the id of the target domain
  - label.key = 'team'
  - label.value = 'before'
  - label.created_at: the time this run wrote
  - label.updated_at: the time this run wrote
  - label.id: same as the id of the label attached in advance
  - label.field_id: same as the id of the label attached in advance
  - field_id: same as the id of the label attached in advance

<a id="purging-a-user-granted-nothing-cannot-purge-the-label"></a>

#### [a-user-granted-nothing-cannot-purge-the-label](/tests/scenario/bai_scenario/manager/entity_label/test_purging.py): pass

when a user with no permission purges a label, the request is rejected

Given

- 1 domains with 1 labels each and one user
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.purge: user-1 purges the label under key team

Then

- the call is rejected
  - rejected: GenericBadRequest

<a id="purging-an-unknown-label-id-is-refused"></a>

#### [an-unknown-label-id-is-refused](/tests/scenario/bai_scenario/manager/entity_label/test_purging.py): pass

when a user granted update permission purges an unknown label id, the request is rejected

Given

- 1 domains and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.purge: user-1 purges one unknown label id

Then

- the call is rejected
  - rejected: GenericBadRequest

### search

<a id="searching-a-reader-pages-through-the-labels-of-two-entities"></a>

#### [a-reader-pages-through-the-labels-of-two-entities](/tests/scenario/bai_scenario/manager/entity_label/test_searching.py): pass

when a user who can read two domains pages through both at once, both labels come back whole

Given

- 2 domains with 1 labels each and one user who can read 2 of them
  - Domain home-1
  - Domain target-1
  - Domain target-2
  - Domain target-1: label team=before
  - Domain target-2: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to read the domain
    - Role domain-reader-1: applies only within the scope it is granted in
    - Role domain-reader-1: READ allowed on every domain
    - regular user user-1: holds Role domain-reader-1
    - Role domain-reader-2: applies only within the scope it is granted in
    - Role domain-reader-2: READ allowed on every domain
    - regular user user-1: holds Role domain-reader-2

When

- EntityLabelAdapter.search: user-1 pages through the labels of 2 domains at once

Then

- every one of the 2 labels attached in advance comes back whole
  - items count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - items[0].present = True
  - items[0].entity_type = 'domain'
  - items[0].entity_id: same as the id of the target domain
  - items[0].key = 'team'
  - items[0].value = 'before'
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].id: same as the id of the label attached in advance
  - items[0].field_id: same as the id of the label attached in advance
  - items[1].present = True
  - items[1].entity_type = 'domain'
  - items[1].entity_id: same as the id of the target domain
  - items[1].key = 'team'
  - items[1].value = 'before'
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[1].id: same as the id of the label attached in advance
  - items[1].field_id: same as the id of the label attached in advance

<a id="searching-a-user-granted-nothing-cannot-page-through-the-named-scopes"></a>

#### [a-user-granted-nothing-cannot-page-through-the-named-scopes](/tests/scenario/bai_scenario/manager/entity_label/test_searching.py): pass

when a user with no permission pages through a domain's labels, the call is rejected for lack of permission

Given

- 1 domains with 1 labels each and one user
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.search: user-1 pages through the labels of 1 domains at once

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_on

<a id="searching-a-reader-pages-through-one-entities-labels-under-a-key"></a>

#### [a-reader-pages-through-one-entities-labels-under-a-key](/tests/scenario/bai_scenario/manager/entity_label/test_searching.py): pass

when a user who can read one domain pages through it narrowed to one key, only that key's label comes back

Given

- 1 domains with 2 labels each and one user who can read 1 of them
  - Domain home-1
  - Domain target-1
  - Domain target-1: label tier=before
  - Domain target-1: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to read the domain
    - Role domain-reader-1: applies only within the scope it is granted in
    - Role domain-reader-1: READ allowed on every domain
    - regular user user-1: holds Role domain-reader-1

When

- EntityLabelAdapter.search_on: user-1 pages through the labels under key team on domain target-1

Then

- every one of the 1 labels attached in advance comes back whole
  - items count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - items[0].present = True
  - items[0].entity_type = 'domain'
  - items[0].entity_id: same as the id of the target domain
  - items[0].key = 'team'
  - items[0].value = 'before'
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[0].id: same as the id of the label attached in advance
  - items[0].field_id: same as the id of the label attached in advance

<a id="searching-a-user-granted-nothing-cannot-page-through-a-held-scope"></a>

#### [a-user-granted-nothing-cannot-page-through-a-held-scope](/tests/scenario/bai_scenario/manager/entity_label/test_searching.py): pass

when a user with no permission pages through a held domain's labels, the call is rejected for lack of permission

Given

- 1 domains with 1 labels each and one user
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.search_on: user-1 pages through the labels under key team on domain target-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

### upsert

<a id="upserting-a-writer-puts-a-new-key-on-an-entity"></a>

#### [a-writer-puts-a-new-key-on-an-entity](/tests/scenario/bai_scenario/manager/entity_label/test_upserting.py): pass

when a user granted update permission puts a new key on a domain, the whole label comes back

Given

- 1 domains and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.upsert: user-1 puts the label team=after on domain target-1

Then

- the whole label that was put on the entity comes back
  - label.entity_type = 'domain'
  - label.entity_id: same as the id of the target domain
  - label.key = 'team'
  - label.value = 'after'
  - label.created_at: the time this run wrote
  - label.updated_at: the time this run wrote
  - label.id: skipped: the database generates it
  - label.field_id: same as the label id

<a id="upserting-a-writer-replaces-the-value-of-an-existing-key"></a>

#### [a-writer-replaces-the-value-of-an-existing-key](/tests/scenario/bai_scenario/manager/entity_label/test_upserting.py): pass

when a user granted update permission writes a key that is already attached, the same label comes back with only its value replaced

Given

- 1 domains with 1 labels each and one user granted permission to update 1 of them
  - Domain home-1
  - Domain target-1
  - Domain target-1: label team=before
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Prepare a user granted permission to update the domain
    - Role domain-writer-1: applies only within the scope it is granted in
    - Role domain-writer-1: READ allowed on every domain
    - Role domain-writer-1: UPDATE allowed on every domain
    - regular user user-1: holds Role domain-writer-1

When

- EntityLabelAdapter.upsert: user-1 puts the label team=after on domain target-1

Then

- the same label comes back with only its value replaced
  - label.entity_type = 'domain'
  - label.entity_id: same as the id of the target domain
  - label.key = 'team'
  - label.value = 'after'
  - label.created_at: the time this run wrote
  - label.updated_at: the time this run wrote
  - label.id: same as the id of the label attached in advance
  - label.field_id: same as the id of the label attached in advance

<a id="upserting-a-user-granted-nothing-cannot-put-a-label-on-the-domain"></a>

#### [a-user-granted-nothing-cannot-put-a-label-on-the-domain](/tests/scenario/bai_scenario/manager/entity_label/test_upserting.py): pass

when a user with no permission puts a label on a domain, the call is rejected for lack of permission

Given

- 1 domains and one user
  - Domain home-1
  - Domain target-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- EntityLabelAdapter.upsert: user-1 puts the label team=after on domain target-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

