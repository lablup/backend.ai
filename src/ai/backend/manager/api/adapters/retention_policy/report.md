## retention_policy

[background](/src/ai/backend/manager/api/adapters/retention_policy/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/retention_policy/adapter.py)

Scenario: complete

- built from ops (8)
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - create: representative success ✓ · representative rejection ✓
  - get: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✓
  - partial_bulk_update: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - search: representative success ✓ · representative rejection ✓
  - update: representative success ✓ · representative rejection ✓

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when one policy exists and the superadmin batch-loads it and one unknown id, they come back in the order asked and the item for the unknown id is empty](#reading-the-superadmin-batch-load-leaves-a-missing-id-empty) | answered |
| [when one policy exists and is batch-loaded without a user context, it is rejected because the caller cannot be known](#reading-a-policy-batch-load-carrying-no-user-is-refused) | rejected |

**create**

| scenario | verdict |
|---|---|
| [when the superadmin creates a policy of the deployments category, the node comes back with that category](#creating-a-policy-for-the-deployments-category-is-made) | answered |
| [when the superadmin creates a policy of the login category, the node comes back with that category](#creating-a-policy-for-the-login-category-is-made) | answered |
| [when the superadmin creates a policy of the logs category, the node comes back with that category](#creating-a-policy-for-the-logs-category-is-made) | answered |
| [when the superadmin creates a policy of the projects category, the node comes back with that category](#creating-a-policy-for-the-projects-category-is-made) | answered |
| [when the superadmin creates a policy of the reconcile_history category, the node comes back with that category](#creating-a-policy-for-the-reconcile-history-category-is-made) | answered |
| [when the superadmin creates a policy of the roles_invitations category, the node comes back with that category](#creating-a-policy-for-the-roles-invitations-category-is-made) | answered |
| [when the superadmin creates a policy of the sessions category, the node comes back with that category](#creating-a-policy-for-the-sessions-category-is-made) | answered |
| [when the superadmin creates a policy of the usage_buckets category, the node comes back with that category](#creating-a-policy-for-the-usage-buckets-category-is-made) | answered |
| [when the superadmin creates a policy of the usage_records category, the node comes back with that category](#creating-a-policy-for-the-usage-records-category-is-made) | answered |
| [creating a policy with enabled false brings back a node that is not enabled](#creating-a-policy-made-inactive-comes-back-inactive) | answered |
| [when the superadmin creates a policy with only a category and retention days, the node comes back with enabled true and an empty last sweep time](#creating-the-superadmin-makes-a-policy-that-is-active-and-never-swept) | answered |
| [when a policy of a category already exists, creating it again for the same category is rejected as a duplicate](#creating-a-second-policy-for-the-same-category-is-refused) | rejected |
| [a user who is not the superadmin creating a policy is rejected for lack of role](#creating-a-user-who-is-not-the-superadmin-may-not-create-a-policy) | rejected |
| [a monitor role creating a policy is rejected for lack of role. A monitor passes the superadmin check for reads only](#creating-the-monitor-may-not-create-a-policy) | rejected |
| [turning permission checks off still does not let a user who is not the superadmin create a policy](#creating-turning-enforcement-off-does-not-let-a-user-create-a-policy) | rejected |

**get**

| scenario | verdict |
|---|---|
| [when one policy exists and the superadmin reads it by id, the whole policy comes back](#reading-the-superadmin-reads-a-policy-by-id) | answered |
| [turning permission checks off lets a user granted nothing read a policy](#reading-turning-enforcement-off-lets-a-user-read-a-policy) | answered |
| [when a user granted nothing reads by id, the call is rejected for lack of permission. Unlike the other catalogs that a read reaches with authentication alone, this read goes through a permission check](#reading-a-user-granted-nothing-may-not-read-a-policy) | rejected |
| [when a user granted nothing reads with an id nothing answers to, the call is rejected for lack of permission, not as not found, because the permission check runs first and no permission is granted on a row that does not exist](#reading-a-user-granted-nothing-reading-an-unknown-policy-id-is-refused-for-permission) | rejected |
| [when the superadmin reads with an id nothing answers to, the call is rejected as not found](#reading-the-superadmin-reading-a-policy-id-nothing-answers-to-is-not-found) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several policies at once, none is deleted and every one comes back in the failed list because the user has no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-policies) | answered |
| [when the superadmin purges two policies and one missing id at once, the two come back in the processed list and the missing id comes back in the failed list because nothing answers to it](#partial_bulk_purging-purging-several-policies-answers-for-the-missing-one) | answered |
| [when two policies exist and are purged at once without a user context, it is rejected because the caller cannot be known](#partial_bulk_purging-a-policy-purge-carrying-no-user-is-refused) | rejected |

**partial_bulk_update**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to edit several policies at once, none is edited and every one comes back in the failed list because the user has no permission](#partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-policies) | answered |
| [when the superadmin changes the retention days of several policies at once, all of them come back with the new days and nothing failed](#partial_bulk_editing-the-superadmin-edits-several-policies-at-once) | answered |
| [when two policies exist and their retention days are changed at once without a user context, it is rejected because the caller cannot be known](#partial_bulk_editing-a-policy-update-carrying-no-user-is-refused) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin purges a policy, the answer carries the id of the policy that was purged](#retiring-the-superadmin-purges-a-policy) | answered |
| [turning permission checks off lets a user granted nothing purge a policy](#retiring-turning-enforcement-off-lets-a-user-purge-a-policy) | answered |
| [when a user granted nothing purges a policy, the call is rejected for lack of permission](#retiring-a-user-granted-nothing-may-not-purge-a-policy) | rejected |
| [when the superadmin purges an id nothing answers to, the call is rejected as not found](#retiring-purging-a-policy-id-nothing-answers-to-is-not-found) | rejected |

**search**

| scenario | verdict |
|---|---|
| [when the call reads with the category of one of several policies of different categories as a filter, only the one policy of that category comes back](#searching-a-category-filter-narrows-the-answer-to-that-category) | answered |
| [when active and inactive policies are mixed and the call reads with the enabled filter, only the active policies come back](#searching-an-enabled-filter-keeps-only-the-active-policies) | answered |
| [when a monitor role reads without a filter, the same answer as for the superadmin comes back. The superadmin check allows reads for a monitor](#searching-the-monitor-searches-policies-like-the-superadmin) | answered |
| [when two policies of different categories exist and the superadmin reads without a filter, both are counted](#searching-the-superadmin-counts-every-policy-laid) | answered |
| [when a user who is not the superadmin asks to read everything, the call is rejected for lack of role](#searching-a-user-who-is-not-the-superadmin-may-not-search-policies) | rejected |

**update**

| scenario | verdict |
|---|---|
| [editing without giving any value brings back a node that changed nothing](#editing-a-policy-edit-giving-no-value-changes-nothing) | answered |
| [turning off the enabled flag of an active policy brings back a node that is not enabled](#editing-disabling-a-policy-answers-it-inactive) | answered |
| [when the superadmin edits only the retention days, the days become the new value and the category and enabled flag stay](#editing-editing-the-retention-days-leaves-the-rest-alone) | answered |
| [turning permission checks off lets a user granted nothing edit a policy](#editing-turning-enforcement-off-lets-a-user-edit-a-policy) | answered |
| [when a user granted nothing edits a policy, the call is rejected for lack of permission](#editing-a-user-granted-nothing-may-not-edit-a-policy) | rejected |
| [when the category of one of two policies is changed to the category of the other, the call is rejected as a duplicate. Unlike at creation, the constraint violation from the repository propagates as it is](#editing-moving-a-policy-to-a-category-already-taken-is-refused) | rejected |
| [when the superadmin edits an id nothing answers to, the call is rejected as not found](#editing-the-superadmin-editing-a-policy-id-nothing-answers-to-is-not-found) | rejected |

### batch_load_by_ids

<a id="reading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py): pass

when one policy exists and the superadmin batch-loads it and one unknown id, they come back in the order asked and the item for the unknown id is empty

Given

- two retention policies of different categories and one superadmin
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.batch_load_by_ids: user-1 batch-loads the policy created in advance and one unknown id

Then

- they come back in the order asked and the item for an unknown id is empty
  - len(items) = 3
  - items[0].id: same as the id of the policy laid
  - items[0].entity_id: same as the id of the policy laid
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - items[1].id: same as the id of the policy laid
  - items[1].entity_id: same as the id of the policy laid
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGIN: 'login'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - items[2] = None

<a id="reading-a-policy-batch-load-carrying-no-user-is-refused"></a>

#### [a-policy-batch-load-carrying-no-user-is-refused](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py): pass

when one policy exists and is batch-loaded without a user context, it is rejected because the caller cannot be known

Given

- two retention policies of different categories and one regular user
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.batch_load_by_ids: batch-loads 2 policies without a user context

Then

- the call is rejected
  - rejected: UnreachableError

### create

<a id="creating-a-policy-for-the-deployments-category-is-made"></a>

#### [a-policy-for-the-deployments-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy of the deployments category, the node comes back with that category

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the deployments category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.DEPLOYMENTS: 'deployments'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-policy-for-the-login-category-is-made"></a>

#### [a-policy-for-the-login-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy of the login category, the node comes back with that category

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the login category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGIN: 'login'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-policy-for-the-logs-category-is-made"></a>

#### [a-policy-for-the-logs-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy of the logs category, the node comes back with that category

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the logs category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-policy-for-the-projects-category-is-made"></a>

#### [a-policy-for-the-projects-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy of the projects category, the node comes back with that category

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the projects category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.PROJECTS: 'projects'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-policy-for-the-reconcile-history-category-is-made"></a>

#### [a-policy-for-the-reconcile-history-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy of the reconcile_history category, the node comes back with that category

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the reconcile_history category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.RECONCILE_HISTORY: 'reconcile_history'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-policy-for-the-roles-invitations-category-is-made"></a>

#### [a-policy-for-the-roles-invitations-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy of the roles_invitations category, the node comes back with that category

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the roles_invitations category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.ROLES_INVITATIONS: 'roles_invitations'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-policy-for-the-sessions-category-is-made"></a>

#### [a-policy-for-the-sessions-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy of the sessions category, the node comes back with that category

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the sessions category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.SESSIONS: 'sessions'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-policy-for-the-usage-buckets-category-is-made"></a>

#### [a-policy-for-the-usage-buckets-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy of the usage_buckets category, the node comes back with that category

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the usage_buckets category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.USAGE_BUCKETS: 'usage_buckets'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-policy-for-the-usage-records-category-is-made"></a>

#### [a-policy-for-the-usage-records-category-is-made](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy of the usage_records category, the node comes back with that category

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the usage_records category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.USAGE_RECORDS: 'usage_records'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-policy-made-inactive-comes-back-inactive"></a>

#### [a-policy-made-inactive-comes-back-inactive](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

creating a policy with enabled false brings back a node that is not enabled

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates an inactive policy for the sessions category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.SESSIONS: 'sessions'>
  - retention_period_days = 90
  - enabled = False
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-the-superadmin-makes-a-policy-that-is-active-and-never-swept"></a>

#### [the-superadmin-makes-a-policy-that-is-active-and-never-swept](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when the superadmin creates a policy with only a category and retention days, the node comes back with enabled true and an empty last sweep time

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the sessions category

Then

- the whole policy just created comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.SESSIONS: 'sessions'>
  - retention_period_days = 90
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="creating-a-second-policy-for-the-same-category-is-refused"></a>

#### [a-second-policy-for-the-same-category-is-refused](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

when a policy of a category already exists, creating it again for the same category is rejected as a duplicate

Given

- one retention policy and one superadmin
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates the policy of the logs category again

Then

- the call is rejected
  - rejected: RetentionPolicyConflict

<a id="creating-a-user-who-is-not-the-superadmin-may-not-create-a-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-create-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

a user who is not the superadmin creating a policy is rejected for lack of role

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the sessions category

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-the-monitor-may-not-create-a-policy"></a>

#### [the-monitor-may-not-create-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

a monitor role creating a policy is rejected for lack of role. A monitor passes the superadmin check for reads only

Given

- one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the sessions category

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="creating-turning-enforcement-off-does-not-let-a-user-create-a-policy"></a>

#### [turning-enforcement-off-does-not-let-a-user-create-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_creating.py): pass

turning permission checks off still does not let a user who is not the superadmin create a policy

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.create: user-1 creates a policy for the sessions category

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### get

<a id="reading-the-superadmin-reads-a-policy-by-id"></a>

#### [the-superadmin-reads-a-policy-by-id](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py): pass

when one policy exists and the superadmin reads it by id, the whole policy comes back

Given

- one retention policy and one superadmin
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.get: user-1 reads the policy of the logs category

Then

- the whole policy seeded in advance comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-turning-enforcement-off-lets-a-user-read-a-policy"></a>

#### [turning-enforcement-off-lets-a-user-read-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py): pass

turning permission checks off lets a user granted nothing read a policy

Given

- one retention policy and one regular user
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.get: user-1 reads the policy of the logs category

Then

- the whole policy seeded in advance comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="reading-a-user-granted-nothing-may-not-read-a-policy"></a>

#### [a-user-granted-nothing-may-not-read-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py): pass

when a user granted nothing reads by id, the call is rejected for lack of permission. Unlike the other catalogs that a read reaches with authentication alone, this read goes through a permission check

Given

- one retention policy and one regular user
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.get: user-1 reads the policy of the logs category

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-a-user-granted-nothing-reading-an-unknown-policy-id-is-refused-for-permission"></a>

#### [a-user-granted-nothing-reading-an-unknown-policy-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py): pass

when a user granted nothing reads with an id nothing answers to, the call is rejected for lack of permission, not as not found, because the permission check runs first and no permission is granted on a row that does not exist

Given

- one retention policy and one regular user
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.get: user-1 reads an id nothing answers to

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="reading-the-superadmin-reading-a-policy-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-reading-a-policy-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/retention_policy/test_reading.py): pass

when the superadmin reads with an id nothing answers to, the call is rejected as not found

Given

- one retention policy and one superadmin
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.get: user-1 reads an id nothing answers to

Then

- the call is rejected
  - rejected: EntityNotFoundError

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-policies"></a>

#### [a-user-granted-nothing-purges-none-of-several-policies](/tests/scenario/bai_scenario/manager/retention_policy/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several policies at once, none is deleted and every one comes back in the failed list because the user has no permission

Given

- two retention policies of different categories and one regular user
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.partial_bulk_purge: user-1 purges 2 policies at once

Then

- no policy is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target policy
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target policy
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-policies-answers-for-the-missing-one"></a>

#### [purging-several-policies-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/retention_policy/test_partial_bulk_purging.py): pass

when the superadmin purges two policies and one missing id at once, the two come back in the processed list and the missing id comes back in the failed list because nothing answers to it

Given

- two retention policies of different categories and one superadmin
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.partial_bulk_purge: user-1 purges 2 policies and one missing id at once

Then

- every target policy comes back in the processed list, and the missing id comes back in the failed list because nothing answers to it
  - successes count = 2
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGIN: 'login'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the missing id put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-a-policy-purge-carrying-no-user-is-refused"></a>

#### [a-policy-purge-carrying-no-user-is-refused](/tests/scenario/bai_scenario/manager/retention_policy/test_partial_bulk_purging.py): pass

when two policies exist and are purged at once without a user context, it is rejected because the caller cannot be known

Given

- two retention policies of different categories and one regular user
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.partial_bulk_purge: purges 2 policies at once without a user context

Then

- the call is rejected
  - rejected: UnreachableError

### partial_bulk_update

<a id="partial_bulk_editing-a-user-granted-nothing-edits-none-of-several-policies"></a>

#### [a-user-granted-nothing-edits-none-of-several-policies](/tests/scenario/bai_scenario/manager/retention_policy/test_partial_bulk_editing.py): pass

when a user granted nothing tries to edit several policies at once, none is edited and every one comes back in the failed list because the user has no permission

Given

- two retention policies of different categories and one regular user
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.partial_bulk_update: user-1 edits the retention days of 2 policies at once

Then

- no policy is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target policy
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target policy
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_editing-the-superadmin-edits-several-policies-at-once"></a>

#### [the-superadmin-edits-several-policies-at-once](/tests/scenario/bai_scenario/manager/retention_policy/test_partial_bulk_editing.py): pass

when the superadmin changes the retention days of several policies at once, all of them come back with the new days and nothing failed

Given

- two retention policies of different categories and one superadmin
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.partial_bulk_update: user-1 edits the retention days of 2 policies at once

Then

- every target policy comes back with the new retention days and nothing failed
  - successes count = 2
  - failed = []
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 180
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGIN: 'login'>
  - retention_period_days = 180
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="partial_bulk_editing-a-policy-update-carrying-no-user-is-refused"></a>

#### [a-policy-update-carrying-no-user-is-refused](/tests/scenario/bai_scenario/manager/retention_policy/test_partial_bulk_editing.py): pass

when two policies exist and their retention days are changed at once without a user context, it is rejected because the caller cannot be known

Given

- two retention policies of different categories and one regular user
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.partial_bulk_update: edits the retention days of 2 policies at once without a user context

Then

- the call is rejected
  - rejected: UnreachableError

### purge

<a id="retiring-the-superadmin-purges-a-policy"></a>

#### [the-superadmin-purges-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py): pass

when the superadmin purges a policy, the answer carries the id of the policy that was purged

Given

- one retention policy and one superadmin
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.purge: user-1 purges the policy of the logs category

Then

- the id of the deleted policy comes back
  - id: same as the policy seeded in advance

<a id="retiring-turning-enforcement-off-lets-a-user-purge-a-policy"></a>

#### [turning-enforcement-off-lets-a-user-purge-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py): pass

turning permission checks off lets a user granted nothing purge a policy

Given

- one retention policy and one regular user
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.purge: user-1 purges the policy of the logs category

Then

- the id of the deleted policy comes back
  - id: same as the policy seeded in advance

<a id="retiring-a-user-granted-nothing-may-not-purge-a-policy"></a>

#### [a-user-granted-nothing-may-not-purge-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py): pass

when a user granted nothing purges a policy, the call is rejected for lack of permission

Given

- one retention policy and one regular user
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.purge: user-1 purges the policy of the logs category

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-purging-a-policy-id-nothing-answers-to-is-not-found"></a>

#### [purging-a-policy-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/retention_policy/test_retiring.py): pass

when the superadmin purges an id nothing answers to, the call is rejected as not found

Given

- one retention policy and one superadmin
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.purge: user-1 purges an id nothing answers to

Then

- the call is rejected
  - rejected: EntityNotFoundError

### search

<a id="searching-a-category-filter-narrows-the-answer-to-that-category"></a>

#### [a-category-filter-narrows-the-answer-to-that-category](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py): pass

when the call reads with the category of one of several policies of different categories as a filter, only the one policy of that category comes back

Given

- two retention policies of different categories and one superadmin
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.search: user-1 reads with the logs category filter

Then

- only the one policy the filter names comes back
  - items = ['logs']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-an-enabled-filter-keeps-only-the-active-policies"></a>

#### [an-enabled-filter-keeps-only-the-active-policies](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py): pass

when active and inactive policies are mixed and the call reads with the enabled filter, only the active policies come back

Given

- one active retention policy, one inactive and one superadmin
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days, inactive
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.search: user-1 reads with the enabled filter

Then

- only the policies that must appear in the response come back
  - items = ['logs']
  - total_count = 1
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-monitor-searches-policies-like-the-superadmin"></a>

#### [the-monitor-searches-policies-like-the-superadmin](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py): pass

when a monitor role reads without a filter, the same answer as for the superadmin comes back. The superadmin check allows reads for a monitor

Given

- two retention policies of different categories and one monitor
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.search: user-1 reads everything without a filter

Then

- only the policies that must appear in the response come back
  - items = ['login', 'logs']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-superadmin-counts-every-policy-laid"></a>

#### [the-superadmin-counts-every-policy-laid](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py): pass

when two policies of different categories exist and the superadmin reads without a filter, both are counted

Given

- two retention policies of different categories and one superadmin
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.search: user-1 reads everything without a filter

Then

- only the policies that must appear in the response come back
  - items = ['login', 'logs']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-policies"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-policies](/tests/scenario/bai_scenario/manager/retention_policy/test_searching.py): pass

when a user who is not the superadmin asks to read everything, the call is rejected for lack of role

Given

- two retention policies of different categories and one regular user
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.search: user-1 reads everything without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### update

<a id="editing-a-policy-edit-giving-no-value-changes-nothing"></a>

#### [a-policy-edit-giving-no-value-changes-nothing](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py): pass

editing without giving any value brings back a node that changed nothing

Given

- one retention policy and one superadmin
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.update: user-1 edits the policy of the logs category without giving a value

Then

- the whole policy seeded in advance comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-disabling-a-policy-answers-it-inactive"></a>

#### [disabling-a-policy-answers-it-inactive](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py): pass

turning off the enabled flag of an active policy brings back a node that is not enabled

Given

- one retention policy and one superadmin
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.update: user-1 edits the enabled flag of the policy of the logs category

Then

- the whole policy seeded in advance comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 30
  - enabled = False
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-editing-the-retention-days-leaves-the-rest-alone"></a>

#### [editing-the-retention-days-leaves-the-rest-alone](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py): pass

when the superadmin edits only the retention days, the days become the new value and the category and enabled flag stay

Given

- one retention policy and one superadmin
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.update: user-1 edits the retention days of the policy of the logs category

Then

- the whole policy seeded in advance comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 180
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-turning-enforcement-off-lets-a-user-edit-a-policy"></a>

#### [turning-enforcement-off-lets-a-user-edit-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py): pass

turning permission checks off lets a user granted nothing edit a policy

Given

- one retention policy and one regular user
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.update: user-1 edits the retention days of the policy of the logs category

Then

- the whole policy seeded in advance comes back
  - id: skipped: the database generates it
  - category = <RetentionCategory.LOGS: 'logs'>
  - retention_period_days = 180
  - enabled = True
  - last_swept_at = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="editing-a-user-granted-nothing-may-not-edit-a-policy"></a>

#### [a-user-granted-nothing-may-not-edit-a-policy](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py): pass

when a user granted nothing edits a policy, the call is rejected for lack of permission

Given

- one retention policy and one regular user
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.update: user-1 edits the retention days of the policy of the logs category

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="editing-moving-a-policy-to-a-category-already-taken-is-refused"></a>

#### [moving-a-policy-to-a-category-already-taken-is-refused](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py): pass

when the category of one of two policies is changed to the category of the other, the call is rejected as a duplicate. Unlike at creation, the constraint violation from the repository propagates as it is

Given

- two retention policies of different categories and one superadmin
  - Retention policy logs: kept for 30 days
  - Retention policy login: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.update: user-1 changes the category of the logs policy to login

Then

- the call is rejected
  - rejected: UniqueConstraintViolationError

<a id="editing-the-superadmin-editing-a-policy-id-nothing-answers-to-is-not-found"></a>

#### [the-superadmin-editing-a-policy-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/retention_policy/test_editing.py): pass

when the superadmin edits an id nothing answers to, the call is rejected as not found

Given

- one retention policy and one superadmin
  - Retention policy logs: kept for 30 days
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- RetentionPolicyAdapter.update: user-1 edits the retention days of an id nothing answers to

Then

- the call is rejected
  - rejected: EntityNotFoundError

