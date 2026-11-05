## client_ip_masking

[background](/src/ai/backend/manager/api/adapters/client_ip_masking/KNOWLEDGE.md) · [adapter](/src/ai/backend/manager/api/adapters/client_ip_masking/adapter.py)

Scenario: complete

- built from ops (5)
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - partial_bulk_purge: representative success ✓ · representative rejection ✓
  - purge: representative success ✓ · representative rejection ✓
  - upsert: representative success ✓ · representative rejection ✓

**admin_search**

| scenario | verdict |
|---|---|
| [when the monitor role reads without a filter, the same response as the superadmin comes back. The superadmin check allows the monitor's read](#searching-the-monitor-searches-masking-policies-like-the-superadmin) | answered |
| [when two policies of different targets exist and the superadmin reads without a filter, both are counted](#searching-the-superadmin-counts-every-masking-policy-laid) | answered |
| [when a user who is not the superadmin requests a read of everything, it is rejected because the role is insufficient](#searching-a-user-who-is-not-the-superadmin-may-not-search-masking-policies) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when the superadmin batch-loads two policies created in advance and one unknown id, they come back in the order asked and the item for the unknown id is empty](#reading-the-superadmin-batch-load-leaves-a-missing-id-empty) | answered |
| [when two policies exist and they are batch-loaded without a user context, it is rejected because the caller cannot be known](#reading-a-batch-load-carrying-no-user-is-refused) | rejected |

**partial_bulk_purge**

| scenario | verdict |
|---|---|
| [when a user granted nothing tries to purge several policies at once, nothing is purged and every one comes back in the failed list because there is no permission](#partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-masking-policies) | answered |
| [when the superadmin purges two policies and an unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it](#partial_bulk_purging-purging-several-masking-policies-answers-for-the-missing-one) | answered |
| [when two policies exist and are purged at once without a user context, it is rejected because the caller cannot be known](#partial_bulk_purging-a-policy-purge-carrying-no-user-is-refused) | rejected |

**purge**

| scenario | verdict |
|---|---|
| [when the superadmin deletes a policy by id, a response comes back carrying the whole deleted policy](#retiring-the-superadmin-purges-a-masking-policy) | answered |
| [turning permission enforcement off lets even a user granted nothing delete a policy](#retiring-turning-enforcement-off-lets-a-user-purge-a-masking-policy) | answered |
| [when a user granted nothing deletes a policy, it is rejected for a lack of permission. This is a different check from the registration rejected for an insufficient role](#retiring-a-user-granted-nothing-may-not-purge-a-masking-policy) | rejected |
| [when a user granted nothing deletes an id nothing answers to, it is rejected for a lack of permission rather than a missing target, because the permission check runs first and no permission is granted on a row that does not exist](#retiring-a-user-granted-nothing-purging-an-unknown-masking-policy-id-is-refused-for-permission) | rejected |
| [when the superadmin deletes an id nothing answers to, it is rejected because the target cannot be found](#retiring-purging-a-masking-policy-id-nothing-answers-to-is-not-found) | rejected |

**upsert**

| scenario | verdict |
|---|---|
| [when it is registered with only a target and a mode, the node comes back with both prefix lengths empty](#upserting-a-masking-policy-put-without-prefixes-carries-empty-prefixes) | answered |
| [when a policy with prefix lengths is registered again on its target with only a target and a mode, the prefix lengths are cleared. Registration does not merge with the existing values but changes the row as a whole](#upserting-putting-a-policy-again-without-prefixes-clears-the-stored-prefixes) | answered |
| [when a policy is registered on a target that already has one in a different mode, the node comes back with the row of the same id changed to the new mode rather than a new row](#upserting-putting-a-policy-on-a-target-that-has-one-rewrites-the-same-row) | answered |
| [when no policy exists and the superadmin registers one with a target, a mode and two prefix lengths, the node comes back carrying the given values](#upserting-the-superadmin-puts-a-masking-policy-on-a-target) | answered |
| [when a user who is not the superadmin registers a policy, it is rejected because the role is insufficient](#upserting-a-user-who-is-not-the-superadmin-may-not-put-a-masking-policy) | rejected |
| [when the monitor role registers a policy, it is rejected because the role is insufficient. The monitor passes only reads in the superadmin check](#upserting-the-monitor-may-not-put-a-masking-policy) | rejected |
| [turning permission enforcement off still does not let a user who is not the superadmin register a policy](#upserting-turning-enforcement-off-does-not-let-a-user-put-a-masking-policy) | rejected |

### admin_search

<a id="searching-the-monitor-searches-masking-policies-like-the-superadmin"></a>

#### [the-monitor-searches-masking-policies-like-the-superadmin](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py): pass

when the monitor role reads without a filter, the same response as the superadmin comes back. The superadmin check allows the monitor's read

Given

- two client IP masking policies of different targets and one monitor
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - client IP masking policy login_history: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.admin_search: user-1 reads every masking policy without a filter

Then

- only the policies that must appear in the answer come back
  - items = ['default', 'login_history']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-the-superadmin-counts-every-masking-policy-laid"></a>

#### [the-superadmin-counts-every-masking-policy-laid](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py): pass

when two policies of different targets exist and the superadmin reads without a filter, both are counted

Given

- two client IP masking policies of different targets and one superadmin
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - client IP masking policy login_history: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.admin_search: user-1 reads every masking policy without a filter

Then

- only the policies that must appear in the answer come back
  - items = ['default', 'login_history']
  - total_count = 2
  - has_next_page = False
  - has_previous_page = False

<a id="searching-a-user-who-is-not-the-superadmin-may-not-search-masking-policies"></a>

#### [a-user-who-is-not-the-superadmin-may-not-search-masking-policies](/tests/scenario/bai_scenario/manager/client_ip_masking/test_searching.py): pass

when a user who is not the superadmin requests a read of everything, it is rejected because the role is insufficient

Given

- two client IP masking policies of different targets and one regular user
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - client IP masking policy login_history: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.admin_search: user-1 reads every masking policy without a filter

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="reading-the-superadmin-batch-load-leaves-a-missing-id-empty"></a>

#### [the-superadmin-batch-load-leaves-a-missing-id-empty](/tests/scenario/bai_scenario/manager/client_ip_masking/test_reading.py): pass

when the superadmin batch-loads two policies created in advance and one unknown id, they come back in the order asked and the item for the unknown id is empty

Given

- two client IP masking policies of different targets and one superadmin
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - client IP masking policy login_history: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.batch_load_by_ids: user-1 batch-loads the 2 policies created in advance and one unknown id

Then

- they come back in the order asked and the item for an unknown id is empty
  - len(items) = 3
  - items[0].id: same as the policy created in advance
  - items[0].entity_id: same as the policy created in advance
  - items[0].target_type = 'default'
  - items[0].mode = 'truncate'
  - items[0].ipv4_prefix = 24
  - items[0].ipv6_prefix = 48
  - items[0].created_at: the time this run wrote
  - items[0].updated_at: the time this run wrote
  - items[1].id: same as the policy created in advance
  - items[1].entity_id: same as the policy created in advance
  - items[1].target_type = 'login_history'
  - items[1].mode = 'truncate'
  - items[1].ipv4_prefix = 24
  - items[1].ipv6_prefix = 48
  - items[1].created_at: the time this run wrote
  - items[1].updated_at: the time this run wrote
  - items[2] = None

<a id="reading-a-batch-load-carrying-no-user-is-refused"></a>

#### [a-batch-load-carrying-no-user-is-refused](/tests/scenario/bai_scenario/manager/client_ip_masking/test_reading.py): pass

when two policies exist and they are batch-loaded without a user context, it is rejected because the caller cannot be known

Given

- two client IP masking policies of different targets and one regular user
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - client IP masking policy login_history: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.batch_load_by_ids: batch-loads 2 policies without a user context

Then

- the call is rejected
  - rejected: UnreachableError

### partial_bulk_purge

<a id="partial_bulk_purging-a-user-granted-nothing-purges-none-of-several-masking-policies"></a>

#### [a-user-granted-nothing-purges-none-of-several-masking-policies](/tests/scenario/bai_scenario/manager/client_ip_masking/test_partial_bulk_purging.py): pass

when a user granted nothing tries to purge several policies at once, nothing is purged and every one comes back in the failed list because there is no permission

Given

- two client IP masking policies of different targets and one regular user
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - client IP masking policy login_history: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.partial_bulk_purge: user-1 purges 2 client IP masking policies at once

Then

- no policy is processed and every target comes back in the failed list
  - successes = []
  - failed count = 2
  - failed[0].id: same as the id of the target policy
  - failed[0].message: a reason containing 'Insufficient permission'
  - failed[1].id: same as the id of the target policy
  - failed[1].message: a reason containing 'Insufficient permission'

<a id="partial_bulk_purging-purging-several-masking-policies-answers-for-the-missing-one"></a>

#### [purging-several-masking-policies-answers-for-the-missing-one](/tests/scenario/bai_scenario/manager/client_ip_masking/test_partial_bulk_purging.py): pass

when the superadmin purges two policies and an unknown id at once, the two come back in the processed list and the unknown id comes back in the failed list because no target answers to it

Given

- two client IP masking policies of different targets and one superadmin
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - client IP masking policy login_history: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.partial_bulk_purge: user-1 purges 2 client IP masking policies and one unknown id at once

Then

- every policy comes back in the processed list and the unknown id comes back in the failed list because no target answers to it
  - successes count = 2
  - id: same as the policy made in advance
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - id: same as the policy made in advance
  - target_type = 'login_history'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: the time this run wrote
  - updated_at: the time this run wrote
  - failed count = 1
  - failed[0].id: same as the unknown id put in the request
  - failed[0].message: a reason containing 'not found'

<a id="partial_bulk_purging-a-policy-purge-carrying-no-user-is-refused"></a>

#### [a-policy-purge-carrying-no-user-is-refused](/tests/scenario/bai_scenario/manager/client_ip_masking/test_partial_bulk_purging.py): pass

when two policies exist and are purged at once without a user context, it is rejected because the caller cannot be known

Given

- two client IP masking policies of different targets and one regular user
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - client IP masking policy login_history: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.partial_bulk_purge: purges 2 policies at once without a user context

Then

- the call is rejected
  - rejected: UnreachableError

### purge

<a id="retiring-the-superadmin-purges-a-masking-policy"></a>

#### [the-superadmin-purges-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

when the superadmin deletes a policy by id, a response comes back carrying the whole deleted policy

Given

- one client IP masking policy and one superadmin
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.purge: user-1 deletes the policy for default

Then

- the whole deleted policy comes back
  - id: same as the policy made in advance
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="retiring-turning-enforcement-off-lets-a-user-purge-a-masking-policy"></a>

#### [turning-enforcement-off-lets-a-user-purge-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

turning permission enforcement off lets even a user granted nothing delete a policy

Given

- one client IP masking policy and one regular user
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.purge: user-1 deletes the policy for default

Then

- the whole deleted policy comes back
  - id: same as the policy made in advance
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="retiring-a-user-granted-nothing-may-not-purge-a-masking-policy"></a>

#### [a-user-granted-nothing-may-not-purge-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

when a user granted nothing deletes a policy, it is rejected for a lack of permission. This is a different check from the registration rejected for an insufficient role

Given

- one client IP masking policy and one regular user
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.purge: user-1 deletes the policy for default

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-a-user-granted-nothing-purging-an-unknown-masking-policy-id-is-refused-for-permission"></a>

#### [a-user-granted-nothing-purging-an-unknown-masking-policy-id-is-refused-for-permission](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

when a user granted nothing deletes an id nothing answers to, it is rejected for a lack of permission rather than a missing target, because the permission check runs first and no permission is granted on a row that does not exist

Given

- one client IP masking policy and one regular user
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.purge: user-1 deletes an id nothing answers to

Then

- the call is rejected
  - rejected: NotEnoughPermission

<a id="retiring-purging-a-masking-policy-id-nothing-answers-to-is-not-found"></a>

#### [purging-a-masking-policy-id-nothing-answers-to-is-not-found](/tests/scenario/bai_scenario/manager/client_ip_masking/test_retiring.py): pass

when the superadmin deletes an id nothing answers to, it is rejected because the target cannot be found

Given

- one client IP masking policy and one superadmin
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.purge: user-1 deletes an id nothing answers to

Then

- the call is rejected
  - rejected: EntityNotFoundError

### upsert

<a id="upserting-a-masking-policy-put-without-prefixes-carries-empty-prefixes"></a>

#### [a-masking-policy-put-without-prefixes-carries-empty-prefixes](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

when it is registered with only a target and a mode, the node comes back with both prefix lengths empty

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.upsert: user-1 registers a truncate mode policy on the default target

Then

- the whole registered policy comes back
  - id: skipped: the database generates it
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = None
  - ipv6_prefix = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="upserting-putting-a-policy-again-without-prefixes-clears-the-stored-prefixes"></a>

#### [putting-a-policy-again-without-prefixes-clears-the-stored-prefixes](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

when a policy with prefix lengths is registered again on its target with only a target and a mode, the prefix lengths are cleared. Registration does not merge with the existing values but changes the row as a whole

Given

- one client IP masking policy and one superadmin
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.upsert: user-1 registers a truncate mode policy on the default target again

Then

- the row with the same id comes back changed to the given values
  - id: same as the policy made in advance
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = None
  - ipv6_prefix = None
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="upserting-putting-a-policy-on-a-target-that-has-one-rewrites-the-same-row"></a>

#### [putting-a-policy-on-a-target-that-has-one-rewrites-the-same-row](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

when a policy is registered on a target that already has one in a different mode, the node comes back with the row of the same id changed to the new mode rather than a new row

Given

- one client IP masking policy and one superadmin
  - client IP masking policy default: truncate mode, prefix length v4 24, v6 48
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.upsert: user-1 registers a drop mode policy on the default target again with prefix lengths

Then

- the row with the same id comes back changed to the given values
  - id: same as the policy made in advance
  - target_type = 'default'
  - mode = 'drop'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="upserting-the-superadmin-puts-a-masking-policy-on-a-target"></a>

#### [the-superadmin-puts-a-masking-policy-on-a-target](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

when no policy exists and the superadmin registers one with a target, a mode and two prefix lengths, the node comes back carrying the given values

Given

- one superadmin
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - superadmin user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.upsert: user-1 registers a truncate mode policy on the default target with prefix lengths

Then

- the whole registered policy comes back
  - id: skipped: the database generates it
  - target_type = 'default'
  - mode = 'truncate'
  - ipv4_prefix = 24
  - ipv6_prefix = 48
  - created_at: the time this run wrote
  - updated_at: the time this run wrote

<a id="upserting-a-user-who-is-not-the-superadmin-may-not-put-a-masking-policy"></a>

#### [a-user-who-is-not-the-superadmin-may-not-put-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

when a user who is not the superadmin registers a policy, it is rejected because the role is insufficient

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.upsert: user-1 registers a truncate mode policy on the default target with prefix lengths

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="upserting-the-monitor-may-not-put-a-masking-policy"></a>

#### [the-monitor-may-not-put-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

when the monitor role registers a policy, it is rejected because the role is insufficient. The monitor passes only reads in the superadmin check

Given

- one monitor
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - monitor user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.upsert: user-1 registers a truncate mode policy on the default target with prefix lengths

Then

- the call is rejected
  - rejected: InsufficientPrivilege

<a id="upserting-turning-enforcement-off-does-not-let-a-user-put-a-masking-policy"></a>

#### [turning-enforcement-off-does-not-let-a-user-put-a-masking-policy](/tests/scenario/bai_scenario/manager/client_ip_masking/test_upserting.py): pass

turning permission enforcement off still does not let a user who is not the superadmin register a policy

Given

- one regular user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project

When

- ClientIPMaskingAdapter.upsert: user-1 registers a truncate mode policy on the default target with prefix lengths

Then

- the call is rejected
  - rejected: InsufficientPrivilege

