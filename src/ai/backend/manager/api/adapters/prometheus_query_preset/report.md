## prometheus_query_preset

[background](/src/ai/backend/manager/api/adapters/prometheus_query_preset/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/prometheus_query_preset/adapter.py)

Scenario: incomplete 3 / 10

- built from ops (5)
  - batch_load_by_ids: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - purge: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
- direct implementation (5)
  - admin_preview: success present 2 · rejection present 2 (global_scope)
  - create: success present 4 · rejection present 4 (global_scope)
  - execute_preset: success present 3 · rejection present 4 (single_entity)
  - partial_bulk_update: success present 3 · rejection absent (partial_bulk): SCENARIO-GAP
  - update: success present 6 · rejection present 3 (single_entity)

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [even when presets exist, reading an empty id list answers an empty response](#loading-loading-an-empty-id-list-answers-an-empty-list) | answered |
| [when two presets and one absent id are read at once, the two present ones come back as nodes and the absent one as an empty item, in the requested order](#loading-loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-gap) | answered |

**get**

| scenario | verdict |
|---|---|
| [when a preset exists and a user granted nothing reads it by id, the whole preset comes back](#reading-a-user-granted-nothing-reads-a-preset-by-id) | answered |
| [when a preset exists and it is read by id without a user context, it is rejected because the caller cannot be known](#reading-a-call-carrying-no-user-may-not-read-a-preset) | rejected |
| [when a user who can read in public reads an id that does not exist, it is rejected. Because there is no target to require permission on, the response does not reveal whether it does not exist or cannot be reached](#reading-an-id-nothing-answers-to-is-refused) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several presets at once, nothing is deleted and all come back in the failed list for lack of permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-presets) | answered |
| [when the superadmin purges two presets and one absent id at once, the two come back as they were before deletion and the absent id comes back in the failed list because the target is not found](#partial_bulk_purging-purging-several-presets-answers-for-the-missing-one) | answered |

**purge**

| scenario | verdict |
|---|---|
| [when a preset exists and the superadmin deletes it, a response carrying the deleted id comes back](#purging-the-superadmin-removes-a-preset) | answered |
| [turning the permission check off lets even a user granted nothing delete a preset](#purging-turning-enforcement-off-lets-a-user-remove-a-preset) | answered |
| [when the same preset exists and a user granted nothing deletes it, it is rejected for lack of permission](#purging-a-user-granted-nothing-may-not-remove-a-preset) | rejected |
| [when the superadmin deletes an id that does not exist, it is rejected because the target is not found](#purging-removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when two presets exist and a user granted nothing searches without a filter, both are counted](#searching-a-user-granted-nothing-counts-every-preset) | answered |
| [when presets are split across two categories and one category filter is used, only the presets of that category come back](#searching-filtering-by-category-keeps-only-the-presets-filed-under-it) | answered |
| [when three presets have different names and a name filter is used, only the preset of that name comes back](#searching-filtering-by-name-keeps-only-the-preset-of-that-name) | answered |
| [when there are 11 presets and a search gives no page size, ten items come back and it answers that there is a next page](#searching-omitting-the-page-size-answers-ten-and-says-there-is-a-next-page) | answered |
| [when a preset exists and it is searched without a user context, it is rejected because the caller cannot be known](#searching-a-call-carrying-no-user-may-not-search-presets) | rejected |

**admin_preview**

| scenario | verdict |
|---|---|
| [when the superadmin previews giving only a template, it answers with an instant query, and the time window of the query the mock server received is the server's default time window and the labels are empty](#previewing-previewing-a-template-is-an-instant-query-with-the-server-window-and-no-label) | answered |
| [when the monitor role previews a template, the result the mock server answered comes back. The superadmin check allows the monitor only for reads](#previewing-the-monitor-role-previews-a-template) | answered |
| [when the superadmin previews a template that renders an empty query, Prometheus rejects the query and that rejection propagates changed into an evaluation failure. It is rejected with a different error from the same scenario in run](#previewing-a-query-prometheus-refuses-is-refused-as-an-evaluation-failure) | rejected |
| [when a user who is not the superadmin tries to preview, it is rejected for lack of role](#previewing-a-user-who-is-not-the-superadmin-may-not-preview-a-template) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a preset again with a name another preset already uses, it is created. Preset names have no unique constraint](#creating-a-name-another-preset-already-holds-is-allowed) | answered |
| [when a category exists and the superadmin creates a preset naming it, the category in the response references it](#creating-creating-a-preset-under-a-category-points-the-node-at-that-category) | answered |
| [when the superadmin creates a preset with a time window, the node carries that time window](#creating-creating-a-preset-with-a-window-carries-that-window-on-the-node) | answered |
| [when the superadmin creates a preset specifying only a name, a metric name, a template and allowed label lists, the whole node comes back with rank 0 and an empty category, description and time window](#creating-creating-a-preset-with-the-required-values-answers-with-the-whole-node) | answered |
| [when the superadmin creates a preset naming a category id that does not exist, it is rejected because the category does not exist. The repository's reference constraint blocks it, and it has not been moved to a domain error](#creating-a-category-id-nothing-answers-to-is-refused) | rejected |
| [when a user who is not the superadmin tries to create a preset, it is rejected for lack of role](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-preset) | rejected |
| [when the monitor role tries to create a preset, it is rejected for lack of role. The superadmin check allows the monitor only for reads](#creating-the-monitor-role-may-not-create-a-preset) | rejected |
| [turning the permission check off still rejects creating a preset](#creating-turning-enforcement-off-still-does-not-let-a-user-create-a-preset) | rejected |

**execute_preset**

| scenario | verdict |
|---|---|
| [when the superadmin runs a preset giving a start, an end and a step, the mock server answers with a range query](#executing-running-a-preset-over-a-range-is-a-range-query) | answered |
| [when the superadmin runs a preset with no time window, giving a time window and no query range, it answers with an instant query and the query the mock server received carries the requested time window](#executing-running-a-preset-without-a-range-is-an-instant-query-carrying-the-asked-window) | answered |
| [turning the permission check off lets even a user granted nothing run a preset](#executing-turning-enforcement-off-lets-a-user-run-a-preset) | answered |
| [when the superadmin runs without labels a preset that renders an empty query without them, Prometheus rejects the query and that rejection propagates as a failure to get the metric](#executing-a-query-prometheus-refuses-is-refused-as-a-failed-metric-read) | rejected |
| [when a user granted nothing runs a preset, it is rejected for lack of permission. Run requires the same permission as read](#executing-a-user-granted-nothing-may-not-run-a-preset) | rejected |
| [when the superadmin runs an id that does not exist, it is rejected because the target is not found. Run raises this error by reading the preset directly in the service, so it differs in kind from the not-found of edit and delete](#executing-running-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |
| [when a user granted nothing runs an id that does not exist, it is rejected for lack of permission rather than as not found, because a row that does not exist has no permission granted](#executing-running-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when the superadmin edits several presets at once and gives one a broken template, only that one comes back in the failed list for the template check and the rest are edited](#partial_bulk_editing-a-broken-template-fails-only-the-preset-it-was-meant-for) | answered |
| [when a user granted nothing tries to edit several presets at once, nothing is edited and all come back in the failed list for lack of permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets) | answered |
| [when the superadmin changes the descriptions of several presets at once, all come back with the new description and none failed](#partial_bulk_editing-the-superadmin-edits-several-presets-at-once) | answered |

**update**

| scenario | verdict |
|---|---|
| [when the superadmin edits without giving any value, the node comes back with nothing changed](#editing-an-update-giving-no-value-answers-the-node-unchanged) | answered |
| [when the superadmin edits only the filter labels of a preset that has both filter and group labels, the filter labels are the new value and the group labels stay as they are](#editing-changing-only-the-filter-labels-keeps-the-group-labels) | answered |
| [when the superadmin edits a preset that has a description to clear it, the description is gone](#editing-clearing-the-description-leaves-it-empty) | answered |
| [when the superadmin moves a preset filed under one of two categories to the other, the category in the response references it](#editing-moving-a-preset-to-another-category-points-the-node-at-that-one) | answered |
| [when a preset exists and the superadmin edits only the template, the template is the new value and the rest stays as it is](#editing-the-superadmin-changes-the-template-and-the-rest-stays) | answered |
| [turning the permission check off lets even a user granted nothing edit a preset](#editing-turning-enforcement-off-lets-a-user-edit-a-preset) | answered |
| [when the same preset exists and a user granted nothing edits its name, it is rejected for lack of permission. This entity belongs to no scope, so there is no way to grant permission on it](#editing-a-user-granted-nothing-may-not-edit-a-preset) | rejected |
| [when the superadmin edits the name of an id that does not exist, it is rejected because the target is not found](#editing-editing-an-id-nothing-answers-to-is-not-found-for-a-superadmin) | rejected |
| [when the superadmin edits a preset naming a category id that does not exist, it is rejected because the category does not exist. The repository's reference constraint blocks it, and it has not been moved to a domain error](#editing-moving-a-preset-to-a-category-id-nothing-answers-to-is-refused) | rejected |

### batch_load_by_ids

<a id="loading-loading-an-empty-id-list-answers-an-empty-list"></a>

#### [loading-an-empty-id-list-answers-an-empty-list](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_loading.py): pass

even when presets exist, reading an empty id list answers an empty response

Given

- 1 presets and one user
  - Query preset wanted-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.batch_load_by_ids: user-1 reads with an empty id list

Then

- an empty response comes back
  - answer = []

<a id="loading-loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-gap"></a>

#### [loading-laid-ids-and-an-unknown-one-answers-in-order-with-a-gap](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_loading.py): pass

when two presets and one absent id are read at once, the two present ones come back as nodes and the absent one as an empty item, in the requested order

Given

- 2 presets and one user
  - Query preset wanted-1
  - Query preset other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.batch_load_by_ids: user-1 reads the ids of 2 presets seeded in advance and one absent id at once

Then

- the items come back in the order requested and the item for an unknown id is empty
  - len = 3
  - [0]: same as the whole preset of the id requested at position 1
  - [1]: same as the whole preset of the id requested at position 2
  - [2] = None

### get

<a id="reading-a-user-granted-nothing-reads-a-preset-by-id"></a>

#### [a-user-granted-nothing-reads-a-preset-by-id](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_reading.py): pass

when a preset exists and a user granted nothing reads it by id, the whole preset comes back

Given

- one existing preset and one user who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.get: user-1 reads by preset-1

Then

- the whole preset seeded in advance comes back
  - id: same as the preset seeded in advance
  - name = 'preset-1'
  - description = 'a query preset created in advance'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-a-call-carrying-no-user-may-not-read-a-preset"></a>

#### [a-call-carrying-no-user-may-not-read-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_reading.py): pass

when a preset exists and it is read by id without a user context, it is rejected because the caller cannot be known

Given

- one existing preset and no caller
  - Query preset preset-1

When

- PrometheusQueryPresetAdapter.get: reads preset-1 without a user context

Then

- the call is rejected
  - rejected: UnreachableError

<a id="reading-an-id-nothing-answers-to-is-refused"></a>

#### [an-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_reading.py): pass

when a user who can read in public reads an id that does not exist, it is rejected. Because there is no target to require permission on, the response does not reveal whether it does not exist or cannot be reached

Given

- one existing preset and one user who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.get: user-1 reads by an absent id

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-presets"></a>

#### [a-user-granted-nothing-purges-none-of-several-presets](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several presets at once, nothing is deleted and all come back in the failed list for lack of permission

Given

- 2 presets and one user
  - Query preset wanted-1
  - Query preset other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.partial_bulk_purge: user-1 purges 2 presets at once

Then

- no preset is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target preset
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target preset
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-presets-answers-for-the-missing-one"></a>

#### [purging-several-presets-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_partial_bulk_purging.py): pass

when the superadmin purges two presets and one absent id at once, the two come back as they were before deletion and the absent id comes back in the failed list because the target is not found

Given

- 2 presets and one superadmin
  - Query preset wanted-1
  - Query preset other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.partial_bulk_purge: user-1 purges 2 presets at once and one absent id

Then

- every target preset comes back as it was before deletion, and the absent id comes back in the failed list because the target is not found
  - successes count = 2
  - failed count = 1
  - successes[0]: same as the whole target preset
  - successes[1]: same as the whole target preset
  - failed[0].id: same as the absent id put in the request
  - failed[0].message: a reason containing 'not found'

### purge

<a id="purging-the-superadmin-removes-a-preset"></a>

#### [the-superadmin-removes-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py): pass

when a preset exists and the superadmin deletes it, a response carrying the deleted id comes back

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.purge: user-1 deletes preset-1

Then

- the response names the preset that was deleted
  - id: same as the preset seeded in advance

<a id="purging-turning-enforcement-off-lets-a-user-remove-a-preset"></a>

#### [turning-enforcement-off-lets-a-user-remove-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py): pass

turning the permission check off lets even a user granted nothing delete a preset

Given

- one existing preset and one user who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.purge: user-1 deletes preset-1

Then

- the response names the preset that was deleted
  - id: same as the preset seeded in advance

<a id="purging-a-user-granted-nothing-may-not-remove-a-preset"></a>

#### [a-user-granted-nothing-may-not-remove-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py): pass

when the same preset exists and a user granted nothing deletes it, it is rejected for lack of permission

Given

- one existing preset and one user who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.purge: user-1 deletes preset-1

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="purging-removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [removing-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_purging.py): pass

when the superadmin deletes an id that does not exist, it is rejected because the target is not found

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.purge: user-1 deletes an absent id

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search

<a id="searching-a-user-granted-nothing-counts-every-preset"></a>

#### [a-user-granted-nothing-counts-every-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py): pass

when two presets exist and a user granted nothing searches without a filter, both are counted

Given

- 2 presets and one user
  - Query preset wanted-1
  - Query preset other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.search: user-1 searches everything without a filter

Then

- every preset seeded in advance is counted, and only those
  - items = ['other-1', 'wanted-1']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-filtering-by-category-keeps-only-the-presets-filed-under-it"></a>

#### [filtering-by-category-keeps-only-the-presets-filed-under-it](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py): pass

when presets are split across two categories and one category filter is used, only the presets of that category come back

Given

- three presets split across two categories and one user
  - Category wanted-1
  - Category other-1
  - Query preset wanted-2: belongs to a category
  - Query preset beside-1: belongs to a category
  - Query preset elsewhere-1: belongs to a category
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.search: user-1 searches with a category filter

Then

- every preset seeded in advance is counted, and only those
  - items = ['beside-1', 'wanted-2']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-filtering-by-name-keeps-only-the-preset-of-that-name"></a>

#### [filtering-by-name-keeps-only-the-preset-of-that-name](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py): pass

when three presets have different names and a name filter is used, only the preset of that name comes back

Given

- 3 presets and one user
  - Query preset wanted-1
  - Query preset other-1
  - Query preset other-2
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.search: user-1 searches with the name filter wanted-1

Then

- only the one matching the name filter is counted
  - items = ['wanted-1']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-omitting-the-page-size-answers-ten-and-says-there-is-a-next-page"></a>

#### [omitting-the-page-size-answers-ten-and-says-there-is-a-next-page](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py): pass

when there are 11 presets and a search gives no page size, ten items come back and it answers that there is a next page

Given

- 11 presets and one user
  - Query preset wanted-1
  - Query preset other-1
  - Query preset other-2
  - Query preset other-3
  - Query preset other-4
  - Query preset other-5
  - Query preset other-6
  - Query preset other-7
  - Query preset other-8
  - Query preset other-9
  - Query preset other-10
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.search: user-1 searches everything without a filter

Then

- one page comes back and the response says there is a next page
  - items = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching-a-call-carrying-no-user-may-not-search-presets"></a>

#### [a-call-carrying-no-user-may-not-search-presets](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_searching.py): pass

when a preset exists and it is searched without a user context, it is rejected because the caller cannot be known

Given

- one existing preset and no caller
  - Query preset preset-1

When

- PrometheusQueryPresetAdapter.search: searches everything without a user context

Then

- the call is rejected
  - rejected: UnreachableError

### admin_preview

<a id="previewing-previewing-a-template-is-an-instant-query-with-the-server-window-and-no-label"></a>

#### [previewing-a-template-is-an-instant-query-with-the-server-window-and-no-label](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py): pass

when the superadmin previews giving only a template, it answers with an instant query, and the time window of the query the mock server received is the server's default time window and the labels are empty

Given

- no preset and one superadmin
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.admin_preview: user-1 previews a template

Then

- the result carrying the query the mock server received comes back
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[2m]))')])]

<a id="previewing-the-monitor-role-previews-a-template"></a>

#### [the-monitor-role-previews-a-template](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py): pass

when the monitor role previews a template, the result the mock server answered comes back. The superadmin check allows the monitor only for reads

Given

- no preset and one monitor
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - monitor user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - monitor user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.admin_preview: user-1 previews a template

Then

- the result carrying the query the mock server received comes back
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[2m]))')])]

<a id="previewing-a-query-prometheus-refuses-is-refused-as-an-evaluation-failure"></a>

#### [a-query-prometheus-refuses-is-refused-as-an-evaluation-failure](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py): pass

when the superadmin previews a template that renders an empty query, Prometheus rejects the query and that rejection propagates changed into an evaluation failure. It is rejected with a different error from the same scenario in run

Given

- no preset and one superadmin
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.admin_preview: user-1 previews a template that renders an empty query

Then

- the call is rejected
  - rejected: PrometheusQueryEvaluationFailed

<a id="previewing-a-user-who-is-not-the-superadmin-may-not-preview-a-template"></a>

#### [a-user-who-is-not-the-superadmin-may-not-preview-a-template](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_previewing.py): pass

when a user who is not the superadmin tries to preview, it is rejected for lack of role

Given

- no preset and one user
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.admin_preview: user-1 previews a template

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### create

<a id="creating-a-name-another-preset-already-holds-is-allowed"></a>

#### [a-name-another-preset-already-holds-is-allowed](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py): pass

when the superadmin creates a preset again with a name another preset already uses, it is created. Preset names have no unique constraint

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.create: user-1 creates another preset with the name preset-1 that already exists

Then

- the whole preset just created comes back
  - id: skipped: the database generates it
  - name = 'preset-1'
  - description = None
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-creating-a-preset-under-a-category-points-the-node-at-that-category"></a>

#### [creating-a-preset-under-a-category-points-the-node-at-that-category](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py): pass

when a category exists and the superadmin creates a preset naming it, the category in the response references it

Given

- one category and one superadmin
  - Category category-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.create: user-1 creates a preset named cpu-by-kernel under the category seeded in advance

Then

- the whole preset just created comes back
  - id: skipped: the database generates it
  - name = 'cpu-by-kernel'
  - description = None
  - rank = 0
  - category_id: same as the category seeded in advance
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-creating-a-preset-with-a-window-carries-that-window-on-the-node"></a>

#### [creating-a-preset-with-a-window-carries-that-window-on-the-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py): pass

when the superadmin creates a preset with a time window, the node carries that time window

Given

- no preset and one superadmin
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.create: user-1 creates a preset named cpu-by-kernel

Then

- the whole preset just created comes back
  - id: skipped: the database generates it
  - name = 'cpu-by-kernel'
  - description = None
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = '5m'
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-creating-a-preset-with-the-required-values-answers-with-the-whole-node"></a>

#### [creating-a-preset-with-the-required-values-answers-with-the-whole-node](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py): pass

when the superadmin creates a preset specifying only a name, a metric name, a template and allowed label lists, the whole node comes back with rank 0 and an empty category, description and time window

Given

- no preset and one superadmin
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.create: user-1 creates a preset named cpu-by-kernel

Then

- the whole preset just created comes back
  - id: skipped: the database generates it
  - name = 'cpu-by-kernel'
  - description = None
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-category-id-nothing-answers-to-is-refused"></a>

#### [a-category-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py): pass

when the superadmin creates a preset naming a category id that does not exist, it is rejected because the category does not exist. The repository's reference constraint blocks it, and it has not been moved to a domain error

Given

- no preset and one superadmin
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.create: user-1 creates a preset named cpu-by-kernel under an unknown category id

Then

- the call is rejected
  - rejected: ForeignKeyViolationError

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-preset"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py): pass

when a user who is not the superadmin tries to create a preset, it is rejected for lack of role

Given

- no preset and one user
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.create: user-1 creates a preset named cpu-by-kernel

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-the-monitor-role-may-not-create-a-preset"></a>

#### [the-monitor-role-may-not-create-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py): pass

when the monitor role tries to create a preset, it is rejected for lack of role. The superadmin check allows the monitor only for reads

Given

- no preset and one monitor
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - monitor user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - monitor user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.create: user-1 creates a preset named cpu-by-kernel

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-still-does-not-let-a-user-create-a-preset"></a>

#### [turning-enforcement-off-still-does-not-let-a-user-create-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_creating.py): pass

turning the permission check off still rejects creating a preset

Given

- no preset and one user
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.create: user-1 creates a preset named cpu-by-kernel

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### execute_preset

<a id="executing-running-a-preset-over-a-range-is-a-range-query"></a>

#### [running-a-preset-over-a-range-is-a-range-query](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py): pass

when the superadmin runs a preset giving a start, an end and a step, the mock server answers with a range query

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1: sets the time window to 1h
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.execute_preset: user-1 runs preset-1 (a query range given)

Then

- the result carrying the query the mock server received comes back
  - status = 'success'
  - result_type = 'matrix'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[1h]))')])]

<a id="executing-running-a-preset-without-a-range-is-an-instant-query-carrying-the-asked-window"></a>

#### [running-a-preset-without-a-range-is-an-instant-query-carrying-the-asked-window](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py): pass

when the superadmin runs a preset with no time window, giving a time window and no query range, it answers with an instant query and the query the mock server received carries the requested time window

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.execute_preset: user-1 runs preset-1 (time window 30s)

Then

- the result carrying the query the mock server received comes back
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[30s]))')])]

<a id="executing-turning-enforcement-off-lets-a-user-run-a-preset"></a>

#### [turning-enforcement-off-lets-a-user-run-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py): pass

turning the permission check off lets even a user granted nothing run a preset

Given

- one existing preset and one user who can read presets
  - Query preset preset-1: sets the time window to 1h
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.execute_preset: user-1 runs preset-1 (nothing given)

Then

- the result carrying the query the mock server received comes back
  - status = 'success'
  - result_type = 'vector'
  - result = [([], [(1000.0, 'avg by () (rate(container_cpu_seconds_total{}[1h]))')])]

<a id="executing-a-query-prometheus-refuses-is-refused-as-a-failed-metric-read"></a>

#### [a-query-prometheus-refuses-is-refused-as-a-failed-metric-read](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py): pass

when the superadmin runs without labels a preset that renders an empty query without them, Prometheus rejects the query and that rejection propagates as a failure to get the metric

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1: has a template that renders to an empty query without labels
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.execute_preset: user-1 runs preset-1 (nothing given)

Then

- the call is rejected
  - rejected: FailedToGetMetric

<a id="executing-a-user-granted-nothing-may-not-run-a-preset"></a>

#### [a-user-granted-nothing-may-not-run-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py): pass

when a user granted nothing runs a preset, it is rejected for lack of permission. Run requires the same permission as read

Given

- one existing preset and one user with no permission
  - Query preset preset-1
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- PrometheusQueryPresetAdapter.execute_preset: user-1 runs preset-1 (nothing given)

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="executing-running-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [running-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py): pass

when the superadmin runs an id that does not exist, it is rejected because the target is not found. Run raises this error by reading the preset directly in the service, so it differs in kind from the not-found of edit and delete

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.execute_preset: user-1 runs an absent id (nothing given)

Then

- the call is rejected
  - rejected: PrometheusQueryPresetNotFound

<a id="executing-running-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user"></a>

#### [running-an-id-nothing-answers-to-is-refused-as-permission-for-a-plain-user](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_executing.py): pass

when a user granted nothing runs an id that does not exist, it is rejected for lack of permission rather than as not found, because a row that does not exist has no permission granted

Given

- one existing preset and one user who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.execute_preset: user-1 runs an absent id (nothing given)

Then

- the call is rejected
  - rejected: NotEnoughPermission

### partial_bulk_update

<a id="partial_bulk_editing-a-broken-template-fails-only-the-preset-it-was-meant-for"></a>

#### [a-broken-template-fails-only-the-preset-it-was-meant-for](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_partial_bulk_editing.py): pass

when the superadmin edits several presets at once and gives one a broken template, only that one comes back in the failed list for the template check and the rest are edited

Given

- 2 presets and one superadmin
  - Query preset wanted-1
  - Query preset other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.partial_bulk_update: user-1 edits the descriptions of 2 presets at once, the first with a broken template too

Then

- the first, whose template is broken, comes back in the failed list for that reason, and the rest come back in the processed list with the new description
  - successes count = 1
  - successes[0]: same as the whole target preset carrying the new description
  - successes[0].updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the id of the first preset
  - failed[0].message: a reason containing 'Unsupported template variable'

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-presets"></a>

#### [a-user-granted-nothing-edits-none-of-several-presets](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_partial_bulk_editing.py): pass

when a user granted nothing tries to edit several presets at once, nothing is edited and all come back in the failed list for lack of permission

Given

- 2 presets and one user
  - Query preset wanted-1
  - Query preset other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.partial_bulk_update: user-1 edits the descriptions of 2 presets at once

Then

- no preset is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target preset
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target preset
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-presets-at-once"></a>

#### [the-superadmin-edits-several-presets-at-once](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_partial_bulk_editing.py): pass

when the superadmin changes the descriptions of several presets at once, all come back with the new description and none failed

Given

- 2 presets and one superadmin
  - Query preset wanted-1
  - Query preset other-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.partial_bulk_update: user-1 edits the descriptions of 2 presets at once

Then

- every target preset comes back with the new description and none failed
  - successes count = 2
  - successes[0]: same as the whole target preset carrying the new description
  - successes[0].updated_at: the time this run wrote
  - successes[1]: same as the whole target preset carrying the new description
  - successes[1].updated_at: the time this run wrote
  - failed = []

### update

<a id="editing-an-update-giving-no-value-answers-the-node-unchanged"></a>

#### [an-update-giving-no-value-answers-the-node-unchanged](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py): pass

when the superadmin edits without giving any value, the node comes back with nothing changed

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.update: user-1 edits preset-1 (empty request)

Then

- the whole preset seeded in advance comes back
  - id: same as the preset seeded in advance
  - name = 'preset-1'
  - description = 'a query preset created in advance'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-changing-only-the-filter-labels-keeps-the-group-labels"></a>

#### [changing-only-the-filter-labels-keeps-the-group-labels](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py): pass

when the superadmin edits only the filter labels of a preset that has both filter and group labels, the filter labels are the new value and the group labels stay as they are

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1: limits filter labels to kernel_id, limits group labels to agent_id
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.update: user-1 edits preset-1 (filter label change)

Then

- the whole preset seeded in advance comes back
  - id: same as the preset seeded in advance
  - name = 'preset-1'
  - description = 'a query preset created in advance'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = ['session_id']
  - options.group_labels = ['agent_id']
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-clearing-the-description-leaves-it-empty"></a>

#### [clearing-the-description-leaves-it-empty](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py): pass

when the superadmin edits a preset that has a description to clear it, the description is gone

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.update: user-1 edits preset-1 (clear the description)

Then

- the whole preset seeded in advance comes back
  - id: same as the preset seeded in advance
  - name = 'preset-1'
  - description = None
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-moving-a-preset-to-another-category-points-the-node-at-that-one"></a>

#### [moving-a-preset-to-another-category-points-the-node-at-that-one](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py): pass

when the superadmin moves a preset filed under one of two categories to the other, the category in the response references it

Given

- two categories, one preset filed under one of them and one superadmin
  - Category home-1
  - Category elsewhere-1
  - Query preset preset-1: belongs to a category
  - Domain home-2
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.update: user-1 edits preset-1 (move to another category)

Then

- the whole preset seeded in advance comes back
  - id: same as the preset seeded in advance
  - name = 'preset-1'
  - description = 'a query preset created in advance'
  - rank = 0
  - category_id: same as the other category
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-the-superadmin-changes-the-template-and-the-rest-stays"></a>

#### [the-superadmin-changes-the-template-and-the-rest-stays](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py): pass

when a preset exists and the superadmin edits only the template, the template is the new value and the rest stays as it is

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.update: user-1 edits preset-1 (template change)

Then

- the whole preset seeded in advance comes back
  - id: same as the preset seeded in advance
  - name = 'preset-1'
  - description = 'a query preset created in advance'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'sum by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-turning-enforcement-off-lets-a-user-edit-a-preset"></a>

#### [turning-enforcement-off-lets-a-user-edit-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py): pass

turning the permission check off lets even a user granted nothing edit a preset

Given

- one existing preset and one user who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.update: user-1 edits preset-1 (rename)

Then

- the whole preset seeded in advance comes back
  - id: same as the preset seeded in advance
  - name = 'cpu-by-session'
  - description = 'a query preset created in advance'
  - rank = 0
  - category_id = None
  - metric_name = 'container_cpu_seconds_total'
  - query_template = 'avg by (${{group_by}}) (rate(container_cpu_seconds_total{${{labels}}}[${{window}}]))'
  - time_window = None
  - options.filter_labels = []
  - options.group_labels = []
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-a-user-granted-nothing-may-not-edit-a-preset"></a>

#### [a-user-granted-nothing-may-not-edit-a-preset](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py): pass

when the same preset exists and a user granted nothing edits its name, it is rejected for lack of permission. This entity belongs to no scope, so there is no way to grant permission on it

Given

- one existing preset and one user who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - regular user user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - regular user user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.update: user-1 edits preset-1 (rename)

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-editing-an-id-nothing-answers-to-is-not-found-for-a-superadmin"></a>

#### [editing-an-id-nothing-answers-to-is-not-found-for-a-superadmin](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py): pass

when the superadmin edits the name of an id that does not exist, it is rejected because the target is not found

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.update: user-1 edits an absent id (rename)

Then

- the call is rejected
  - rejected: EntityNotFoundError

<a id="editing-moving-a-preset-to-a-category-id-nothing-answers-to-is-refused"></a>

#### [moving-a-preset-to-a-category-id-nothing-answers-to-is-refused](/tests/scenario/bai_scenario/manager/prometheus_query_preset/test_editing.py): pass

when the superadmin edits a preset naming a category id that does not exist, it is rejected because the category does not exist. The repository's reference constraint blocks it, and it has not been moved to a domain error

Given

- one existing preset and one superadmin who can read presets
  - Query preset preset-1
  - Domain home-1
  - Prepare a user granted read permission on prometheus_query_preset in public
    - Prepare one user in the domain
      - Project resource policy default: the personal project created along with a user looks it up by this name
      - User resource policy user-policy-1: up to 10 folders per user
      - Keypair policy keypair-policy-1: up to 5 concurrent sessions
      - superadmin user-1: has their own keypair and personal project
    - Role public-reader-1: applies only within the scope it is granted in
    - Role public-reader-1: READ allowed on every prometheus_query_preset
    - superadmin user-1: holds Role public-reader-1

When

- PrometheusQueryPresetAdapter.update: user-1 edits preset-1 (move to an unknown category id)

Then

- the call is rejected
  - rejected: ForeignKeyViolationError

