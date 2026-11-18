## login_history

[adapter](/src/ai/backend/manager/api/adapters/login_history/adapter.py)

Scenario: complete

- built from ops (3)
  - admin_search: representative success ✓ · representative rejection ✓
  - batch_load_by_ids: representative success ✓ · representative rejection ✓
  - my_search: representative success ✓ · representative rejection ✓

**admin_search**

| scenario | verdict |
|---|---|
| [when the superadmin calls the search gated by the global role with a filter, an order and a page, the first page of the filtered records comes back in the requested order regardless of the user](#searching-the-superadmin-searches-the-login-history-of-every-user) | answered |
| [when a regular user granted READ on users in the domain scope calls the search gated by the global role, it is rejected](#searching-a-regular-user-may-not-search-the-login-history-of-every-user) | rejected |

**batch_load_by_ids**

| scenario | verdict |
|---|---|
| [when a user granted READ on themselves reads two of their own records by id, whole nodes come back in the requested order](#batch_loading-a-user-granted-read-on-themselves-loads-their-own-records-in-order) | answered |
| [when a user granted READ on themselves reads a record of their own and a record of another user, their own comes back as a whole node and only the other user's item answers with a permission failure](#batch_loading-a-record-of-another-user-is-refused-in-its-own-slot) | rejected |

**my_search**

| scenario | verdict |
|---|---|
| [when a user granted READ on themselves searches with a filter, an order and a page, the first page of their own filtered records comes back in the requested order and the records of other users are left out](#searching-a-user-granted-read-on-themselves-searches-their-own-login-history) | answered |
| [when a user granted nothing searches their own history, it is rejected with a permission failure even for themselves](#searching-a-user-granted-nothing-may-not-search-their-own-login-history) | rejected |

### admin_search

<a id="searching-the-superadmin-searches-the-login-history-of-every-user"></a>

#### [the-superadmin-searches-the-login-history-of-every-user](/tests/scenario/bai_scenario/manager/login_history/test_searching.py): pass

when the superadmin calls the search gated by the global role with a filter, an order and a page, the first page of the filtered records comes back in the requested order regardless of the user

Given

- one domain, one superadmin, and four records left by two users: one success, one blocked, one invalid credentials and one inactive
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
  - regular user user-1: has one login attempt record whose result is success
  - regular user user-1: has one login attempt record whose result is failed_blocked
  - regular user user-2: has one login attempt record whose result is failed_invalid_credentials
  - regular user user-2: has one login attempt record whose result is failed_user_inactive

When

- LoginHistoryAdapter.admin_search: user-3 searches the login history of every user

Then

- only the first page of the filtered records in the requested order comes back, and a next page remains
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False
  - items.length = 2
  - items[0].id: same as the record seeded in advance
  - items[0].field_id: same as the record seeded in advance
  - items[0].user_id: same as the record owner
  - items[0].domain_name = 'home-1'
  - items[0].result = 'failed_blocked'
  - items[0].fail_reason = 'reason of failed_blocked'
  - items[0].client_ip = '203.0.113.10'
  - items[0].created_at: the time this run wrote
  - items[1].id: same as the record seeded in advance
  - items[1].field_id: same as the record seeded in advance
  - items[1].user_id: same as the record owner
  - items[1].domain_name = 'home-1'
  - items[1].result = 'failed_invalid_credentials'
  - items[1].fail_reason = 'reason of failed_invalid_credentials'
  - items[1].client_ip = '203.0.113.10'
  - items[1].created_at: the time this run wrote

<a id="searching-a-regular-user-may-not-search-the-login-history-of-every-user"></a>

#### [a-regular-user-may-not-search-the-login-history-of-every-user](/tests/scenario/bai_scenario/manager/login_history/test_searching.py): pass

when a regular user granted READ on users in the domain scope calls the search gated by the global role, it is rejected

Given

- one domain, one user who left a record, and a regular caller granted the user READ permission in the domain scope
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: has one login attempt record whose result is success
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-2: holds Role user-role-1

When

- LoginHistoryAdapter.admin_search: user-2 searches the login history of every user

Then

- the call is rejected
  - rejected: InsufficientPrivilege

### batch_load_by_ids

<a id="batch_loading-a-user-granted-read-on-themselves-loads-their-own-records-in-order"></a>

#### [a-user-granted-read-on-themselves-loads-their-own-records-in-order](/tests/scenario/bai_scenario/manager/login_history/test_batch_loading.py): pass

when a user granted READ on themselves reads two of their own records by id, whole nodes come back in the requested order

Given

- one domain and two users. The caller holds the READ permission on their own user, and the records are one success and one blocked of the caller, and one success of the other user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: has one login attempt record whose result is success
  - regular user user-1: has one login attempt record whose result is failed_blocked
  - regular user user-2: has one login attempt record whose result is success
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- LoginHistoryAdapter.batch_load_by_ids: user-1 reads 2 records by id at once

Then

- for each item in request order, a whole node or a permission failure comes back
  - length = 2
  - [0].id: same as the record seeded in advance
  - [0].field_id: same as the record seeded in advance
  - [0].user_id: same as the record owner
  - [0].domain_name = 'home-1'
  - [0].result = 'failed_blocked'
  - [0].fail_reason = 'reason of failed_blocked'
  - [0].client_ip = '203.0.113.10'
  - [0].created_at: the time this run wrote
  - [1].id: same as the record seeded in advance
  - [1].field_id: same as the record seeded in advance
  - [1].user_id: same as the record owner
  - [1].domain_name = 'home-1'
  - [1].result = 'success'
  - [1].fail_reason = None
  - [1].client_ip = None
  - [1].created_at: the time this run wrote

<a id="batch_loading-a-record-of-another-user-is-refused-in-its-own-slot"></a>

#### [a-record-of-another-user-is-refused-in-its-own-slot](/tests/scenario/bai_scenario/manager/login_history/test_batch_loading.py): pass

when a user granted READ on themselves reads a record of their own and a record of another user, their own comes back as a whole node and only the other user's item answers with a permission failure

Given

- one domain and two users. The caller holds the READ permission on their own user, and the records are one success and one blocked of the caller, and one success of the other user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: has one login attempt record whose result is success
  - regular user user-1: has one login attempt record whose result is failed_blocked
  - regular user user-2: has one login attempt record whose result is success
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- LoginHistoryAdapter.batch_load_by_ids: user-1 reads 2 records by id at once

Then

- for each item in request order, a whole node or a permission failure comes back
  - length = 2
  - [0].id: same as the record seeded in advance
  - [0].field_id: same as the record seeded in advance
  - [0].user_id: same as the record owner
  - [0].domain_name = 'home-1'
  - [0].result = 'success'
  - [0].fail_reason = None
  - [0].client_ip = None
  - [0].created_at: the time this run wrote
  - rejected: NotEnoughPermission

### my_search

<a id="searching-a-user-granted-read-on-themselves-searches-their-own-login-history"></a>

#### [a-user-granted-read-on-themselves-searches-their-own-login-history](/tests/scenario/bai_scenario/manager/login_history/test_searching.py): pass

when a user granted READ on themselves searches with a filter, an order and a page, the first page of their own filtered records comes back in the requested order and the records of other users are left out

Given

- one domain and two users: four records of the caller (success, blocked, invalid credentials, inactive), one invalid credentials record of the other user, and the caller holds the READ permission on their own user
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: has one login attempt record whose result is success
  - regular user user-1: has one login attempt record whose result is failed_blocked
  - regular user user-1: has one login attempt record whose result is failed_invalid_credentials
  - regular user user-1: has one login attempt record whose result is failed_user_inactive
  - regular user user-2: has one login attempt record whose result is failed_invalid_credentials
  - a role assignment granting the user the READ permissions
    - Role user-role-1: applies only within the scope it is granted in
    - Role user-role-1: READ allowed on every user
    - regular user user-1: holds Role user-role-1

When

- LoginHistoryAdapter.my_search: user-1 searches their own login history

Then

- only the first page of the filtered records in the requested order comes back, and a next page remains
  - total_count = 3
  - has_next_page = True
  - has_previous_page = False
  - items.length = 2
  - items[0].id: same as the record seeded in advance
  - items[0].field_id: same as the record seeded in advance
  - items[0].user_id: same as the record owner
  - items[0].domain_name = 'home-1'
  - items[0].result = 'failed_blocked'
  - items[0].fail_reason = 'reason of failed_blocked'
  - items[0].client_ip = '203.0.113.10'
  - items[0].created_at: the time this run wrote
  - items[1].id: same as the record seeded in advance
  - items[1].field_id: same as the record seeded in advance
  - items[1].user_id: same as the record owner
  - items[1].domain_name = 'home-1'
  - items[1].result = 'failed_invalid_credentials'
  - items[1].fail_reason = 'reason of failed_invalid_credentials'
  - items[1].client_ip = '203.0.113.10'
  - items[1].created_at: the time this run wrote

<a id="searching-a-user-granted-nothing-may-not-search-their-own-login-history"></a>

#### [a-user-granted-nothing-may-not-search-their-own-login-history](/tests/scenario/bai_scenario/manager/login_history/test_searching.py): pass

when a user granted nothing searches their own history, it is rejected with a permission failure even for themselves

Given

- one domain and two users: four records of the caller (success, blocked, invalid credentials, inactive), one invalid credentials record of the other user, and the caller holds no permission
  - Domain home-1
  - Prepare one user in the domain
    - Project resource policy default: the personal project created along with a user looks it up by this name
    - User resource policy user-policy-1: up to 10 folders per user
    - Keypair policy keypair-policy-1: up to 5 concurrent sessions
    - regular user user-1: has their own keypair and personal project
    - User resource policy user-policy-2: up to 10 folders per user
    - Keypair policy keypair-policy-2: up to 5 concurrent sessions
    - regular user user-2: has their own keypair and personal project
  - regular user user-1: has one login attempt record whose result is success
  - regular user user-1: has one login attempt record whose result is failed_blocked
  - regular user user-1: has one login attempt record whose result is failed_invalid_credentials
  - regular user user-1: has one login attempt record whose result is failed_user_inactive
  - regular user user-2: has one login attempt record whose result is failed_invalid_credentials

When

- LoginHistoryAdapter.my_search: user-1 searches their own login history

Then

- the call is rejected
  - rejected: NotEnoughPermission

