## prometheus_query_preset_category

[background](/src/ai/backend/manager/api/adapters/prometheus_query_preset_category/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/prometheus_query_preset_category/adapter.py)

Scenario: incomplete 1 / 6

- built from ops (6)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - create: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [even when categories exist, loading with an empty id list answers an empty list](#loading-loading-an-empty-id-list-answers-an-empty-list) | answered |
| [when two categories and one missing id are loaded in one call, the two that exist come back as nodes and the missing one as a rejection, in the order requested](#loading-loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-rejection) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a category with a name and a description, the node comes back carrying the values as given](#creating-creating-a-category-with-a-description-carries-it-on-the-node) | answered |
| [when the superadmin creates a category with only a name, the whole node comes back with an empty description](#creating-creating-a-category-with-a-name-alone-answers-with-the-whole-node) | answered |
| [when the superadmin creates a category again with a name another category already holds, it is rejected as a duplicate name. The unique constraint of the repository rejects it and it is not translated into a domain error](#creating-a-name-another-category-already-holds-is-refused) | rejected |
| [when a user who is not the superadmin tries to create a category, the role rejects it](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-category) | rejected |
| [turning permission enforcement off still rejects creating a category](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-category) | rejected |

**get**

| scenario | verdict |
|---|---|
| [with one category laid, when a user granted nothing reads it by id, the whole category comes back](#reading-a-user-granted-nothing-reads-a-category-by-id) | answered |
| [with one category laid, when it is read by id with no user context, the call is rejected because the caller is unknown](#reading-a-call-carrying-no-user-may-not-read-a-category) | rejected |
| [when a user who can read in public reads a missing id, the call is rejected. There is no target to require permission for, so the answer does not reveal whether it does not exist or cannot be accessed](#reading-an-id-nothing-answers-to-is-refused) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several categories in one call, none is deleted and every one comes back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-categories) | answered |
| [when the superadmin purges two categories and one missing id in one call, the two come back as they were before deletion and the missing id comes back in the failed list because there is no such target](#partial_bulk_purging-purging-several-categories-answers-for-the-missing-one) | answered |

**purge**

| scenario | verdict |
|---|---|
| [with one category laid, when the superadmin deletes it, the answer carries the id that was deleted](#purging-the-superadmin-removes-a-category) | answered |
| [turning permission enforcement off lets a user granted nothing delete a category](#purging-turning-enforcement-off-lets-a-user-remove-a-category) | answered |
| [with the same category laid, when a user granted nothing deletes it, the call is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-remove-a-category) | rejected |
| [when the superadmin deletes a missing id, the call is rejected because there is no such target](#purging-removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

**search**

| scenario | verdict |
|---|---|
| [with two categories laid, when a user granted nothing searches without a filter, both are counted](#searching-a-user-granted-nothing-counts-every-category) | answered |
| [with three categories of different names, when they are searched with a filter on one name, only the category of that name comes back](#searching-filtering-by-name-keeps-only-the-category-of-that-name) | answered |
| [with 11 categories laid, when they are searched without a page size, ten come back and the answer says there is a next page](#searching-omitting-the-page-size-answers-ten-and-says-there-is-a-next-page) | answered |
| [with one category laid, when it is searched with no user context, the call is rejected for an authentication failure](#searching-a-call-carrying-no-user-may-not-search-categories) | rejected |

### batch_load_by_ids

<a id="loading-loading-an-empty-id-list-answers-an-empty-list"></a>

#### [loading-an-empty-id-list-answers-an-empty-list](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_loading.py): pass

even when categories exist, loading with an empty id list answers an empty list

Given

- 1 categories and one user
  - Category wanted-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.batch_load_by_ids: user-1 loads with an empty id list

Then

- an empty response comes back
  - answer = []

<a id="loading-loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-rejection"></a>

#### [loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-rejection](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_loading.py): pass

when two categories and one missing id are loaded in one call, the two that exist come back as nodes and the missing one as a rejection, in the order requested

Given

- 2 categories and one user
  - Category wanted-1
  - Category other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.batch_load_by_ids: user-1 loads the ids of the 2 categories seeded in advance and one missing id in one call

Then

- the items come back in the order requested and the item for an unknown id carries a denial
  - len = 3
  - [0]: same as the whole category of the id requested at position 1
  - [1]: same as the whole category of the id requested at position 2
  - rejected: NotEnoughPermission

### create

<a id="creating-creating-a-category-with-a-description-carries-it-on-the-node"></a>

#### [creating-a-category-with-a-description-carries-it-on-the-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py): pass

when the superadmin creates a category with a name and a description, the node comes back carrying the values as given

Given

- no category and one superadmin
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.create: user-1 creates it with the name cpu

Then

- the whole category just created comes back
  - id: skipped: the database generates it
  - name = 'cpu'
  - description = 'a freshly created category'
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-creating-a-category-with-a-name-alone-answers-with-the-whole-node"></a>

#### [creating-a-category-with-a-name-alone-answers-with-the-whole-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py): pass

when the superadmin creates a category with only a name, the whole node comes back with an empty description

Given

- no category and one superadmin
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.create: user-1 creates it with the name cpu

Then

- the whole category just created comes back
  - id: skipped: the database generates it
  - name = 'cpu'
  - description = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-name-another-category-already-holds-is-refused"></a>

#### [a-name-another-category-already-holds-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py): pass

when the superadmin creates a category again with a name another category already holds, it is rejected as a duplicate name. The unique constraint of the repository rejects it and it is not translated into a domain error

Given

- one existing category and one superadmin
  - Category category-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.create: user-1 creates it again with the name category-1, which already exists

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-category"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py): pass

when a user who is not the superadmin tries to create a category, the role rejects it

Given

- no category and one user
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.create: user-1 creates it with the name cpu

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-category"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_creating.py): pass

turning permission enforcement off still rejects creating a category

Given

- no category and one user
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.create: user-1 creates it with the name cpu

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-a-user-granted-nothing-reads-a-category-by-id"></a>

#### [a-user-granted-nothing-reads-a-category-by-id](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_reading.py): pass

with one category laid, when a user granted nothing reads it by id, the whole category comes back

Given

- one existing category and one user
  - Category category-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.get: user-1 reads a category by category-1

Then

- the whole category seeded in advance comes back
  - id: same as the category seeded in advance
  - name = 'category-1'
  - description = 'a category created in advance'
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-a-call-carrying-no-user-may-not-read-a-category"></a>

#### [a-call-carrying-no-user-may-not-read-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_reading.py): pass

with one category laid, when it is read by id with no user context, the call is rejected because the caller is unknown

Given

- one existing category and no caller
  - Category category-1

When

- PrometheusQueryPresetCategoryAdapter.get: reads category-1 with no user context

Then

- the call is rejected
  - rejected: UnreachableError

<a id="reading-an-id-nothing-answers-to-is-refused"></a>

#### [an-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_reading.py): pass

when a user who can read in public reads a missing id, the call is rejected. There is no target to require permission for, so the answer does not reveal whether it does not exist or cannot be accessed

Given

- one existing category and one user
  - Category category-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.get: user-1 reads a category by a missing id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-categories"></a>

#### [a-user-granted-nothing-purges-none-of-several-categories](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several categories in one call, none is deleted and every one comes back in the failed list for lack of permission

Given

- 2 categories and one user
  - Category wanted-1
  - Category other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.partial_bulk_purge: user-1 purges 2 categories in one call

Then

- no category is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target category
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target category
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-categories-answers-for-the-missing-one"></a>

#### [purging-several-categories-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_partial_bulk_purging.py): pass

when the superadmin purges two categories and one missing id in one call, the two come back as they were before deletion and the missing id comes back in the failed list because there is no such target

Given

- 2 categories and one superadmin
  - Category wanted-1
  - Category other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.partial_bulk_purge: user-1 purges 2 categories and one missing id in one call

Then

- every target category comes back as it was before deletion, and the missing id comes back in the failed list because there is no such target
  - successes count = 2
  - failed count = 1
  - successes[0]: same as the whole target category
  - successes[1]: same as the whole target category
  - failed[0].id: same as the missing id in the request
  - failed[0].message: a reason containing 'not found'

### purge

<a id="purging-the-superadmin-removes-a-category"></a>

#### [the-superadmin-removes-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_purging.py): pass

with one category laid, when the superadmin deletes it, the answer carries the id that was deleted

Given

- one existing category and one superadmin
  - Category category-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.purge: user-1 deletes category-1

Then

- the response names the category that was deleted
  - id: same as the category seeded in advance

<a id="purging-turning-enforcement-off-lets-a-user-remove-a-category"></a>

#### [turning-enforcement-off-lets-a-user-remove-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_purging.py): pass

turning permission enforcement off lets a user granted nothing delete a category

Given

- one existing category and one user
  - Category category-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.purge: user-1 deletes category-1

Then

- the response names the category that was deleted
  - id: same as the category seeded in advance

<a id="purging-a-user-granted-nothing-may-not-remove-a-category"></a>

#### [a-user-granted-nothing-may-not-remove-a-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_purging.py): pass

with the same category laid, when a user granted nothing deletes it, the call is rejected for lack of permission

Given

- one existing category and one user
  - Category category-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.purge: user-1 deletes category-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_purging.py): pass

when the superadmin deletes a missing id, the call is rejected because there is no such target

Given

- one existing category and one superadmin
  - Category category-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.purge: user-1 deletes a missing id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search

<a id="searching-a-user-granted-nothing-counts-every-category"></a>

#### [a-user-granted-nothing-counts-every-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py): pass

with two categories laid, when a user granted nothing searches without a filter, both are counted

Given

- 2 categories and one user
  - Category wanted-1
  - Category other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.search: user-1 searches every category without a filter

Then

- every category seeded in advance is counted, and only those
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-filtering-by-name-keeps-only-the-category-of-that-name"></a>

#### [filtering-by-name-keeps-only-the-category-of-that-name](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py): pass

with three categories of different names, when they are searched with a filter on one name, only the category of that name comes back

Given

- 3 categories and one user
  - Category wanted-1
  - Category other-1
  - Category other-2
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.search: user-1 searches with a filter on the name wanted-1

Then

- only the one matching the name filter is counted
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-omitting-the-page-size-answers-ten-and-says-there-is-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-and-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py): pass

with 11 categories laid, when they are searched without a page size, ten come back and the answer says there is a next page

Given

- 11 categories and one user
  - Category wanted-1
  - Category other-1
  - Category other-2
  - Category other-3
  - Category other-4
  - Category other-5
  - Category other-6
  - Category other-7
  - Category other-8
  - Category other-9
  - Category other-10
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset_category in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset_category
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetCategoryAdapter.search: user-1 searches every category without a filter

Then

- one page comes back and the response says there is a next page
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-call-carrying-no-user-may-not-search-categories"></a>

#### [a-call-carrying-no-user-may-not-search-categories](/tests/scenario/bai_scenario/manager/prometheus_query_preset_category/test_searching.py): pass

with one category laid, when it is searched with no user context, the call is rejected for an authentication failure

Given

- one existing category and no caller
  - Category category-1

When

- PrometheusQueryPresetCategoryAdapter.search: searches every category with no user context

Then

- the call is rejected
  - rejected: UnreachableError

