## audit_log

[background](/src/ai/backend/manager/api/adapters/audit_log/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/audit_log/adapter.py)

Scenario: incomplete 1 / 5

- built from ops (5)
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - batch_load_scopes_by_ids: representative success ✓ · representative rejection ✗: SCENARIO-GAP
  - scoped_search: representative success ✓ · representative rejection ✓
  - search_scopes: representative success ✓ · representative rejection ✓

**admin_search**

| scenario | verdict |
|---|---|
| [when one run left records on several entities and its run filter is used, every record that run left comes back, and only those](#searching-a-run-filter-answers-every-record-the-run-left-and-only-those) | answered |
| [when success records and rejected records are mixed and a success status filter is used, only the successful records come back](#searching-a-status-filter-narrows-the-answer-to-the-status-it-names) | answered |
| [when two users each left records and one user filter is used, only the records that user triggered come back](#searching-an-actor-filter-narrows-the-answer-to-the-user-who-triggered-it) | answered |
| [when a search gives no page size, ten items come back and it answers that there is a next page](#searching-omitting-the-page-size-caps-the-page-and-says-more-follow) | answered |
| [because searching is a read operation, a monitor-role user also passes the superadmin check and gets the same response as the superadmin](#searching-the-monitor-role-searching-sees-the-same-records-as-the-superadmin) | answered |
| [when there are two records and the superadmin searches without a filter, both come back with the newest first](#searching-the-superadmin-searching-without-a-filter-sees-every-record-newest-first) | answered |
| [when a search uses a cursor that cannot be decoded, it is rejected as a broken cursor](#searching-a-cursor-that-cannot-be-decoded-is-refused) | rejected |
| [when a user who is neither the superadmin nor a monitor searches everything, it is rejected for lack of role](#searching-a-user-who-is-not-the-superadmin-may-not-search-every-record) | rejected |
| [when a search names both the offset and cursor pagination modes at once, it is rejected as invalid input](#searching-naming-two-pagination-modes-at-once-is-refused) | rejected |
| [turning the permission check off still does not let a user who is not the superadmin search everything](#searching-turning-enforcement-off-does-not-let-a-plain-user-search-every-record) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when an empty id list is read, an empty response comes back without passing the permission check](#batch_loading-reading-an-empty-list-answers-empty-without-passing-the-gate) | answered |
| [when the superadmin reads two present ids and one absent id at once, they come back in the requested order and the item for an absent id is empty](#batch_loading-the-superadmin-reading-present-and-absent-ids-is-answered-in-order-with-a-gap) | answered |
| [when a user granted read on only one project reads a readable record, an unreadable record and an absent id at once, a whole record, a permission failure and an empty item come back in the requested order](#batch_loading-a-granted-reader-gets-a-node-a-rejection-and-a-gap-in-order) | rejected |
| [when a user granted read only on the scope a record left reads that record and a record of another project, the record reached through the scope comes back and the other answers with a permission failure](#batch_loading-a-record-is-read-through-a-scope-it-recorded) | rejected |
| [when a user granted read only on the user who triggered a record reads that record and a record of another project, the record reached through the triggering user comes back and the other answers with a permission failure](#batch_loading-a-record-is-read-through-the-user-who-triggered-it) | rejected |
| [when a user without read permission reads two records about themselves by id, every item answers with a permission failure](#batch_loading-a-user-granted-nothing-is-refused-in-every-slot-even-for-records-about-themselves) | rejected |
| [when a monitor-role user granted nothing reads two ids, every item answers with a permission failure](#batch_loading-the-monitor-role-without-a-grant-is-refused-in-every-slot) | rejected |

**batch_load_scopes_by_ids**

| scenario | verdict |
|---|---|
| [when the superadmin batch-loads the two scopes a record left and one unknown id, they come back in the order asked and the item for the unknown id is empty](#batch_loading_scopes-the-superadmin-batch-load-leaves-a-missing-scope-id-empty) | answered |

**scoped_search**

| scenario | verdict |
|---|---|
| [when a record about another entity carries a project as its scope and that project is named in a search, the record comes back even though its target entity is not that project](#scoped_searching-a-record-tagged-with-a-scope-is-found-by-searching-that-scope) | answered |
| [when one entity holds records left by two runs and it is searched with one run filter, every record that run left comes back](#scoped_searching-a-run-filter-narrows-within-the-named-scope) | answered |
| [when one entity holds a success record and a rejected record and it is searched with a success status filter, only the successful record comes back](#scoped_searching-a-status-filter-narrows-within-the-named-scope) | answered |
| [when two users each left a record and a user granted read on one of them searches naming that user as the one who triggered records, only the records that user triggered come back](#scoped_searching-a-user-granted-read-on-an-actor-reads-only-what-that-actor-triggered) | answered |
| [when each of two entities has one record and a user granted read on only one of them searches naming that entity, only the records of that entity come back](#scoped_searching-a-user-granted-read-on-an-entity-reads-only-that-entitys-records) | answered |
| [when a user granted read on both of two entities searches naming both, both records come back with the newest first](#scoped_searching-naming-several-readable-entities-merges-their-records-newest-first) | answered |
| [when the named entity holds many records and no page size is given, ten items come back and it answers that there is a next page](#scoped_searching-omitting-the-page-size-caps-a-scoped-page-and-says-more-follow) | answered |
| [when the superadmin searches naming an id that is no entity, it passes the permission check and an empty page comes back instead of a rejection](#scoped_searching-the-superadmin-naming-an-entity-nothing-answers-to-finds-nothing) | answered |
| [turning the permission check off lets even a user granted nothing search the records of a named entity](#scoped_searching-turning-enforcement-off-reads-a-named-entitys-records-without-a-grant) | answered |
| [when the named id is not in id form, it is rejected as invalid input](#scoped_searching-a-scope-id-that-is-not-an-entity-id-is-refused) | rejected |
| [when a user granted no read on themselves searches naming themselves as the one who triggered records, it is rejected for lack of permission, because there is no separate call that reads one's own records](#scoped_searching-a-user-granted-nothing-may-not-read-even-the-records-they-triggered) | rejected |
| [when a user granted nothing searches naming an entity, it is rejected for lack of permission](#scoped_searching-a-user-granted-nothing-may-not-scope-search-an-entity) | rejected |
| [when a user granted read on another entity searches naming an id that is no entity, it is rejected for lack of permission because no permission is granted on that id](#scoped_searching-naming-an-entity-nothing-answers-to-is-refused-as-permission) | rejected |
| [when a user granted read on only one of two entities searches naming both, the whole request is rejected for lack of permission instead of giving only what is readable](#scoped_searching-one-unreadable-entity-among-those-named-refuses-the-whole-read) | rejected |
| [even a monitor-role user is rejected for lack of permission when searching naming an entity without a grant. The monitor passes only the superadmin check, and this search is protected by the permission graph](#scoped_searching-the-monitor-role-without-a-grant-may-not-scope-search) | rejected |

**search_scopes**

| scenario | verdict |
|---|---|
| [when a user granted read on only one scope a record left searches, every scope that record left comes back](#scope_searching-a-reader-of-one-scope-reads-every-scope-of-the-record) | answered |
| [when a user granted read only on the entity a record is about searches, the scopes of that record come back](#scope_searching-a-reader-of-the-entity-a-record-is-about-reads-its-scopes) | answered |
| [when a user granted read only on the user who triggered a record searches, the scopes of that record come back](#scope_searching-a-reader-of-the-user-who-triggered-a-record-reads-its-scopes) | answered |
| [when a user granted read on the target of a record that left no scope searches, an empty page comes back](#scope_searching-a-record-that-recorded-no-scope-answers-an-empty-page) | answered |
| [when a record that left two scopes is searched naming the identifier of one scope, only that scope comes back](#scope_searching-a-scope-id-filter-narrows-the-answer-to-that-scope) | answered |
| [when a record that left two scopes is searched naming only the project type, only the project scope comes back](#scope_searching-a-scope-type-filter-narrows-the-answer-to-that-type) | answered |
| [when the superadmin searches a record that left two scopes, both scopes come back](#scope_searching-the-superadmin-reads-every-scope-a-record-recorded) | answered |
| [turning the permission check off lets even a user granted nothing search the scopes of a record](#scope_searching-turning-enforcement-off-reads-the-scopes-without-a-grant) | answered |
| [when a user who can read none of the owners of a record searches, it is rejected for lack of permission](#scope_searching-a-user-who-can-read-no-owner-is-refused) | rejected |
| [when the superadmin searches with an id that matches no record, it is rejected as not found](#scope_searching-searching-a-record-that-does-not-exist-is-not-found) | rejected |
| [when a monitor-role user granted nothing searches, it is rejected for lack of permission. This search is protected by the permission graph](#scope_searching-the-monitor-role-without-a-grant-is-refused) | rejected |

### admin_search

<a id="searching-a-run-filter-answers-every-record-the-run-left-and-only-those"></a>

#### [a-run-filter-answers-every-record-the-run-left-and-only-those](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

when one run left records on several entities and its run filter is used, every record that run left comes back, and only those

Given

- records one run left on each of two users, one record another run left, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - regular user user-1: 'edited' record, recorded in the same run as another record
  - regular user user-2: 'created' record, recorded in the same run as another record
  - regular user user-1: 'ran-separately' record

When

- AuditLogAdapter.admin_search: user-3 searches with a run filter

Then

- the named records come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'edited'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'created'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="searching-a-status-filter-narrows-the-answer-to-the-status-it-names"></a>

#### [a-status-filter-narrows-the-answer-to-the-status-it-names](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

when success records and rejected records are mixed and a success status filter is used, only the successful records come back

Given

- a successful record and a rejected record, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - superadmin user-1: 'succeeded' record
  - superadmin user-1: 'was-refused' record, status denied

When

- AuditLogAdapter.admin_search: user-1 searches with a success status filter

Then

- the named records come back in order, and only those
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'succeeded'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'succeeded was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="searching-an-actor-filter-narrows-the-answer-to-the-user-who-triggered-it"></a>

#### [an-actor-filter-narrows-the-answer-to-the-user-who-triggered-it](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

when two users each left records and one user filter is used, only the records that user triggered come back

Given

- records two users each left, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - regular user user-1: 'acted-by-me' record, the user who ran it is specified
  - regular user user-2: 'acted-by-another' record, the user who ran it is specified

When

- AuditLogAdapter.admin_search: user-3 searches with a triggered-user filter

Then

- the named records come back in order, and only those
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'acted-by-me'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'acted-by-me was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by: same as the user who ran it

<a id="searching-omitting-the-page-size-caps-the-page-and-says-more-follow"></a>

#### [omitting-the-page-size-caps-the-page-and-says-more-follow](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

when a search gives no page size, ten items come back and it answers that there is a next page

Given

- 11 records and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - superadmin user-1: 'op-0' record
  - superadmin user-1: 'op-1' record
  - superadmin user-1: 'op-2' record
  - superadmin user-1: 'op-3' record
  - superadmin user-1: 'op-4' record
  - superadmin user-1: 'op-5' record
  - superadmin user-1: 'op-6' record
  - superadmin user-1: 'op-7' record
  - superadmin user-1: 'op-8' record
  - superadmin user-1: 'op-9' record
  - superadmin user-1: 'op-10' record

When

- AuditLogAdapter.admin_search: user-1 searches without a page size

Then

- the default page size comes back and the answer says another page follows
  - items_count = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="searching-the-monitor-role-searching-sees-the-same-records-as-the-superadmin"></a>

#### [the-monitor-role-searching-sees-the-same-records-as-the-superadmin](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

because searching is a read operation, a monitor-role user also passes the superadmin check and gets the same response as the superadmin

Given

- two records from different times and one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - monitor user-1: 'edited' record
  - monitor user-1: 'created' record

When

- AuditLogAdapter.admin_search: user-1 searches everything without a filter

Then

- the named records come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'edited'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'created'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="searching-the-superadmin-searching-without-a-filter-sees-every-record-newest-first"></a>

#### [the-superadmin-searching-without-a-filter-sees-every-record-newest-first](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

when there are two records and the superadmin searches without a filter, both come back with the newest first

Given

- two records from different times and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - superadmin user-1: 'edited' record
  - superadmin user-1: 'created' record

When

- AuditLogAdapter.admin_search: user-1 searches everything without a filter

Then

- the named records come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'edited'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'created'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="searching-a-cursor-that-cannot-be-decoded-is-refused"></a>

#### [a-cursor-that-cannot-be-decoded-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

when a search uses a cursor that cannot be decoded, it is rejected as a broken cursor

Given

- two records from different times and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - superadmin user-1: 'edited' record
  - superadmin user-1: 'created' record

When

- AuditLogAdapter.admin_search: user-1 searches with a broken cursor

Then

- the call is rejected
  - rejected: InvalidCursor

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-every-record"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-every-record](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

when a user who is neither the superadmin nor a monitor searches everything, it is rejected for lack of role

Given

- two records from different times and one user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: 'edited' record
  - regular user user-1: 'created' record

When

- AuditLogAdapter.admin_search: user-1 searches everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="searching-naming-two-pagination-modes-at-once-is-refused"></a>

#### [naming-two-pagination-modes-at-once-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

when a search names both the offset and cursor pagination modes at once, it is rejected as invalid input

Given

- two records from different times and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - superadmin user-1: 'edited' record
  - superadmin user-1: 'created' record

When

- AuditLogAdapter.admin_search: user-1 searches naming both pagination modes at once

Then

- the call is rejected
  - rejected: InvalidGraphQLParameters

<a id="searching-turning-enforcement-off-does-not-let-a-plain-user-search-every-record"></a>

#### [turning-enforcement-off-does-not-let-a-plain-user-search-every-record](/tests/scenario/bai_scenario/manager/audit_log/test_searching.py): pass

turning the permission check off still does not let a user who is not the superadmin search everything

Given

- two records from different times and one user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: 'edited' record
  - regular user user-1: 'created' record

When

- AuditLogAdapter.admin_search: user-1 searches everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-reading-an-empty-list-answers-empty-without-passing-the-gate"></a>

#### [reading-an-empty-list-answers-empty-without-passing-the-gate](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py): pass

when an empty id list is read, an empty response comes back without passing the permission check

Given

- two records about the caller to read by id, and one user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: 'edited' record
  - regular user user-1: 'created' record

When

- AuditLogAdapter.batch_load_by_ids: user-1 reads with an empty id list

Then

- for each item in request order, a node, a rejection, or an empty item comes back
  - length = 0

<a id="batch_loading-the-superadmin-reading-present-and-absent-ids-is-answered-in-order-with-a-gap"></a>

#### [the-superadmin-reading-present-and-absent-ids-is-answered-in-order-with-a-gap](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py): pass

when the superadmin reads two present ids and one absent id at once, they come back in the requested order and the item for an absent id is empty

Given

- two records about the caller to read by id, and one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project
  - superadmin user-1: 'edited' record
  - superadmin user-1: 'created' record

When

- AuditLogAdapter.batch_load_by_ids: user-1 reads two present ids and one absent id at once

Then

- for each item in request order, a node, a rejection, or an empty item comes back
  - length = 3
  - [0].id: skipped: the database generates it
  - [0].action_id: skipped: a new one is generated each run
  - [0].operation = 'edited'
  - [0].entity_type = 'user'
  - [0].entity_id: same as the entity the record is about
  - [0].target_entity_id: same as the entity the record is about
  - [0].status = <AuditLogStatus.SUCCESS: 'success'>
  - [0].description = 'edited was recorded'
  - [0].created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - [0].request_id = None
  - [0].acted_as = None
  - [0].duration = None
  - [0].client_ip = None
  - [0].triggered_by = None
  - [1] = None
  - [2].id: skipped: the database generates it
  - [2].action_id: skipped: a new one is generated each run
  - [2].operation = 'created'
  - [2].entity_type = 'user'
  - [2].entity_id: same as the entity the record is about
  - [2].target_entity_id: same as the entity the record is about
  - [2].status = <AuditLogStatus.SUCCESS: 'success'>
  - [2].description = 'created was recorded'
  - [2].created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - [2].request_id = None
  - [2].acted_as = None
  - [2].duration = None
  - [2].client_ip = None
  - [2].triggered_by = None

<a id="batch_loading-a-granted-reader-gets-a-node-a-rejection-and-a-gap-in-order"></a>

#### [a-granted-reader-gets-a-node-a-rejection-and-a-gap-in-order](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py): pass

when a user granted read on only one project reads a readable record, an unreadable record and an absent id at once, a whole record, a permission failure and an empty item come back in the requested order

Given

- two records of different projects, and one user granted read permission on the first project only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1

When

- AuditLogAdapter.batch_load_by_ids: user-1 reads a readable record, an unreadable record and an absent id, in that order

Then

- for each item in request order, a node, a rejection, or an empty item comes back
  - length = 3
  - [0].id: skipped: the database generates it
  - [0].action_id: skipped: a new one is generated each run
  - [0].operation = 'edited'
  - [0].entity_type = 'project'
  - [0].entity_id: same as the entity the record is about
  - [0].target_entity_id: same as the entity the record is about
  - [0].status = <AuditLogStatus.SUCCESS: 'success'>
  - [0].description = 'edited was recorded'
  - [0].created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - [0].request_id = None
  - [0].acted_as = None
  - [0].duration = None
  - [0].client_ip = None
  - [0].triggered_by = None
  - rejected: NotEnoughPermission
  - [2] = None

<a id="batch_loading-a-record-is-read-through-a-scope-it-recorded"></a>

#### [a-record-is-read-through-a-scope-it-recorded](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py): pass

when a user granted read only on the scope a record left reads that record and a record of another project, the record reached through the scope comes back and the other answers with a permission failure

Given

- a record about one user that left a project as its scope, one record on another project, and one user granted read permission on the scope project only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: 'linked' record, 1 scopes added
  - Project other-1: 'created' record
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-2: holds Role record-reader-1

When

- AuditLogAdapter.batch_load_by_ids: user-2 reads two present ids at once

Then

- for each item in request order, a node, a rejection, or an empty item comes back
  - length = 2
  - [0].id: skipped: the database generates it
  - [0].action_id: skipped: a new one is generated each run
  - [0].operation = 'linked'
  - [0].entity_type = 'user'
  - [0].entity_id: same as the entity the record is about
  - [0].target_entity_id: same as the entity the record is about
  - [0].status = <AuditLogStatus.SUCCESS: 'success'>
  - [0].description = 'linked was recorded'
  - [0].created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - [0].request_id = None
  - [0].acted_as = None
  - [0].duration = None
  - [0].client_ip = None
  - [0].triggered_by = None
  - rejected: NotEnoughPermission

<a id="batch_loading-a-record-is-read-through-the-user-who-triggered-it"></a>

#### [a-record-is-read-through-the-user-who-triggered-it](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py): pass

when a user granted read only on the user who triggered a record reads that record and a record of another project, the record reached through the triggering user comes back and the other answers with a permission failure

Given

- a record about one project triggered by another user, one record on another project, and one user granted read permission on the triggering user only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - Project team-1: 'acted-on-a-project' record, the user who ran it is specified
  - Project other-1: 'created' record
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every user
  - regular user user-2: holds Role record-reader-1

When

- AuditLogAdapter.batch_load_by_ids: user-2 reads two present ids at once

Then

- for each item in request order, a node, a rejection, or an empty item comes back
  - length = 2
  - [0].id: skipped: the database generates it
  - [0].action_id: skipped: a new one is generated each run
  - [0].operation = 'acted-on-a-project'
  - [0].entity_type = 'project'
  - [0].entity_id: same as the entity the record is about
  - [0].target_entity_id: same as the entity the record is about
  - [0].status = <AuditLogStatus.SUCCESS: 'success'>
  - [0].description = 'acted-on-a-project was recorded'
  - [0].created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - [0].request_id = None
  - [0].acted_as = None
  - [0].duration = None
  - [0].client_ip = None
  - [0].triggered_by: same as the user who ran it
  - rejected: NotEnoughPermission

<a id="batch_loading-a-user-granted-nothing-is-refused-in-every-slot-even-for-records-about-themselves"></a>

#### [a-user-granted-nothing-is-refused-in-every-slot-even-for-records-about-themselves](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py): pass

when a user without read permission reads two records about themselves by id, every item answers with a permission failure

Given

- two records about the caller to read by id, and one user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - regular user user-1: 'edited' record
  - regular user user-1: 'created' record

When

- AuditLogAdapter.batch_load_by_ids: user-1 reads two present ids at once

Then

- for each item in request order, a node, a rejection, or an empty item comes back
  - length = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

<a id="batch_loading-the-monitor-role-without-a-grant-is-refused-in-every-slot"></a>

#### [the-monitor-role-without-a-grant-is-refused-in-every-slot](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading.py): pass

when a monitor-role user granted nothing reads two ids, every item answers with a permission failure

Given

- two records about the caller to read by id, and one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project
  - monitor user-1: 'edited' record
  - monitor user-1: 'created' record

When

- AuditLogAdapter.batch_load_by_ids: user-1 reads two present ids at once

Then

- for each item in request order, a node, a rejection, or an empty item comes back
  - length = 2
  - rejected: NotEnoughPermission
  - rejected: NotEnoughPermission

### batch_load_scopes_by_ids

<a id="batch_loading_scopes-the-superadmin-batch-load-leaves-a-missing-scope-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-scope-id-empty](/tests/scenario/bai_scenario/manager/audit_log/test_batch_loading_scopes.py): pass

when the superadmin batch-loads the two scopes a record left and one unknown id, they come back in the order asked and the item for the unknown id is empty

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added

When

- AuditLogAdapter.batch_load_scopes_by_ids: user-3 reads the scopes of one record and one unknown id at once

Then

- they come back in the order asked and the item for an unknown id is empty
  - len(items) = 3
  - items[0].id: same as the scope entry the search read
  - items[0].field_id: same as the scope entry the search read
  - items[0].audit_log_id: same as the scope entry the search read
  - items[0].scope_type = 'project'
  - items[0].scope_id: same as the scope entry the search read
  - items[1].id: same as the scope entry the search read
  - items[1].field_id: same as the scope entry the search read
  - items[1].audit_log_id: same as the scope entry the search read
  - items[1].scope_type = 'user'
  - items[1].scope_id: same as the scope entry the search read
  - items[2] = None

### scoped_search

<a id="scoped_searching-a-record-tagged-with-a-scope-is-found-by-searching-that-scope"></a>

#### [a-record-tagged-with-a-scope-is-found-by-searching-that-scope](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when a record about another entity carries a project as its scope and that project is named in a search, the record comes back even though its target entity is not that project

Given

- a record about another entity carrying a project as its scope, and one user granted read permission on that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: 'linked' record, 1 scopes added
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-2: holds Role record-reader-1

When

- AuditLogAdapter.scoped_search: user-2 searches naming an entity

Then

- the named records come back in order, and only those
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'linked'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'linked was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="scoped_searching-a-run-filter-narrows-within-the-named-scope"></a>

#### [a-run-filter-narrows-within-the-named-scope](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when one entity holds records left by two runs and it is searched with one run filter, every record that run left comes back

Given

- one project holding two records one run left and one record another run left, and one user granted read permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-1: 'edited' record, recorded in the same run as another record
  - Project team-1: 'created' record, recorded in the same run as another record
  - Project team-1: 'ran-separately' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity with a run filter

Then

- the named records come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'edited'
  - entity_type = 'project'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'created'
  - entity_type = 'project'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="scoped_searching-a-status-filter-narrows-within-the-named-scope"></a>

#### [a-status-filter-narrows-within-the-named-scope](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when one entity holds a success record and a rejected record and it is searched with a success status filter, only the successful record comes back

Given

- one project holding a successful record and a rejected record, and one user granted read permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-1: 'succeeded' record
  - Project team-1: 'was-refused' record, status denied
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity with a success status filter

Then

- the named records come back in order, and only those
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'succeeded'
  - entity_type = 'project'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'succeeded was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="scoped_searching-a-user-granted-read-on-an-actor-reads-only-what-that-actor-triggered"></a>

#### [a-user-granted-read-on-an-actor-reads-only-what-that-actor-triggered](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when two users each left a record and a user granted read on one of them searches naming that user as the one who triggered records, only the records that user triggered come back

Given

- records two users each triggered, and another user granted read permission on that user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - regular user user-1: 'acted-by-me' record, the user who ran it is specified
  - regular user user-2: 'acted-by-another' record, the user who ran it is specified
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every user
  - regular user user-3: holds Role record-reader-1

When

- AuditLogAdapter.scoped_search: user-3 searches naming the user who triggered records

Then

- the named records come back in order, and only those
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'acted-by-me'
  - entity_type = 'user'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'acted-by-me was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by: same as the user who ran it

<a id="scoped_searching-a-user-granted-read-on-an-entity-reads-only-that-entitys-records"></a>

#### [a-user-granted-read-on-an-entity-reads-only-that-entitys-records](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when each of two entities has one record and a user granted read on only one of them searches naming that entity, only the records of that entity come back

Given

- two records of different projects, and one user granted read permission on the the first projects
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity

Then

- the named records come back in order, and only those
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'edited'
  - entity_type = 'project'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="scoped_searching-naming-several-readable-entities-merges-their-records-newest-first"></a>

#### [naming-several-readable-entities-merges-their-records-newest-first](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when a user granted read on both of two entities searches naming both, both records come back with the newest first

Given

- two records of different projects, and one user granted read permission on the the first and the second projects
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1
  - Role record-reader-2: applies only within the scope it is granted in
  - Role record-reader-2: READ allowed on every project
  - regular user user-1: holds Role record-reader-2

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity

Then

- the named records come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'edited'
  - entity_type = 'project'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'created'
  - entity_type = 'project'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'created was recorded'
  - created_at = datetime.datetime(2026, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="scoped_searching-omitting-the-page-size-caps-a-scoped-page-and-says-more-follow"></a>

#### [omitting-the-page-size-caps-a-scoped-page-and-says-more-follow](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when the named entity holds many records and no page size is given, ten items come back and it answers that there is a next page

Given

- one project holding 11 records, and one user granted read permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-1: 'op-0' record
  - Project team-1: 'op-1' record
  - Project team-1: 'op-2' record
  - Project team-1: 'op-3' record
  - Project team-1: 'op-4' record
  - Project team-1: 'op-5' record
  - Project team-1: 'op-6' record
  - Project team-1: 'op-7' record
  - Project team-1: 'op-8' record
  - Project team-1: 'op-9' record
  - Project team-1: 'op-10' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity

Then

- the default page size comes back and the answer says another page follows
  - items_count = 10
  - total_count = 11
  - has_next_page = True
  - has_previous_page = False

<a id="scoped_searching-the-superadmin-naming-an-entity-nothing-answers-to-finds-nothing"></a>

#### [the-superadmin-naming-an-entity-nothing-answers-to-finds-nothing](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when the superadmin searches naming an id that is no entity, it passes the permission check and an empty page comes back instead of a rejection

Given

- two records of different projects, and one superadmin with no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity

Then

- the answer is empty
  - items = []
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="scoped_searching-turning-enforcement-off-reads-a-named-entitys-records-without-a-grant"></a>

#### [turning-enforcement-off-reads-a-named-entitys-records-without-a-grant](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

turning the permission check off lets even a user granted nothing search the records of a named entity

Given

- two records of different projects, and one user with no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity

Then

- the named records come back in order, and only those
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - id: skipped: the database generates it
  - action_id: skipped: a new one is generated each run
  - operation = 'edited'
  - entity_type = 'project'
  - entity_id: same as the entity the record is about
  - target_entity_id: same as the entity the record is about
  - status = <AuditLogStatus.SUCCESS: 'success'>
  - description = 'edited was recorded'
  - created_at = datetime.datetime(2026, 1, 2, 0, 0, tzinfo=datetime.timezone.utc)
  - request_id = None
  - acted_as = None
  - duration = None
  - client_ip = None
  - triggered_by = None

<a id="scoped_searching-a-scope-id-that-is-not-an-entity-id-is-refused"></a>

#### [a-scope-id-that-is-not-an-entity-id-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when the named id is not in id form, it is rejected as invalid input

Given

- two records of different projects, and one user granted read permission on the the first projects
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1

When

- AuditLogAdapter.scoped_search: user-1 searches naming a value that is not an id

Then

- the call is rejected
  - rejected: InvalidAPIParameters

<a id="scoped_searching-a-user-granted-nothing-may-not-read-even-the-records-they-triggered"></a>

#### [a-user-granted-nothing-may-not-read-even-the-records-they-triggered](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when a user granted no read on themselves searches naming themselves as the one who triggered records, it is rejected for lack of permission, because there is no separate call that reads one's own records

Given

- records two users each triggered, and the first of those users
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: 'acted-by-me' record, the user who ran it is specified
  - regular user user-2: 'acted-by-another' record, the user who ran it is specified

When

- AuditLogAdapter.scoped_search: user-1 searches naming the user who triggered records

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-a-user-granted-nothing-may-not-scope-search-an-entity"></a>

#### [a-user-granted-nothing-may-not-scope-search-an-entity](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when a user granted nothing searches naming an entity, it is rejected for lack of permission

Given

- two records of different projects, and one user with no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-naming-an-entity-nothing-answers-to-is-refused-as-permission"></a>

#### [naming-an-entity-nothing-answers-to-is-refused-as-permission](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when a user granted read on another entity searches naming an id that is no entity, it is rejected for lack of permission because no permission is granted on that id

Given

- two records of different projects, and one user granted read permission on the the first projects
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-one-unreadable-entity-among-those-named-refuses-the-whole-read"></a>

#### [one-unreadable-entity-among-those-named-refuses-the-whole-read](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

when a user granted read on only one of two entities searches naming both, the whole request is rejected for lack of permission instead of giving only what is readable

Given

- two records of different projects, and one user granted read permission on the the first projects
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scoped_searching-the-monitor-role-without-a-grant-may-not-scope-search"></a>

#### [the-monitor-role-without-a-grant-may-not-scope-search](/tests/scenario/bai_scenario/manager/audit_log/test_scoped_searching.py): pass

even a monitor-role user is rejected for lack of permission when searching naming an entity without a grant. The monitor passes only the superadmin check, and this search is protected by the permission graph

Given

- two records of different projects, and one monitor with no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Project team-1: 'edited' record
  - Project other-1: 'created' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- AuditLogAdapter.scoped_search: user-1 searches naming an entity

Then

- the call is rejected
  - rejected: NotEnoughPermission

### search_scopes

<a id="scope_searching-a-reader-of-one-scope-reads-every-scope-of-the-record"></a>

#### [a-reader-of-one-scope-reads-every-scope-of-the-record](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when a user granted read on only one scope a record left searches, every scope that record left comes back

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one user granted read permission on the scope project only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-3: holds Role record-reader-1

When

- AuditLogAdapter.search_scopes: user-3 searches the scopes of one record

Then

- the scopes of the record come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - [0].id: skipped: the database generates it
  - [0].field_id: skipped: the database generates it
  - [0].audit_log_id: same as the record searched
  - [0].scope_type = 'project'
  - [0].scope_id: same as the scope the record left
  - [1].id: skipped: the database generates it
  - [1].field_id: skipped: the database generates it
  - [1].audit_log_id: same as the record searched
  - [1].scope_type = 'user'
  - [1].scope_id: same as the scope the record left

<a id="scope_searching-a-reader-of-the-entity-a-record-is-about-reads-its-scopes"></a>

#### [a-reader-of-the-entity-a-record-is-about-reads-its-scopes](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when a user granted read only on the entity a record is about searches, the scopes of that record come back

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one user granted read permission on the target project only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-3: holds Role record-reader-1

When

- AuditLogAdapter.search_scopes: user-3 searches the scopes of one record

Then

- the scopes of the record come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - [0].id: skipped: the database generates it
  - [0].field_id: skipped: the database generates it
  - [0].audit_log_id: same as the record searched
  - [0].scope_type = 'project'
  - [0].scope_id: same as the scope the record left
  - [1].id: skipped: the database generates it
  - [1].field_id: skipped: the database generates it
  - [1].audit_log_id: same as the record searched
  - [1].scope_type = 'user'
  - [1].scope_id: same as the scope the record left

<a id="scope_searching-a-reader-of-the-user-who-triggered-a-record-reads-its-scopes"></a>

#### [a-reader-of-the-user-who-triggered-a-record-reads-its-scopes](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when a user granted read only on the user who triggered a record searches, the scopes of that record come back

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one user granted read permission on the triggering user only
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every user
  - regular user user-3: holds Role record-reader-1

When

- AuditLogAdapter.search_scopes: user-3 searches the scopes of one record

Then

- the scopes of the record come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - [0].id: skipped: the database generates it
  - [0].field_id: skipped: the database generates it
  - [0].audit_log_id: same as the record searched
  - [0].scope_type = 'project'
  - [0].scope_id: same as the scope the record left
  - [1].id: skipped: the database generates it
  - [1].field_id: skipped: the database generates it
  - [1].audit_log_id: same as the record searched
  - [1].scope_type = 'user'
  - [1].scope_id: same as the scope the record left

<a id="scope_searching-a-record-that-recorded-no-scope-answers-an-empty-page"></a>

#### [a-record-that-recorded-no-scope-answers-an-empty-page](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when a user granted read on the target of a record that left no scope searches, an empty page comes back

Given

- a record of one project that left no scope, and one user granted read permission on that project
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project team-1: 'succeeded' record
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
  - Role record-reader-1: applies only within the scope it is granted in
  - Role record-reader-1: READ allowed on every project
  - regular user user-1: holds Role record-reader-1

When

- AuditLogAdapter.search_scopes: user-1 searches the scopes of one record

Then

- the scopes of the record come back in order, and only those
  - item_count = 0
  - total_count = 0
  - has_next_page = False
  - has_previous_page = False

<a id="scope_searching-a-scope-id-filter-narrows-the-answer-to-that-scope"></a>

#### [a-scope-id-filter-narrows-the-answer-to-that-scope](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when a record that left two scopes is searched naming the identifier of one scope, only that scope comes back

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added

When

- AuditLogAdapter.search_scopes: user-3 searches the scopes of one record, naming the identifier of one scope

Then

- the scopes of the record come back in order, and only those
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - [0].id: skipped: the database generates it
  - [0].field_id: skipped: the database generates it
  - [0].audit_log_id: same as the record searched
  - [0].scope_type = 'user'
  - [0].scope_id: same as the scope the record left

<a id="scope_searching-a-scope-type-filter-narrows-the-answer-to-that-type"></a>

#### [a-scope-type-filter-narrows-the-answer-to-that-type](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when a record that left two scopes is searched naming only the project type, only the project scope comes back

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added

When

- AuditLogAdapter.search_scopes: user-3 searches the scopes of one record, naming only the project type

Then

- the scopes of the record come back in order, and only those
  - item_count = 1
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False
  - [0].id: skipped: the database generates it
  - [0].field_id: skipped: the database generates it
  - [0].audit_log_id: same as the record searched
  - [0].scope_type = 'project'
  - [0].scope_id: same as the scope the record left

<a id="scope_searching-the-superadmin-reads-every-scope-a-record-recorded"></a>

#### [the-superadmin-reads-every-scope-a-record-recorded](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when the superadmin searches a record that left two scopes, both scopes come back

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one superadmin
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - superadmin user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added

When

- AuditLogAdapter.search_scopes: user-3 searches the scopes of one record

Then

- the scopes of the record come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - [0].id: skipped: the database generates it
  - [0].field_id: skipped: the database generates it
  - [0].audit_log_id: same as the record searched
  - [0].scope_type = 'project'
  - [0].scope_id: same as the scope the record left
  - [1].id: skipped: the database generates it
  - [1].field_id: skipped: the database generates it
  - [1].audit_log_id: same as the record searched
  - [1].scope_type = 'user'
  - [1].scope_id: same as the scope the record left

<a id="scope_searching-turning-enforcement-off-reads-the-scopes-without-a-grant"></a>

#### [turning-enforcement-off-reads-the-scopes-without-a-grant](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

turning the permission check off lets even a user granted nothing search the scopes of a record

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one user with no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added

When

- AuditLogAdapter.search_scopes: user-3 searches the scopes of one record

Then

- the scopes of the record come back in order, and only those
  - item_count = 2
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False
  - [0].id: skipped: the database generates it
  - [0].field_id: skipped: the database generates it
  - [0].audit_log_id: same as the record searched
  - [0].scope_type = 'project'
  - [0].scope_id: same as the scope the record left
  - [1].id: skipped: the database generates it
  - [1].field_id: skipped: the database generates it
  - [1].audit_log_id: same as the record searched
  - [1].scope_type = 'user'
  - [1].scope_id: same as the scope the record left

<a id="scope_searching-a-user-who-can-read-no-owner-is-refused"></a>

#### [a-user-who-can-read-no-owner-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when a user who can read none of the owners of a record searches, it is rejected for lack of permission

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one user with no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - regular user user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added

When

- AuditLogAdapter.search_scopes: user-3 searches the scopes of one record

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="scope_searching-searching-a-record-that-does-not-exist-is-not-found"></a>

#### [searching-a-record-that-does-not-exist-is-not-found](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when the superadmin searches with an id that matches no record, it is rejected as not found

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- AuditLogAdapter.search_scopes: user-1 searches the scopes of one record

Then

- the call is rejected
  - rejected: FieldNotFoundError

<a id="scope_searching-the-monitor-role-without-a-grant-is-refused"></a>

#### [the-monitor-role-without-a-grant-is-refused](/tests/scenario/bai_scenario/manager/audit_log/test_scope_searching.py): pass

when a monitor-role user granted nothing searches, it is rejected for lack of permission. This search is protected by the permission graph

Given

- a record about one project was triggered by another user and left another project and one user as its scopes, and one monitor-role user with no permission
  - Domain home-1
  - Project resource policy default: the personal project created along with a user looks it up by this name
  - Project team-1
  - Project other-1
  - Prepare one user in the domain
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
    - User resource policy user-policy-3: up to 10 folders per user
    - Keypair policy keypair-policy-3: up to 5 concurrent sessions
    - monitor user-3: has their own keypair and personal project
  - Project team-1: 'linked' record, 2 scopes added

When

- AuditLogAdapter.search_scopes: user-3 searches the scopes of one record

Then

- the call is rejected
  - rejected: NotEnoughPermission

